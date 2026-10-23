from fastapi import APIRouter, Body
from typing import Optional, Dict, Any, List
import time

from app.services.classification_service import ClassificationService
from app.services.risk_assessment_service import RiskAssessmentService


# Small, transparent smoke-test set. These examples exercise the current rule
# engine; they are not a CUAD/held-out benchmark and must not be presented as
# evidence of generalization performance.
COMPARISON_CASES = [
    ("Limitation of Liability", "high", "In no event shall either party's liability be limited, and each party shall be fully liable for all damages."),
    ("Automatic Renewal", "high", "This agreement automatically renews for successive one-year terms unless notice is given 90 days before expiry."),
    ("Termination", "high", "The provider may terminate this agreement immediately without notice."),
    ("Indemnification", "high", "Contractor shall indemnify, defend, and hold harmless Client from any and all claims and attorneys' fees."),
    ("Confidentiality", "low", "Each party shall protect the other's confidential information using reasonable care."),
    ("Payment Terms", "low", "Client shall remit payment within thirty days of invoice date."),
]


def _simple_keyword_baseline(text: str) -> str:
    """Intentionally basic reference baseline for the fixture comparison."""
    value = text.lower()
    for terms, label in (
        (("liability", "liable", "damages"), "Limitation of Liability"),
        (("renew", "successive"), "Automatic Renewal"),
        (("terminat", "cancel"), "Termination"),
        (("indemnif", "hold harmless"), "Indemnification"),
        (("confidential", "non-disclosure"), "Confidentiality"),
        (("payment", "invoice", "remit"), "Payment Terms"),
    ):
        if any(term in value for term in terms):
            return label
    return "General Provisions"


def _classification_metrics(predictions: List[str], expected: List[str]) -> Dict[str, Any]:
    labels = sorted(set(expected))
    per_label = []
    for label in labels:
        tp = sum(p == label and y == label for p, y in zip(predictions, expected))
        fp = sum(p == label and y != label for p, y in zip(predictions, expected))
        fn = sum(p != label and y == label for p, y in zip(predictions, expected))
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_label.append((precision, recall, f1))
    n = max(1, len(expected))
    return {
        "accuracy": round(100 * sum(p == y for p, y in zip(predictions, expected)) / n, 1),
        "macro_precision": round(100 * sum(x[0] for x in per_label) / max(1, len(per_label)), 1),
        "macro_recall": round(100 * sum(x[1] for x in per_label) / max(1, len(per_label)), 1),
        "macro_f1": round(100 * sum(x[2] for x in per_label) / max(1, len(per_label)), 1),
    }


def _smoke_comparison() -> Dict[str, Any]:
    expected_categories = [case[0] for case in COMPARISON_CASES]
    expected_risks = [case[1] for case in COMPARISON_CASES]
    baseline_categories = []
    active_categories = []
    baseline_risks = []
    active_risks = []

    for _, _, text in COMPARISON_CASES:
        baseline_category = _simple_keyword_baseline(text)
        baseline_categories.append(baseline_category)
        baseline_risks.append(RiskAssessmentService.assess_risk(text, baseline_category).risk_level)

        result = ClassificationService.classify_clause(text)
        active_categories.append(result.category)
        active_risks.append(RiskAssessmentService.assess_risk(text, result.category).risk_level)

    rows = []
    for name, categories, risks, kind in (
        ("Simple keyword baseline", baseline_categories, baseline_risks, "rule baseline"),
        ("Current CLAUSENT pipeline", active_categories, active_risks, "regex classification + rule risk assessment"),
    ):
        rows.append({
            "name": name,
            "type": kind,
            "classification": _classification_metrics(categories, expected_categories),
            "risk": _classification_metrics(risks, expected_risks),
        })
    return {
        "status": "smoke_test_only",
        "description": "Computed at request time on the six built-in examples in evaluation.py. This is a functional comparison, not an independent or held-out benchmark.",
        "sample_count": len(COMPARISON_CASES),
        "models": rows,
    }

router = APIRouter(prefix="/evaluation", tags=["Evaluation & Benchmarks"])

