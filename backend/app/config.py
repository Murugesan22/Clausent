import os
from pathlib import Path
from typing import List

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent

# Automatically load backend/.env
env_file = BASE_DIR / ".env"
if env_file.exists():
    try:
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    if k not in os.environ:
                        os.environ[k] = v
    except Exception:
        pass

def get_env_list(key: str, default: str) -> List[str]:
    raw = os.getenv(key, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


class Settings:
    BASE_DIR: Path = BASE_DIR
    APP_NAME: str = os.getenv("APP_NAME", "CLAUSENT")
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = os.getenv("APP_ENV", "development")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")

    BACKEND_HOST: str = os.getenv("HOST", os.getenv("BACKEND_HOST", "0.0.0.0"))
    BACKEND_PORT: int = int(os.getenv("PORT", os.getenv("BACKEND_PORT", "8000")))

    # CORS
    FRONTEND_ORIGINS: List[str] = get_env_list(
        "FRONTEND_ORIGIN",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000"
    )

    # Database (automatically adapts Render's postgres:// URI scheme to SQLAlchemy's postgresql://)
    raw_db_url = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{(BASE_DIR / 'clausent.db').as_posix()}"
    )
    if raw_db_url.startswith("postgres://"):
        raw_db_url = raw_db_url.replace("postgres://", "postgresql://", 1)
    DATABASE_URL: str = raw_db_url

    # File Storage
    UPLOAD_DIR: Path = BASE_DIR / os.getenv("UPLOAD_DIR", "data/uploads")
    REPORT_DIR: Path = BASE_DIR / os.getenv("REPORT_DIR", "data/reports")
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "25"))
    ALLOWED_EXTENSIONS: List[str] = get_env_list("ALLOWED_EXTENSIONS", "pdf,docx,txt")

    # Models Cache
    MODEL_CACHE_DIR: Path = BASE_DIR / os.getenv("MODEL_CACHE_DIR", "data/models")
    LEGAL_BERT_MODEL: str = os.getenv("LEGAL_BERT_MODEL", "nlpaueb/legal-bert-base-uncased")
    ENABLE_LEGAL_BERT: bool = os.getenv("ENABLE_LEGAL_BERT", "True").lower() in ("true", "1", "yes")

    # SLM Settings
    SLM_PROVIDER: str = os.getenv("SLM_PROVIDER", "mock_local")  # mock_local, hf_local, api
    SLM_MODEL_NAME: str = os.getenv("SLM_MODEL_NAME", "Qwen/Qwen2.5-3B-Instruct")
    SLM_DEVICE: str = os.getenv("SLM_DEVICE", "cpu")

    # LLM Settings
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "mock_local")  # mock_local, gemini, openai, ollama
    LLM_MODEL_NAME: str = os.getenv("LLM_MODEL_NAME", "gemini-2.5-flash")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_TIMEOUT_SECONDS: int = int(os.getenv("LLM_TIMEOUT_SECONDS", "30"))

    # Translation
    TRANSLATION_PROVIDER: str = os.getenv("TRANSLATION_PROVIDER", "indic_nllb")
    DEFAULT_TARGET_LANGUAGE: str = os.getenv("DEFAULT_TARGET_LANGUAGE", "English")

    SUPPORTED_LANGUAGES: List[str] = ["English", "Tamil", "Hindi", "Malayalam", "Telugu"]

    def ensure_directories(self):
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        self.REPORT_DIR.mkdir(parents=True, exist_ok=True)
        self.MODEL_CACHE_DIR.mkdir(parents=True, exist_ok=True)

settings = Settings()
settings.ensure_directories()
