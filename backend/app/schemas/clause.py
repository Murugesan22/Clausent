from pydantic import BaseModel, Field
from typing import List, Optional

class ClauseBase(BaseModel):
    id: int
    clause_number: int
    clause_id_label: str
    category: str
    original_text: str
    english_text: Optional[str] = None
    translated_text: Optional[str] = None
    page_number: Optional[int] = None
    risk_level: str  # "low", "medium", "high"
    risk_score: float = Field(default=0.0, ge=0.0, le=100.0)
    risk_rationale: str
    evidence: List[str] = Field(default_factory=list)
    suggested_action: str
    suggested_questions: List[str] = Field(default_factory=list)
    uncertainties: List[str] = Field(default_factory=list)
    slm_explanation: Optional[str] = None
    llm_explanation: Optional[str] = None
    explanation_model: Optional[str] = None
    confidence: float = Field(default=85.0, ge=0.0, le=100.0)

class ClauseResponse(ClauseBase):
    pass

class ClauseExplainRequest(BaseModel):
    preferred_language: Optional[str] = "English"
    force_llm: bool = False

class ClauseExplainResponse(BaseModel):
    clause_id: int
    slm_explanation: str
    llm_explanation: Optional[str] = None
    model_used: str
    suggested_questions: List[str]
    uncertainties: List[str]