EVALUATION_METRICS = {
    "summary": {
        "macro_f1": 78.2,
        "risk_recall_high": 78.6,
        "multilingual_bleu": 36.8,
        "multilingual_chrf": 54.1,
        "slm_faithfulness": 74.5,
        "hallucination_rate": 14.0,
        "compute_cost_reduction": 42.6,
        "total_test_clauses": 9280,
        "total_annotated_contracts": 510,
        "inter_annotator_agreement_kappa": 0.86,
    },
    "benchmark_info": {
        "dataset_name": "CUAD v1.0 (Contract Understanding Atticus Dataset) + IndicLegal Multilingual Corpus",
        "benchmark_split": "80% Training/Calibration, 20% Held-Out Test Set (9,280 segmented clauses)",
        "annotator_verification": "Dual-blind legal review with Cohen's Kappa agreement κ = 0.86",
        "evaluation_standard": "Macro-averaged Precision, Recall, and F1 per category, ROC-AUC for severe risk, chrF++ and SacreBLEU for translation",
        "last_validated": "October 2026",
    },
    "cuad_classification": {
        "overall_accuracy": 77.8,
        "macro_precision": 77.4,
        "macro_recall": 79.1,
        "macro_f1": 78.2,
        "categories": [
            {"category": "Limitation of Liability", "precision": 0.77, "recall": 0.75, "f1": 0.760, "support": 820, "risk_bias": "High"},
            {"category": "Indemnification", "precision": 0.78, "recall": 0.79, "f1": 0.785, "support": 940, "risk_bias": "High"},
            {"category": "Termination for Convenience", "precision": 0.74, "recall": 0.72, "f1": 0.730, "support": 760, "risk_bias": "Medium/High"},
            {"category": "Automatic Renewal", "precision": 0.79, "recall": 0.77, "f1": 0.780, "support": 680, "risk_bias": "Medium/High"},
            {"category": "Confidentiality", "precision": 0.80, "recall": 0.78, "f1": 0.790, "support": 1120, "risk_bias": "Low"},
            {"category": "Payment Terms", "precision": 0.78, "recall": 0.80, "f1": 0.790, "support": 1050, "risk_bias": "Low"},
            {"category": "Governing Law & Dispute Resolution", "precision": 0.76, "recall": 0.75, "f1": 0.755, "support": 890, "risk_bias": "Medium"},
            {"category": "Non-Compete", "precision": 0.72, "recall": 0.71, "f1": 0.715, "support": 540, "risk_bias": "Medium"},
            {"category": "Warranty Disclaimer", "precision": 0.75, "recall": 0.76, "f1": 0.755, "support": 630, "risk_bias": "Medium"},
            {"category": "Force Majeure", "precision": 0.79, "recall": 0.78, "f1": 0.785, "support": 710, "risk_bias": "Low"},
            {"category": "Intellectual Property", "precision": 0.73, "recall": 0.72, "f1": 0.725, "support": 580, "risk_bias": "Medium/High"},
            {"category": "Assignment", "precision": 0.76, "recall": 0.75, "f1": 0.755, "support": 480, "risk_bias": "Low"},
            {"category": "Definitions", "precision": 0.80, "recall": 0.79, "f1": 0.795, "support": 950, "risk_bias": "Low"},
            {"category": "General Provisions", "precision": 0.71, "recall": 0.70, "f1": 0.705, "support": 700, "risk_bias": "Low"},
        ],
        "model_comparison": [
            {
                "model": "Keyword / Regex Taxonomy Baseline",
                "macro_precision": 72.4,
                "macro_recall": 70.8,
                "macro_f1": 71.6,
                "inference_ms": 1.4,
                "notes": "Fastest execution, vulnerable to paraphrasing & novel legal phrasing"
            },
            {
                "model": "Legal-BERT Dense Embeddings",
                "macro_precision": 76.1,
                "macro_recall": 74.3,
                "macro_f1": 75.2,
                "inference_ms": 18.5,
                "notes": "nlpaueb/legal-bert-base-uncased CLS representation captures legal nuance"
            },
            {
                "model": "CLAUSENT Hybrid Pipeline (Ensemble)",
                "macro_precision": 78.0,
                "macro_recall": 77.1,
                "macro_f1": 77.5,
                "inference_ms": 21.2,
                "notes": "Combines syntactic boundary analysis, regex taxonomy, and Legal-BERT vector representations"
            }
        ]
    },
    "risk_assessment": {
        "critical_false_negative_rate": 21.4,
        "calibration_error_ece": None,
        "levels": [
            {"level": "High Risk", "precision": 0.78, "recall": 0.786, "f1": 0.783, "support": 2340, "color": "var(--risk-high)"},
            {"level": "Medium Risk", "precision": 0.75, "recall": 0.76, "f1": 0.755, "support": 3120, "color": "var(--risk-med)"},
            {"level": "Low Risk", "precision": 0.79, "recall": 0.77, "f1": 0.780, "support": 3820, "color": "var(--risk-low)"}
        ],
        "confusion_matrix": {
            "labels": ["High", "Medium", "Low"],
            "matrix": [
                [1839, 350, 151],  # Illustrative High -> Pred High, Medium, Low
                [400, 2371, 349],  # Illustrative Medium -> Pred High, Medium, Low
                [450, 429, 2941]   # Illustrative Low -> Pred High, Medium, Low
            ]
        }
    },
    "multilingual": {
        "languages": [
            {
                "language": "English",
                "native_name": "English",
                "detection_accuracy": 78.0,
                "bleu_score": 36.8,
                "chrf_score": 54.1,
                "semantic_similarity": 0.780,
                "risk_parity": 78.0
            },
            {
                "language": "Tamil",
                "native_name": "தமிழ்",
                "detection_accuracy": 76.2,
                "bleu_score": 34.8,
                "chrf_score": 52.1,
                "semantic_similarity": 0.742,
                "risk_parity": 75.8
            },
            {
                "language": "Hindi",
                "native_name": "हिन्दी",
                "detection_accuracy": 78.1,
                "bleu_score": 38.4,
                "chrf_score": 57.2,
                "semantic_similarity": 0.771,
                "risk_parity": 78.0
            },
            {
                "language": "Malayalam",
                "native_name": "മലയാളം",
                "detection_accuracy": 73.9,
                "bleu_score": 32.6,
                "chrf_score": 49.5,
                "semantic_similarity": 0.718,
                "risk_parity": 72.6
            },
            {
                "language": "Telugu",
                "native_name": "తెలుగు",
                "detection_accuracy": 75.4,
                "bleu_score": 35.9,
                "chrf_score": 53.4,
                "semantic_similarity": 0.751,
                "risk_parity": 76.1
            }
        ]
    },
    "slm_vs_llm": {
        "traffic_distribution": {
            "slm_routed_percent": 71.2,
            "llm_routed_percent": 28.8
        },
        "comparison": [
            {
                "tier": "SLM — Qwen2.5-3B-Instruct (Local / Fast)",
                "role": "Routine low/medium risk clause summarization & plain-English explanation",
                "latency_ms": 142,
                "cost_per_1k_clauses": "$0.00",
                "rouge_1": 62.4,
                "rouge_2": 38.9,
                "rouge_l": 58.2,
                "factuality_score": 74.2,
                "hallucination_rate": 15.8,
                "routed_share": "71.2% (Low & Medium Risk Clauses)"
            },
            {
                "tier": "LLM — Gemini 2.5 Flash / OpenAI (Deep Counsel)",
                "role": "Deep legal reasoning, red-flag analysis, and mitigation strategy generation",
                "latency_ms": 1420,
                "cost_per_1k_clauses": "$1.40",
                "rouge_1": 74.8,
                "rouge_2": 51.2,
                "rouge_l": 71.0,
                "factuality_score": 78.1,
                "hallucination_rate": 12.4,
                "routed_share": "28.8% (High & Critical Risk Clauses)"
            }
        ],
        "compute_efficiency": {
            "all_llm_cost_index": 100.0,
            "hybrid_orchestrated_cost_index": 17.6,
            "total_savings_percent": 42.6,
            "latency_reduction_percent": 31.5
        }
    }
}

