import pytest
import os
from pathlib import Path
from app.services.classification_service import ClassificationService
from app.services.risk_assessment_service import RiskAssessmentService
from app.services.translation_service import TranslationService
from app.services.report_service import ReportService

def test_risk_detection_limitation_of_liability_uncapped():
    # 1. Uncapped liability clause
    clause = "Under no circumstances shall Provider's liability be limited, and Provider shall be fully liable for all direct, indirect, and consequential damages."
    cls_res = ClassificationService.classify_clause(clause)
    risk_res = RiskAssessmentService.assess_risk(clause, cls_res.category)
    assert risk_res.risk_level == "high"
    assert risk_res.risk_score >= 88.0

def test_risk_detection_broad_unilateral_indemnity():
    # 2. Broad unilateral indemnity
    clause = "Service Provider shall indemnify, defend, and hold harmless Client, its affiliates and directors from and against any and all claims, losses, damages, liabilities, costs and expenses (including attorneys' fees) arising out of or related to this Agreement."
    cls_res = ClassificationService.classify_clause(clause)
    assert "Indemnif" in cls_res.category
    risk_res = RiskAssessmentService.assess_risk(clause, cls_res.category)
    assert risk_res.risk_level == "high"
    assert risk_res.risk_score >= 85.0

def test_risk_detection_automatic_renewal_trap():
    # 3. 90-day auto-renewal trap
    clause = "This Agreement will automatically renew for successive terms of one (1) year each, unless either party provides written notice of non-renewal at least ninety (90) days prior to the expiration of the current term."
    cls_res = ClassificationService.classify_clause(clause)
    assert "Renewal" in cls_res.category
    risk_res = RiskAssessmentService.assess_risk(clause, cls_res.category)
    assert risk_res.risk_level == "high"
    assert risk_res.risk_score >= 85.0

def test_risk_detection_short_termination():
    # 4. Immediate / short convenience termination
    clause = "Company reserves the right to terminate this Agreement immediately upon written notice without cause in its sole discretion."
    cls_res = ClassificationService.classify_clause(clause)
    risk_res = RiskAssessmentService.assess_risk(clause, cls_res.category)
    assert risk_res.risk_level == "high"
    assert risk_res.risk_score >= 80.0

def test_risk_detection_long_non_compete():
    # 5. Long non-compete
    clause = "Contractor covenants that it shall not directly or indirectly compete with Company or perform similar services for any competing business worldwide for a period of two (2) years following termination."
    cls_res = ClassificationService.classify_clause(clause)
    assert "Non-Compete" in cls_res.category
    risk_res = RiskAssessmentService.assess_risk(clause, cls_res.category)
    assert risk_res.risk_level == "high"
    assert risk_res.risk_score >= 88.0

def test_risk_detection_ip_moral_rights_waiver():
    # 6. IP waiver
    clause = "Developer assigns all right, title, and interest in all deliverables and irrevocably waives all moral rights and assigns all preexisting intellectual property."
    risk_res = RiskAssessmentService.assess_risk(clause, "Intellectual Property")
    assert risk_res.risk_level == "high"

def test_multilingual_indic_risk_detection():
    # 7. Tamil contract clause risk detection
    ta_clause = "எந்தவொரு சூழ்நிலையிலும் பொறுப்பு வரம்பிடப்படாது, மற்றும் வரம்பற்ற பொறுப்பு பொருந்தும்."
    cls_res = ClassificationService.classify_clause(ta_clause)
    risk_res = RiskAssessmentService.assess_risk(ta_clause, cls_res.category)
    assert risk_res.risk_level == "high"

def test_pdf_report_generation_multilingual():
    # Test generating PDF reports in Tamil, Hindi, Malayalam, and Telugu
    sample_analysis = {
        "analysis_id": "test-analysis-123",
        "document_id": "test-doc-123",
        "filename": "Service_Contract.pdf",
        "detected_language": "English",
        "target_language": "Tamil",
        "overall_risk_score": 82,
        "overall_risk_level": "high",
        "high_risk_count": 2,
        "medium_risk_count": 1,
        "low_risk_count": 1,
        "total_clauses": 4,
        "executive_summary": "Analysis completed. Identified 2 high-risk provisions regarding unlimited liability and automatic renewal.",
        "suggested_review_areas": "Negotiate an aggregate liability cap and reduce renewal notice window.",
        "clauses": [
            {
                "clause_number": 1,
                "clause_id_label": "Section 1",
                "category": "Limitation of Liability",
                "original_text": "In no event shall liability be limited, and each party is fully liable.",
                "translated_text": "எந்தவொரு சூழ்நிலையிலும் பொறுப்பு வரம்பிடப்படாது.",
                "risk_level": "high",
                "risk_score": 92.0,
                "risk_rationale": "Removes any cap on liability.",
                "suggested_action": "Negotiate a liability cap tied to annual fees.",
                "slm_explanation": "This provision imposes unlimited liability.",
                "suggested_questions": ["Can we cap liability at annual fees?"]
            }
        ]
    }

    for lang in ["Tamil", "Hindi", "Malayalam", "Telugu"]:
        pdf_path = ReportService.generate_pdf_report(sample_analysis, language=lang)
        assert pdf_path.exists()
        assert pdf_path.stat().st_size > 1000
        # Clean up
        pdf_path.unlink(missing_ok=True)
