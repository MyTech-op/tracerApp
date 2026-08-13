from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List


class BaseAIProvider(ABC):
    @abstractmethod
    def generate_seo_fix(
        self,
        issue_type: str,
        page_title: Optional[str],
        h1: Optional[str],
        body_sample: Optional[str]
    ) -> Dict[str, Any]:
        """
        Generates AI recommendations for a specific SEO issue.
        """
        pass

    @abstractmethod
    def detect_industry(
        self,
        domain: str,
        page_titles: List[str],
        sample_texts: List[str]
    ) -> str:
        """
        Detects website industry/niche based on crawled page titles and body text.
        """
        pass

    @abstractmethod
    def generate_keywords(
        self,
        seed_topic: str,
        domain: str,
        industry: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generates keyword strategy with search volume, difficulty, intent, and content brief.
        """
        pass

    @abstractmethod
    def generate_backlink_profile(
        self,
        domain: str,
        industry: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generates an AI-estimated backlink profile and toxic link assessment.
        """
        pass