@router.get("/metrics")
def get_metrics():
    """
    Returns comprehensive evaluation and benchmarking metrics across CUAD classification,
    risk assessment, multilingual NLP, and hybrid SLM-LLM orchestration.
    """
    # Historical scorecard values below are retained for the existing UI, but
    # they are not backed by training/evaluation artifacts in this repository.
    # The smoke comparison is computed from the active code on every request.
    return {
        **EVALUATION_METRICS,
        "comparison": _smoke_comparison(),
        "benchmark_notice": (
            "The displayed CUAD/multilingual/SLM-LLM scorecard values are static and "
            "cannot be verified from this repository. Only the small built-in smoke "
            "comparison is computed from the current rule engine; it is not a held-out benchmark."
        ),
    }

@router.post("/test-clause")
def test_clause_evaluation(payload: Dict[str, Any] = Body(...)):
    """
    Evaluates a single clause live through the active classification and risk engine.
    """
    clause_text = payload.get("text", "").strip()
    if not clause_text:
        return {"error": True, "message": "Clause text cannot be empty."}

    start_time = time.perf_counter()

    # 1. Classification
    classification_res = ClassificationService.classify_clause(clause_text)
    category = classification_res.category or "General Provisions"
    confidence = classification_res.confidence or 70.0
    evidence = classification_res.evidence_spans or []

    # 2. Risk Assessment
    risk_res = RiskAssessmentService.assess_risk(clause_text, category)
    risk_level = risk_res.risk_level or "low"
    risk_score = risk_res.risk_score or 25
    rationale = risk_res.rationale or ""
    suggested_action = risk_res.suggested_action or ""
    uncertainty = risk_res.uncertainties[0] if risk_res.uncertainties else ""

    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

    # Expected comparison if user provided expected values
    expected_cat = payload.get("expected_category")
    expected_risk = payload.get("expected_risk")

    category_match = None
    if expected_cat:
        category_match = expected_cat.lower() in category.lower() or category.lower() in expected_cat.lower()

    risk_match = None
    if expected_risk:
        risk_match = expected_risk.lower() == risk_level.lower()

    return {
        "success": True,
        "input_text": clause_text,
        "latency_ms": elapsed_ms,
        "classification": {
            "predicted_category": category,
            "confidence": confidence,
            "evidence": evidence,
            "expected_category": expected_cat,
            "matches_expected": category_match
        },
        "risk_assessment": {
            "predicted_risk_level": risk_level,
            "risk_score": risk_score,
            "rationale": rationale,
            "suggested_action": suggested_action,
            "uncertainty": uncertainty,
            "expected_risk": expected_risk,
            "matches_expected": risk_match
        }
    }
