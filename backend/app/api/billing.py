"""
Stripe billing: agency pricing tiers (Starter / Growth / Agency).

- GET  /billing/status    -> current plan + usage limits + subscription state
- POST /billing/checkout  -> {plan} -> Stripe Checkout URL
- POST /billing/portal    -> Stripe billing portal URL (manage / cancel)
- POST /billing/webhook   -> Stripe webhook (sync plan from Stripe)

All endpoints degrade gracefully: if STRIPE_SECRET_KEY is not set, checkout /
portal return 501 and status reports billing_configured=false. This keeps
local development and the free tier fully functional without Stripe.
"""
import logging
from datetime import datetime
from typing import Optional

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.core.plans import (
    PLANS,
    get_plan,
    plan_limits_response,
)
from app.models import User, Subscription
from app.api.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/billing", tags=["Billing"])

# Cache for auto-created prices: plan_id -> stripe price id
_price_cache: dict[str, str] = {}


def _billing_enabled() -> bool:
    return bool(settings.STRIPE_SECRET_KEY.strip())


def _stripe() -> stripe:
    if not _billing_enabled():
        raise HTTPException(status_code=501, detail="Billing is not configured (STRIPE_SECRET_KEY not set)")
    stripe.api_key = settings.STRIPE_SECRET_KEY
    return stripe


def _get_or_create_subscription(db: Session, user: User) -> Subscription:
    sub = db.query(Subscription).filter(Subscription.user_id == user.id).first()
    if sub is None:
        sub = Subscription(user_id=user.id, plan="free", status="inactive")
        db.add(sub)
        db.commit()
        db.refresh(sub)
    return sub


def _ensure_customer(s: stripe, user: User, sub: Subscription) -> str:
    if sub.stripe_customer_id:
        return sub.stripe_customer_id
    customer = s.Customer.create(email=user.email, metadata={"user_id": user.id})
    sub.stripe_customer_id = customer.id
    return customer.id


def _ensure_price(s: stripe, plan_id: str) -> str:
    """Return the plan's Stripe Price ID, auto-creating it on first use."""
    plan = get_plan(plan_id)
    if plan.stripe_price_id:
        return plan.stripe_price_id
    if plan_id in _price_cache:
        return _price_cache[plan_id]
    price = s.Price.create(
        currency="usd",
        unit_amount=plan.price_monthly_usd * 100,
        recurring={"interval": "month"},
        product_data={
            "name": f"SEOOps {plan.name}",
            "metadata": {"plan": plan.id},
        },
        metadata={"plan": plan.id},
    )
    _price_cache[plan_id] = price.id
    return price.id


def _plan_for_price(s: stripe, price_id: Optional[str]) -> str:
    if not price_id:
        return "free"
    for pid, plan in PLANS.items():
        if plan.stripe_price_id == price_id:
            return pid
    try:
        price = s.Price.retrieve(price_id)
        meta_plan = (price.get("metadata") or {}).get("plan")
        if meta_plan in PLANS:
            return meta_plan
    except Exception:
        pass
    return "free"


def _apply_subscription_status(db: Session, user: User, sub: Subscription,
                               status: str, plan: str, price_id: Optional[str],
                               period_end: Optional[datetime]) -> None:
    sub.status = status
    sub.plan = plan
    sub.stripe_price_id = price_id
    sub.current_period_end = period_end
    sub.updated_at = datetime.utcnow()
    if status in ("active", "trialing"):
        user.plan = plan
    elif status in ("canceled", "unpaid", "incomplete_expired"):
        user.plan = "free"
        sub.status = "canceled"
    # past_due / incomplete keep the paid plan so limits don't hard-flip mid-cycle
    db.commit()


class CheckoutRequest(BaseModel):
    plan: str


class CheckoutResponse(BaseModel):
    url: str


class BillingStatusResponse(BaseModel):
    billing_configured: bool
    plan: str
    plan_name: str
    price_monthly_usd: int
    max_sites: int
    sites_used: int
    sites_remaining: int
    max_pages_per_scan: int
    scan_interval_hours: int
    can_add_site: bool
    next_plan: Optional[str] = None
    subscription_status: str = "none"
    subscription_id: Optional[str] = None
    current_period_end: Optional[datetime] = None
    plans: dict


