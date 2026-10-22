from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from app.schemas.clause import ClauseResponse

class AnalysisStartRequest(BaseModel):
    document_id: str
    target_language: str = "English"
    source_language: Optional[str] = "Auto detect"

class AnalysisStartResponse(BaseModel):
    analysis_id: str
    document_id: str
    status: str
    message: str

class AnalysisStatusResponse(BaseModel):
    analysis_id: str
    document_id: str
    status: str  # pending, processing, completed, failed
    current_stage: str
    progress_percent: int
    completed_stages: List[str]
    error_message: Optional[str] = None

class AnalysisResultResponse(BaseModel):
    analysis_id: str
    document_id: str
    filename: str
    detected_language: str
    target_language: str
    overall_risk_score: int
    overall_risk_level: str  # low, medium, high
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    total_clauses: int
    executive_summary: str
    suggested_review_areas: str
    clauses: List[ClauseResponse]
    created_at: datetime
    completed_at: Optional[datetime] = None
    status: str
    disclaimer: str = (
        "Clausent provides preliminary AI-assisted contract risk analysis for informational and educational "
        "purposes only. It does not provide legal advice and does not substitute for review by a qualified legal professional."
    )
