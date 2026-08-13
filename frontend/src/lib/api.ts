import axios from 'axios';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

export interface User {
  id: number;
  email: string;
  plan: string;
  created_at: string;
}

export interface UserSettings {
  agency_name?: string;
  semrush_api_key_set: boolean;
  ahrefs_api_key_set: boolean;
}

export interface Website {
  id: number;
  user_id: number;
  domain: string;
  status: string;
  last_scan_at?: string;
  created_at: string;
}

export interface CrawlJob {
  id: number;
  website_id: number;
  status: string;
  total_pages_scanned: number;
  total_issues_found: number;
  error_message?: string;
  started_at: string;
  finished_at?: string;
}

export interface PageItem {
  id: number;
  website_id: number;
  url: string;
  status_code: number;
  title?: string;
  meta_description?: string;
  h1?: string;
  canonical?: string;
  word_count: number;
  missing_alt_count: number;
  seo_score: number;
  last_crawled_at: string;
}

export interface AISuggestion {
  id: number;
  issue_id: number;
  suggested_title?: string;
  suggested_meta?: string;
  suggested_h1?: string;
  suggested_h2_snippet?: string;
  reasoning?: string;
  status: string;
}

export interface SEOIssue {
  id: number;
  page_id: number;
  issue_type: string;
  severity: 'critical' | 'warning' | 'info';
  description: string;
  status: string;
  page_url?: string;
  suggestions: AISuggestion[];
}

export interface LeadItem {
  id: number;
  website_id: number;
  name?: string;
  email?: string;
  phone?: string;
  message?: string;
  source: string;
  utm_source?: string;
  utm_medium?: string;
  utm_campaign?: string;
  page_url?: string;
  created_at: string;
}

export interface KeywordItem {
  keyword: string;
  search_volume: number;
  difficulty: string;
  intent: string;
  suggested_page: string;
}

export interface BacklinkItem {
  referring_domain: string;
  domain_authority: number;
  target_url: string;
  link_type: string;
  is_toxic: boolean;
}

export interface BacklinkProfile {
  website_id: number;
  total_backlinks: number;
  referring_domains: number;
  dofollow_ratio: string;
  toxic_score: number;
  top_backlinks: BacklinkItem[];
}

export interface CompetitorBenchmark {
  client_domain: string;
  competitor_domain: string;
  client_score: number;
  competitor_score: number;
  client_pages_count: number;
  competitor_pages_count: number;
  client_avg_words: number;
  competitor_avg_words: number;
  client_missing_meta_count: number;
  competitor_missing_meta_count: number;
  client_backlink_score: number;
  competitor_backlink_score: number;
  ai_competitive_insight: string;
}

export interface ReportSiteSnapshot {
  id: number;
  domain: string;
  status: string;
  industry?: string;
  current_score?: number;
  baseline_score?: number;
  score_delta?: number;
  pages_count: number;
  open_issues: number;
  critical_issues: number;
  warning_issues: number;
  info_issues: number;
  approved_fixes: number;
  leads_captured: number;
  total_scans: number;
  last_scan_at?: string;
}

export interface ReportOverview {
  generated_at: string;
  summary: {
    total_sites: number;
    total_pages_scanned: number;
    avg_health_score?: number;
    open_issues: number;
    critical_issues: number;
    warning_issues: number;
    info_issues: number;
    approved_fixes: number;
    leads_captured: number;
    total_scans: number;
  };
  sites: ReportSiteSnapshot[];
}

export interface ScorePoint {
  date: string;
  score: number;
  issues: number;
  pages: number;
}

export interface GSCMetricPoint {
  date: string;
  clicks: number;
  impressions: number;
  ctr: number;
  position: number;
}

export interface GSCQueryRow {
  query: string;
  date: string;
  clicks: number;
  impressions: number;
  ctr: number;
  position: number;
}

export interface GSCBlock {
  connected: boolean;
  site_url?: string;
  last_sync_at?: string;
  status: string;
  error_message?: string;
  metrics: GSCMetricPoint[];
  top_queries: GSCQueryRow[];
}

export interface WebsiteReport extends ReportSiteSnapshot {
  score_history: ScorePoint[];
  severity_breakdown: { critical: number; warning: number; info: number };
  issue_breakdown: { issue_type: string; count: number; severity: string }[];
  top_pages: PageItem[];
  fixes_timeline: {
    id: number;
    page_url: string;
    issue_type: string;
    applied_title?: string;
    applied_meta?: string;
    approved_at: string;
  }[];
  leads_by_source: { source: string; count: number }[];
  changes_detected: number;
  versions_deployed: number;
  gsc: GSCBlock;
}
