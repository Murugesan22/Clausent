from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database.models import DocumentModel, AnalysisJobModel, ClauseModel, ReportModel

class DocumentRepository:
    @staticmethod
    def create(db: Session, doc: DocumentModel) -> DocumentModel:
        db.add(doc)
        db.commit()
        db.refresh(doc)
        return doc

    @staticmethod
    def get_by_id(db: Session, doc_id: str) -> Optional[DocumentModel]:
        return db.query(DocumentModel).filter(DocumentModel.id == doc_id).first()

    @staticmethod
    def list_all(db: Session, limit: int = 100) -> List[DocumentModel]:
        return db.query(DocumentModel).order_by(desc(DocumentModel.upload_timestamp)).limit(limit).all()

    @staticmethod
    def delete(db: Session, doc_id: str) -> bool:
        doc = db.query(DocumentModel).filter(DocumentModel.id == doc_id).first()
        if doc:
            db.delete(doc)
            db.commit()
            return True
        return False

class AnalysisRepository:
    @staticmethod
    def create(db: Session, job: AnalysisJobModel) -> AnalysisJobModel:
        db.add(job)
        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def get_by_id(db: Session, analysis_id: str) -> Optional[AnalysisJobModel]:
        return db.query(AnalysisJobModel).filter(AnalysisJobModel.id == analysis_id).first()

    @staticmethod
    def get_latest_for_document(db: Session, doc_id: str) -> Optional[AnalysisJobModel]:
        return db.query(AnalysisJobModel).filter(
            AnalysisJobModel.document_id == doc_id
        ).order_by(desc(AnalysisJobModel.created_at)).first()

    @staticmethod
    def update_progress(
        db: Session,
        analysis_id: str,
        stage: str,
        percent: int,
        status: str = "processing"
    ):
        job = db.query(AnalysisJobModel).filter(AnalysisJobModel.id == analysis_id).first()
        if job:
            job.current_stage = stage
            job.progress_percent = percent
            job.status = status
            stages = job.completed_stages
            if stage not in stages:
                stages.append(stage)
                job.completed_stages = stages
            db.commit()

    @staticmethod
    def complete(
        db: Session,
        analysis_id: str,
        overall_score: int,
        overall_risk: str,
        high_cnt: int,
        med_cnt: int,
        low_cnt: int,
        total_cnt: int,
        summary: str,
        review_areas: str
    ):
        job = db.query(AnalysisJobModel).filter(AnalysisJobModel.id == analysis_id).first()
        if job:
            job.status = "completed"
            job.progress_percent = 100
            job.overall_risk_score = overall_score
            job.overall_risk_level = overall_risk
            job.high_risk_count = high_cnt
            job.medium_risk_count = med_cnt
            job.low_risk_count = low_cnt
            job.total_clauses = total_cnt
            job.executive_summary = summary
            job.suggested_review_areas = review_areas
            job.completed_at = datetime.now(timezone.utc)
            db.commit()

    @staticmethod
    def fail(db: Session, analysis_id: str, error_message: str):
        job = db.query(AnalysisJobModel).filter(AnalysisJobModel.id == analysis_id).first()
        if job:
            job.status = "failed"
            job.error_message = error_message
            db.commit()

class ClauseRepository:
    @staticmethod
    def bulk_create(db: Session, clauses: List[ClauseModel]):
        db.add_all(clauses)
        db.commit()

    @staticmethod
    def list_by_analysis(db: Session, analysis_id: str, risk_filter: Optional[str] = None) -> List[ClauseModel]:
        query = db.query(ClauseModel).filter(ClauseModel.analysis_id == analysis_id)
        if risk_filter and risk_filter.lower() != "all":
            query = query.filter(ClauseModel.risk_level == risk_filter.lower())
        return query.order_by(ClauseModel.clause_number).all()

    @staticmethod
    def get_by_id(db: Session, clause_id: int) -> Optional[ClauseModel]:
        return db.query(ClauseModel).filter(ClauseModel.id == clause_id).first()

    @staticmethod
    def update_explanation(
        db: Session,
        clause_id: int,
        slm_explain: Optional[str] = None,
        llm_explain: Optional[str] = None,
        model_name: Optional[str] = None
    ):
        clause = db.query(ClauseModel).filter(ClauseModel.id == clause_id).first()
        if clause:
            if slm_explain:
                clause.slm_explanation = slm_explain
            if llm_explain:
                clause.llm_explanation = llm_explain
            if model_name:
                clause.explanation_model = model_name
            db.commit()

class ReportRepository:
    @staticmethod
    def create(db: Session, report: ReportModel) -> ReportModel:
        db.add(report)
        db.commit()
        db.refresh(report)
        return report

    @staticmethod
    def get_by_analysis(db: Session, analysis_id: str) -> Optional[ReportModel]:
        return db.query(ReportModel).filter(ReportModel.analysis_id == analysis_id).first()
