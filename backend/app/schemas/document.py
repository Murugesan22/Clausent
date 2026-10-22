from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    file_type: str
    file_size_bytes: int
    upload_timestamp: datetime
    message: str

class DocumentMetadataResponse(BaseModel):
    id: str
    filename: str
    original_name: str
    file_type: str
    file_size_bytes: int
    upload_timestamp: datetime
    detected_language: Optional[str] = None
    language_confidence: Optional[float] = None
    status: str
    error_message: Optional[str] = None
    character_count: Optional[int] = None
    preview_text: Optional[str] = None

class DocumentListItem(BaseModel):
    id: str
    filename: str
    upload_date: str
    language: str
    overall_risk: str
    flagged_clauses: int
    status: str
    total_clauses: int
