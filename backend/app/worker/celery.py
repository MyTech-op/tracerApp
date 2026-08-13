from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery_app = Celery(
    "seoops_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kathmandu",
    enable_utc=True,
    imports=["app.worker.tasks"]
)

# Daily automated crawl of every tracked website so reporting score trends
# accumulate without manual scans. Run with: celery -A app.worker.celery beat
celery_app.conf.beat_schedule = {
    "daily-scheduled-seo-scans": {
        "task": "run_scheduled_website_scans",
        "schedule": crontab(hour=settings.SCHEDULED_SCAN_HOUR, minute=0),
    },
    "gsc-daily-sync": {
        "task": "sync_all_gsc_profiles",
        "schedule": crontab(hour=(settings.SCHEDULED_SCAN_HOUR + 1) % 24, minute=30),
    },
}
