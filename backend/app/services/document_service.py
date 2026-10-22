import os
import uuid
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import UploadFile

from app.config import settings
from app.core.exceptions import (
    DocumentValidationError, ExtractionError, SegmentationError,
    ClassificationError, RiskAssessmentError
)
from app.core.logging_config import logger
from app.utils.file_validation import validate_uploaded_file, generate_safe_filename
from app.database.models import DocumentModel, AnalysisJobModel, ClauseModel
from app.database.repositories import DocumentRepository, AnalysisRepository, ClauseRepository
from app.services.extraction_service import ExtractionService
from app.services.language_detection_service import LanguageDetectionService
from app.services.normalization_service import NormalizationService
from app.services.translation_service import TranslationService
from app.services.segmentation_service import SegmentationService
from app.services.classification_service import ClassificationService
from app.services.risk_assessment_service import RiskAssessmentService
from app.services.explanation_service import ExplanationOrchestrator

class DocumentService:
    @staticmethod
    def save_upload(file: UploadFile, db: Session) -> DocumentModel:
        """
        Validates and persists uploaded contract file to storage and database.
        """
        ext = validate_uploaded_file(file)
        internal_name, clean_name, doc_id = generate_safe_filename(file.filename)
        dest_path = settings.UPLOAD_DIR / internal_name

        # Enforce size limit during chunked read
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        total_size = 0

        try:
            with open(dest_path, "wb") as out_file:
                while chunk := file.file.read(1024 * 64):
                    total_size += len(chunk)
                    if total_size > max_bytes:
                        out_file.close()
                        dest_path.unlink(missing_ok=True)
                        raise DocumentValidationError(
                            f"File size exceeds maximum permitted limit of {settings.MAX_UPLOAD_SIZE_MB} MB."
                        )
                    out_file.write(chunk)
        except DocumentValidationError:
            raise
        except Exception as e:
            logger.error(f"Failed to write uploaded file: {e}")
            raise DocumentValidationError(f"Could not save uploaded file: {str(e)}")

        doc_record = DocumentModel(
            id=doc_id,
            filename=internal_name,
            original_name=clean_name,
            file_type=ext,
            file_size_bytes=total_size,
            storage_path=str(dest_path),
            upload_timestamp=datetime.now(timezone.utc),
            status="uploaded"
        )
        return DocumentRepository.create(db, doc_record)

    @classmethod
    def execute_pipeline(
        cls,
        document_id: str,
        target_language: str,
        source_language_pref: str,
        db: Session
    ) -> AnalysisJobModel:
        """
        Executes the complete end-to-end 12-stage NLP analysis pipeline.
        Updates real database status at each milestone for frontend polling.
        """
        doc = DocumentRepository.get_by_id(db, document_id)
        if not doc:
            raise DocumentValidationError("Referenced document does not exist.")

        analysis_id = str(uuid.uuid4())
        job = AnalysisJobModel(
            id=analysis_id,
            document_id=document_id,
            target_language=target_language,
            status="processing",
            current_stage="Document received",
            progress_percent=5,
            completed_stages=["Document received"]
        )
        AnalysisRepository.create(db, job)

        file_path = Path(doc.storage_path)

        try:
            # Stage 1: Text Extraction
            AnalysisRepository.update_progress(db, analysis_id, "Extracting text", 15)
            ext_res = ExtractionService.extract_from_file(file_path, doc.file_type)

            if ext_res.is_scanned:
                AnalysisRepository.fail(db, analysis_id, ext_res.message)
                doc.status = "failed"
                doc.error_message = ext_res.message
                db.commit()
                return job

            raw_text = ext_res.full_text
            doc.extracted_text = raw_text

            # Stage 2: Language Detection
            AnalysisRepository.update_progress(db, analysis_id, "Detecting language", 25)
            if source_language_pref and source_language_pref != "Auto detect":
                detected_lang = source_language_pref
                lang_conf = 1.0
            else:
                detected_lang, lang_conf = LanguageDetectionService.detect_language(raw_text)

            doc.detected_language = detected_lang
            doc.language_confidence = lang_conf

            # Stage 3: Normalization
            AnalysisRepository.update_progress(db, analysis_id, "Normalizing text", 35)
            normalized_text, norm_meta = NormalizationService.normalize_document(raw_text)
            doc.normalized_text = normalized_text
            db.commit()

            # Stage 4: Translation to English if required
            AnalysisRepository.update_progress(db, analysis_id, "Translating contract if necessary", 45)
            english_text, trans_method = TranslationService.translate_to_english(normalized_text, detected_lang)

            # Stage 5: Clause Segmentation
            AnalysisRepository.update_progress(db, analysis_id, "Segmenting clauses", 55)
            raw_clauses = SegmentationService.segment_text(english_text, ext_res.page_texts)
            if not raw_clauses:
                raise SegmentationError("No legal clauses could be identified from the document structure.")

            # If original was non-English, also segment original text to pair original clauses
            orig_clauses = []
            if detected_lang.lower() != "english":
                orig_clauses = SegmentationService.segment_text(normalized_text, ext_res.page_texts)

            # Stage 6 & 7: Legal-BERT Classification & Risk Assessment
            AnalysisRepository.update_progress(db, analysis_id, "Classifying clauses & assessing risks", 70)

            clause_models: List[ClauseModel] = []
            high_count = 0
            med_count = 0
            low_count = 0

            for idx, rc in enumerate(raw_clauses):
                orig_text = orig_clauses[idx].text if idx < len(orig_clauses) else rc.text
                eng_text = rc.text

                # Classify
                cls_result = ClassificationService.classify_clause(eng_text)

                # Assess Risk
                risk_result = RiskAssessmentService.assess_risk(eng_text, cls_result.category)

                if risk_result.risk_level == "high":
                    high_count += 1
                elif risk_result.risk_level == "medium":
                    med_count += 1
                else:
                    low_count += 1

                # Stage 8 & 9: SLM & LLM Orchestrated Explanations
                exp_result = ExplanationOrchestrator.orchestrate_explanation(
                    clause_text=eng_text,
                    category=cls_result.category,
                    risk_level=risk_result.risk_level,
                    rationale=risk_result.rationale,
                    evidence=risk_result.evidence,
                    target_language=target_language
                )

                # Translate clause text into target language if non-English
                if target_language.lower() != "english":
                    clause_translated_text = TranslationService.translate_text(eng_text, target_language)
                else:
                    clause_translated_text = eng_text

                c_model = ClauseModel(
                    analysis_id=analysis_id,
                    clause_number=rc.clause_number,
                    clause_id_label=rc.clause_id_label,
                    category=cls_result.category,
                    original_text=orig_text,
                    english_text=eng_text,
                    translated_text=clause_translated_text,
                    page_number=rc.page_number,
                    risk_level=risk_result.risk_level,
                    risk_score=risk_result.risk_score,
                    risk_rationale=exp_result.get("risk_rationale", risk_result.rationale),
                    evidence_json="[]",
                    suggested_action=exp_result.get("suggested_action", risk_result.suggested_action),
                    suggested_questions_json="[]",
                    uncertainties_json="[]",
                    slm_explanation=exp_result.get("slm_explanation"),
                    llm_explanation=exp_result.get("llm_explanation"),
                    explanation_model=exp_result.get("explanation_model"),
                    confidence=cls_result.confidence
                )
                c_model.evidence = risk_result.evidence
                c_model.suggested_questions = risk_result.suggested_questions
                c_model.uncertainties = risk_result.uncertainties

                clause_models.append(c_model)

            # Persist clauses
            ClauseRepository.bulk_create(db, clause_models)

            # Stage 10: Generating Summary & Finalizing
            AnalysisRepository.update_progress(db, analysis_id, "Preparing report", 90)

            total_c = len(clause_models)
            avg_score = sum(c.risk_score for c in clause_models) / max(1, total_c)
            # Weighted overall score prioritizing high-risk provisions
            overall_score = min(100, int(avg_score * 0.5 + (high_count * 20 + med_count * 8)))

            if high_count >= 2 or overall_score >= 65:
                overall_risk = "high"
                overall_score = max(overall_score, 74)
            elif high_count == 1 or med_count >= 2 or overall_score >= 40:
                overall_risk = "medium"
                overall_score = max(overall_score, 45)
            else:
                overall_risk = "low"
                overall_score = min(overall_score, 35)

            summary = (
                f"Analysis completed for {doc.original_name}. Identified {total_c} contractual clauses across "
                f"the document. Found {high_count} high-risk provisions, {med_count} medium-risk provisions, "
                f"and {low_count} standard/low-risk commercial clauses."
            )
            if high_count > 0:
                summary += " Key areas of exposure include potential uncapped liabilities, one-sided indemnification, or renewal terms."

            review_areas = (
                "Prior to signing, recommend negotiating liability caps, clarifying dispute resolution venue, "
                "and verifying that termination and indemnification provisions provide mutual reciprocity."
            )

            # If user requested analysis in non-English, localize summary and review areas
            if target_language.lower() != "english":
                summary = TranslationService.translate_text(summary, target_language)
                review_areas = TranslationService.translate_text(review_areas, target_language)

            # Complete job
            AnalysisRepository.complete(
                db=db,
                analysis_id=analysis_id,
                overall_score=overall_score,
                overall_risk=overall_risk,
                high_cnt=high_count,
                med_cnt=med_count,
                low_cnt=low_count,
                total_cnt=total_c,
                summary=summary,
                review_areas=review_areas
            )
            doc.status = "analyzed"
            db.commit()

            logger.info(f"Analysis {analysis_id} completed successfully for document {doc.original_name}.")
            return job

        except Exception as e:
            logger.error(f"Pipeline failure for document {document_id}: {e}", exc_info=True)
            AnalysisRepository.fail(db, analysis_id, str(e))
            doc.status = "failed"
            doc.error_message = str(e)
            db.commit()
            raise
