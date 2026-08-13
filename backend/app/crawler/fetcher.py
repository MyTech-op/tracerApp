import logging
import httpx
from app.crawler.parser import SEOParser

logger = logging.getLogger(__name__)


class PageFetcher:
    @staticmethod
    def fetch_page(url: str) -> dict:
        """
        Fetches URL HTML using HTTP client (httpx) with fallbacks, parsing SEO data.
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 (SEOOpsBot/1.0)"
        }
        
        # 1. Try standard request
        try:
            with httpx.Client(timeout=12.0, follow_redirects=True, verify=False) as client:
                response = client.get(url, headers=headers)
                return SEOParser.parse_html(url, response.text, status_code=response.status_code)
        except Exception as e1:
            logger.warning(f"HTTPS/primary fetch failed for {url}: {str(e1)}")
            
            # 2. Fallback: If URL started with https, try http
            if url.startswith("https://"):
                fallback_url = "http://" + url[8:]
                try:
                    with httpx.Client(timeout=12.0, follow_redirects=True, verify=False) as client:
                        response = client.get(fallback_url, headers=headers)
                        return SEOParser.parse_html(url, response.text, status_code=response.status_code)
                except Exception as e2:
                    logger.warning(f"HTTP fallback fetch failed for {fallback_url}: {str(e2)}")

            # 3. If completely unreachable
            return {
                "url": url,
                "status_code": 500,
                "title": None,
                "meta_description": None,
                "h1": None,
                "canonical": None,
                "robots": None,
                "schema_type": None,
                "word_count": 0,
                "images_count": 0,
                "missing_alt_count": 0,
                "internal_links": [],
                "external_links": [],
                "text_body_sample": ""
            }

