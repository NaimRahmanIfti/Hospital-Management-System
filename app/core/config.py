# app/core/config.py

# pydantic_settings gives us BaseSettings — a special class that
# reads values from environment variables or a .env file automatically
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Central config for the entire app.
    Every setting has a TYPE (str, int, bool) — Pydantic enforces this.
    If DATABASE_URL is missing from .env, Pydantic raises an error immediately
    instead of letting a bug hide until runtime.
    """

    # ── App info ─────────────────────────────────────────────────────
    APP_NAME: str = "Hospital Management System"
    # DEBUG=True means SQLAlchemy will print every SQL query to the terminal.
    # This is incredibly useful while learning — you see exactly what query
    # your Python code generates. Set to False in production.
    DEBUG: bool = True

    # ── Database ─────────────────────────────────────────────────────
    # This is the PostgreSQL connection string. The format is:
    # postgresql://USERNAME:PASSWORD@HOST:PORT/DATABASE_NAME
    #
    # When Docker is running (docker-compose), the HOST is the service
    # name ("db"), not localhost. We set this in .env so it's easy to swap.
    DATABASE_URL: str ="sqlite:///./hms_dev.db"

    # ── Security / JWT ────────────────────────────────────────────────
    # SECRET_KEY is used to sign JWT tokens. Think of it as a private stamp.
    # Anyone with this key can forge tokens, so keep it secret.
    SECRET_KEY: str = "dev-secret-change-in-production"
    # HS256 = HMAC-SHA256 — the algorithm used to sign/verify JWT tokens.
    # It's the industry standard for simple stateless auth.
    ALGORITHM: str = "HS256"

    # How long until a login token expires. 30 minutes is standard.
    # After this, the user must log in again.
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # ── File storage (AWS S3) ─────────────────────────────────────────
    # STORAGE_BACKEND picks WHERE uploaded files (lab reports, scans) go:
    #   "local" → a folder on disk. Good for development, no AWS needed.
    #   "s3"    → an Amazon S3 bucket. Used in production on AWS.
    # The rest of the code never checks this value itself — it asks
    # app/core/storage.py for "the storage", and gets the right one.
    STORAGE_BACKEND: str = "local"
    LOCAL_STORAGE_DIR: str = "./uploads"

    # Which AWS data center region to use. us-west-1 = N. California.
    AWS_REGION: str = "us-west-1"
    # The bucket name is created by Terraform later (Phase 2).
    S3_BUCKET_NAME: str = ""
    # How long a download link stays valid. 5 minutes: long enough to
    # click, short enough that a leaked link soon becomes useless.
    S3_PRESIGNED_URL_EXPIRE_SECONDS: int = 300

    # NOTICE: there is NO AWS_ACCESS_KEY / AWS_SECRET_KEY here.
    # boto3 finds credentials by itself (the "credential chain"):
    #   on your laptop → ~/.aws/credentials (from `aws configure`)
    #   on AWS (ECS)   → the IAM role attached to the container
    # Keys never live in code or .env. That is the AWS best practice.

    # Upload rules. Medical files can be large, but not unlimited.
    MAX_UPLOAD_MB: int = 10

    class Config:
        # Tells Pydantic: "read from this file if environment variables
        # aren't set directly". This is how local development works.
        env_file = ".env"
        case_sensitive = True


# We create ONE instance here.
# Every other file does: from app.core.config import settings
# They all share this same object — not creating new ones each time.
# This is the Singleton pattern.
settings = Settings()