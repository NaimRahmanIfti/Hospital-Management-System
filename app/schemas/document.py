# app/schemas/document.py
#
# Schemas = the API's shape (what JSON goes out). Model = the DB's shape.
# Notice storage_key is NOT in the response: clients never need to know
# where/how we store the file. They ask the API for a download link.

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class DocumentResponse(BaseModel):
    # from_attributes=True → Pydantic can read a SQLAlchemy object
    # (document.id, document.patient_id...) instead of needing a dict.
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    medical_record_id: Optional[int] = None
    uploaded_by_id: int
    original_filename: str
    content_type: str
    size_bytes: int
    description: Optional[str] = None
    created_at: Optional[datetime] = None


class DownloadLink(BaseModel):
    url: str            # S3 presigned URL (prod) or API path (local dev)
    expires_in: int     # seconds until the link stops working
