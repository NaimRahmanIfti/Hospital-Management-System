# app/core/storage.py
#
# WHY THIS FILE EXISTS
# ────────────────────
# Hospitals have FILES: lab reports (PDF), X-ray images, scanned prescriptions.
# Files do NOT belong in the database (a 5 MB PDF in a Postgres row makes
# backups huge and queries slow). The database stores only a small "pointer"
# (the key). The file itself lives in file storage.
#
# In production that storage is Amazon S3:
#   - virtually unlimited space, you pay per GB (~$0.023/GB/month)
#   - designed for 99.999999999% (11 nines) durability: files are copied
#     across several data centers automatically
#   - encryption at rest, private by default
#
# THE DESIGN: Strategy pattern (same idea as your BaseService ABC)
#
#        StorageBackend  (abstract — "what any storage must be able to do")
#          ▲         ▲
#          │         │
#   LocalStorage   S3Storage
#   (dev laptop)   (AWS production)
#
# Routers call get_storage() and use the interface. They never know whether
# the file goes to disk or to S3. To switch, you change ONE env variable:
#   STORAGE_BACKEND=s3
# This is the Dependency Inversion Principle: depend on the abstraction.

from abc import ABC, abstractmethod
from functools import lru_cache
from pathlib import Path
from typing import Optional

from app.core.config import settings


class StorageBackend(ABC):
    """The contract every storage backend must follow."""

    @abstractmethod
    def save(self, key: str, data: bytes, content_type: str) -> None:
        """Store `data` under the name `key`."""

    @abstractmethod
    def load(self, key: str) -> bytes:
        """Return the bytes stored under `key`."""

    @abstractmethod
    def delete(self, key: str) -> None:
        """Remove the file stored under `key` (no error if missing)."""

    @abstractmethod
    def get_download_url(self, key: str, filename: str) -> Optional[str]:
        """
        Return a temporary URL the browser can download from directly,
        or None if this backend can't do that (then the API streams the file).
        """


# ── 1. Local disk (development) ───────────────────────────────────
class LocalStorage(StorageBackend):
    """Saves files in a folder. No AWS account needed."""

    def __init__(self, base_dir: str):
        self._base = Path(base_dir).resolve()
        self._base.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        # SECURITY: a key like "../../etc/passwd" must not escape the folder.
        # resolve() turns the path into its real absolute form, then we check
        # it is still inside base_dir. (This attack is called "path traversal".)
        path = (self._base / key).resolve()
        if not path.is_relative_to(self._base):
            raise ValueError("Invalid storage key")
        return path

    def save(self, key: str, data: bytes, content_type: str) -> None:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def load(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def delete(self, key: str) -> None:
        self._path(key).unlink(missing_ok=True)

    def get_download_url(self, key: str, filename: str) -> Optional[str]:
        return None  # a disk folder can't hand out URLs; the API streams instead


# ── 2. Amazon S3 (production) ─────────────────────────────────────
def make_s3_client(region: str):
    """
    Build a boto3 S3 client the right way.

    No keys are passed: boto3 uses the credential chain (see config.py).

    signature_version="s3v4": presigned URLs must use Signature Version 4.
    Without this, boto3 may produce old SigV2 links, which newer regions
    reject and AWS is retiring. (Our test suite caught exactly this bug.)
    """
    import boto3  # imported here so local dev doesn't need AWS set up
    from botocore.config import Config

    return boto3.client(
        "s3",
        region_name=region,
        config=Config(signature_version="s3v4", retries={"max_attempts": 3, "mode": "standard"}),
    )



class S3Storage(StorageBackend):
    """
    Stores files in an S3 bucket using boto3 (the official AWS SDK for Python).

    S3 vocabulary:
      bucket = a top-level container (like a drive), name is globally unique
      key    = the file's full name inside the bucket, e.g.
               "patients/42/3f9a...c1.pdf". The "/" just looks like folders.
      object = the file (bytes + metadata) stored at a key
    """

    def __init__(self, bucket: str, region: str, client=None):
        if not bucket:
            raise ValueError("S3_BUCKET_NAME must be set when STORAGE_BACKEND=s3")
        self._bucket = bucket
        self._s3 = client or make_s3_client(region)

    def save(self, key: str, data: bytes, content_type: str) -> None:
        self._s3.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
            # Encrypt the file at rest with keys AWS manages (SSE-S3).
            # Medical data (PHI) must be encrypted: a HIPAA expectation.
            # The bucket also enforces this by default; being explicit
            # documents the intent and protects against a misconfigured bucket.
            ServerSideEncryption="AES256",
        )

    def load(self, key: str) -> bytes:
        response = self._s3.get_object(Bucket=self._bucket, Key=key)
        return response["Body"].read()

    def delete(self, key: str) -> None:
        # S3 delete is idempotent: deleting a missing key is not an error.
        self._s3.delete_object(Bucket=self._bucket, Key=key)

    def get_download_url(self, key: str, filename: str) -> Optional[str]:
        # A PRESIGNED URL is a normal https link with a cryptographic
        # signature in the query string. It works:
        #   - only for THIS one object
        #   - only for GET (download, not upload or delete)
        #   - only until it expires (300 seconds by default)
        # So the bucket stays 100% private, but our API can grant
        # one-time access after checking the user may see this file.
        # Bonus: the browser downloads straight from S3, so big files
        # don't pass through (and slow down) our FastAPI server.
        safe_name = filename.replace('"', "")
        return self._s3.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": self._bucket,
                "Key": key,
                # Makes the browser save it with the original filename.
                "ResponseContentDisposition": f'attachment; filename="{safe_name}"',
            },
            ExpiresIn=settings.S3_PRESIGNED_URL_EXPIRE_SECONDS,
        )


# ── Factory ───────────────────────────────────────────────────────
# @lru_cache makes this return the SAME object every call (a singleton),
# so we create the boto3 client once, not on every request.
@lru_cache
def get_storage() -> StorageBackend:
    if settings.STORAGE_BACKEND == "s3":
        return S3Storage(bucket=settings.S3_BUCKET_NAME, region=settings.AWS_REGION)
    return LocalStorage(settings.LOCAL_STORAGE_DIR)
