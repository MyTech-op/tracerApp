import hashlib


def generate_content_hash(
    title: str | None,
    meta_description: str | None,
    h1: str | None,
    text_content: str | None,
    schema_type: str | None
) -> str:
    """
    Generate SHA-256 hash representing the key SEO content of a page.
    If the hash matches the previous crawl's hash, content has not changed.
    """
    raw_data = "|".join([
        (title or "").strip(),
        (meta_description or "").strip(),
        (h1 or "").strip(),
        (text_content or "").strip()[:1000],  # Hash first 1000 chars of body text for stability
        (schema_type or "").strip()
    ])
    return hashlib.sha256(raw_data.encode("utf-8")).hexdigest()
