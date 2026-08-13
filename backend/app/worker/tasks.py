import hashlib
import logging
from datetime import datetime
from urllib.parse import urlparse
from app.worker.celery import celery_app
from app.core.db import SessionLocal
from app.models import Website, Page, PageSnapshot, PageChange, SEOIssue, AISuggestion, CrawlJob
from app.crawler.fetcher import PageFetcher
from app.crawler.hasher import generate_content_hash
from app.seo.rules import SEORulesEngine
from app.seo.score import calculate_page_score
from app.ai.factory import get_ai_provider

logger = logging.getLogger(__name__)


@celery_app.task(name="run_website_crawl")
def run_website_crawl(job_id: int, website_id: int, max_pages: int = 25):
    db = SessionLocal()
    job = db.query(CrawlJob).filter(CrawlJob.id == job_id).first()
    website = db.query(Website).filter(Website.id == website_id).first()

    if not job or not website:
        db.close()
        return {"status": "error", "message": "Job or website not found"}

    try:
        job.status = "crawling"
        job.started_at = datetime.utcnow()
        website.status = "scanning"
        db.commit()

        # Build seed URL from domain
        domain = website.domain.strip()
        if not domain.startswith("http://") and not domain.startswith("https://"):
            seed_url = f"https://{domain}"
        else:
            seed_url = domain

        visited_urls = set()
        queue = [seed_url]
        pages_scanned = 0
        total_issues = 0

        ai_provider = get_ai_provider()

        while queue and pages_scanned < max_pages:
            target_url = queue.pop(0)

            # Normalize URL hash
            url_hash = hashlib.sha256(target_url.encode("utf-8")).hexdigest()
            if url_hash in visited_urls:
                continue
            visited_urls.add(url_hash)

            # 1. Fetch & Parse Page
            seo_data = PageFetcher.fetch_page(target_url)
            pages_scanned += 1

            # Queue newly discovered internal links
            for link in seo_data.get("internal_links", []):
                link_hash = hashlib.sha256(link.encode("utf-8")).hexdigest()
                if link_hash not in visited_urls and link not in queue:
                    queue.append(link)

            # 2. Compute Content Hash
            content_hash = generate_content_hash(
                title=seo_data.get("title"),
                meta_description=seo_data.get("meta_description"),
                h1=seo_data.get("h1"),
                text_content=seo_data.get("text_body_sample"),
                schema_type=seo_data.get("schema_type")
            )

            # 3. Evaluate SEO Rules & Score
            issues = SEORulesEngine.evaluate_page(seo_data, website.detected_industry)
            score = calculate_page_score(issues)

            # Check if page exists in DB (Tier 1: pages)
            existing_page = db.query(Page).filter(
                Page.website_id == website_id,
                Page.url_hash == url_hash
            ).first()

            if existing_page:
                is_changed = (existing_page.last_content_hash != content_hash)
                
                # Update Tier 1 current live state
                existing_page.status_code = seo_data.get("status_code", 200)
                existing_page.title = seo_data.get("title")
                existing_page.meta_description = seo_data.get("meta_description")
                existing_page.h1 = seo_data.get("h1")
                existing_page.canonical = seo_data.get("canonical")
                existing_page.robots = seo_data.get("robots")
                existing_page.schema_type = seo_data.get("schema_type")
                existing_page.word_count = seo_data.get("word_count", 0)
                existing_page.images_count = seo_data.get("images_count", 0)
                existing_page.missing_alt_count = seo_data.get("missing_alt_count", 0)
                existing_page.internal_links_count = len(seo_data.get("internal_links", []))
                existing_page.external_links_count = len(seo_data.get("external_links", []))
                existing_page.last_content_hash = content_hash
                existing_page.seo_score = score
                existing_page.last_crawled_at = datetime.utcnow()
                page_obj = existing_page
            else:
                is_changed = True
                page_obj = Page(
                    website_id=website_id,
                    url=target_url,
                    url_hash=url_hash,
                    status_code=seo_data.get("status_code", 200),
                    title=seo_data.get("title"),
                    meta_description=seo_data.get("meta_description"),
                    h1=seo_data.get("h1"),
                    canonical=seo_data.get("canonical"),
                    robots=seo_data.get("robots"),
                    schema_type=seo_data.get("schema_type"),
                    word_count=seo_data.get("word_count", 0),
                    images_count=seo_data.get("images_count", 0),
                    missing_alt_count=seo_data.get("missing_alt_count", 0),
                    internal_links_count=len(seo_data.get("internal_links", [])),
                    external_links_count=len(seo_data.get("external_links", [])),
                    last_content_hash=content_hash,
                    seo_score=score,
                    last_crawled_at=datetime.utcnow()
                )
                db.add(page_obj)
                db.flush()

            # 4. Incremental Optimization: Only write Tier 2 Snapshot & Tier 3 Changes if content changed
            if is_changed:
                snapshot = PageSnapshot(
                    page_id=page_obj.id,
                    snapshot_hash=content_hash,
                    raw_seo_json=seo_data,
                    created_at=datetime.utcnow()
                )
                db.add(snapshot)
                db.flush()

                page_change = PageChange(
                    page_id=page_obj.id,
                    current_snapshot_id=snapshot.id,
                    diff_json={
                        "title_changed": is_changed,
                        "word_count": seo_data.get("word_count", 0),
                        "issues_count": len(issues)
                    },
                    created_at=datetime.utcnow()
                )
                db.add(page_change)

            # Clear old open issues for this page and re-populate
            db.query(SEOIssue).filter(SEOIssue.page_id == page_obj.id).delete()
            
            for issue_dict in issues:
                total_issues += 1
                new_issue = SEOIssue(
                    page_id=page_obj.id,
                    issue_type=issue_dict["issue_type"],
                    severity=issue_dict["severity"],
                    description=issue_dict["description"],
                    status="open"
                )
                db.add(new_issue)
                db.flush()

                # Trigger AI suggestion ONLY if critical or warning issue
                if issue_dict["severity"] in ["critical", "warning"]:
                    try:
                        ai_res = ai_provider.generate_seo_fix(
                            issue_type=issue_dict["issue_type"],
                            page_title=seo_data.get("title"),
                            h1=seo_data.get("h1"),
                            body_sample=seo_data.get("text_body_sample")
                        )
                        suggestion = AISuggestion(
                            issue_id=new_issue.id,
                            suggested_title=ai_res.get("suggested_title"),
                            suggested_meta=ai_res.get("suggested_meta"),
                            suggested_h1=ai_res.get("suggested_h1"),
                            suggested_h2_snippet=ai_res.get("suggested_h2_snippet"),
                            reasoning=ai_res.get("reasoning"),
                            status="pending"
                        )
                        db.add(suggestion)
                    except Exception as e:
                        logger.warning(f"AI fix generation failed for issue {new_issue.id}: {str(e)}")

            db.commit()

        # Auto-detect industry & baseline score if not set
        all_pages = db.query(Page).filter(Page.website_id == website_id).all()
        if all_pages:
            avg_score = round(sum(p.seo_score for p in all_pages) / len(all_pages))
            if website.baseline_score is None:
                website.baseline_score = avg_score

            if not website.detected_industry:
                titles = [p.title for p in all_pages if p.title]
                samples = [p.meta_description for p in all_pages if p.meta_description]
                website.detected_industry = ai_provider.detect_industry(website.domain, titles, samples)

        # Finalize job status
        job.status = "completed"
        job.total_pages_scanned = pages_scanned
        job.total_issues_found = total_issues
        job.avg_score = avg_score if all_pages else None
        job.finished_at = datetime.utcnow()
        website.status = "active"
        website.last_scan_at = datetime.utcnow()
        db.commit()

        return {"status": "completed", "pages_scanned": pages_scanned, "issues_found": total_issues}

    except Exception as e:
        logger.error(f"Crawl job {job_id} failed: {str(e)}")
        job.status = "failed"
        job.error_message = str(e)
        job.finished_at = datetime.utcnow()
        website.status = "error"
        db.commit()
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()


