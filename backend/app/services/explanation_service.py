from typing import Dict, List, Optional
from app.services.slm_service import SLMService
from app.services.llm_service import LLMService
from app.services.translation_service import TranslationService
from app.core.logging_config import logger

class ExplanationOrchestrator:
    """
    Hybrid SLM-LLM Orchestration Service.
    Intelligently routes clauses to SLM or LLM based on risk level, complexity,
    and user preferences, translating results into the target language.
    """

    @classmethod
    def orchestrate_explanation(
        cls,
        clause_text: str,
        category: str,
        risk_level: str,
        rationale: str,
        evidence: List[str],
        target_language: str = "English",
        force_llm: bool = False
    ) -> Dict:
        """
        Orchestrates explanation generation:
        - Low/Medium routine clauses -> SLM
        - High-risk or complex clauses -> SLM (summary) + LLM (detailed analysis)
        - Force LLM on user request
        """
        # 1. Always generate concise SLM explanation
        slm_result = SLMService.generate_explanation(clause_text, category, risk_level)
        raw_slm_text = slm_result["explanation"]
        slm_model = slm_result["model"]

        # 2. Determine if LLM detailed analysis is warranted
        llm_text = None
        llm_model = None

        should_invoke_llm = force_llm or (risk_level == "high") or (category in ("Limitation of Liability", "Indemnification", "Non-Compete"))

        if should_invoke_llm:
            try:
                llm_result = LLMService.generate_detailed_analysis(
                    clause_text=clause_text,
                    category=category,
                    risk_level=risk_level,
                    rationale=rationale,
                    evidence=evidence,
                    target_language=target_language
                )
                llm_text = llm_result["detailed_explanation"]
                llm_model = llm_result["model"]

            except Exception as e:
                logger.warning(f"LLM detailed analysis failed for clause ({e}). Retaining SLM summary.")

        # 3. Translate explanations into target language if non-English
        translated_slm = raw_slm_text
        if target_language.lower() != "english":
            translated_slm = TranslationService.translate_explanation(raw_slm_text, target_language)

        model_attribution = f"{slm_model}"
        if llm_model:
            model_attribution += f" + {llm_model}"

        return {
            "slm_explanation": translated_slm,
            "raw_slm_explanation": raw_slm_text,
            "llm_explanation": llm_text,
            "explanation_model": model_attribution,
            "target_language": target_language
        }
