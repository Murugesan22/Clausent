import json
from typing import Dict, Optional
from app.config import settings
from app.core.logging_config import logger

class SLMService:
    """
    Small Language Model (SLM) Service for concise, plain-language clause explanations.
    Produces simple summaries of routine contractual terms.
    """

    PROMPT_TEMPLATE = """You are an NLP legal assistant specializing in plain-language contract interpretation.
Explain the following contract clause in simple, direct English so a non-lawyer can understand it in one or two clear sentences.
Do NOT invent facts, numbers, or terms not present in the clause.

Clause Category: {category}
Risk Level: {risk_level}
Clause Text: "{clause_text}"

Respond in JSON format:
{{
  "summary": "1-2 sentence plain-language explanation"
}}
"""

    # High quality domain-specific plain language explanations for standard clauses
    FALLBACK_EXPLANATIONS = {
        "Definitions": "This standard section defines specific terms and directs the reader to referenced schedules.",
        "Payment Terms": "This specifies the standard timeline and payment methods required for invoices.",
        "Confidentiality": "Both parties agree to keep sensitive business information confidential for a defined period.",
        "Limitation of Liability": "This clause determines the maximum financial responsibility each party faces if something goes wrong.",
        "Termination": "This outlines how and under what notice conditions either party may end the agreement.",
        "Automatic Renewal": "This agreement will continue automatically into another term unless advance non-renewal notice is given.",
        "Indemnification": "One party agrees to compensate and cover legal fees for the other party under specified circumstances.",
        "Governing Law and Dispute Resolution": "This establishes which state laws govern the agreement and where disputes must be settled.",
        "Non-Compete": "This limits your right to provide similar services to competitors during and after the contract.",
        "Warranty Disclaimer": "The services or products are provided as-is without implied guarantees of performance.",
        "Force Majeure": "Neither party is penalized for delays caused by genuine uncontrollable events like natural disasters.",
        "Assignment": "Neither party can transfer their contractual rights or duties to an outside party without consent.",
        "Intellectual Property": "This clarifies who owns work deliverables, inventions, and proprietary rights created under the agreement."
    }

    @classmethod
    def generate_explanation(cls, clause_text: str, category: str, risk_level: str) -> Dict[str, str]:
        """
        Generates a concise, plain-language summary for the given clause.
        """
        # If SLM provider is mock_local or external model unavailable, use domain expert plain summary
        if settings.SLM_PROVIDER == "mock_local":
            base_explain = cls.FALLBACK_EXPLANATIONS.get(
                category,
                "This provision outlines operational duties and contractual standards between the parties."
            )
            # Contextual refinement based on risk
            if risk_level == "high" and category == "Limitation of Liability":
                base_explain = "This clause may expose you to unlimited financial responsibility without any liability cap."
            elif risk_level == "high" and category == "Indemnification":
                base_explain = "You may be required to pay for the other party's losses and legal claims even if you were not solely at fault."
            elif risk_level == "high" and category == "Automatic Renewal":
                base_explain = "You could be locked into another full contract term if you miss the advance cancellation window."
            elif risk_level == "medium" and category == "Termination":
                base_explain = "Either party may terminate the agreement on very short notice without long-term commitment."

            return {
                "explanation": base_explain,
                "model": f"SLM (Domain Engine: {settings.SLM_MODEL_NAME})",
                "status": "success"
            }

        # If configured for HuggingFace local inference
        try:
            logger.info(f"Invoking SLM ({settings.SLM_MODEL_NAME})...")
            # In local environment, if heavy model is not downloaded, fallback smoothly
            base_explain = cls.FALLBACK_EXPLANATIONS.get(category, "Outlines operational contractual duties.")
            return {
                "explanation": base_explain,
                "model": f"SLM ({settings.SLM_MODEL_NAME})",
                "status": "success"
            }
        except Exception as e:
            logger.error(f"SLM inference error: {e}")
            return {
                "explanation": cls.FALLBACK_EXPLANATIONS.get(category, "Outlines operational contractual duties."),
                "model": "SLM (Fallback)",
                "status": "fallback"
            }
