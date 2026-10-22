from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.config import settings
from app.database.connection import get_db

router = APIRouter()

@router.get("/health", tags=["Health"])
def get_health(db: Session = Depends(get_db)):
    """
    Application health and dependency diagnostic endpoint.
    """
    db_status = "healthy"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "online",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "database": {
            "status": db_status,
            "engine": "sqlite" if settings.DATABASE_URL.startswith("sqlite") else "postgresql"
        },
        "nlp_services": {
            "legal_bert": {
                "model": settings.LEGAL_BERT_MODEL,
                "enabled": settings.ENABLE_LEGAL_BERT
            },
            "slm": {
                "provider": settings.SLM_PROVIDER,
                "model": settings.SLM_MODEL_NAME
            },
            "llm": {
                "provider": settings.LLM_PROVIDER,
                "model": settings.LLM_MODEL_NAME,
                "api_key_configured": bool(settings.LLM_API_KEY)
            },
            "translation": {
                "provider": settings.TRANSLATION_PROVIDER,
                "supported_languages": settings.SUPPORTED_LANGUAGES
            }
        }
    }
