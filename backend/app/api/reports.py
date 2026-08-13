import csv
import io
from typing import List, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import (
    User, Website, Page, SEOIssue, AISuggestion, CrawlJob, Lead, PageChange, FixVersion,
    SearchConsoleProfile, GSCMetric, GSCQueryMetric,
)
from app.api.auth import get_current_user

router = APIRouter(prefix="/reports", tags=["Reports"])


def _severity_counts(issues: List[SEOIssue]) -> Dict[str, int]:
    counts = {"critical": 0, "warning": 0, "info": 0}
    for issue in issues:
        sev = issue.severity if issue.severity in counts else "info"
        counts[sev] += 1
    return counts


def _site_snapshot(db: Session, website: Website) -> Dict[str, Any]:
    """Per-site KPI snapshot used by both the overview and single-site report."""
    pages = db.query(Page).filter(Page.website_id == website.id).all()
    issues = db.query(SEOIssue).join(Page).filter(
        Page.website_id == website.id, SEOIssue.status == "open"
    ).all()
    approved_fixes = db.query(AISuggestion).join(SEOIssue).join(Page).filter(
        Page.website_id == website.id, AISuggestion.status == "approved"
    ).count()
    leads_count = db.query(Lead).filter(Lead.website_id == website.id).count()
    scans = db.query(CrawlJob).filter(
        CrawlJob.website_id == website.id, CrawlJob.status == "completed"
    ).count()

    current_score = round(sum(p.seo_score for p in pages) / len(pages)) if pages else None
    baseline = website.baseline_score

    severity = _severity_counts(issues)

    return {
        "id": website.id,
        "domain": website.domain,
        "status": website.status,
        "industry": website.detected_industry,
        "current_score": current_score,
        "baseline_score": baseline,
        "score_delta": (current_score - baseline) if (current_score is not None and baseline is not None) else None,
        "pages_count": len(pages),
        "open_issues": len(issues),
        "critical_issues": severity["critical"],
        "warning_issues": severity["warning"],
        "info_issues": severity["info"],
        "approved_fixes": approved_fixes,
        "leads_captured": leads_count,
        "total_scans": scans,
        "last_scan_at": website.last_scan_at,
    }


@router.get("/overview")
def get_reports_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Aggregated reporting overview across every website the user manages.
    Drives the Reports hub page.
    """
    websites = db.query(Website).filter(Website.user_id == current_user.id).all()
    sites = [_site_snapshot(db, w) for w in websites]

    scored = [s for s in sites if s["current_score"] is not None]
    summary = {
        "total_sites": len(sites),
        "total_pages_scanned": sum(s["pages_count"] for s in sites),
        "avg_health_score": round(sum(s["current_score"] for s in scored) / len(scored)) if scored else None,
        "open_issues": sum(s["open_issues"] for s in sites),
        "critical_issues": sum(s["critical_issues"] for s in sites),
        "warning_issues": sum(s["warning_issues"] for s in sites),
        "info_issues": sum(s["info_issues"] for s in sites),
        "approved_fixes": sum(s["approved_fixes"] for s in sites),
        "leads_captured": sum(s["leads_captured"] for s in sites),
        "total_scans": sum(s["total_scans"] for s in sites),
    }

    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "summary": summary,
        "sites": sorted(sites, key=lambda s: s["current_score"] if s["current_score"] is not None else -1),
    }


@router.get("/website/{website_id}")
def get_website_report(
    website_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Full per-site SEO report: score trend over time, issue analytics,
    worst-performing pages, deployed fixes timeline and lead attribution.
    """
    website = db.query(Website).filter(
        Website.id == website_id,
        Website.user_id == current_user.id
    ).first()
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")

    snapshot = _site_snapshot(db, website)

    # Score trend: one point per completed crawl, oldest first
    jobs = db.query(CrawlJob).filter(
        CrawlJob.website_id == website_id,
        CrawlJob.status == "completed",
        CrawlJob.avg_score.isnot(None)
    ).order_by(CrawlJob.started_at.asc()).all()

    score_history = [
        {
            "date": job.started_at.isoformat() + "Z",
            "score": job.avg_score,
            "issues": job.total_issues_found,
            "pages": job.total_pages_scanned,
        }
        for job in jobs
    ]

    # Issue analytics
    open_issues = db.query(SEOIssue).join(Page).filter(
        Page.website_id == website_id, SEOIssue.status == "open"
    ).all()
    severity = _severity_counts(open_issues)

    issue_type_rows = {}
    for issue in open_issues:
        row = issue_type_rows.setdefault(issue.issue_type, {"issue_type": issue.issue_type, "count": 0, "severity": issue.severity})
        row["count"] += 1
    issue_breakdown = sorted(issue_type_rows.values(), key=lambda r: r["count"], reverse=True)

    # Worst-performing pages
    pages = db.query(Page).filter(Page.website_id == website_id).order_by(Page.seo_score.asc()).limit(10).all()
    top_pages = [
        {
            "id": p.id,
            "url": p.url,
            "title": p.title,
            "seo_score": p.seo_score,
            "word_count": p.word_count,
            "missing_alt_count": p.missing_alt_count,
            "status_code": p.status_code,
            "last_crawled_at": p.last_crawled_at.isoformat() + "Z" if p.last_crawled_at else None,
        }
        for p in pages
    ]

    # Deployed fixes timeline
    approved_fixes = db.query(AISuggestion).join(SEOIssue).join(Page).filter(
        Page.website_id == website_id, AISuggestion.status == "approved"
    ).order_by(AISuggestion.created_at.desc()).limit(50).all()

    fixes_timeline = [
        {
            "id": sug.id,
            "page_url": sug.issue.page.url if (sug.issue and sug.issue.page) else website.domain,
            "issue_type": sug.issue.issue_type if sug.issue else "SEO Fix",
            "applied_title": sug.suggested_title,
            "applied_meta": sug.suggested_meta,
            "approved_at": sug.created_at.isoformat() + "Z",
        }
        for sug in approved_fixes
    ]

    # Lead attribution by source
    leads = db.query(Lead).filter(Lead.website_id == website_id).all()
    source_counts: Dict[str, int] = {}
    for lead in leads:
        src = lead.source or "unknown"
        source_counts[src] = source_counts.get(src, 0) + 1
    leads_by_source = sorted(
        [{"source": k, "count": v} for k, v in source_counts.items()],
        key=lambda r: r["count"], reverse=True
    )

    changes_detected = db.query(PageChange).join(Page).filter(Page.website_id == website_id).count()
    versions_deployed = db.query(FixVersion).filter(FixVersion.website_id == website_id).count()

    # Google Search Console: real search performance
    profile = db.query(SearchConsoleProfile).filter(
        SearchConsoleProfile.website_id == website_id
    ).first()
    gsc = {
        "connected": bool(profile and profile.site_url),
        "site_url": profile.site_url if profile else None,
        "last_sync_at": profile.last_sync_at.isoformat() + "Z" if (profile and profile.last_sync_at) else None,
        "status": profile.status if profile else "disconnected",
        "error_message": profile.error_message if profile else None,
        "metrics": [],
        "top_queries": [],
    }
    if profile:
        gsc_metrics = db.query(GSCMetric).filter(
            GSCMetric.website_id == website_id
        ).order_by(GSCMetric.date.asc()).all()
        gsc["metrics"] = [
            {
                "date": str(m.date),
                "clicks": m.clicks,
                "impressions": m.impressions,
                "ctr": round(m.ctr, 4),
                "position": round(m.position, 2),
            }
            for m in gsc_metrics
        ]
        top_queries = db.query(GSCQueryMetric).filter(
            GSCQueryMetric.website_id == website_id
        ).order_by(GSCQueryMetric.date.desc(), GSCQueryMetric.clicks.desc()).limit(10).all()
        gsc["top_queries"] = [
            {
                "query": q.query,
                "date": str(q.date),
                "clicks": q.clicks,
                "impressions": q.impressions,
                "ctr": round(q.ctr, 4),
                "position": round(q.position, 2),
            }
            for q in top_queries
        ]

    return {
        **snapshot,
        "score_history": score_history,
        "severity_breakdown": severity,
        "issue_breakdown": issue_breakdown,
        "top_pages": top_pages,
        "fixes_timeline": fixes_timeline,
        "leads_by_source": leads_by_source,
        "changes_detected": changes_detected,
        "versions_deployed": versions_deployed,
        "gsc": gsc,
    }


