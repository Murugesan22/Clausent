from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.repositories import AnalysisRepository, DocumentRepository, ClauseRepository
from app.services.report_service import ReportService
from app.core.logging_config import logger

router = APIRouter(prefix="/reports", tags=["Reports"])

def _build_analysis_dict(job, doc, clauses) -> dict:
    return {
        "analysis_id": job.id,
        "document_id": job.document_id,
        "filename": doc.original_name if doc else "Contract",
        "detected_language": doc.detected_language if doc else "English",
        "target_language": job.target_language,
        "overall_risk_score": job.overall_risk_score,
        "overall_risk_level": job.overall_risk_level,
        "high_risk_count": job.high_risk_count,
        "medium_risk_count": job.medium_risk_count,
        "low_risk_count": job.low_risk_count,
        "total_clauses": job.total_clauses,
        "executive_summary": job.executive_summary,
        "suggested_review_areas": job.suggested_review_areas,
        "created_at": job.created_at.isoformat(),
        "clauses": [
            {
                "id": c.id,
                "clause_number": c.clause_number,
                "clause_id_label": c.clause_id_label,
                "category": c.category,
                "original_text": c.original_text,
                "english_text": c.english_text,
                "translated_text": c.translated_text,
                "page_number": c.page_number,
                "risk_level": c.risk_level,
                "risk_score": c.risk_score,
                "risk_rationale": c.risk_rationale,
                "suggested_action": c.suggested_action,
                "slm_explanation": c.slm_explanation,
                "llm_explanation": c.llm_explanation,
                "confidence": c.confidence
            }
            for c in clauses
        ]
    }

@router.get("/{analysis_or_doc_id}/pdf")
def download_pdf_report(
    analysis_or_doc_id: str,
    language: Optional[str] = Query(default=None),
    db: Session = Depends(get_db)
):
    """
    Generates and downloads a formatted PDF contract assessment report.
    Supports optional ?language=Tamil/Hindi/Malayalam/Telugu to generate the report in that language.
    """
    job = AnalysisRepository.get_by_id(db, analysis_or_doc_id)
    if not job:
        job = AnalysisRepository.get_latest_for_document(db, analysis_or_doc_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis record not found.")

    doc = DocumentRepository.get_by_id(db, job.document_id)
    clauses = ClauseRepository.list_by_analysis(db, job.id)
    analysis_data = _build_analysis_dict(job, doc, clauses)

    pdf_path = ReportService.generate_pdf_report(analysis_data, language=language)
    if not pdf_path.exists():
        raise HTTPException(status_code=500, detail="PDF generation failed.")

    return FileResponse(
        path=str(pdf_path),
        filename=pdf_path.name,
        media_type="application/pdf"
    )

@router.get("/{analysis_or_doc_id}/json")
def export_json_report(analysis_or_doc_id: str, db: Session = Depends(get_db)):
    """
    Exports structured JSON analysis results.
    """
    job = AnalysisRepository.get_by_id(db, analysis_or_doc_id)
    if not job:
        job = AnalysisRepository.get_latest_for_document(db, analysis_or_doc_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis record not found.")

    doc = DocumentRepository.get_by_id(db, job.document_id)
    clauses = ClauseRepository.list_by_analysis(db, job.id)
    analysis_data = _build_analysis_dict(job, doc, clauses)

    json_content = ReportService.generate_json_export(analysis_data)
    filename = f"Clausent_Analysis_{job.id[:8]}.json"

    return Response(
        content=json_content,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@router.get("/{analysis_or_doc_id}/csv")
def export_csv_report(analysis_or_doc_id: str, db: Session = Depends(get_db)):
    """
    Exports clause-level assessment in CSV format.
    """
    job = AnalysisRepository.get_by_id(db, analysis_or_doc_id)
    if not job:
        job = AnalysisRepository.get_latest_for_document(db, analysis_or_doc_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis record not found.")

    doc = DocumentRepository.get_by_id(db, job.document_id)
    clauses = ClauseRepository.list_by_analysis(db, job.id)
    analysis_data = _build_analysis_dict(job, doc, clauses)

    csv_content = ReportService.generate_csv_export(analysis_data["clauses"])
    filename = f"Clausent_Clauses_{job.id[:8]}.csv"

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
