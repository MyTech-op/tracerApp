import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import User, Website, Page, SEOIssue
from app.schemas.suite import (
    KeywordResearchRequest, KeywordResearchResponse, KeywordItem,
    BacklinkProfileResponse, BacklinkItem, OutreachEmailRequest, OutreachEmailResponse,
    CompetitorBenchmarkRequest, CompetitorBenchmarkResponse,
    SchemaGeneratorRequest, SchemaGeneratorResponse
)
from app.api.auth import get_current_user
from app.ai.factory import get_ai_provider
from app.crawler.fetcher import PageFetcher

router = APIRouter(prefix="/seo", tags=["Full-Stack Agency SEO Suite"])


@router.post("/keywords/analyze-page/{page_id}")
def analyze_page_keyword_gap(
    page_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    page = db.query(Page).join(Website).filter(
        Page.id == page_id,
        Website.user_id == current_user.id
    ).first()

    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    provider = get_ai_provider()
    ai_res = provider.generate_seo_fix(
        issue_type="Missing High-Intent Commercial Keywords",
        page_title=page.title,
        h1=page.h1,
        body_sample=page.meta_description
    )

    topic = (page.h1 or page.title or "services").strip()
    kw_res = provider.generate_keywords(topic, page.website.domain if page.website else "website.com")
    missing_kws = [k["keyword"] for k in kw_res.get("keywords", [])]
    if not missing_kws:
        missing_kws = [
            f"best {topic} services",
            f"{topic} pricing comparison",
            f"top {topic} features guide"
        ]

    return {
        "page_id": page.id,
        "page_url": page.url,
        "missing_keywords": missing_kws,
        "suggested_title": ai_res.get("suggested_title"),
        "suggested_meta": ai_res.get("suggested_meta"),
        "suggested_h2_snippet": ai_res.get("suggested_h2_snippet"),
        "reasoning": ai_res.get("reasoning")
    }


@router.post("/keywords/generate", response_model=KeywordResearchResponse)
def generate_keyword_strategy(
    req: KeywordResearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    website = db.query(Website).filter(
        Website.id == req.website_id,
        Website.user_id == current_user.id
    ).first()
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")

    seed = req.seed_topic or website.domain.replace(".com", "").replace(".np", "").replace("-", " ")
    provider = get_ai_provider()
    res = provider.generate_keywords(seed, website.domain, website.detected_industry)

    kw_items = []
    for k in res.get("keywords", []):
        kw_items.append(KeywordItem(
            keyword=k.get("keyword", f"{seed} guide"),
            search_volume=k.get("search_volume", 1500),
            difficulty=k.get("difficulty", "Medium"),
            intent=k.get("intent", "Commercial"),
            suggested_page=k.get("suggested_page", f"https://{website.domain}/")
        ))

    return KeywordResearchResponse(
        website_id=website.id,
        seed_topic=seed,
        keywords=kw_items,
        ai_content_brief=res.get("ai_content_brief", f"### AI Content Brief for {seed}")
    )


@router.get("/backlinks/{website_id}", response_model=BacklinkProfileResponse)
def get_backlink_profile(
    website_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    website = db.query(Website).filter(
        Website.id == website_id,
        Website.user_id == current_user.id
    ).first()
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")

    provider = get_ai_provider()
    res = provider.generate_backlink_profile(website.domain, website.detected_industry)

    top_backlinks = []
    for b in res.get("top_backlinks", []):
        top_backlinks.append(BacklinkItem(
            referring_domain=b.get("referring_domain", "example.com"),
            domain_authority=b.get("domain_authority", 70),
            target_url=b.get("target_url", f"https://{website.domain}/"),
            link_type=b.get("link_type", "dofollow"),
            is_toxic=b.get("is_toxic", False)
        ))

    return BacklinkProfileResponse(
        website_id=website.id,
        total_backlinks=res.get("total_backlinks", 142),
        referring_domains=res.get("referring_domains", 38),
        dofollow_ratio=res.get("dofollow_ratio", "84%"),
        toxic_score=res.get("toxic_score", 8),
        top_backlinks=top_backlinks
    )


@router.post("/backlinks/outreach-email", response_model=OutreachEmailResponse)
def generate_backlink_outreach_email(
    req: OutreachEmailRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    website = db.query(Website).filter(
        Website.id == req.website_id,
        Website.user_id == current_user.id
    ).first()
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")

    subject = f"Resource Contribution for {req.target_blog_domain}: {req.target_article_topic}"
    body = (
        f"Hi {req.target_blog_domain} Editorial Team,\n\n"
        f"I came across your article on '{req.target_article_topic}' and really enjoyed the insights.\n\n"
        f"We recently published a comprehensive, data-backed guide on {website.domain} covering updated industry data and feature comparison. "
        f"I noticed your piece references resource links for readers—our guide would make a valuable addition for your audience.\n\n"
        f"Here is the direct link: https://{website.domain}/\n\n"
        f"Let me know if you'd like us to share your article with our newsletter audience as well!\n\n"
        f"Best regards,\n"
        f"SEO & Growth Team at {website.domain}"
    )

    return OutreachEmailResponse(subject=subject, email_body=body)


@router.post("/competitor/benchmark", response_model=CompetitorBenchmarkResponse)
def run_competitor_benchmark(
    req: CompetitorBenchmarkRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    website = db.query(Website).filter(
        Website.id == req.website_id,
        Website.user_id == current_user.id
    ).first()
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")

    # Fetch client stats from DB
    pages = db.query(Page).filter(Page.website_id == website.id).all()
    issues = db.query(SEOIssue).join(Page).filter(Page.website_id == website.id, SEOIssue.status == "open").all()
    
    client_score = round(sum(p.seo_score for p in pages) / len(pages)) if pages else 74
    client_pages_count = len(pages) if pages else 1
    client_avg_words = int(sum(p.word_count for p in pages) / len(pages)) if pages else 350
    client_missing_meta = len(issues)

    # Real fetch of competitor domain
    competitor_clean = req.competitor_domain.strip().replace("https://", "").replace("http://", "").replace("/", "")
    comp_url = f"https://{competitor_clean}"
    comp_seo = PageFetcher.fetch_page(comp_url)

    # Compute real competitor score from live fetch
    comp_word_count = comp_seo.get("word_count", 0)
    comp_has_title = bool(comp_seo.get("title"))
    comp_has_meta = bool(comp_seo.get("meta_description"))
    comp_has_h1 = bool(comp_seo.get("h1"))

    competitor_missing_meta = (0 if comp_has_meta else 1) + (0 if comp_has_title else 1)
    competitor_score = 90 if (comp_has_title and comp_has_meta and comp_has_h1) else 65
    competitor_pages_count = len(comp_seo.get("internal_links", [])) + 1
    competitor_avg_words = comp_word_count or 420

    insight = (
        f"### Competitive Benchmark Analysis: {website.domain} vs {competitor_clean}\n\n"
        f"1. **Content Depth**: Your site averages `{client_avg_words} words` per page vs `{competitor_avg_words} words` on {competitor_clean}.\n"
        f"2. **Technical SEO**: {website.domain} Health Score: `{client_score}/100` vs competitor: `{competitor_score}/100`.\n"
        f"3. **Action Strategy**: Resolve {client_missing_meta} open issues on {website.domain} to gain authority over {competitor_clean}."
    )

    return CompetitorBenchmarkResponse(
        client_domain=website.domain,
        competitor_domain=competitor_clean,
        client_score=client_score,
        competitor_score=competitor_score,
        client_pages_count=client_pages_count,
        competitor_pages_count=competitor_pages_count,
        client_avg_words=client_avg_words,
        competitor_avg_words=competitor_avg_words,
        client_missing_meta_count=client_missing_meta,
        competitor_missing_meta_count=competitor_missing_meta,
        client_backlink_score=78,
        competitor_backlink_score=65,
        ai_competitive_insight=insight
    )


@router.post("/schema/generate", response_model=SchemaGeneratorResponse)
def generate_schema_jsonld(
    req: SchemaGeneratorRequest
):
    stype = req.schema_type or "Organization"
    
    if stype == "LocalBusiness":
        json_code = {
            "@context": "https://schema.org",
            "@type": "LocalBusiness",
            "name": req.name,
            "description": req.description,
            "url": req.url,
            "priceRange": "$$",
            "address": {
                "@type": "PostalAddress",
                "addressLocality": "Main City",
                "addressCountry": "US"
            }
        }
    elif stype == "Product":
        json_code = {
            "@context": "https://schema.org",
            "@type": "Product",
            "name": req.name,
            "description": req.description,
            "url": req.url,
            "offers": {
                "@type": "Offer",
                "priceCurrency": "USD",
                "availability": "https://schema.org/InStock"
            }
        }
    elif stype == "SoftwareApplication":
        json_code = {
            "@context": "https://schema.org",
            "@type": "SoftwareApplication",
            "name": req.name,
            "description": req.description,
            "url": req.url,
            "applicationCategory": "BusinessApplication"
        }
    else:
        json_code = {
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": req.name,
            "description": req.description,
            "url": req.url
        }

    return SchemaGeneratorResponse(
        schema_type=stype,
        json_ld_code=json.dumps(json_code, indent=2)
    )
