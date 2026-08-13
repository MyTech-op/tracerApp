"""
Agency pricing tiers and limit enforcement.

Tiers are keyed by the `User.plan` column value. Limits are enforced at the
API boundary (site creation, manual scans) and inside the crawl task itself
(page cap), so no path can exceed a plan even if a caller forgets to check.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User
from app.models.website import Website
from app.models import CrawlJob


@dataclass(frozen=True)
class Plan:
    id: str
    name: str
    price_monthly_usd: int
    max_sites: int
    max_pages_per_scan: int
    scan_interval_hours: int  # minimum hours between scans of the same site
    description: str
    stripe_price_id: Optional[str] = None


def _env_price_id(setting: str) -> Optional[str]:
    val = getattr(settings, setting, "") or ""
    return val.strip() or None


PLANS: dict[str, Plan] = {
    "free": Plan(
        id="free",
        name="Free",
        price_monthly_usd=0,
        max_sites=1,
        max_pages_per_scan=10,
        scan_interval_hours=24,
        description="Evaluate SEOOps with one tracked site.",
    ),
    "starter": Plan(
        id="starter",
        name="Starter",
        price_monthly_usd=49,
        max_sites=3,
        max_pages_per_scan=25,
        scan_interval_hours=24,
        description="For freelancers with a handful of client sites.",
        stripe_price_id=_env_price_id("STRIPE_PRICE_STARTER"),
    ),
    "growth": Plan(
        id="growth",
        name="Growth",
        price_monthly_usd=99,
        max_sites=10,
        max_pages_per_scan=50,
        scan_interval_hours=6,
        description="For growing agencies — 4 scans a day per site.",
        stripe_price_id=_env_price_id("STRIPE_PRICE_GROWTH"),
    ),
    "agency": Plan(
        id="agency",
        name="Agency",
        price_monthly_usd=199,
        max_sites=25,
        max_pages_per_scan=100,
        scan_interval_hours=2,
        description="White-label scale — scans every 2 hours.",
        stripe_price_id=_env_price_id("STRIPE_PRICE_AGENCY"),
    ),
}

PLAN_ORDER = ["free", "starter", "growth", "agency"]


def get_plan(plan_id: str) -> Plan:
    return PLANS.get((plan_id or "free").lower(), PLANS["free"])


def site_count(db: Session, user: User) -> int:
    return db.query(Website).filter(Website.user_id == user.id).count()


def site_limit_check(db: Session, user: User) -> tuple[bool, int, int]:
    """Returns (allowed, used, limit) for the user's current plan."""
    plan = get_plan(user.plan)
    used = site_count(db, user)
    return used < plan.max_sites, used, plan.max_sites


def last_scan_at(db: Session, website_id: int) -> Optional[datetime]:
    job = (
        db.query(CrawlJob)
        .filter(CrawlJob.website_id == website_id)
        .order_by(CrawlJob.started_at.desc())
        .first()
    )
    if job and job.started_at:
        return job.started_at
    return None


def scan_allowed(db: Session, user: User, website_id: int) -> tuple[bool, Optional[datetime]]:
    """
    Returns (allowed, next_allowed_at) honoring the plan's scan interval.
    The interval is measured from the most recent scan start.
    """
    plan = get_plan(user.plan)
    last = last_scan_at(db, website_id)
    if last is None:
        return True, None
    next_at = last + timedelta(hours=plan.scan_interval_hours)
    return datetime.utcnow() >= next_at, next_at


def page_cap(user: User) -> int:
    """Max pages per scan for the user's plan."""
    return get_plan(user.plan).max_pages_per_scan


def enforce_page_cap(user: User, requested: Optional[int]) -> int:
    """Clamp a requested max_pages down to the plan's cap."""
    cap = page_cap(user)
    if requested is None or requested <= 0:
        return cap
    return min(requested, cap)


def plan_limits_response(user: User, db: Session) -> dict:
    plan = get_plan(user.plan)
    allowed, used, limit = site_limit_check(db, user)
    return {
        "plan": plan.id,
        "plan_name": plan.name,
        "price_monthly_usd": plan.price_monthly_usd,
        "max_sites": plan.max_sites,
        "sites_used": used,
        "sites_remaining": max(0, limit - used),
        "max_pages_per_scan": plan.max_pages_per_scan,
        "scan_interval_hours": plan.scan_interval_hours,
        "can_add_site": allowed,
        "next_plan": _next_plan_id(plan.id),
    }


def _next_plan_id(plan_id: str) -> Optional[str]:
    idx = PLAN_ORDER.index(plan_id) if plan_id in PLAN_ORDER else 0
    return PLAN_ORDER[idx + 1] if idx + 1 < len(PLAN_ORDER) else None
