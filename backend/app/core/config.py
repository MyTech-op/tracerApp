import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "SEOOps API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    DATABASE_URL: str = "mysql+pymysql://seoops_user:seoops_password@localhost:3306/seoops_db"
    REDIS_URL: str = "redis://localhost:6379/0"

    SECRET_KEY: str = "seoops_super_secret_jwt_key_2026_change_me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    AI_PROVIDER: str = "gemini"
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    # Hour (0-23, server-local) for the daily automated crawl of every tracked website.
    # Keeps report score trends populated without manual scans.
    SCHEDULED_SCAN_HOUR: int = 6

    # Secret guarding the POST/GET /scan/cron endpoint used by serverless cron
    # schedulers (e.g. Vercel Cron sends `Authorization: Bearer <CRON_SECRET>`).
    # Empty = cron scanning disabled.
    CRON_SECRET: str = ""

    # Google Search Console OAuth (create a Google Cloud OAuth client, scope:
    # https://www.googleapis.com/auth/webmasters.readonly)
    GSC_CLIENT_ID: str = ""
    GSC_CLIENT_SECRET: str = ""
    GSC_REDIRECT_URI: str = "http://localhost:8000/api/v1/gsc/callback"
    FRONTEND_URL: str = "http://localhost:3000"

    # Stripe billing (set STRIPE_SECRET_KEY to activate checkout/portal/webhook).
    # Price IDs are optional — when blank, prices are auto-created on first checkout.
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_STARTER: str = ""
    STRIPE_PRICE_GROWTH: str = ""
    STRIPE_PRICE_AGENCY: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