@router.get("/status", response_model=BillingStatusResponse)
def billing_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    limits = plan_limits_response(current_user, db)
    sub = db.query(Subscription).filter(Subscription.user_id == current_user.id).first()
    return BillingStatusResponse(
        billing_configured=_billing_enabled(),
        **limits,
        subscription_status=sub.status if sub else "none",
        subscription_id=sub.stripe_subscription_id if sub else None,
        current_period_end=sub.current_period_end if sub else None,
        plans={
            pid: {
                "id": p.id,
                "name": p.name,
                "price_monthly_usd": p.price_monthly_usd,
                "max_sites": p.max_sites,
                "max_pages_per_scan": p.max_pages_per_scan,
                "scan_interval_hours": p.scan_interval_hours,
                "description": p.description,
            }
            for pid, p in PLANS.items()
        },
    )


@router.post("/checkout", response_model=CheckoutResponse)
def create_checkout(
    req: CheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if req.plan not in PLANS or req.plan == "free":
        raise HTTPException(status_code=400, detail="Invalid plan for checkout")
    if req.plan == current_user.plan and _billing_enabled():
        sub = db.query(Subscription).filter(Subscription.user_id == current_user.id).first()
        if sub and sub.status in ("active", "trialing"):
            raise HTTPException(status_code=400, detail="You are already on this plan")

    s = _stripe()
    sub = _get_or_create_subscription(db, current_user)
    customer_id = _ensure_customer(s, current_user, sub)
    db.commit()

    price_id = _ensure_price(s, req.plan)
    session = s.checkout.Session.create(
        mode="subscription",
        customer=customer_id,
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=f"{settings.FRONTEND_URL}/billing?checkout=success",
        cancel_url=f"{settings.FRONTEND_URL}/billing?checkout=cancelled",
        client_reference_id=str(current_user.id),
        metadata={"user_id": current_user.id, "plan": req.plan},
    )
    return CheckoutResponse(url=session.url)


@router.post("/portal", response_model=CheckoutResponse)
def create_portal(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    s = _stripe()
    sub = db.query(Subscription).filter(Subscription.user_id == current_user.id).first()
    if not sub or not sub.stripe_customer_id:
        raise HTTPException(status_code=400, detail="No active subscription to manage")
    session = s.billing_portal.Session.create(
        customer=sub.stripe_customer_id,
        return_url=f"{settings.FRONTEND_URL}/billing",
    )
    return CheckoutResponse(url=session.url)


@router.post("/webhook")
async def billing_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if _billing_enabled() and settings.STRIPE_WEBHOOK_SECRET.strip() and sig_header:
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid signature")
    else:
        # Local / dev mode (or webhook secret not configured): trust the raw event.
        import json
        event = json.loads(payload)

    event_type = event.get("type", "")
    data = event.get("data", {}).get("object", {})

    if event_type == "checkout.session.completed":
        user_id = int(data.get("metadata", {}).get("user_id") or data.get("client_reference_id") or 0)
        plan = data.get("metadata", {}).get("plan") or "starter"
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            sub = _get_or_create_subscription(db, user)
            sub.stripe_customer_id = data.get("customer") or sub.stripe_customer_id
            sub.stripe_subscription_id = data.get("subscription") or sub.stripe_subscription_id
            _apply_subscription_status(db, user, sub, "active", plan, None, None)
        return {"received": True}

    if event_type == "customer.subscription.updated":
        sub_id = data.get("id")
        customer_id = data.get("customer")
        sub = None
        if sub_id:
            sub = db.query(Subscription).filter(Subscription.stripe_subscription_id == sub_id).first()
        if sub is None and customer_id:
            sub = db.query(Subscription).filter(Subscription.stripe_customer_id == customer_id).first()
        if sub:
            user = db.query(User).filter(User.id == sub.user_id).first()
            if user:
                s = _stripe() if _billing_enabled() else None
                price_id = None
                items = data.get("items", {}).get("data", [])
                if items:
                    price_id = items[0].get("price", {}).get("id")
                plan = _plan_for_price(s, price_id) if s else (get_plan(sub.plan).id if sub.plan else "free")
                period_end = data.get("current_period_end")
                end_dt = datetime.utcfromtimestamp(period_end) if period_end else None
                _apply_subscription_status(db, user, sub, data.get("status", "active"), plan, price_id, end_dt)
        return {"received": True}

    if event_type in ("customer.subscription.deleted", "customer.subscription.canceled"):
        sub_id = data.get("id")
        sub = None
        if sub_id:
            sub = db.query(Subscription).filter(Subscription.stripe_subscription_id == sub_id).first()
        if sub:
            user = db.query(User).filter(User.id == sub.user_id).first()
            if user:
                _apply_subscription_status(db, user, sub, "canceled", "free", None, None)
        return {"received": True}

    return {"received": True, "ignored": event_type}
