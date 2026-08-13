from typing import Optional, List
from pydantic import BaseModel


# 1. Keyword Research Schemas
class KeywordItem(BaseModel):
    keyword: str
    search_volume: int
    difficulty: str  # Easy, Medium, Hard
    intent: str      # Commercial, Informational, Transactional
    suggested_page: str


class KeywordResearchRequest(BaseModel):
    website_id: int
    seed_topic: Optional[str] = None


class KeywordResearchResponse(BaseModel):
    website_id: int
    seed_topic: str
    keywords: List[KeywordItem]
    ai_content_brief: str


# 2. Backlink Intelligence & Outreach Schemas
class BacklinkItem(BaseModel):
    referring_domain: str
    domain_authority: int
    target_url: str
    link_type: str  # dofollow / nofollow
    is_toxic: bool


class BacklinkProfileResponse(BaseModel):
    website_id: int
    total_backlinks: int
    referring_domains: int
    dofollow_ratio: str
    toxic_score: int  # 0 to 100
    top_backlinks: List[BacklinkItem]


class OutreachEmailRequest(BaseModel):
    website_id: int
    target_blog_domain: str
    target_article_topic: str


class OutreachEmailResponse(BaseModel):
    subject: str
    email_body: str


# 3. Competitor Benchmark Schemas
class CompetitorBenchmarkRequest(BaseModel):
    website_id: int
    competitor_domain: str


class CompetitorBenchmarkResponse(BaseModel):
    client_domain: str
    competitor_domain: str
    
    client_score: int
    competitor_score: int
    
    client_pages_count: int
    competitor_pages_count: int
    
    client_avg_words: int
    competitor_avg_words: int
    
    client_missing_meta_count: int
    competitor_missing_meta_count: int
    
    client_backlink_score: int
    competitor_backlink_score: int
    
    ai_competitive_insight: str


# 4. Schema Generator Schemas
class SchemaGeneratorRequest(BaseModel):
    schema_type: str  # LocalBusiness, Organization, Trip, FAQPage
    name: str
    description: str
    url: str


class SchemaGeneratorResponse(BaseModel):
    schema_type: str
    json_ld_code: str
