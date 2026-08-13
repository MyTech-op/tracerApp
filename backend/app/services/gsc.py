"""Google Search Console integration.

OAuth2 (web-server flow) + Search Analytics API via plain httpx — no Google SDKs,
so the serverless bundle stays small. Tokens are encrypted at rest via
app.core.security.encrypt_secret.
"""
import logging
from datetime import datetime, timedelta, date
from typing import Dict, Any, List, Optional
from urllib.parse import urlencode

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import encrypt_secret, decrypt_secret, sign_state
from app.models import Website, SearchConsoleProfile, GSCMetric, GSCQueryMetric

logger = logging.getLogger(__name__)

TOKEN_URL = "https://oauth2.googleapis.com/token"
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
WEBMASTERS_BASE = "https://searchconsole.googleapis.com/webmasters/v3"
SCOPE = "https://www.googleapis.com/auth/webmasters.readonly"
SYNC_DAYS = 30
TOP_QUERY_LIMIT = 25


class GSCError(Exception):
    pass


# ---------------------------------------------------------------- OAuth flow

def build_auth_url(website_id: int) -> str:
    """Build the Google OAuth consent URL for a website (state is HMAC-signed)."""
    state = sign_state(str(website_id))
    params = {
        "client_id": settings.GSC_CLIENT_ID,
        "redirect_uri": settings.GSC_REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPE,
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    return f"{AUTH_URL}?{urlencode(params)}"


def _post_token(params: Dict[str, str], client: httpx.Client) -> Dict[str, Any]:
    res = client.post(TOKEN_URL, data=params)
    if res.status_code != 200:
        raise GSCError(f"Token request failed ({res.status_code}): {res.text[:300]}")
    data = res.json()
    if "access_token" not in data:
        raise GSCError(f"Token response missing access_token: {res.text[:300]}")
    return data


def exchange_code(code: str, client: Optional[httpx.Client] = None) -> Dict[str, Any]:
    """Exchange an authorization code for access + refresh tokens."""
    with (client or httpx.Client(timeout=30)) as c:
        return _post_token({
            "code": code,
            "client_id": settings.GSC_CLIENT_ID,
            "client_secret": settings.GSC_CLIENT_SECRET,
            "redirect_uri": settings.GSC_REDIRECT_URI,
            "grant_type": "authorization_code",
        }, c)


def _refresh_token(refresh_token: str, client: httpx.Client) -> Dict[str, Any]:
    return _post_token({
        "client_id": settings.GSC_CLIENT_ID,
        "client_secret": settings.GSC_CLIENT_SECRET,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }, client)


def _access_token(profile: SearchConsoleProfile, client: httpx.Client) -> str:
    """Return a valid access token, refreshing + persisting it if expired/near expiry."""
    now = datetime.utcnow()
    expires_at = profile.token_expires_at or now - timedelta(seconds=1)
    if expires_at > now + timedelta(minutes=2) and profile.access_token_encrypted:
        return decrypt_secret(profile.access_token_encrypted)

    data = _refresh_token(decrypt_secret(profile.refresh_token_encrypted), client)
    profile.access_token_encrypted = encrypt_secret(data["access_token"])
    profile.token_expires_at = now + timedelta(seconds=int(data.get("expires_in", 3600)))
    return data["access_token"]


# ------------------------------------------------------------------ API calls

def _list_sites(access_token: str, client: httpx.Client) -> List[str]:
    res = client.get(
        f"{WEBMASTERS_BASE}/sites",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    if res.status_code != 200:
        raise GSCError(f"Failed to list GSC sites ({res.status_code}): {res.text[:300]}")
    entries = res.json().get("siteEntry", [])
    return [e.get("siteUrl", "") for e in entries]


def pick_matching_property(site_urls: List[str], domain: str) -> Optional[str]:
    """Prefer an exact sc-domain/https match for the tracked domain."""
    domain = domain.lower().strip()
    exact = [
        u for u in site_urls
        if u.lower() in (f"sc-domain:{domain}", f"https://{domain}/", f"http://{domain}/")
    ]
    if exact:
        return exact[0]
    sc_domain = [u for u in site_urls if u.lower().startswith("sc-domain:")]
    if sc_domain:
        return sc_domain[0]
    return None


def _search_analytics(access_token: str, site_url: str, start_date: date, end_date: date,
                      dimensions: List[str], row_limit: int, client: httpx.Client) -> List[Dict[str, Any]]:
    from urllib.parse import quote
    url = f"{WEBMASTERS_BASE}/sites/{quote(site_url, safe='')}/searchAnalytics/query"
    res = client.post(
        url,
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "dimensions": dimensions,
            "rowLimit": row_limit,
            "type": "web",
        },
    )
    if res.status_code != 200:
        raise GSCError(f"Search Analytics failed ({res.status_code}): {res.text[:300]}")
    return res.json().get("rows", [])


# ----------------------------------------------------------------------- sync

def _sync_with_client(db: Session, website: Website, client: httpx.Client) -> Dict[str, Any]:
    profile = db.query(SearchConsoleProfile).filter(
        SearchConsoleProfile.website_id == website.id
    ).first()
    if not profile or not profile.refresh_token_encrypted:
        return {"status": "not_connected"}

    try:
        access_token = _access_token(profile, client)

        # Resolve the GSC property (auto-pick once, persist it)
        if not profile.site_url:
            sites = _list_sites(access_token, client)
            matched = pick_matching_property(sites, website.domain)
            if not matched:
                profile.status = "error"
                profile.error_message = (
                    f"No Search Console property found for {website.domain}. "
                    "Verify the domain in Google Search Console first."
                )
                db.commit()
                return {"status": "error", "error_message": profile.error_message}
            profile.site_url = matched

        start = date.today() - timedelta(days=SYNC_DAYS - 1)
        end = date.today()

        # Daily site-level metrics
        daily_rows = _search_analytics(access_token, profile.site_url, start, end, ["date"], 1000, client)
        for row in daily_rows:
            keys = row.get("keys", [])
            if not keys:
                continue
            try:
                metric_date = datetime.strptime(keys[0], "%Y-%m-%d").date()
            except ValueError:
                continue
            metric = db.query(GSCMetric).filter(
                GSCMetric.website_id == website.id, GSCMetric.date == metric_date
            ).first()
            if metric is None:
                metric = GSCMetric(website_id=website.id, date=metric_date)
                db.add(metric)
            metric.clicks = int(row.get("clicks", 0))
            metric.impressions = int(row.get("impressions", 0))
            metric.ctr = float(row.get("ctr", 0.0))
            metric.position = float(row.get("position", 0.0))

        # Top queries snapshot for the window (bounded storage: one row per query per sync day)
        query_rows = _search_analytics(access_token, profile.site_url, start, end, ["query"], TOP_QUERY_LIMIT, client)
        today = date.today()
        db.query(GSCQueryMetric).filter(
            GSCQueryMetric.website_id == website.id, GSCQueryMetric.date == today
        ).delete(synchronize_session=False)
        for row in query_rows:
            keys = row.get("keys", [])
            if not keys:
                continue
            db.add(GSCQueryMetric(
                website_id=website.id,
                date=today,
                query=keys[0][:255],
                clicks=int(row.get("clicks", 0)),
                impressions=int(row.get("impressions", 0)),
                ctr=float(row.get("ctr", 0.0)),
                position=float(row.get("position", 0.0)),
            ))

        profile.status = "connected"
        profile.error_message = None
        profile.last_sync_at = datetime.utcnow()
        db.commit()
        return {"status": "ok", "rows": len(daily_rows)}
    except Exception as e:
        db.rollback()
        profile.status = "error"
        profile.error_message = str(e)[:500]
        db.commit()
        logger.warning(f"GSC sync failed for {website.domain}: {str(e)}")
        return {"status": "error", "error_message": str(e)}


def sync_gsc_for_website(db: Session, website: Website, client: Optional[httpx.Client] = None) -> Dict[str, Any]:
    """Sync Search Console data for one website. `client` is injectable for tests."""
    if client is not None:
        return _sync_with_client(db, website, client)
    with httpx.Client(timeout=45) as c:
        return _sync_with_client(db, website, c)


def sync_all_gsc_profiles(db: Session) -> Dict[str, Any]:
    """Sync every connected website's Search Console data (daily task)."""
    websites = db.query(Website).join(SearchConsoleProfile).all()
    results = []
    for website in websites:
        res = sync_gsc_for_website(db, website)
        results.append({"domain": website.domain, **res})
    return {"synced": len(websites), "results": results}


def connect_website(db: Session, website: Website, code: str) -> Dict[str, Any]:
    """Complete the OAuth handshake: exchange code, store tokens, auto-pick property."""
    token_data = exchange_code(code)
    profile = db.query(SearchConsoleProfile).filter(
        SearchConsoleProfile.website_id == website.id
    ).first()
    if profile is None:
        profile = SearchConsoleProfile(website_id=website.id)
        db.add(profile)

    profile.access_token_encrypted = encrypt_secret(token_data["access_token"])
    profile.refresh_token_encrypted = encrypt_secret(token_data["refresh_token"])
    profile.token_expires_at = datetime.utcnow() + timedelta(seconds=int(token_data.get("expires_in", 3600)))
    profile.status = "connected"
    profile.error_message = None
    db.commit()

    # Immediate first sync (also auto-picks the property if a match exists)
    return sync_gsc_for_website(db, website)
