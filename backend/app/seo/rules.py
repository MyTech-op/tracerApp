from typing import List, Dict, Any, Optional


class SEORulesEngine:
    @staticmethod
    def evaluate_page(page_data: Dict[str, Any], industry: Optional[str] = None) -> List[Dict[str, Any]]:
        issues = []

        title = page_data.get("title")
        meta = page_data.get("meta_description")
        h1 = page_data.get("h1")
        canonical = page_data.get("canonical")
        missing_alt = page_data.get("missing_alt_count", 0)
        word_count = page_data.get("word_count", 0)
        status_code = page_data.get("status_code", 200)

        # Rule 1: HTTP Status Error
        if status_code >= 400:
            issues.append({
                "issue_type": "Broken Page Status",
                "severity": "critical",
                "description": f"Page returned HTTP status code {status_code}."
            })

        # Rule 2: Missing Title
        if not title or len(title.strip()) == 0:
            issues.append({
                "issue_type": "Missing Title",
                "severity": "critical",
                "description": "Page is missing a HTML <title> tag."
            })
        elif len(title) > 60:
            issues.append({
                "issue_type": "Title Too Long",
                "severity": "warning",
                "description": f"Title tag is {len(title)} characters (recommended max 60 chars)."
            })

        # Rule 3: Missing Meta Description
        if not meta or len(meta.strip()) == 0:
            issues.append({
                "issue_type": "Missing Meta Description",
                "severity": "critical",
                "description": "Page is missing a meta description tag."
            })
        elif len(meta) > 160:
            issues.append({
                "issue_type": "Meta Description Too Long",
                "severity": "warning",
                "description": f"Meta description is {len(meta)} characters (recommended max 160 chars)."
            })

        # Rule 4: Title equals Meta
        if title and meta and title.strip().lower() == meta.strip().lower():
            issues.append({
                "issue_type": "Title Equals Meta Description",
                "severity": "warning",
                "description": "Title tag and meta description are identical."
            })

        # Rule 5: Missing H1
        if not h1 or len(h1.strip()) == 0:
            issues.append({
                "issue_type": "Missing H1",
                "severity": "critical",
                "description": "Page is missing a primary <h1> heading tag."
            })

        # Rule 6: Missing Canonical Tag
        if not canonical:
            issues.append({
                "issue_type": "Missing Canonical Tag",
                "severity": "warning",
                "description": "Page is missing a rel='canonical' tag."
            })

        # Rule 7: Missing Alt Tags
        if missing_alt > 0:
            issues.append({
                "issue_type": "Missing Alt Text",
                "severity": "warning",
                "description": f"{missing_alt} image(s) on the page are missing descriptive alt attribute."
            })

        # Rule 8: Low Word Count
        if word_count < 250:
            issues.append({
                "issue_type": "Thin Content",
                "severity": "info",
                "description": f"Page content has only {word_count} words (recommended minimum 250 words)."
            })

        # Rule 9: Missing High-Intent Commercial Keywords (Dynamic Industry Terms)
        combined_text = f"{title or ''} {meta or ''} {h1 or ''}".lower()
        
        # Universal commercial intent terms
        commercial_terms = ["cost", "price", "package", "review", "guide", "service", "pricing", "buy", "best", "features"]
        if industry and ("travel" in industry.lower() or "tour" in industry.lower()):
            commercial_terms.extend(["destinations", "tours", "trips"])
        elif industry and ("e-commerce" in industry.lower() or "retail" in industry.lower()):
            commercial_terms.extend(["shipping", "discount", "order", "store", "product"])
        elif industry and ("tech" in industry.lower() or "software" in industry.lower()):
            commercial_terms.extend(["platform", "demo", "solution", "integration"])

        found_terms = [t for t in commercial_terms if t in combined_text]
        
        if len(found_terms) < 2 and word_count > 50:
            issues.append({
                "issue_type": "Missing High-Intent Commercial Keywords",
                "severity": "warning",
                "description": f"Page lacks high-converting commercial intent search terms ({', '.join(commercial_terms[:4])}). Adding targeted long-tail keywords will increase search conversions."
            })

        return issues
