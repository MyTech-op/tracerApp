from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.core.config import settings
from app.core.db import engine, Base
# Import all models to register with Base
import app.models

from app.api import auth, website, scan, pages, issues, ai, lead, suite, portal, reports, gsc, billing, settings as settings_api

from sqlalchemy import inspect, text

# Create database tables automatically on startup if they don't exist
try:
    Base.metadata.create_all(bind=engine)
except Exception:
    pass

def sync_db_columns():
    try:
        with engine.connect() as conn:
            inspector = inspect(engine)
            if "crawl_jobs" in inspector.get_table_names():
                job_cols = [c["name"] for c in inspector.get_columns("crawl_jobs")]
                if "avg_score" not in job_cols:
                    conn.execute(text("ALTER TABLE crawl_jobs ADD COLUMN avg_score INTEGER NULL"))
            if "users" in inspector.get_table_names():
                user_cols = [c["name"] for c in inspector.get_columns("users")]
                if "logo" not in user_cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN logo TEXT NULL"))
            conn.commit()
    except Exception:
        pass

sync_db_columns()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(website.router, prefix=settings.API_V1_STR)
app.include_router(scan.router, prefix=settings.API_V1_STR)
app.include_router(pages.router, prefix=settings.API_V1_STR)
app.include_router(issues.router, prefix=settings.API_V1_STR)
app.include_router(ai.router, prefix=settings.API_V1_STR)
app.include_router(lead.router, prefix=settings.API_V1_STR)
app.include_router(suite.router, prefix=settings.API_V1_STR)
app.include_router(portal.router, prefix=settings.API_V1_STR)
app.include_router(reports.router, prefix=settings.API_V1_STR)
app.include_router(gsc.router, prefix=settings.API_V1_STR)
app.include_router(billing.router, prefix=settings.API_V1_STR)
app.include_router(settings_api.router, prefix=settings.API_V1_STR)


@app.get("/")
def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "running",
        "docs": f"{settings.API_V1_STR}/docs"
    }


@app.get("/docs", include_in_schema=False)
def redirect_docs():
    return RedirectResponse(url=f"{settings.API_V1_STR}/docs")


@app.get("/redoc", include_in_schema=False)
def redirect_redoc():
    return RedirectResponse(url=f"{settings.API_V1_STR}/redoc")


@app.get("/health")
def health_check():
    return {"status": "ok"}
