from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, status
from sqlalchemy.orm import Session

from app.database.connection import get_db, SessionLocal
from app.database.repositories import DocumentRepository, AnalysisRepository, ClauseRepository
from app.schemas.analysis import (
    AnalysisStartResponse, AnalysisStatusResponse, AnalysisResultResponse
)
from app.schemas.clause import (
    ClauseResponse, ClauseExplainRequest, ClauseExplainResponse
)
from app.services.document_service import DocumentService
from app.services.llm_service import LLMService
from app.services.explanation_service import ExplanationOrchestrator
from app.services.translation_service import TranslationService
from app.core.logging_config import logger

router = APIRouter(prefix="/analysis", tags=["Analysis"])

def run_pipeline_task(document_id: str, target_lang: str, source_lang: str):
    """Background worker for contract processing."""
    db: Session = SessionLocal()
    try:
        DocumentService.execute_pipeline(
            document_id=document_id,
            target_language=target_lang,
            source_language_pref=source_lang,
            db=db
        )
    except Exception as e:
        logger.error(f"Background analysis task failed for {document_id}: {e}", exc_info=True)
    finally:
        db.close()

@router.post("/{document_id}/start", response_model=AnalysisStartResponse)
def start_analysis(
    document_id: str,
    background_tasks: BackgroundTasks,
    target_language: str = Query(default="English"),
    source_language: str = Query(default="Auto detect"),
    db: Session = Depends(get_db)
):
    """
    Initiates contract processing pipeline.
    Runs asynchronously in the background while client polls the status endpoint.
    """
    doc = DocumentRepository.get_by_id(db, document_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    # Schedule background execution
    background_tasks.add_task(run_pipeline_task, document_id, target_language, source_language)

    # Return immediate acknowledgement
    return AnalysisStartResponse(
        analysis_id=document_id,  # Client can poll by document_id or retrieve latest
        document_id=document_id,
        status="started",
        message="Contract analysis initiated in background. Poll status endpoint for progress."
    )

@router.get("/{analysis_or_doc_id}/status", response_model=AnalysisStatusResponse)
def get_analysis_status(analysis_or_doc_id: str, db: Session = Depends(get_db)):
    """
    Returns real-time processing progress and active milestone.
    """
    # Check if ID is direct analysis_id or document_id
    job = AnalysisRepository.get_by_id(db, analysis_or_doc_id)
    if not job:
        job = AnalysisRepository.get_latest_for_document(db, analysis_or_doc_id)

    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis job not found.")

    return AnalysisStatusResponse(
        analysis_id=job.id,
        document_id=job.document_id,
        status=job.status,
        current_stage=job.current_stage,
        progress_percent=job.progress_percent,
        completed_stages=job.completed_stages,
        error_message=job.error_message
    )

@router.get("/{analysis_or_doc_id}/results", response_model=AnalysisResultResponse)
def get_analysis_results(analysis_or_doc_id: str, db: Session = Depends(get_db)):
    """
    Returns full analysis results, including executive summary, risk score, and clauses.
    """
    job = AnalysisRepository.get_by_id(db, analysis_or_doc_id)
    if not job:
        job = AnalysisRepository.get_latest_for_document(db, analysis_or_doc_id)

    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis job not found.")

    doc = DocumentRepository.get_by_id(db, job.document_id)
    clauses = ClauseRepository.list_by_analysis(db, job.id)

    clause_responses = [
        ClauseResponse(
            id=c.id,
            clause_number=c.clause_number,
            clause_id_label=c.clause_id_label,
            category=c.category,
            original_text=c.original_text,
            english_text=c.english_text,
            translated_text=c.translated_text,
            page_number=c.page_number,
            risk_level=c.risk_level,
            risk_score=c.risk_score,
            risk_rationale=c.risk_rationale,
            evidence=c.evidence,
            suggested_action=c.suggested_action,
            suggested_questions=c.suggested_questions,
            uncertainties=c.uncertainties,
            slm_explanation=c.slm_explanation,
            llm_explanation=c.llm_explanation,
            explanation_model=c.explanation_model,
            confidence=c.confidence
        )
        for c in clauses
    ]

    return AnalysisResultResponse(
        analysis_id=job.id,
        document_id=job.document_id,
        filename=doc.original_name if doc else "Contract",
        detected_language=doc.detected_language if doc else "English",
        target_language=job.target_language,
        overall_risk_score=job.overall_risk_score,
        overall_risk_level=job.overall_risk_level,
        high_risk_count=job.high_risk_count,
        medium_risk_count=job.medium_risk_count,
        low_risk_count=job.low_risk_count,
        total_clauses=job.total_clauses,
        executive_summary=job.executive_summary or "Contract analysis completed.",
        suggested_review_areas=job.suggested_review_areas or "Standard review recommended.",
        clauses=clause_responses,
        created_at=job.created_at,
        completed_at=job.completed_at,
        status=job.status
    )

@router.get("/{analysis_id}/clauses", response_model=List[ClauseResponse])
def get_clauses(
    analysis_id: str,
    risk: Optional[str] = Query(default="all"),
    db: Session = Depends(get_db)
):
    """
    Returns filtered clauses for a specific analysis job.
    """
    clauses = ClauseRepository.list_by_analysis(db, analysis_id, risk_filter=risk)
    return [
        ClauseResponse(
            id=c.id,
            clause_number=c.clause_number,
            clause_id_label=c.clause_id_label,
            category=c.category,
            original_text=c.original_text,
            english_text=c.english_text,
            translated_text=c.translated_text,
            page_number=c.page_number,
            risk_level=c.risk_level,
            risk_score=c.risk_score,
            risk_rationale=c.risk_rationale,
            evidence=c.evidence,
            suggested_action=c.suggested_action,
            suggested_questions=c.suggested_questions,
            uncertainties=c.uncertainties,
            slm_explanation=c.slm_explanation,
            llm_explanation=c.llm_explanation,
            explanation_model=c.explanation_model,
            confidence=c.confidence
        )
        for c in clauses
    ]

@router.get("/{analysis_id}/clauses/{clause_id}", response_model=ClauseResponse)
def get_clause_detail(analysis_id: str, clause_id: int, db: Session = Depends(get_db)):
    """
    Returns detailed analysis for a specific clause.
    """
    clause = ClauseRepository.get_by_id(db, clause_id)
    if not clause or clause.analysis_id != analysis_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clause not found.")

    return ClauseResponse(
        id=clause.id,
        clause_number=clause.clause_number,
        clause_id_label=clause.clause_id_label,
        category=clause.category,
        original_text=clause.original_text,
        english_text=clause.english_text,
        translated_text=clause.translated_text,
        page_number=clause.page_number,
        risk_level=clause.risk_level,
        risk_score=clause.risk_score,
        risk_rationale=clause.risk_rationale,
        evidence=clause.evidence,
        suggested_action=clause.suggested_action,
        suggested_questions=clause.suggested_questions,
        uncertainties=clause.uncertainties,
        slm_explanation=clause.slm_explanation,
        llm_explanation=clause.llm_explanation,
        explanation_model=clause.explanation_model,
        confidence=clause.confidence
    )

@router.post("/{analysis_id}/clauses/{clause_id}/explain", response_model=ClauseExplainResponse)
def explain_clause(
    analysis_id: str,
    clause_id: int,
    req: ClauseExplainRequest,
    db: Session = Depends(get_db)
):
    """
    Requests on-demand LLM detailed explanation for a clause.
    """
    clause = ClauseRepository.get_by_id(db, clause_id)
    if not clause or clause.analysis_id != analysis_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clause not found.")

    res = ExplanationOrchestrator.orchestrate_explanation(
        clause_text=clause.original_text,
        category=clause.category,
        risk_level=clause.risk_level,
        rationale=clause.risk_rationale,
        evidence=clause.evidence,
        target_language=req.preferred_language or "English",
        force_llm=True
    )

    # Update clause in DB with new explanation
    ClauseRepository.update_explanation(
        db=db,
        clause_id=clause_id,
        slm_explain=res.get("slm_explanation"),
        llm_explain=res.get("llm_explanation"),
        model_name=res.get("explanation_model")
    )

    return ClauseExplainResponse(
        clause_id=clause.id,
        slm_explanation=res.get("slm_explanation", ""),
        llm_explanation=res.get("llm_explanation"),
        model_used=res.get("explanation_model", "LLM"),
        suggested_questions=clause.suggested_questions,
        uncertainties=clause.uncertainties
    )

@router.post("/{analysis_or_doc_id}/translate", response_model=AnalysisResultResponse)
def translate_analysis(
    analysis_or_doc_id: str,
    target_language: str = Query(default="English"),
    db: Session = Depends(get_db)
):
    """
    Translates the contract findings, explanations, and executive summary into the target language.
    """
    job = AnalysisRepository.get_by_id(db, analysis_or_doc_id)
    if not job:
        job = AnalysisRepository.get_latest_for_document(db, analysis_or_doc_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis job not found.")

    job.target_language = target_language
    db.commit()

    doc = DocumentRepository.get_by_id(db, job.document_id)
    clauses = ClauseRepository.list_by_analysis(db, job.id)

    base_data = {
        "analysis_id": job.id,
        "document_id": job.document_id,
        "filename": doc.original_name if doc else "Contract",
        "detected_language": doc.detected_language if doc else "English",
        "target_language": target_language,
        "overall_risk_score": job.overall_risk_score,
        "overall_risk_level": job.overall_risk_level,
        "high_risk_count": job.high_risk_count,
        "medium_risk_count": job.medium_risk_count,
        "low_risk_count": job.low_risk_count,
        "total_clauses": job.total_clauses,
        "executive_summary": job.executive_summary or "Contract analysis completed.",
        "suggested_review_areas": job.suggested_review_areas or "Standard review recommended.",
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
                "evidence": c.evidence,
                "suggested_action": c.suggested_action,
                "suggested_questions": c.suggested_questions,
                "uncertainties": c.uncertainties,
                "slm_explanation": c.slm_explanation,
                "llm_explanation": c.llm_explanation,
                "explanation_model": c.explanation_model,
                "confidence": c.confidence
            }
            for c in clauses
        ],
        "created_at": job.created_at,
        "completed_at": job.completed_at,
        "status": job.status
    }

    translated_data = TranslationService.translate_analysis_data(base_data, target_language)

    clause_responses = [
        ClauseResponse(
            id=c["id"],
            clause_number=c["clause_number"],
            clause_id_label=c["clause_id_label"],
            category=c.get("category_display") or c["category"],
            original_text=c["original_text"],
            english_text=c.get("english_text"),
            translated_text=c.get("translated_text"),
            page_number=c.get("page_number"),
            risk_level=c["risk_level"],
            risk_score=c["risk_score"],
            risk_rationale=c["risk_rationale"],
            evidence=c["evidence"],
            suggested_action=c["suggested_action"],
            suggested_questions=c.get("suggested_questions", []),
            uncertainties=c.get("uncertainties", []),
            slm_explanation=c.get("slm_explanation"),
            llm_explanation=c.get("llm_explanation"),
            explanation_model=c.get("explanation_model"),
            confidence=c["confidence"]
        )
        for c in translated_data["clauses"]
    ]

    return AnalysisResultResponse(
        analysis_id=job.id,
        document_id=job.document_id,
        filename=translated_data["filename"],
        detected_language=translated_data["detected_language"],
        target_language=target_language,
        overall_risk_score=job.overall_risk_score,
        overall_risk_level=job.overall_risk_level,
        high_risk_count=job.high_risk_count,
        medium_risk_count=job.medium_risk_count,
        low_risk_count=job.low_risk_count,
        total_clauses=job.total_clauses,
        executive_summary=translated_data["executive_summary"],
        suggested_review_areas=translated_data["suggested_review_areas"],
        clauses=clause_responses,
        created_at=job.created_at,
        completed_at=job.completed_at,
        status=job.status
    )
