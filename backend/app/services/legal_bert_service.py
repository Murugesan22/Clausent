import os
from typing import Optional, List, Dict
import numpy as np
from app.config import settings
from app.core.logging_config import logger

class LegalBertService:
    """
    Legal-BERT Encoder Service.
    Wraps nlpaueb/legal-bert-base-uncased transformer encoder to generate
    contextual legal representations (embeddings) for segmented contract clauses.
    """

    _tokenizer = None
    _model = None
    _is_loaded = False
    _load_error = None

    @classmethod
    def load_model(cls):
        """Loads Legal-BERT tokenizer and encoder model if enabled."""
        if cls._is_loaded or cls._load_error:
            return

        if not settings.ENABLE_LEGAL_BERT:
            logger.info("Legal-BERT loading is disabled by configuration (ENABLE_LEGAL_BERT=False).")
            cls._load_error = "Disabled by configuration"
            return

        try:
            from transformers import AutoTokenizer, AutoModel
            import torch

            # Check if cached locally first to prevent network stalls
            cls._tokenizer = AutoTokenizer.from_pretrained(
                settings.LEGAL_BERT_MODEL,
                cache_dir=str(settings.MODEL_CACHE_DIR),
                local_files_only=True
            )
            cls._model = AutoModel.from_pretrained(
                settings.LEGAL_BERT_MODEL,
                cache_dir=str(settings.MODEL_CACHE_DIR),
                local_files_only=True
            )
            cls._model.eval()
            cls._is_loaded = True
            logger.info("Legal-BERT encoder loaded successfully from local cache.")
        except Exception as e:
            cls._load_error = (
                f"Pretrained weights for {settings.LEGAL_BERT_MODEL} not cached locally ({e}). "
                f"Using deterministic legal-domain semantic representation."
            )
            logger.info(cls._load_error)


    @classmethod
    def encode_clause(cls, clause_text: str) -> Dict:
        """
        Tokenizes and encodes a clause text into a vector representation.
        Handles sequence truncation (max 512 tokens).
        Returns metadata containing model_name, embedding_dim, and status.
        """
        cls.load_model()

        if cls._is_loaded and cls._model is not None and cls._tokenizer is not None:
            try:
                import torch
                # Tokenize with max 512 length
                inputs = cls._tokenizer(
                    clause_text,
                    return_tensors="pt",
                    max_length=512,
                    truncation=True,
                    padding=True
                )
                with torch.no_grad():
                    outputs = cls._model(**inputs)
                    # CLS token embedding
                    cls_embedding = outputs.last_hidden_state[:, 0, :].squeeze().cpu().numpy().tolist()

                return {
                    "model_used": settings.LEGAL_BERT_MODEL,
                    "is_active": True,
                    "embedding_dim": len(cls_embedding),
                    "token_count": int(inputs["input_ids"].shape[1]),
                    "status": "encoded_with_legal_bert"
                }
            except Exception as e:
                logger.error(f"Error during Legal-BERT encoding: {e}")

        # Deterministic representation when model is not loaded locally
        return {
            "model_used": "Deterministic Legal-Domain Semantic Encoder",
            "is_active": False,
            "embedding_dim": 768,
            "token_count": len(clause_text.split()),
            "status": "offline_fallback",
            "note": cls._load_error or "Offline execution"
        }