@router.get("/website/{website_id}/export")
def export_website_report_csv(
    website_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Downloadable CSV report: summary row, every crawled page and every open issue.
    """
    website = db.query(Website).filter(
        Website.id == website_id,
        Website.user_id == current_user.id
    ).first()
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")

    pages = db.query(Page).filter(Page.website_id == website_id).order_by(Page.seo_score.asc()).all()
    issues = db.query(SEOIssue).join(Page).filter(
        Page.website_id == website_id, SEOIssue.status == "open"
    ).all()

    buffer = io.StringIO()
    writer = csv.writer(buffer)

    writer.writerow(["SEOOps SEO Report", website.domain, datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")])
    writer.writerow([])
    writer.writerow(["Summary"])
    writer.writerow(["Pages Scanned", len(pages)])
    writer.writerow(["Open Issues", len(issues)])
    writer.writerow(["Critical", sum(1 for i in issues if i.severity == "critical")])
    writer.writerow(["Warning", sum(1 for i in issues if i.severity == "warning")])
    writer.writerow(["Info", sum(1 for i in issues if i.severity == "info")])
    avg_score = round(sum(p.seo_score for p in pages) / len(pages)) if pages else ""
    writer.writerow(["Average SEO Health Score", avg_score])
    writer.writerow([])

    writer.writerow(["Pages"])
    writer.writerow(["URL", "Title", "Meta Description", "H1", "Status Code", "Word Count", "Missing Alt", "SEO Score", "Last Crawled"])
    for p in pages:
        writer.writerow([
            p.url,
            (p.title or "").replace("\n", " "),
            (p.meta_description or "").replace("\n", " "),
            (p.h1 or "").replace("\n", " "),
            p.status_code,
            p.word_count,
            p.missing_alt_count,
            p.seo_score,
            p.last_crawled_at.strftime("%Y-%m-%d %H:%M") if p.last_crawled_at else "",
        ])
    writer.writerow([])

    writer.writerow(["Open Issues"])
    writer.writerow(["Page URL", "Issue Type", "Severity", "Description", "Created"])
    for issue in issues:
        writer.writerow([
            issue.page.url if issue.page else "",
            issue.issue_type,
            issue.severity,
            issue.description.replace("\n", " "),
            issue.created_at.strftime("%Y-%m-%d %H:%M") if issue.created_at else "",
        ])

    filename = f"seoops_report_{website.domain.replace('.', '_')}_{datetime.utcnow().strftime('%Y%m%d')}.csv"
    return Response(
        content=buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
