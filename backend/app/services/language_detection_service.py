import re
from typing import Tuple
from app.core.exceptions import LanguageDetectionError
from app.core.logging_config import logger

class LanguageDetectionService:
    # Unicode script ranges for supported Indian languages
    SCRIPT_RANGES = {
        "Tamil": (0x0B80, 0x0BFF),
        "Telugu": (0x0C00, 0x0C7F),
        "Malayalam": (0x0D00, 0x0D7F),
        "Hindi": (0x0900, 0x097F),  # Devanagari script
    }

    LANG_CODE_MAP = {
        "en": "English",
        "ta": "Tamil",
        "hi": "Hindi",
        "ml": "Malayalam",
        "te": "Telugu",
    }

    @classmethod
    def detect_language(cls, text: str) -> Tuple[str, float]:
        """
        Detects document language using a combination of Unicode script analysis
        and statistical n-gram detection (langdetect).
        Returns (language_name, confidence).
        """
        if not text or len(text.strip()) < 10:
            return "English", 0.50

        # Sample up to first 2500 characters for speed and reliability
        sample = text[:2500]

        # 1. Script-based character frequency analysis (100% deterministic for Indic scripts)
        script_counts = {lang: 0 for lang in cls.SCRIPT_RANGES}
        total_indic = 0

        for ch in sample:
            code = ord(ch)
            for lang, (start, end) in cls.SCRIPT_RANGES.items():
                if start <= code <= end:
                    script_counts[lang] += 1
                    total_indic += 1
                    break

        if total_indic >= 15:
            # Significant Indic characters found
            pred_lang = max(script_counts, key=script_counts.get)
            pred_ratio = script_counts[pred_lang] / max(1, total_indic)
            confidence = min(0.99, max(0.70, round(pred_ratio, 2)))
            logger.info(f"Detected {pred_lang} via Unicode script analysis (conf: {confidence})")
            return pred_lang, confidence

        # 2. Statistical langdetect for Latin / English / other scripts
        try:
            from langdetect import detect_langs
            predictions = detect_langs(sample)
            if predictions:
                top = predictions[0]
                lang_code = top.lang.lower()
                confidence = round(top.prob, 2)
                mapped_lang = cls.LANG_CODE_MAP.get(lang_code, "English")
                logger.info(f"Detected {mapped_lang} via langdetect (raw code: {lang_code}, conf: {confidence})")
                return mapped_lang, confidence
        except Exception as e:
            logger.warning(f"langdetect error or not available: {e}. Falling back to English default.")

        # Default fallback
        return "English", 0.85
