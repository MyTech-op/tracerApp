import json
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup


class SEOParser:
    @staticmethod
    def parse_html(url: str, html_content: str, status_code: int = 200) -> dict:
        soup = BeautifulSoup(html_content, "html.parser")
        parsed_url = urlparse(url)
        base_domain = parsed_url.netloc

        # Title Tag
        title_tag = soup.find("title")
        title = title_tag.get_text().strip() if title_tag else None

        # Meta Description
        meta_tag = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
        meta_description = meta_tag.get("content").strip() if meta_tag and meta_tag.get("content") else None

        # H1 Tag
        h1_tag = soup.find("h1")
        h1 = h1_tag.get_text().strip() if h1_tag else None

        # Canonical Tag
        canonical_tag = soup.find("link", attrs={"rel": "canonical"})
        canonical = canonical_tag.get("href").strip() if canonical_tag and canonical_tag.get("href") else None

        # Robots Tag
        robots_tag = soup.find("meta", attrs={"name": "robots"})
        robots = robots_tag.get("content").strip() if robots_tag and robots_tag.get("content") else None

        # Schema JSON-LD
        schema_type = None
        schema_tags = soup.find_all("script", attrs={"type": "application/ld+json"})
        for tag in schema_tags:
            try:
                data = json.loads(tag.string)
                if isinstance(data, dict):
                    schema_type = data.get("@type", "JSON-LD")
                elif isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                    schema_type = data[0].get("@type", "JSON-LD")
                if schema_type:
                    break
            except Exception:
                pass

        # Text Body & Word Count
        for elem in soup(["script", "style", "nav", "footer", "header"]):
            elem.extract()
        text_body = soup.get_text(separator=" ")
        words = [w for w in text_body.split() if len(w) > 1]
        word_count = len(words)

        # Images Analysis
        images = soup.find_all("img")
        images_count = len(images)
        missing_alt_count = sum(1 for img in images if not img.get("alt") or not img.get("alt").strip())

        # Internal & External Links Extraction
        internal_links = set()
        external_links = set()

        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if href.startswith("#") or href.startswith("javascript:") or href.startswith("mailto:"):
                continue
            
            full_url = urljoin(url, href)
            parsed_href = urlparse(full_url)

            if parsed_href.scheme in ["http", "https"]:
                if parsed_href.netloc == base_domain:
                    # Strip fragment and normalized path
                    clean_url = f"{parsed_href.scheme}://{parsed_href.netloc}{parsed_href.path}"
                    if clean_url.endswith("/") and len(clean_url) > 10:
                        clean_url = clean_url[:-1]
                    internal_links.add(clean_url)
                else:
                    external_links.add(full_url)

        return {
            "url": url,
            "status_code": status_code,
            "title": title,
            "meta_description": meta_description,
            "h1": h1,
            "canonical": canonical,
            "robots": robots,
            "schema_type": schema_type,
            "word_count": word_count,
            "images_count": images_count,
            "missing_alt_count": missing_alt_count,
            "internal_links": list(internal_links),
            "external_links": list(external_links),
            "text_body_sample": text_body[:1500]
        }