@celery_app.task(name="run_scheduled_website_scans")
def run_scheduled_website_scans():
    """
    Celery Beat entrypoint: kicks off a crawl for every tracked website that is
    not currently scanning. Keeps report score trends populated automatically.
    """
    db = SessionLocal()
    started = 0
    skipped = 0
    try:
        websites = db.query(Website).filter(Website.status != "scanning").all()
        for website in websites:
            try:
                job = CrawlJob(website_id=website.id, status="pending")
                db.add(job)
                db.commit()
                db.refresh(job)

                try:
                    run_website_crawl.delay(job.id, website.id)
                except Exception:
                    # Celery broker unavailable: fall back to inline execution
                    run_website_crawl(job.id, website.id)
                started += 1
            except Exception as e:
                logger.warning(f"Scheduled scan failed for website {website.id}: {str(e)}")
                skipped += 1
                db.rollback()
        return {"status": "completed", "scans_started": started, "skipped": skipped}
    finally:
        db.close()


@celery_app.task(name="sync_all_gsc_profiles")
def sync_all_gsc_profiles():
    """
    Daily Celery task: pull Google Search Console data for every connected
    website so reports show real click/impression trends.
    """
    from app.services.gsc import sync_all_gsc_profiles as run_sync
    db = SessionLocal()
    try:
        return run_sync(db)
    finally:
        db.close()
