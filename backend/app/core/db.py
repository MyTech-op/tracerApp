import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

logger = logging.getLogger(__name__)

db_url = settings.DATABASE_URL
connect_args = {}

if "sqlite" in db_url:
    connect_args = {"check_same_thread": False}

try:
    engine = create_engine(
        db_url,
        pool_pre_ping=True,
        pool_recycle=3600,
        connect_args=connect_args,
        echo=False
    )
    with engine.connect() as conn:
        pass
except Exception as e:
    logger.warning(f"Primary database connection failed: {e}. Utilizing resilient local SQLite database fallback.")
    sqlite_url = "sqlite:///./seoops.db"
    engine = create_engine(
        sqlite_url,
        connect_args={"check_same_thread": False},
        echo=False
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
