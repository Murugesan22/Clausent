import pytest
from app.utils.text_processing import normalize_legal_text, validate_text_content
from app.services.language_detection_service import LanguageDetectionService
from app.services.segmentation_service import SegmentationService
from app.services.classification_service import ClassificationService
from app.services.risk_assessment_service import RiskAssessmentService
from app.services.slm_service import SLMService
from app.services.translation_service import TranslationService

def test_normalization_preserves_legal_terms():
    raw = "Client  shall   pay  within\n\n\n30 days. Damages   are not limited."
    normalized = normalize_legal_text(raw)
    assert "30 days" in normalized
    assert "not limited" in normalized
    assert "   " not in normalized

def test_validate_text_content_empty_or_short():
    valid, msg = validate_text_content("")
    assert not valid
    valid, msg = validate_text_content("abc")
    assert not valid
    valid, msg = validate_text_content("This is a legally binding contract agreement between Party A and Party B.")
    assert valid

def test_language_detection():
    # English
    lang, conf = LanguageDetectionService.detect_language("This Agreement is entered into on this day.")
    assert lang == "English"
    assert conf > 0.6

    # Tamil
    ta_text = "இந்த ஒப்பந்தம் இரு தரப்பினருக்கும் இடையே மேற்கொள்ளப்படுகிறது."
    lang, conf = LanguageDetectionService.detect_language(ta_text)
    assert lang == "Tamil"

    # Hindi
    hi_text = "यह समझौता दोनों पक्षों के बीच किया जाता है।"
    lang, conf = LanguageDetectionService.detect_language(hi_text)
    assert lang == "Hindi"

    # Malayalam
    ml_text = "ഈ കരാർ രണ്ട് കക്ഷികൾ തമ്മിൽ ഒപ്പുവെച്ചിരിക്കുന്നു."
    lang, conf = LanguageDetectionService.detect_language(ml_text)
    assert lang == "Malayalam"

    # Telugu
    te_text = "ఈ ఒప్పందం ఇరు పక్షాల మధ్య కుదుర్చుకోబడింది."
    lang, conf = LanguageDetectionService.detect_language(te_text)
    assert lang == "Telugu"

def test_clause_segmentation():
    sample_doc = """
1. Definitions
Capitalized terms used in this Agreement shall have the meanings ascribed to them in Schedule A.

2. Payment Terms
Client shall remit payment within thirty (30) days of invoice date via wire transfer or ACH.

3. Limitation of Liability
In no event shall either party's liability be limited, and each party shall be fully liable for all damages.
"""
    clauses = SegmentationService.segment_text(sample_doc)
    assert len(clauses) >= 3
    assert any("Definitions" in c.text for c in clauses)
    assert any("Payment" in c.text for c in clauses)
    assert any("Limitation" in c.text for c in clauses)

def test_classification_and_risk_assessment():
    liability_clause = "In no event shall either party's liability be limited, and each party shall be fully liable for any and all direct, indirect, or consequential damages."
    cls_res = ClassificationService.classify_clause(liability_clause)
    assert cls_res.category == "Limitation of Liability"

    risk_res = RiskAssessmentService.assess_risk(liability_clause, cls_res.category)
    assert risk_res.risk_level == "high"
    assert risk_res.risk_score >= 85.0
    assert "unlimited" in risk_res.rationale.lower() or "liability" in risk_res.rationale.lower()

    # Routine payment clause
    payment_clause = "Client shall remit payment within thirty (30) days of invoice date via wire transfer."
    p_cls = ClassificationService.classify_clause(payment_clause)
    assert p_cls.category == "Payment Terms"

    p_risk = RiskAssessmentService.assess_risk(payment_clause, p_cls.category)
    assert p_risk.risk_level == "low"

def test_slm_explanation_generation():
    exp = SLMService.generate_explanation(
        clause_text="Client shall remit payment within thirty (30) days of invoice date.",
        category="Payment Terms",
        risk_level="low"
    )
    assert "explanation" in exp
    assert len(exp["explanation"]) > 10

def test_translation_service():
    eng, method = TranslationService.translate_to_english("This is an agreement", "English")
    assert eng == "This is an agreement"

    # Explanation translation
    trans_ta = TranslationService.translate_explanation(
        "Unlimited liability may expose you to unlimited financial damages",
        "Tamil"
    )
    assert "பொறுப்பு" in trans_ta or "Tamil" in trans_ta
