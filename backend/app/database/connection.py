from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.config import settings
from app.core.logging_config import logger

# Database connection parameters
engine_kwargs = {"echo": False, "future": True}
if settings.DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # Industry-grade PostgreSQL connection pooling
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_recycle"] = 1800

try:
    engine = create_engine(settings.DATABASE_URL, **engine_kwargs)
except Exception as e:
    logger.warning(f"Could not create engine for {settings.DATABASE_URL}: {e}. Falling back to SQLite.")
    engine = create_engine("sqlite:///./clausent.db", connect_args={"check_same_thread": False}, echo=False, future=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    global engine, SessionLocal
    from app.database import models  # noqa: F401
    try:
        with engine.connect() as conn:
            pass
        Base.metadata.create_all(bind=engine)
        logger.info(f"Database initialized successfully ({engine.url.drivername}) with tables: {list(Base.metadata.tables.keys())}")
    except Exception as e:
        logger.warning(f"Could not connect to primary database ({settings.DATABASE_URL}). Reverting to SQLite fallback: {e}")
        engine = create_engine("sqlite:///./clausent.db", connect_args={"check_same_thread": False}, echo=False, future=True)
        SessionLocal.configure(bind=engine)
        Base.metadata.create_all(bind=engine)
        logger.info(f"Fallback SQLite initialized with tables: {list(Base.metadata.tables.keys())}")

