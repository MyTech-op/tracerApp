import json
import logging
from typing import Dict, Any, Optional, List
from openai import OpenAI
from app.ai.provider import BaseAIProvider
from app.core.config import settings

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseAIProvider):
    def __init__(self):
        if settings.OPENAI_API_KEY:
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        else:
            self.client = None

    def generate_seo_fix(
        self,
        issue_type: str,
        page_title: Optional[str],
        h1: Optional[str],
        body_sample: Optional[str]
    ) -> Dict[str, Any]:
        if not self.client:
            return {
                "suggested_title": f"Optimized {page_title or 'Page Title'}",
                "suggested_meta": f"Comprehensive guide to {h1 or page_title or 'this page topic'}. Learn key insights.",
                "suggested_h1": h1 or page_title,
                "reasoning": "Fallback OpenAI recommendation (API Key not configured)."
            }

        prompt = f"""
You are an expert technical SEO specialist.
Target Page Issue: {issue_type}
Current Title: {page_title or 'N/A'}
Current H1: {h1 or 'N/A'}
Content Sample: {(body_sample or '')[:500]}

Generate an optimal meta description and title tag fixing the issue.
Return strict JSON with keys:
- suggested_title (string, max 60 chars)
- suggested_meta (string, max 155 chars)
- suggested_h1 (string)
- reasoning (string brief rationale)
"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            return {
                "suggested_title": f"Optimized - {page_title or 'Page Title'}",
                "suggested_meta": f"Discover insights about {h1 or page_title or 'our services'}. Read more here.",
                "suggested_h1": h1,
                "reasoning": f"Generated fallback recommendation due to OpenAI API error: {str(e)}"
            }

    def detect_industry(
        self,
        domain: str,
        page_titles: List[str],
        sample_texts: List[str]
    ) -> str:
        return "General Business"

    def generate_keywords(
        self,
        seed_topic: str,
        domain: str,
        industry: Optional[str] = None
    ) -> Dict[str, Any]:
        return {
            "keywords": [
                {
                    "keyword": f"best {seed_topic} pricing & packages",
                    "search_volume": 2400,
                    "difficulty": "Medium",
                    "intent": "Commercial",
                    "suggested_page": f"https://{domain}/pricing"
                }
            ],
            "ai_content_brief": f"### AI Content Brief for {seed_topic}"
        }

    def generate_backlink_profile(
        self,
        domain: str,
        industry: Optional[str] = None
    ) -> Dict[str, Any]:
        return {
            "total_backlinks": 120,
            "referring_domains": 30,
            "dofollow_ratio": "80%",
            "toxic_score": 10,
            "top_backlinks": []
        }
