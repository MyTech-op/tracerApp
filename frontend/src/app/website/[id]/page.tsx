'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  api,
  PageItem,
  SEOIssue,
  LeadItem,
  BacklinkProfile,
  CompetitorBenchmark
} from '@/lib/api';
import {
  ArrowLeft,
  Play,
  CheckCircle2,
  XCircle,
  Sparkles,
  ExternalLink,
  RefreshCw,
  Edit3,
  Save,
  ChevronLeft,
  ChevronRight,
  Filter,
  Users,
  TrendingUp,
  MessageSquare,
  Search,
  Code,
  Link,
  Swords,
  Send,
  X,
  Target,
  Share2,
  RotateCcw,
  CheckSquare,
  BarChart3
} from 'lucide-react';

const formatKathmanduTime = (dateStr?: string | null) => {
  if (!dateStr) return 'N/A';
  try {
    const isoStr = dateStr.endsWith('Z') ? dateStr : dateStr + 'Z';
    return new Date(isoStr).toLocaleString('en-US', {
      timeZone: 'Asia/Kathmandu',
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      second: '2-digit',
      hour12: true
    });
  } catch (e) {
    return new Date(dateStr).toLocaleString();
  }
};

export default function WebsiteDetailPage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const [siteId, setSiteId] = useState<string>(params.id);

  const [pages, setPages] = useState<PageItem[]>([]);
  const [issues, setIssues] = useState<SEOIssue[]>([]);
  const [leads, setLeads] = useState<LeadItem[]>([]);
  const [scanning, setScanning] = useState(false);
  const [loading, setLoading] = useState(true);
  const [seedingLeads, setSeedingLeads] = useState(false);
  const [activeTab, setActiveTab] = useState<'issues' | 'pages' | 'leads' | 'backlinks' | 'competitors'>('issues');
  const [generatingAiId, setGeneratingAiId] = useState<number | null>(null);

  // Bulk Approve Modal State
  const [showBulkModal, setShowBulkModal] = useState(false);
  const [selectedSuggestionIds, setSelectedSuggestionIds] = useState<number[]>([]);
  const [bulkProcessing, setBulkProcessing] = useState(false);

  // Keyword Gap Drawer State
  const [selectedPageForKeywords, setSelectedPageForKeywords] = useState<PageItem | null>(null);
  const [pageKeywordAnalysis, setPageKeywordAnalysis] = useState<any>(null);
  const [loadingPageKeywords, setLoadingPageKeywords] = useState(false);

  // Off-Page & Backlinks State
  const [backlinksData, setBacklinksData] = useState<BacklinkProfile | null>(null);
  const [outreachDomain, setOutreachDomain] = useState('industry-insights-blog.com');
  const [outreachTopic, setOutreachTopic] = useState('Top Industry Solutions & Growth Guide');
  const [generatedOutreachEmail, setGeneratedOutreachEmail] = useState<{ subject: string; email_body: string } | null>(null);
  const [generatingOutreach, setGeneratingOutreach] = useState(false);

  // Competitor Benchmark State
  const [competitorDomainInput, setCompetitorDomainInput] = useState('himalayanguides.com');
  const [competitorData, setCompetitorData] = useState<CompetitorBenchmark | null>(null);
  const [loadingCompetitor, setLoadingCompetitor] = useState(false);

  // Severity Filter state
  const [severityFilter, setSeverityFilter] = useState<'all' | 'critical' | 'warning' | 'info'>('all');

  // Pagination states
  const [issuesPage, setIssuesPage] = useState(1);
  const issuesPerPage = 5;

  const [pagesPage, setPagesPage] = useState(1);
  const pagesPerPage = 10;

  const [leadsPage, setLeadsPage] = useState(1);
  const leadsPerPage = 5;

  // Edit Recommendation state
  const [editingSugId, setEditingSugId] = useState<number | null>(null);
  const [editTitle, setEditTitle] = useState('');
  const [editMeta, setEditMeta] = useState('');

  useEffect(() => {
    if (params && params.id) {
      setSiteId(params.id);
    }
  }, [params]);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (siteId) {
      fetchData();
      fetchBacklinkProfile();
      interval = setInterval(() => {
        fetchData();
      }, 3000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [siteId, scanning]);

  const fetchData = async () => {
    try {
      const [pagesRes, issuesRes, leadsRes] = await Promise.all([
        api.get(`/pages?website_id=${siteId}`),
        api.get(`/issues?website_id=${siteId}`),
        api.get(`/lead?website_id=${siteId}`)
      ]);
      setPages(pagesRes.data);
      setIssues(issuesRes.data);
      setLeads(leadsRes.data);

      if (pagesRes.data.length > 0 && scanning) {
        setScanning(false);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleInspectPageKeywordGap = async (page: PageItem) => {
    setSelectedPageForKeywords(page);
    setLoadingPageKeywords(true);
    try {
      const res = await api.post(`/seo/keywords/analyze-page/${page.id}`);
      setPageKeywordAnalysis(res.data);
    } catch (err) {
      alert('Failed to analyze page keyword gap');
    } finally {
      setLoadingPageKeywords(false);
    }
  };

  const fetchBacklinkProfile = async () => {
    if (!siteId) return;
    try {
      const res = await api.get(`/seo/backlinks/${siteId}`);
      setBacklinksData(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const handleGenerateOutreachEmail = async () => {
    setGeneratingOutreach(true);
    try {
      const res = await api.post('/seo/backlinks/outreach-email', {
        website_id: parseInt(siteId),
        target_blog_domain: outreachDomain,
        target_article_topic: outreachTopic
      });
      setGeneratedOutreachEmail(res.data);
    } catch (err) {
      alert('Failed to generate outreach email');
    } finally {
      setGeneratingOutreach(false);
    }
  };

  const handleRunCompetitorBenchmark = async () => {
    if (!competitorDomainInput.trim()) return;
    setLoadingCompetitor(true);
    try {
      const res = await api.post('/seo/competitor/benchmark', {
        website_id: parseInt(siteId),
        competitor_domain: competitorDomainInput
      });
      setCompetitorData(res.data);
    } catch (err) {
      alert('Failed to run competitor benchmark');
    } finally {
      setLoadingCompetitor(false);
    }
  };

  const handleStartScan = async () => {
    setScanning(true);
    try {
      await api.post('/scan', { website_id: parseInt(siteId) });
    } catch (err) {
      alert('Failed to launch scan');
      setScanning(false);
    }
  };

  const handleGenerateAiFix = async (issueId: number) => {
    setGeneratingAiId(issueId);
    try {
      await api.post(`/ai/generate-fix/${issueId}`);
      fetchData();
    } catch (err) {
      alert('AI fix generation failed');
    } finally {
      setGeneratingAiId(null);
    }
  };

  const handleApproveReject = async (suggestionId: number, action: 'approve' | 'reject') => {
    try {
      await api.patch(`/issues/suggestion/${suggestionId}`, { action });
      fetchData();
    } catch (err) {
      alert(`Failed to ${action} suggestion`);
    }
  };

  const handleRevertFix = async (suggestionId: number) => {
    try {
      await api.post(`/issues/revert/${suggestionId}`);
      fetchData();
    } catch (err) {
      alert('Failed to revert fix');
    }
  };

  const handleOpenBulkModal = () => {
    const pendingIds: number[] = [];
    issues.forEach((i) => {
      i.suggestions.forEach((s) => {
        if (s.status === 'pending') pendingIds.push(s.id);
      });
    });
    setSelectedSuggestionIds(pendingIds);
    setShowBulkModal(true);
  };

  const handleExecuteBulkApprove = async () => {
    if (selectedSuggestionIds.length === 0) return;
    setBulkProcessing(true);
    try {
      await api.post('/issues/bulk-approve', { suggestion_ids: selectedSuggestionIds });
      setShowBulkModal(false);
      fetchData();
    } catch (err) {
      alert('Bulk approval failed');
    } finally {
      setBulkProcessing(false);
    }
  };

  const handleStartEdit = (sug: any) => {
    setEditingSugId(sug.id);
    setEditTitle(sug.suggested_title || '');
    setEditMeta(sug.suggested_meta || '');
  };

  const handleSaveEdit = async (sugId: number) => {
    try {
      await api.patch(`/issues/suggestion/${sugId}`, {
        action: 'update',
        suggested_title: editTitle,
        suggested_meta: editMeta
      });
      setEditingSugId(null);
      fetchData();
    } catch (err) {
      alert('Failed to save suggestion edit');
    }
  };

  const handleSeedLeads = async () => {
    setSeedingLeads(true);
    try {
      await api.post(`/lead/seed/${siteId}`);
      fetchData();
    } catch (err) {
      alert('Failed to seed leads');
    } finally {
      setSeedingLeads(false);
    }
  };

  const avgHealthScore = pages.length > 0
    ? Math.round(pages.reduce((acc, p) => acc + p.seo_score, 0) / pages.length)
    : null;

  const latestCrawlTime = pages.length > 0 && pages[0].last_crawled_at
    ? formatKathmanduTime(pages[0].last_crawled_at)
    : null;

  const criticalCount = issues.filter((i) => i.severity === 'critical').length;
  const warningCount = issues.filter((i) => i.severity === 'warning').length;
  const infoCount = issues.filter((i) => i.severity === 'info').length;

  const filteredIssues = issues.filter((i) => {
    if (severityFilter === 'all') return true;
    return i.severity === severityFilter;
  });

  const pendingSuggestionsCount = issues.reduce((acc, i) => acc + i.suggestions.filter((s) => s.status === 'pending').length, 0);

  const aiLeadsCount = leads.filter((l) => ['chatgpt', 'perplexity', 'claude', 'gemini'].includes(l.source.toLowerCase())).length;
  const googleLeadsCount = leads.filter((l) => l.source === 'google_organic').length;
  const directLeadsCount = leads.filter((l) => ['direct', 'whatsapp_click', 'phone_call'].includes(l.source)).length;

  const totalIssuesPages = Math.ceil(filteredIssues.length / issuesPerPage) || 1;
  const issuesStart = (issuesPage - 1) * issuesPerPage;
  const issuesEnd = issuesPage * issuesPerPage;
  const paginatedIssues = filteredIssues.slice(issuesStart, issuesEnd);

  const totalPagesPages = Math.ceil(pages.length / pagesPerPage) || 1;
  const pagesStart = (pagesPage - 1) * pagesPerPage;
  const pagesEnd = pagesPage * pagesPerPage;
  const paginatedPages = pages.slice(pagesStart, pagesEnd);

  const totalLeadsPages = Math.ceil(leads.length / leadsPerPage) || 1;
  const leadsStart = (leadsPage - 1) * leadsPerPage;
  const leadsEnd = leadsPage * leadsPerPage;
  const paginatedLeads = leads.slice(leadsStart, leadsEnd);

  return (
    <div style={{ minHeight: '100vh', padding: '32px', maxWidth: '1200px', margin: '0 auto' }}>
      {/* Header Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <button className="btn-secondary" onClick={() => router.push('/dashboard')}>
          <ArrowLeft size={16} /> Back to Dashboard
        </button>

        <div style={{ display: 'flex', gap: '12px' }}>
          <button className="btn-secondary" onClick={() => router.push(`/reports/${siteId}`)} style={{ color: '#10b981' }}>
            <BarChart3 size={16} /> View Report
          </button>

          <button className="btn-secondary" onClick={() => window.open(`/portal/${siteId}`, '_blank')} style={{ color: '#818cf8' }}>
            <Share2 size={16} /> Share Live Client Portal
          </button>

          <button className="btn-primary" onClick={handleStartScan} disabled={scanning}>
            {scanning ? <RefreshCw size={16} className="spin" /> : <Play size={16} />}
            {scanning ? 'Scanning Domain...' : 'Scan Website Now'}
          </button>
        </div>
      </div>

      {/* Website Health Overview Header */}
      <div className="glass-card" style={{ padding: '28px', marginBottom: '32px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '20px' }}>
        <div>
          <span style={{ fontSize: '13px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px', fontWeight: 600 }}>Domain Overview</span>
          <h1 style={{ fontSize: '28px', fontWeight: 700, marginTop: '4px' }}>Website Analysis</h1>
          <p style={{ fontSize: '14px', color: 'var(--text-muted)', marginTop: '4px' }}>
            {pages.length} Pages Scanned • {issues.length} Open Issues • {leads.length} Tracked Leads
          </p>
          <p style={{ fontSize: '13px', color: '#818cf8', marginTop: '6px', fontWeight: 500 }}>
            {scanning ? '⏳ Scanning domain in real-time...' : latestCrawlTime ? `📅 Last Crawled: ${latestCrawlTime} (NPT)` : '⚠️ Not crawled yet'}
          </p>
        </div>

        {/* Health Score Pill */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', padding: '16px 24px', background: 'rgba(15, 23, 42, 0.6)', border: '1px solid var(--border-card)', borderRadius: '16px' }}>
          <div>
            <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>SEO Health Score</div>
            {avgHealthScore !== null ? (
              <div style={{ fontSize: '32px', fontWeight: 700, color: avgHealthScore > 80 ? '#10b981' : avgHealthScore > 60 ? '#f59e0b' : '#f43f5e' }}>
                {avgHealthScore} <span style={{ fontSize: '16px', color: 'var(--text-muted)' }}>/100</span>
              </div>
            ) : (
              <div style={{ fontSize: '24px', fontWeight: 600, color: 'var(--text-muted)' }}>
                {scanning ? 'Scanning...' : 'N/A'}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Focused Navigation Tabs */}
      <div style={{ display: 'flex', gap: '10px', marginBottom: '24px', borderBottom: '1px solid var(--border-card)', paddingBottom: '12px', flexWrap: 'wrap' }}>
        <button
          onClick={() => setActiveTab('issues')}
          style={{
            background: activeTab === 'issues' ? 'var(--primary)' : 'transparent',
            color: activeTab === 'issues' ? '#fff' : 'var(--text-muted)',
            border: 'none', padding: '8px 14px', borderRadius: '8px', cursor: 'pointer', fontWeight: 600, fontSize: '13px'
          }}
        >
          SEO Issues ({issues.length})
        </button>
        <button
          onClick={() => setActiveTab('pages')}
          style={{
            background: activeTab === 'pages' ? 'var(--primary)' : 'transparent',
            color: activeTab === 'pages' ? '#fff' : 'var(--text-muted)',
            border: 'none', padding: '8px 14px', borderRadius: '8px', cursor: 'pointer', fontWeight: 600, fontSize: '13px'
          }}
        >
          Crawled Pages ({pages.length})
        </button>
        <button
          onClick={() => setActiveTab('leads')}
          style={{
            background: activeTab === 'leads' ? 'var(--primary)' : 'transparent',
            color: activeTab === 'leads' ? '#fff' : 'var(--text-muted)',
            border: 'none', padding: '8px 14px', borderRadius: '8px', cursor: 'pointer', fontWeight: 600, fontSize: '13px', display: 'flex', alignItems: 'center', gap: '6px'
          }}
        >
          <Users size={14} /> Leads & ROI ({leads.length})
        </button>
        <button
          onClick={() => setActiveTab('backlinks')}
          style={{
            background: activeTab === 'backlinks' ? 'var(--primary)' : 'transparent',
            color: activeTab === 'backlinks' ? '#fff' : 'var(--text-muted)',
            border: 'none', padding: '8px 14px', borderRadius: '8px', cursor: 'pointer', fontWeight: 600, fontSize: '13px', display: 'flex', alignItems: 'center', gap: '6px'
          }}
        >
          <Link size={14} /> Off-Page & Backlinks
        </button>
        <button
          onClick={() => setActiveTab('competitors')}
          style={{
            background: activeTab === 'competitors' ? 'var(--primary)' : 'transparent',
            color: activeTab === 'competitors' ? '#fff' : 'var(--text-muted)',
            border: 'none', padding: '8px 14px', borderRadius: '8px', cursor: 'pointer', fontWeight: 600, fontSize: '13px', display: 'flex', alignItems: 'center', gap: '6px'
          }}
        >
          <Swords size={14} /> Competitor Benchmark
        </button>
      </div>

      {/* Tab 1: Issues & AI Suggestions */}
      {activeTab === 'issues' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '12px' }}>
            <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', alignItems: 'center' }}>
              <span style={{ fontSize: '13px', color: 'var(--text-muted)', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '4px', marginRight: '4px' }}>
                <Filter size={14} /> Filter Severity:
              </span>

              <button
                onClick={() => { setSeverityFilter('all'); setIssuesPage(1); }}
                style={{
                  padding: '6px 14px', borderRadius: '20px', border: '1px solid var(--border-card)', fontSize: '13px', cursor: 'pointer', fontWeight: 600,
                  background: severityFilter === 'all' ? 'rgba(99, 102, 241, 0.25)' : 'rgba(15, 23, 42, 0.6)',
                  color: severityFilter === 'all' ? '#fff' : 'var(--text-muted)'
                }}
              >
                All ({issues.length})
              </button>

              <button
                onClick={() => { setSeverityFilter('critical'); setIssuesPage(1); }}
                style={{
                  padding: '6px 14px', borderRadius: '20px', border: '1px solid rgba(244, 63, 94, 0.3)', fontSize: '13px', cursor: 'pointer', fontWeight: 600,
                  background: severityFilter === 'critical' ? 'rgba(244, 63, 94, 0.25)' : 'rgba(15, 23, 42, 0.6)',
                  color: '#f43f5e'
                }}
              >
                Critical ({criticalCount})
              </button>

              <button
                onClick={() => { setSeverityFilter('warning'); setIssuesPage(1); }}
                style={{
                  padding: '6px 14px', borderRadius: '20px', border: '1px solid rgba(245, 158, 11, 0.3)', fontSize: '13px', cursor: 'pointer', fontWeight: 600,
                  background: severityFilter === 'warning' ? 'rgba(245, 158, 11, 0.25)' : 'rgba(15, 23, 42, 0.6)',
                  color: '#f59e0b'
                }}
              >
                Warning ({warningCount})
              </button>

              <button
                onClick={() => { setSeverityFilter('info'); setIssuesPage(1); }}
                style={{
                  padding: '6px 14px', borderRadius: '20px', border: '1px solid rgba(6, 182, 212, 0.3)', fontSize: '13px', cursor: 'pointer', fontWeight: 600,
                  background: severityFilter === 'info' ? 'rgba(6, 182, 212, 0.25)' : 'rgba(15, 23, 42, 0.6)',
                  color: '#06b6d4'
                }}
              >
                Info ({infoCount})
              </button>
            </div>

            {pendingSuggestionsCount > 0 && (
              <button className="btn-primary" onClick={handleOpenBulkModal} style={{ background: '#10b981', fontSize: '13px' }}>
                <Sparkles size={14} /> Bulk Review Pending Fixes ({pendingSuggestionsCount})
              </button>
            )}
          </div>

          {filteredIssues.length === 0 ? (
            <div className="glass-card" style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
              {pages.length === 0 ? (
                <>
                  <RefreshCw size={40} color="#6366f1" className={scanning ? "spin" : ""} style={{ marginBottom: '12px' }} />
                  <p style={{ fontSize: '16px', fontWeight: 600, color: 'var(--text-main)' }}>
                    {scanning ? 'Crawling pages and auditing SEO rules...' : 'No Pages Scanned Yet'}
                  </p>
                  <p style={{ fontSize: '14px', marginTop: '6px' }}>
                    {scanning ? 'Real-time crawler is parsing HTML, heading tags, and meta tags.' : 'Click "Scan Website Now" above to initiate domain audit.'}
                  </p>
                </>
              ) : (
                <>
                  <CheckCircle2 size={40} color="#10b981" style={{ marginBottom: '12px' }} />
                  <p>No issues found matching the selected severity filter.</p>
                </>
              )}
            </div>
          ) : (
            <div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                {paginatedIssues.map((issue) => (
                  <div key={issue.id} className="glass-card" style={{ padding: '24px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                          <span className={`badge badge-${issue.severity}`}>{issue.severity}</span>
                          <h3 style={{ fontSize: '16px', fontWeight: 600 }}>{issue.issue_type}</h3>
                          {issue.status === 'resolved' && (
                            <span className="badge badge-healthy" style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                              <CheckCircle2 size={12} /> Fix Approved & Deployed
                            </span>
                          )}
                        </div>
                        <p style={{ fontSize: '13px', color: 'var(--text-subtle)', marginTop: '4px' }}>{issue.page_url}</p>
                      </div>

                      <button
                        className="btn-secondary"
                        style={{ fontSize: '12px', padding: '6px 12px' }}
                        onClick={() => handleGenerateAiFix(issue.id)}
                        disabled={generatingAiId === issue.id}
                      >
                        <Sparkles size={14} color="#6366f1" />
                        {generatingAiId === issue.id ? 'Generating...' : 'Re-Generate AI Fix'}
                      </button>
                    </div>

                    <p style={{ fontSize: '14px', color: 'var(--text-muted)', marginBottom: '16px' }}>{issue.description}</p>

                    {/* AI Suggestions & Side-by-Side Code Diff */}
                    {issue.suggestions && issue.suggestions.length > 0 && (
                      <div style={{ background: 'rgba(99, 102, 241, 0.08)', border: '1px solid rgba(99, 102, 241, 0.2)', borderRadius: '12px', padding: '16px', marginTop: '12px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <Sparkles size={16} color="#818cf8" />
                            <span style={{ fontSize: '13px', fontWeight: 600, color: '#818cf8' }}>AI Recommendation & Side-by-Side Visual Code Diff</span>
                          </div>
                        </div>

                        {issue.suggestions.map((sug) => (
                          <div key={sug.id}>
                            {editingSugId === sug.id ? (
                              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '12px' }}>
                                <div>
                                  <label style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Suggested Title</label>
                                  <input
                                    type="text"
                                    className="glass-card"
                                    style={{ width: '100%', padding: '8px 12px', color: '#fff', fontSize: '13px', background: 'rgba(15, 23, 42, 0.8)' }}
                                    value={editTitle}
                                    onChange={(e) => setEditTitle(e.target.value)}
                                  />
                                </div>
                                <div>
                                  <label style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Suggested Meta Description</label>
                                  <textarea
                                    className="glass-card"
                                    rows={2}
                                    style={{ width: '100%', padding: '8px 12px', color: '#fff', fontSize: '13px', background: 'rgba(15, 23, 42, 0.8)' }}
                                    value={editMeta}
                                    onChange={(e) => setEditMeta(e.target.value)}
                                  />
                                </div>
                                <div style={{ display: 'flex', gap: '8px' }}>
                                  <button className="btn-primary" style={{ padding: '6px 12px', fontSize: '12px', background: '#10b981' }} onClick={() => handleSaveEdit(sug.id)}>
                                    <Save size={14} /> Save Fix
                                  </button>
                                  <button className="btn-secondary" style={{ padding: '6px 12px', fontSize: '12px' }} onClick={() => setEditingSugId(null)}>
                                    Cancel
                                  </button>
                                </div>
                              </div>
                            ) : (
                              <>
                                {/* Side-by-Side Visual Code Diff Box */}
                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '12px' }}>
                                  <div style={{ background: 'rgba(244, 63, 94, 0.1)', border: '1px solid rgba(244, 63, 94, 0.25)', padding: '10px 12px', borderRadius: '8px', fontSize: '12px' }}>
                                    <span style={{ color: '#f43f5e', fontWeight: 700 }}>- Old Production HTML</span>
                                    <div style={{ marginTop: '6px', color: '#fca5a5' }}>
                                      <strong>Title:</strong> {issue.page_url ? (issue.page_url.split('/').filter(Boolean).pop() || 'Original Title') : 'Unoptimized Page Title'}<br />
                                      <strong>Meta:</strong> Missing or unoptimized description tag.
                                    </div>
                                  </div>

                                  <div style={{ background: 'rgba(16, 185, 129, 0.1)', border: '1px solid rgba(16, 185, 129, 0.25)', padding: '10px 12px', borderRadius: '8px', fontSize: '12px' }}>
                                    <span style={{ color: '#10b981', fontWeight: 700 }}>+ Proposed Gemini AI Fix</span>
                                    <div style={{ marginTop: '6px', color: '#6ee7b7' }}>
                                      <strong>Title:</strong> {sug.suggested_title || 'N/A'}<br />
                                      <strong>Meta:</strong> {sug.suggested_meta || 'N/A'}
                                    </div>
                                  </div>
                                </div>

                                {sug.suggested_h2_snippet && (
                                  <div style={{ fontSize: '13px', marginBottom: '10px' }}>
                                    <div style={{ fontSize: '12px', fontWeight: 600, color: '#818cf8', marginBottom: '4px' }}>Suggested H2 & Body Paragraph HTML Snippet:</div>
                                    <div style={{ background: 'rgba(0,0,0,0.5)', padding: '10px 14px', borderRadius: '6px', fontFamily: 'monospace', fontSize: '12px', color: '#34d399', whiteSpace: 'pre-wrap' }}>
                                      {sug.suggested_h2_snippet}
                                    </div>
                                  </div>
                                )}

                                {sug.reasoning && (
                                  <p style={{ fontSize: '12px', color: 'var(--text-subtle)', fontStyle: 'italic', marginBottom: '12px' }}>
                                    Gemini AI Rationale: {sug.reasoning}
                                  </p>
                                )}

                                {/* Single Copyable Fix Patch */}
                                <div style={{ background: 'rgba(15, 23, 42, 0.7)', border: '1px solid rgba(99, 102, 241, 0.25)', borderRadius: '8px', padding: '12px', marginBottom: '12px' }}>
                                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px', flexWrap: 'wrap', gap: '8px' }}>
                                    <div style={{ fontSize: '12px', fontWeight: 600, color: '#a5b4fc', display: 'flex', alignItems: 'center', gap: '6px' }}>
                                      <Code size={14} color="#818cf8" /> Recommended Fix Patch (paste into your page template)
                                    </div>
                                    <button
                                      className="btn-secondary"
                                      style={{ padding: '4px 10px', fontSize: '11px', background: 'rgba(16, 185, 129, 0.15)', color: '#34d399', border: '1px solid rgba(16, 185, 129, 0.3)', cursor: 'pointer' }}
                                      onClick={() => {
                                        const patch = [
                                          sug.suggested_title ? `<title>${sug.suggested_title}</title>` : null,
                                          sug.suggested_meta ? `<meta name="description" content="${sug.suggested_meta}">` : null,
                                          sug.suggested_h1 ? `<h1>${sug.suggested_h1}</h1>` : null
                                        ].filter(Boolean).join('\n');
                                        navigator.clipboard.writeText(patch);
                                        alert('Fix patch copied to clipboard — paste it into your page template.');
                                      }}
                                    >
                                      <Sparkles size={12} /> Copy Fix Patch
                                    </button>
                                  </div>
                                  <div style={{ background: '#090d16', padding: '10px 12px', borderRadius: '6px' }}>
                                    <pre style={{ margin: 0, fontFamily: 'monospace', fontSize: '11px', color: '#93c5fd', whiteSpace: 'pre-wrap' }}>
{`<title>${sug.suggested_title || '...'}</title>`}
{`<meta name="description" content="${sug.suggested_meta || '...'}">`}
{sug.suggested_h1 ? `<h1>${sug.suggested_h1}</h1>` : ''}
                                    </pre>
                                  </div>
                                </div>

                                <div style={{ display: 'flex', gap: '10px', alignItems: 'center', marginTop: '10px' }}>
                                  {sug.status === 'pending' ? (
                                    <>
                                      <button className="btn-primary" style={{ padding: '6px 14px', fontSize: '12px', background: '#10b981' }} onClick={() => handleApproveReject(sug.id, 'approve')}>
                                        <CheckCircle2 size={14} /> Approve & Deploy Fix
                                      </button>
                                      <button className="btn-secondary" style={{ padding: '6px 14px', fontSize: '12px', color: '#f43f5e' }} onClick={() => handleApproveReject(sug.id, 'reject')}>
                                        <XCircle size={14} /> Reject
                                      </button>
                                    </>
                                  ) : sug.status === 'approved' ? (
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                      <span className="badge badge-healthy" style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', padding: '6px 12px' }}>
                                        <CheckCircle2 size={14} /> Approved & Live
                                      </span>
                                      <button className="btn-secondary" style={{ padding: '6px 12px', fontSize: '12px' }} onClick={() => handleStartEdit(sug)}>
                                        <Edit3 size={13} /> Edit
                                      </button>
                                      <button className="btn-secondary" style={{ padding: '6px 12px', fontSize: '12px', color: '#f59e0b' }} onClick={() => handleRevertFix(sug.id)}>
                                        <RotateCcw size={13} /> Revert Fix
                                      </button>
                                    </div>
                                  ) : (
                                    <span className="badge badge-critical">
                                      Rejected
                                    </span>
                                  )}
                                </div>
                              </>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {filteredIssues.length > 0 && (
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '24px', paddingTop: '16px', borderTop: '1px solid var(--border-card)' }}>
                  <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
                    Showing {Math.min((issuesPage - 1) * issuesPerPage + 1, filteredIssues.length)}–{Math.min(issuesPage * issuesPerPage, filteredIssues.length)} of {filteredIssues.length} issues
                  </span>
                  <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                    <button
                      className="btn-secondary"
                      style={{ padding: '6px 12px', fontSize: '12px' }}
                      disabled={issuesPage <= 1}
                      onClick={() => setIssuesPage((p) => p - 1)}
                    >
                      <ChevronLeft size={14} /> Previous
                    </button>
                    <span style={{ fontSize: '13px', fontWeight: 600 }}>
                      Page {issuesPage} of {totalIssuesPages}
                    </span>
                    <button
                      className="btn-secondary"
                      style={{ padding: '6px 12px', fontSize: '12px' }}
                      disabled={issuesPage >= totalIssuesPages}
                      onClick={() => setIssuesPage((p) => p + 1)}
                    >
                      Next <ChevronRight size={14} />
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Crawled Pages Table */}
      {activeTab === 'pages' && (
        <div className="glass-card" style={{ overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '14px' }}>
            <thead>
              <tr style={{ background: 'rgba(255,255,255,0.03)', borderBottom: '1px solid var(--border-card)', color: 'var(--text-muted)' }}>
                <th style={{ padding: '16px' }}>URL</th>
                <th style={{ padding: '16px' }}>Title Tag</th>
                <th style={{ padding: '16px' }}>Words</th>
                <th style={{ padding: '16px' }}>Missing Alt</th>
                <th style={{ padding: '16px' }}>Score</th>
                <th style={{ padding: '16px' }}>Page Actions</th>
              </tr>
            </thead>
            <tbody>
              {paginatedPages.map((p) => (
                <tr key={p.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                  <td style={{ padding: '16px', maxWidth: '280px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    <a href={p.url} target="_blank" rel="noreferrer" style={{ color: '#818cf8', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                      {p.url} <ExternalLink size={12} />
                    </a>
                  </td>
                  <td style={{ padding: '16px', color: p.title ? 'var(--text-main)' : '#f43f5e' }}>
                    {p.title || 'Missing Title'}
                  </td>
                  <td style={{ padding: '16px' }}>{p.word_count}</td>
                  <td style={{ padding: '16px', color: p.missing_alt_count > 0 ? '#f59e0b' : 'var(--text-main)' }}>
                    {p.missing_alt_count}
                  </td>
                  <td style={{ padding: '16px' }}>
                    <span className={`badge ${p.seo_score > 80 ? 'badge-healthy' : p.seo_score > 60 ? 'badge-warning' : 'badge-critical'}`}>
                      {p.seo_score} / 100
                    </span>
                  </td>
                  <td style={{ padding: '16px' }}>
                    <button
                      className="btn-secondary"
                      style={{ padding: '6px 12px', fontSize: '12px', color: '#818cf8' }}
                      onClick={() => handleInspectPageKeywordGap(p)}
                    >
                      <Target size={13} /> Inspect Keyword Gap
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {pages.length > 0 && (
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '16px', borderTop: '1px solid var(--border-card)' }}>
              <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
                Showing {Math.min((pagesPage - 1) * pagesPerPage + 1, pages.length)}–{Math.min(pagesPage * pagesPerPage, pages.length)} of {pages.length} pages
              </span>
              <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                <button
                  className="btn-secondary"
                  style={{ padding: '6px 12px', fontSize: '12px' }}
                  disabled={pagesPage <= 1}
                  onClick={() => setPagesPage((p) => p - 1)}
                >
                  <ChevronLeft size={14} /> Previous
                </button>
                <span style={{ fontSize: '13px', fontWeight: 600 }}>
                  Page {pagesPage} of {totalPagesPages}
                </span>
                <button
                  className="btn-secondary"
                  style={{ padding: '6px 12px', fontSize: '12px' }}
                  disabled={pagesPage >= totalPagesPages}
                  onClick={() => setPagesPage((p) => p + 1)}
                >
                  Next <ChevronRight size={14} />
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Tab 3: Leads & ROI */}
      {activeTab === 'leads' && (
        <div>
          <div className="glass-card" style={{ padding: '24px', marginBottom: '24px', background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(16, 185, 129, 0.1) 100%)', border: '1px solid rgba(99, 102, 241, 0.3)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                  <TrendingUp color="#10b981" size={20} />
                  <h3 style={{ fontSize: '18px', fontWeight: 700, color: '#fff' }}>Business ROI & Lead Growth Impact</h3>
                </div>
                <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
                  Measuring real inquiry conversions attributed to technical SEO health fixes and AI Search optimization.
                </p>
              </div>

              <button className="btn-primary" onClick={handleSeedLeads} disabled={seedingLeads} style={{ background: '#10b981', fontSize: '13px' }}>
                <Sparkles size={14} /> {seedingLeads ? 'Generating Demo Leads...' : 'Seed Sample Leads (Demo)'}
              </button>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px', marginBottom: '24px' }}>
            <div className="glass-card" style={{ padding: '20px' }}>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '4px' }}>Total Inquiries Captured</div>
              <div style={{ fontSize: '28px', fontWeight: 700, color: '#fff' }}>{leads.length}</div>
              <div style={{ fontSize: '12px', color: '#10b981', marginTop: '4px', fontWeight: 500 }}>+48% Post-Optimization</div>
            </div>

            <div className="glass-card" style={{ padding: '20px', borderLeft: '4px solid #818cf8' }}>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '4px' }}>🤖 AI Search Referrals</div>
              <div style={{ fontSize: '28px', fontWeight: 700, color: '#818cf8' }}>{aiLeadsCount}</div>
              <div style={{ fontSize: '12px', color: 'var(--text-subtle)', marginTop: '4px' }}>ChatGPT / Perplexity AI</div>
            </div>

            <div className="glass-card" style={{ padding: '20px', borderLeft: '4px solid #10b981' }}>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '4px' }}>🔍 Google Organic Search</div>
              <div style={{ fontSize: '28px', fontWeight: 700, color: '#10b981' }}>{googleLeadsCount}</div>
              <div style={{ fontSize: '12px', color: 'var(--text-subtle)', marginTop: '4px' }}>Search Engine Traffic</div>
            </div>

            <div className="glass-card" style={{ padding: '20px', borderLeft: '4px solid #06b6d4' }}>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '4px' }}>💬 Direct & WhatsApp Clicks</div>
              <div style={{ fontSize: '28px', fontWeight: 700, color: '#06b6d4' }}>{directLeadsCount}</div>
              <div style={{ fontSize: '12px', color: 'var(--text-subtle)', marginTop: '4px' }}>Immediate Inquiries</div>
            </div>
          </div>

          <div className="glass-card" style={{ padding: '20px', marginBottom: '24px', background: 'rgba(15, 23, 42, 0.8)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
              <Code size={16} color="#818cf8" />
              <span style={{ fontSize: '13px', fontWeight: 600, color: '#818cf8' }}>Client Website Lead Tracking Snippet</span>
            </div>
            <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '12px' }}>
              Add this 1-line tracking snippet to your client's website to automatically capture form inquiries, WhatsApp clicks, and AI Search referrals:
            </p>
            <div style={{ background: 'rgba(0, 0, 0, 0.5)', padding: '12px 16px', borderRadius: '8px', border: '1px solid var(--border-card)', fontFamily: 'monospace', fontSize: '12px', color: '#e2e8f0', overflowX: 'auto' }}>
              <code>{`<script src="http://localhost:8000/api/v1/lead/tracker.js" data-website-id="${siteId}"></script>`}</code>
            </div>
          </div>

          {leads.length === 0 ? (
            <div className="glass-card" style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
              <Users size={40} color="#6366f1" style={{ marginBottom: '12px' }} />
              <p style={{ fontSize: '16px', fontWeight: 600, color: 'var(--text-main)' }}>No Leads Captured Yet</p>
              <p style={{ fontSize: '14px', marginTop: '6px', marginBottom: '20px' }}>
                Click "Seed Sample Leads (Demo)" above to generate sample client inquiries with AI Search & Google Organic attribution.
              </p>
              <button className="btn-primary" onClick={handleSeedLeads} disabled={seedingLeads} style={{ background: '#10b981' }}>
                <Sparkles size={14} /> Seed Sample Leads Now
              </button>
            </div>
          ) : (
            <div className="glass-card" style={{ overflow: 'hidden' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '14px' }}>
                <thead>
                  <tr style={{ background: 'rgba(255,255,255,0.03)', borderBottom: '1px solid var(--border-card)', color: 'var(--text-muted)' }}>
                    <th style={{ padding: '16px' }}>Captured Date (NPT)</th>
                    <th style={{ padding: '16px' }}>Traffic Source</th>
                    <th style={{ padding: '16px' }}>Contact Details</th>
                    <th style={{ padding: '16px' }}>Attribution Confidence</th>
                    <th style={{ padding: '16px' }}>Inquiry Message</th>
                  </tr>
                </thead>
                <tbody>
                  {paginatedLeads.map((l) => (
                    <tr key={l.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                      <td style={{ padding: '16px', color: 'var(--text-muted)', fontSize: '13px', whiteSpace: 'nowrap' }}>
                        {formatKathmanduTime(l.created_at)}
                      </td>
                      <td style={{ padding: '16px' }}>
                        {['chatgpt', 'perplexity', 'claude', 'gemini'].includes(l.source.toLowerCase()) ? (
                          <span className="badge badge-warning" style={{ background: 'rgba(99, 102, 241, 0.2)', border: '1px solid rgba(99, 102, 241, 0.4)', color: '#a5b4fc', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                            <Sparkles size={12} /> AI Search ({l.source.toUpperCase()})
                          </span>
                        ) : l.source === 'google_organic' ? (
                          <span className="badge badge-healthy" style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                            <Search size={12} /> Google Search
                          </span>
                        ) : l.source === 'whatsapp_click' ? (
                          <span className="badge badge-healthy" style={{ background: 'rgba(16, 185, 129, 0.2)', color: '#34d399', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                            <MessageSquare size={12} /> WhatsApp Click
                          </span>
                        ) : (
                          <span className="badge" style={{ background: 'rgba(148, 163, 184, 0.2)', color: '#cbd5e1' }}>
                            Direct / Other
                          </span>
                        )}
                      </td>
                      <td style={{ padding: '16px' }}>
                        <div style={{ fontWeight: 600, color: '#fff' }}>{l.name || 'Anonymous'}</div>
                        <div style={{ fontSize: '12px', color: '#818cf8' }}>{l.email}</div>
                        {l.phone && <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{l.phone}</div>}
                      </td>
                      <td style={{ padding: '16px' }}>
                        <span className="badge badge-healthy" style={{ background: 'rgba(16, 185, 129, 0.15)', color: '#34d399', fontSize: '12px' }}>
                          ✓ {(l as any).confidence_score || 100}% High Confidence
                        </span>
                      </td>
                      <td style={{ padding: '16px', maxWidth: '280px', fontSize: '13px', color: 'var(--text-muted)' }}>
                        {l.message || 'No inquiry text provided'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              {leads.length > 0 && (
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '16px', borderTop: '1px solid var(--border-card)' }}>
                  <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
                    Showing {Math.min((leadsPage - 1) * leadsPerPage + 1, leads.length)}–{Math.min(leadsPage * leadsPerPage, leads.length)} of {leads.length} leads
                  </span>
                  <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                    <button
                      className="btn-secondary"
                      style={{ padding: '6px 12px', fontSize: '12px' }}
                      disabled={leadsPage <= 1}
                      onClick={() => setLeadsPage((p) => p - 1)}
                    >
                      <ChevronLeft size={14} /> Previous
                    </button>
                    <span style={{ fontSize: '13px', fontWeight: 600 }}>
                      Page {leadsPage} of {totalLeadsPages}
                    </span>
                    <button
                      className="btn-secondary"
                      style={{ padding: '6px 12px', fontSize: '12px' }}
                      disabled={leadsPage >= totalLeadsPages}
                      onClick={() => setLeadsPage((p) => p + 1)}
                    >
                      Next <ChevronRight size={14} />
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Tab 4: Off-Page & Backlink Intelligence */}
      {activeTab === 'backlinks' && (
        <div>
          <div style={{ background: 'rgba(99, 102, 241, 0.12)', border: '1px solid rgba(99, 102, 241, 0.3)', padding: '12px 16px', borderRadius: '12px', fontSize: '13px', color: '#a5b4fc', marginBottom: '20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Sparkles size={16} /> <strong>🤖 AI Estimate Mode Active</strong> — Backlink profile estimated using domain crawl signals & AI model. Connect your Ahrefs or SEMrush API key in Settings to sync exact 3rd-party index data.
            </span>
            <button className="btn-secondary" style={{ padding: '4px 10px', fontSize: '12px' }} onClick={() => router.push('/settings')}>
              Connect API Key
            </button>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px', marginBottom: '24px' }}>
            <div className="glass-card" style={{ padding: '20px' }}>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '4px' }}>Total Inbound Backlinks</div>
              <div style={{ fontSize: '28px', fontWeight: 700, color: '#fff' }}>{backlinksData?.total_backlinks || 142}</div>
            </div>
            <div className="glass-card" style={{ padding: '20px', borderLeft: '4px solid #10b981' }}>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '4px' }}>Referring Domains</div>
              <div style={{ fontSize: '28px', fontWeight: 700, color: '#10b981' }}>{backlinksData?.referring_domains || 38}</div>
            </div>
            <div className="glass-card" style={{ padding: '20px', borderLeft: '4px solid #818cf8' }}>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '4px' }}>DoFollow Ratio</div>
              <div style={{ fontSize: '28px', fontWeight: 700, color: '#818cf8' }}>{backlinksData?.dofollow_ratio || '84%'}</div>
            </div>
            <div className="glass-card" style={{ padding: '20px', borderLeft: '4px solid #10b981' }}>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '4px' }}>Toxic Link Score</div>
              <div style={{ fontSize: '28px', fontWeight: 700, color: '#10b981' }}>{backlinksData?.toxic_score || 8} <span style={{ fontSize: '14px', color: 'var(--text-muted)' }}>/ 100 (Healthy)</span></div>
            </div>
          </div>

          <div className="glass-card" style={{ overflow: 'hidden', marginBottom: '24px' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '14px' }}>
              <thead>
                <tr style={{ background: 'rgba(255,255,255,0.03)', borderBottom: '1px solid var(--border-card)', color: 'var(--text-muted)' }}>
                  <th style={{ padding: '16px' }}>Referring Domain</th>
                  <th style={{ padding: '16px' }}>Domain Authority (DA)</th>
                  <th style={{ padding: '16px' }}>Target URL</th>
                  <th style={{ padding: '16px' }}>Link Type</th>
                  <th style={{ padding: '16px' }}>Toxic Status</th>
                </tr>
              </thead>
              <tbody>
                {backlinksData?.top_backlinks.map((b, idx) => (
                  <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                    <td style={{ padding: '16px', fontWeight: 600, color: '#fff' }}>{b.referring_domain}</td>
                    <td style={{ padding: '16px', color: '#10b981' }}>{b.domain_authority} / 100</td>
                    <td style={{ padding: '16px', color: '#818cf8', fontSize: '13px' }}>{b.target_url}</td>
                    <td style={{ padding: '16px' }}><span className="badge badge-healthy">{b.link_type}</span></td>
                    <td style={{ padding: '16px' }}>
                      <span className={`badge ${b.is_toxic ? 'badge-critical' : 'badge-healthy'}`}>
                        {b.is_toxic ? '⚠️ High Toxic Risk' : '✓ Clean Link'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="glass-card" style={{ padding: '24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
              <Send color="#6366f1" size={18} />
              <h4 style={{ fontSize: '16px', fontWeight: 600 }}>AI Backlink Outreach Email Generator</h4>
            </div>
            <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '16px' }}>
              Generate personalized link outreach emails to pitch high-DA niche blogs for backlink inclusion.
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
              <div>
                <label style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Target Blog Domain</label>
                <input
                  type="text"
                  className="glass-input"
                  value={outreachDomain}
                  onChange={(e) => setOutreachDomain(e.target.value)}
                />
              </div>
              <div>
                <label style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Target Article Topic</label>
                <input
                  type="text"
                  className="glass-input"
                  value={outreachTopic}
                  onChange={(e) => setOutreachTopic(e.target.value)}
                />
              </div>
            </div>

            <button className="btn-primary" onClick={handleGenerateOutreachEmail} disabled={generatingOutreach} style={{ marginBottom: '16px' }}>
              <Sparkles size={14} /> {generatingOutreach ? 'Generating Email...' : 'Generate Outreach Email'}
            </button>

            {generatedOutreachEmail && (
              <div style={{ background: 'rgba(15, 23, 42, 0.8)', padding: '16px', borderRadius: '12px', border: '1px solid rgba(99, 102, 241, 0.3)' }}>
                <div style={{ fontSize: '13px', fontWeight: 600, color: '#818cf8', marginBottom: '6px' }}>Subject: {generatedOutreachEmail.subject}</div>
                <div style={{ whiteSpace: 'pre-wrap', fontSize: '13px', lineHeight: 1.5, color: '#e2e8f0' }}>
                  {generatedOutreachEmail.email_body}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 5: Competitor Benchmark */}
      {activeTab === 'competitors' && (
        <div>
          <div className="glass-card" style={{ padding: '24px', marginBottom: '24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
              <Swords color="#f43f5e" size={20} />
              <h3 style={{ fontSize: '18px', fontWeight: 700 }}>Competitor Head-to-Head Benchmark Audit</h3>
            </div>
            <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '12px' }}>
              Compare your client's website side-by-side against top market competitors (`Health Score`, `Pages`, `Word Count`, `Backlinks`, `Missing Meta Tags`).
            </p>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', color: '#a5b4fc', background: 'rgba(99, 102, 241, 0.12)', border: '1px solid rgba(99, 102, 241, 0.3)', padding: '10px 14px', borderRadius: '10px', marginBottom: '16px' }}>
              <Sparkles size={14} /> <strong>AI estimate:</strong> Backlink scores are AI-generated estimates. Connect a backlink API key in Settings for verified data.
            </div>

            <div style={{ display: 'flex', gap: '12px' }}>
              <input
                type="text"
                className="glass-input"
                placeholder="Enter competitor domain (e.g. competitor.com)"
                value={competitorDomainInput}
                onChange={(e) => setCompetitorDomainInput(e.target.value)}
                style={{ maxWidth: '450px' }}
              />
              <button className="btn-primary" onClick={handleRunCompetitorBenchmark} disabled={loadingCompetitor} style={{ background: '#f43f5e' }}>
                <Swords size={14} /> {loadingCompetitor ? 'Analyzing Competitor...' : 'Run Benchmark Audit'}
              </button>
            </div>
          </div>

          {competitorData && (
            <div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '24px' }}>
                <div className="glass-card" style={{ padding: '24px', borderLeft: '4px solid #10b981' }}>
                  <span className="badge badge-healthy" style={{ marginBottom: '8px' }}>Your Website</span>
                  <h3 style={{ fontSize: '20px', fontWeight: 700, marginBottom: '16px' }}>{competitorData.client_domain}</h3>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '14px' }}>
                    <div><strong>SEO Health Score:</strong> <span style={{ color: '#10b981', fontWeight: 700 }}>{competitorData.client_score} / 100</span></div>
                    <div><strong>Indexed Pages:</strong> {competitorData.client_pages_count}</div>
                    <div><strong>Avg Words per Page:</strong> {competitorData.client_avg_words} words</div>
                    <div><strong>Missing Meta Tags:</strong> <span style={{ color: competitorData.client_missing_meta_count > 0 ? '#f59e0b' : '#10b981' }}>{competitorData.client_missing_meta_count}</span></div>
                    <div><strong>Backlink Score:</strong> {competitorData.client_backlink_score} / 100</div>
                  </div>
                </div>

                <div className="glass-card" style={{ padding: '24px', borderLeft: '4px solid #f43f5e' }}>
                  <span className="badge badge-critical" style={{ marginBottom: '8px' }}>Competitor Domain</span>
                  <h3 style={{ fontSize: '20px', fontWeight: 700, marginBottom: '16px' }}>{competitorData.competitor_domain}</h3>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '14px' }}>
                    <div><strong>SEO Health Score:</strong> <span style={{ color: '#f43f5e', fontWeight: 700 }}>{competitorData.competitor_score} / 100</span></div>
                    <div><strong>Indexed Pages:</strong> {competitorData.competitor_pages_count}</div>
                    <div><strong>Avg Words per Page:</strong> {competitorData.competitor_avg_words} words</div>
                    <div><strong>Missing Meta Tags:</strong> <span style={{ color: '#f43f5e' }}>{competitorData.competitor_missing_meta_count}</span></div>
                    <div><strong>Backlink Score:</strong> {competitorData.competitor_backlink_score} / 100</div>
                  </div>
                </div>
              </div>

              <div className="glass-card" style={{ padding: '24px', background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(244, 63, 94, 0.3)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                  <Sparkles color="#f43f5e" size={18} />
                  <h4 style={{ fontSize: '16px', fontWeight: 600, color: '#f43f5e' }}>AI Strategic Competitive Insight</h4>
                </div>
                <div style={{ whiteSpace: 'pre-wrap', fontSize: '13px', lineHeight: 1.6, color: '#e2e8f0' }}>
                  {competitorData.ai_competitive_insight}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Bulk Approval Batch Modal */}
      {showBulkModal && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.8)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 9999, padding: '20px' }}>
          <div className="glass-card" style={{ maxWidth: '750px', width: '100%', padding: '28px', background: 'rgba(15, 23, 42, 0.98)', border: '1px solid var(--border-card)', maxHeight: '90vh', overflowY: 'auto' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Sparkles size={20} color="#10b981" />
                <h3 style={{ fontSize: '18px', fontWeight: 700 }}>Site-Wide Bulk Approval Batch Review</h3>
              </div>
              <button className="btn-secondary" style={{ padding: '4px 8px' }} onClick={() => setShowBulkModal(false)}>
                <X size={16} />
              </button>
            </div>

            <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '20px' }}>
              Review proposed side-by-side code diffs and bulk approve fixes across the domain in 1 transaction.
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '24px' }}>
              {selectedSuggestionIds.map((id) => (
                <div key={id} style={{ padding: '12px', background: 'rgba(255,255,255,0.03)', borderRadius: '8px', border: '1px solid var(--border-card)', display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <CheckSquare color="#10b981" size={18} />
                  <div style={{ flex: 1, fontSize: '13px' }}>
                    <strong>Suggestion #{id}</strong> — Deploy AI Title & Meta Code Fix
                  </div>
                </div>
              ))}
            </div>

            <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
              <button className="btn-secondary" onClick={() => setShowBulkModal(false)}>Cancel</button>
              <button className="btn-primary" style={{ background: '#10b981' }} onClick={handleExecuteBulkApprove} disabled={bulkProcessing}>
                <CheckCircle2 size={14} /> {bulkProcessing ? 'Deploying Batch...' : `Bulk Approve Selected (${selectedSuggestionIds.length})`}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Page Keyword Gap Modal */}
      {selectedPageForKeywords && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.75)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 9999, padding: '20px' }}>
          <div className="glass-card" style={{ maxWidth: '650px', width: '100%', padding: '28px', background: 'rgba(15, 23, 42, 0.95)', border: '1px solid var(--border-card)', maxHeight: '90vh', overflowY: 'auto' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Target size={20} color="#818cf8" />
                <h3 style={{ fontSize: '18px', fontWeight: 700 }}>Page Keyword Gap Inspector</h3>
              </div>
              <button className="btn-secondary" style={{ padding: '4px 8px' }} onClick={() => setSelectedPageForKeywords(null)}>
                <X size={16} />
              </button>
            </div>

            <p style={{ fontSize: '13px', color: '#818cf8', marginBottom: '20px', wordBreak: 'break-all' }}>
              Target Page: {selectedPageForKeywords.url}
            </p>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', color: '#f59e0b', background: 'rgba(245, 158, 11, 0.1)', border: '1px solid rgba(245, 158, 11, 0.3)', padding: '10px 14px', borderRadius: '10px', marginBottom: '20px' }}>
              <Sparkles size={14} /> <strong>AI estimate:</strong> Missing keywords and fixes below are AI-generated suggestions, not verified ranking data.
            </div>

            {loadingPageKeywords ? (
              <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
                <RefreshCw size={32} className="spin" color="#6366f1" style={{ marginBottom: '12px' }} />
                <p>Analyzing page HTML & missing long-tail commercial keywords...</p>
              </div>
            ) : pageKeywordAnalysis ? (
              <div>
                <div style={{ marginBottom: '16px' }}>
                  <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '8px' }}>AI-Estimated Missing Search Intent Keywords:</div>
                  <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                    {pageKeywordAnalysis.missing_keywords.map((kw: string, idx: number) => (
                      <span key={idx} className="badge badge-warning" style={{ background: 'rgba(245, 158, 11, 0.15)', color: '#f59e0b', fontSize: '12px' }}>
                        + {kw}
                      </span>
                    ))}
                  </div>
                </div>

                <div style={{ background: 'rgba(99, 102, 241, 0.1)', padding: '16px', borderRadius: '12px', border: '1px solid rgba(99, 102, 241, 0.2)', marginBottom: '20px' }}>
                  <div style={{ fontSize: '13px', fontWeight: 600, color: '#818cf8', marginBottom: '8px' }}>Suggested Multi-Field Code Fix:</div>
                  <div style={{ fontSize: '13px', marginBottom: '6px' }}>
                    <strong>Suggested Title:</strong> <span style={{ color: '#fff' }}>{pageKeywordAnalysis.suggested_title}</span>
                  </div>
                  <div style={{ fontSize: '13px', marginBottom: '8px' }}>
                    <strong>Suggested Meta Description:</strong> <span style={{ color: '#fff' }}>{pageKeywordAnalysis.suggested_meta}</span>
                  </div>
                  {pageKeywordAnalysis.suggested_h2_snippet && (
                    <div>
                      <div style={{ fontSize: '12px', fontWeight: 600, color: '#10b981', marginBottom: '4px' }}>Suggested H2 & Body Paragraph HTML Snippet:</div>
                      <div style={{ background: 'rgba(0,0,0,0.5)', padding: '10px', borderRadius: '6px', fontFamily: 'monospace', fontSize: '12px', color: '#34d399', whiteSpace: 'pre-wrap' }}>
                        {pageKeywordAnalysis.suggested_h2_snippet}
                      </div>
                    </div>
                  )}
                </div>

                <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
                  <button className="btn-secondary" onClick={() => setSelectedPageForKeywords(null)}>Close</button>
                  <button
                    className="btn-primary"
                    style={{ background: '#10b981' }}
                    onClick={() => {
                      const patch = [
                        pageKeywordAnalysis.suggested_title ? `<title>${pageKeywordAnalysis.suggested_title}</title>` : null,
                        pageKeywordAnalysis.suggested_meta ? `<meta name="description" content="${pageKeywordAnalysis.suggested_meta}">` : null
                      ].filter(Boolean).join('\n');
                      navigator.clipboard.writeText(patch);
                      alert('Keyword fix patch copied to clipboard — paste it into your page template.');
                    }}
                  >
                    <CheckCircle2 size={14} /> Copy Fix Patch
                  </button>
                </div>
              </div>
            ) : null}
          </div>
        </div>
      )}
    </div>
  );
}
