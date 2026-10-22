import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings, BASE_DIR
from app.core.logging_config import logger
from app.core.exceptions import ClausentBaseException
from app.database.connection import init_db
from app.api.routes import health, documents, analysis, reports

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure directories and database tables exist
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION} ({settings.APP_ENV})...")
    settings.ensure_directories()
    init_db()
    yield
    logger.info(f"Shutting down {settings.APP_NAME}...")

app = FastAPI(
    title="CLAUSENT API",
    description=(
        "CLAUSENT – AI-Powered Multilingual Contract Risk Analyzer.\n"
        "Provides contract text extraction, multilingual language detection, "
        "clause segmentation, Legal-BERT representation, CUAD-aligned clause classification, "
        "independent risk assessment, and hybrid SLM-LLM explanations."
    ),
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS (supports local development origins and any Render-deployed domains)
origins = settings.FRONTEND_ORIGINS
allow_all = "*" in origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if allow_all else origins,
    allow_origin_regex=r"https://.*\.onrender\.com" if not allow_all else None,
    allow_credentials=not allow_all,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom domain exception handler
@app.exception_handler(ClausentBaseException)
async def clausent_exception_handler(request: Request, exc: ClausentBaseException):
    logger.warning(f"Domain exception during '{exc.stage}': {exc.message}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": True,
            "stage": exc.stage,
            "message": exc.message,
            "details": exc.details
        }
    )

# Register API Routers under /api
app.include_router(health.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(analysis.router, prefix="/api")
app.include_router(reports.router, prefix="/api")

# Static frontend assets for unified production deployment
DIST_DIR = BASE_DIR.parent / "dist"
if not DIST_DIR.exists():
    alt_dist = Path("/app/dist")
    if alt_dist.exists():
        DIST_DIR = alt_dist

if (DIST_DIR / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(DIST_DIR / "assets")), name="assets")

@app.get("/")
def root():
    index_file = DIST_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/api/health"
    }

@app.get("/{full_path:path}")
async def serve_spa(request: Request, full_path: str):
    # Do not intercept API, docs, or OpenAPI endpoints
    if full_path.startswith(("api", "docs", "redoc", "openapi.json")):
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": "Not Found"})

    candidate = DIST_DIR / full_path
    if full_path and candidate.is_file():
        return FileResponse(str(candidate))

    index_file = DIST_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))

    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": "Not Found"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=settings.DEBUG
    )
