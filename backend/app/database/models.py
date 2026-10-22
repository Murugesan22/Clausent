import json
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database.connection import Base

def utcnow():
    return datetime.now(timezone.utc)

class DocumentModel(Base):
    __tablename__ = "documents"

    id = Column(String(64), primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_name = Column(String(255), nullable=False)
    file_type = Column(String(16), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    storage_path = Column(String(512), nullable=False)
    upload_timestamp = Column(DateTime, default=utcnow, nullable=False)
    detected_language = Column(String(64), default="English")
    language_confidence = Column(Float, default=1.0)
    extracted_text = Column(Text, nullable=True)
    normalized_text = Column(Text, nullable=True)
    status = Column(String(32), default="uploaded", nullable=False)
    error_message = Column(Text, nullable=True)

    analyses = relationship("AnalysisJobModel", back_populates="document", cascade="all, delete-orphan")

class AnalysisJobModel(Base):
    __tablename__ = "analysis_jobs"

    id = Column(String(64), primary_key=True, index=True)
    document_id = Column(String(64), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    target_language = Column(String(64), default="English", nullable=False)
    overall_risk_score = Column(Integer, default=0, nullable=False)
    overall_risk_level = Column(String(16), default="low", nullable=False)
    high_risk_count = Column(Integer, default=0, nullable=False)
    medium_risk_count = Column(Integer, default=0, nullable=False)
    low_risk_count = Column(Integer, default=0, nullable=False)
    total_clauses = Column(Integer, default=0, nullable=False)
    current_stage = Column(String(64), default="created", nullable=False)
    progress_percent = Column(Integer, default=0, nullable=False)
    completed_stages_json = Column(Text, default="[]", nullable=False)
    executive_summary = Column(Text, nullable=True)
    suggested_review_areas = Column(Text, nullable=True)
    status = Column(String(32), default="pending", nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    document = relationship("DocumentModel", back_populates="analyses")
    clauses = relationship("ClauseModel", back_populates="analysis", cascade="all, delete-orphan", order_by="ClauseModel.clause_number")
    reports = relationship("ReportModel", back_populates="analysis", cascade="all, delete-orphan")

    @property
    def completed_stages(self):
        try:
            return json.loads(self.completed_stages_json or "[]")
        except Exception:
            return []

    @completed_stages.setter
    def completed_stages(self, val):
        self.completed_stages_json = json.dumps(val or [])

class ClauseModel(Base):
    __tablename__ = "clauses"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    analysis_id = Column(String(64), ForeignKey("analysis_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    clause_number = Column(Integer, nullable=False)
    clause_id_label = Column(String(64), nullable=False)
    category = Column(String(255), nullable=False)
    original_text = Column(Text, nullable=False)
    english_text = Column(Text, nullable=True)
    translated_text = Column(Text, nullable=True)
    page_number = Column(Integer, nullable=True)
    risk_level = Column(String(16), default="low", nullable=False)
    risk_score = Column(Float, default=0.0, nullable=False)
    risk_rationale = Column(Text, nullable=False)
    evidence_json = Column(Text, default="[]", nullable=False)
    suggested_action = Column(Text, nullable=False)
    suggested_questions_json = Column(Text, default="[]", nullable=False)
    uncertainties_json = Column(Text, default="[]", nullable=False)
    slm_explanation = Column(Text, nullable=True)
    llm_explanation = Column(Text, nullable=True)
    explanation_model = Column(String(255), nullable=True)
    confidence = Column(Float, default=85.0, nullable=False)

    analysis = relationship("AnalysisJobModel", back_populates="clauses")

    @property
    def evidence(self):
        try:
            return json.loads(self.evidence_json or "[]")
        except Exception:
            return []

    @evidence.setter
    def evidence(self, val):
        self.evidence_json = json.dumps(val or [])

    @property
    def suggested_questions(self):
        try:
            return json.loads(self.suggested_questions_json or "[]")
        except Exception:
            return []

    @suggested_questions.setter
    def suggested_questions(self, val):
        self.suggested_questions_json = json.dumps(val or [])

    @property
    def uncertainties(self):
        try:
            return json.loads(self.uncertainties_json or "[]")
        except Exception:
            return []

    @uncertainties.setter
    def uncertainties(self, val):
        self.uncertainties_json = json.dumps(val or [])

class ReportModel(Base):
    __tablename__ = "reports"

    id = Column(String(64), primary_key=True, index=True)
    analysis_id = Column(String(64), ForeignKey("analysis_jobs.id", ondelete="CASCADE"), nullable=False)
    pdf_path = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    analysis = relationship("AnalysisJobModel", back_populates="reports")
