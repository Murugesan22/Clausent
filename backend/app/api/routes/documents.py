import os
from pathlib import Path
from typing import List
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.repositories import DocumentRepository, AnalysisRepository
from app.schemas.document import DocumentUploadResponse, DocumentMetadataResponse, DocumentListItem
from app.services.document_service import DocumentService
from app.core.exceptions import DocumentValidationError
from app.core.logging_config import logger

router = APIRouter(prefix="/documents", tags=["Documents"])

@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Validates and stores a contract document (PDF, DOCX, TXT).
    """
    try:
        doc = DocumentService.save_upload(file, db)
        return DocumentUploadResponse(
            document_id=doc.id,
            filename=doc.original_name,
            file_type=doc.file_type,
            file_size_bytes=doc.file_size_bytes,
            upload_timestamp=doc.upload_timestamp,
            message="Document uploaded and validated successfully."
        )
    except DocumentValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        logger.error(f"Upload failed: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to process document upload.")

@router.get("", response_model=List[DocumentListItem])
def list_documents(db: Session = Depends(get_db)):
    """
    Lists previously uploaded documents and summary analysis status.
    """
    docs = DocumentRepository.list_all(db)
    items = []
    for d in docs:
        latest_analysis = AnalysisRepository.get_latest_for_document(db, d.id)
        overall_risk = latest_analysis.overall_risk_level if latest_analysis else "unprocessed"
        flagged = (latest_analysis.high_risk_count + latest_analysis.medium_risk_count) if latest_analysis else 0
        total_c = latest_analysis.total_clauses if latest_analysis else 0
        stat = latest_analysis.status.capitalize() if latest_analysis else "Uploaded"

        items.append(DocumentListItem(
            id=d.id,
            filename=d.original_name,
            upload_date=d.upload_timestamp.strftime("%Y-%m-%d"),
            language=d.detected_language or "English",
            overall_risk=overall_risk,
            flagged_clauses=flagged,
            status=stat,
            total_clauses=total_c
        ))
    return items

@router.get("/{document_id}", response_model=DocumentMetadataResponse)
def get_document_metadata(document_id: str, db: Session = Depends(get_db)):
    """
    Returns document details and text preview.
    """
    doc = DocumentRepository.get_by_id(db, document_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    preview = (doc.extracted_text[:400] + "...") if doc.extracted_text else None
    return DocumentMetadataResponse(
        id=doc.id,
        filename=doc.filename,
        original_name=doc.original_name,
        file_type=doc.file_type,
        file_size_bytes=doc.file_size_bytes,
        upload_timestamp=doc.upload_timestamp,
        detected_language=doc.detected_language,
        language_confidence=doc.language_confidence,
        status=doc.status,
        error_message=doc.error_message,
        character_count=len(doc.extracted_text) if doc.extracted_text else 0,
        preview_text=preview
    )

@router.delete("/{document_id}", status_code=status.HTTP_200_OK)
def delete_document(document_id: str, db: Session = Depends(get_db)):
    """
    Deletes the document file and all associated database records.
    """
    doc = DocumentRepository.get_by_id(db, document_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    # Delete local file
    try:
        if doc.storage_path and os.path.exists(doc.storage_path):
            os.remove(doc.storage_path)
    except Exception as e:
        logger.warning(f"Failed to delete file from disk: {e}")

    DocumentRepository.delete(db, document_id)
    return {"message": "Document and associated analysis records deleted successfully."}
