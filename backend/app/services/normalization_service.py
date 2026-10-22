from app.utils.text_processing import normalize_legal_text, validate_text_content
from app.core.exceptions import ExtractionError
from app.core.logging_config import logger

class NormalizationService:
    @staticmethod
    def normalize_document(raw_text: str) -> tuple[str, dict]:
        """
        Normalizes contract text while preserving legal traceability.
        Returns (normalized_text, metadata_dict).
        """
        is_valid, err_msg = validate_text_content(raw_text)
        if not is_valid:
            raise ExtractionError(err_msg)

        normalized = normalize_legal_text(raw_text)
        meta = {
            "raw_char_count": len(raw_text),
            "normalized_char_count": len(normalized),
            "line_count": len(normalized.splitlines()),
            "reduction_ratio": round((len(raw_text) - len(normalized)) / max(1, len(raw_text)), 3)
        }
        logger.info(f"Normalized contract text: {meta['raw_char_count']} chars -> {meta['normalized_char_count']} chars")
        return normalized, meta
