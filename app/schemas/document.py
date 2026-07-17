from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class Document(BaseModel):
    id: UUID
    filename: str
    title: str | None = None
    doc_metadata: dict = {}
    chunk_count: int = 0
    status: str = "processing"
    error: str | None = None
    created_at: datetime
    updated_at: datetime


class DocumentCreate(BaseModel):
    filename: str
    title: str | None = None


class DocumentUploadResponse(BaseModel):
    document_id: UUID
    filename: str
    chunk_count: int
    status: str
