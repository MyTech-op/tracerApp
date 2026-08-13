'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api, ReportOverview, ReportSiteSnapshot } from '@/lib/api';
import {
  BarChart3,
  Globe,
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  Users,
  ArrowRight,
  ArrowUpRight,
  ArrowDownRight,
  Minus,
  FileDown,
  RefreshCw
} from 'lucide-react';

const formatDate = (dateStr?: string) => {
  if (!dateStr) return 'Never scanned';
  try {
    const iso = dateStr.endsWith('Z') ? dateStr : dateStr + 'Z';
    return new Date(iso).toLocaleString('en-US', {
      month: 'short', day: 'numeric', year: 'numeric', hour: 'numeric', minute: '2-digit'
    });
  } catch {
    return dateStr;
  }
};

const scoreColor = (score?: number) => {
  if (score === undefined || score === null) return 'var(--text-muted)';
  if (score > 80) return '#10b981';
  if (score > 60) return '#f59e0b';
  return '#f43f5e';
};

function DeltaBadge({ delta }: { delta?: number }) {
  if (delta === undefined || delta === null) return <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>— baseline</span>;
  const up = delta > 0;
  const flat = delta === 0;
  return (
    <span style={{ fontSize: '12px', fontWeight: 600, color: up ? '#10b981' : flat ? 'var(--text-muted)' : '#f43f5e', display: 'inline-flex', alignItems: 'center', gap: '3px' }}>
      {up ? <ArrowUpRight size={13} /> : flat ? <Minus size={13} /> : <ArrowDownRight size={13} />}
      {up ? '+' : ''}{delta} pts vs baseline
    </span>
  );
}

export default function ReportsPage() {
  const router = useRouter();
  const [data, setData] = useState<ReportOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchReports = async () => {
    setLoading(true);
    try {
      const res = await api.get('/reports/overview');
      setData(res.data);
      setError('');
    } catch (err: any) {
      if (err.response?.status === 401) {
        router.push('/');
      } else {
        setError('Failed to load reports. Is the backend running?');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  const summary = data?.summary;

  return (
    <div style={{ minHeight: '100vh', padding: '32px', maxWidth: '1200px', margin: '0 auto' }}>
      {/* Header */}
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '28px', paddingBottom: '20px', borderBottom: '1px solid var(--border-card)', flexWrap: 'wrap', gap: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ padding: '8px', background: 'rgba(99,102,241,0.2)', borderRadius: '12px' }}>
            <BarChart3 color="#6366f1" size={24} />
          </div>
          <div>
            <h1 style={{ fontSize: '24px', fontWeight: 700 }}>Reporting Center</h1>
            <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
              Client-ready SEO performance reports across every managed domain
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <button className="btn-secondary" onClick={() => router.push('/dashboard')}>
            <Globe size={16} /> Back to Dashboard
          </button>
          <button className="btn-secondary" onClick={fetchReports} disabled={loading}>
            <RefreshCw size={15} className={loading ? 'spin' : ''} /> Refresh
          </button>
        </div>
      </header>

      {error && (
        <div style={{ padding: '16px', background: 'rgba(244, 63, 94, 0.12)', border: '1px solid rgba(244, 63, 94, 0.3)', borderRadius: '10px', color: '#f43f5e', fontSize: '14px', marginBottom: '20px' }}>
          {error}
        </div>
      )}

      {loading && !data ? (
        <div style={{ textAlign: 'center', padding: '80px', color: 'var(--text-muted)' }}>
          <RefreshCw size={32} className="spin" style={{ marginBottom: '12px' }} />
          <p>Compiling reports...</p>
        </div>
      ) : data ? (
        <>
          {/* KPI Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '16px', marginBottom: '32px' }}>
            <div className="glass-card" style={{ padding: '20px' }}>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '4px' }}>Sites Tracked</div>
              <div style={{ fontSize: '28px', fontWeight: 700, color: '#fff' }}>{summary?.total_sites}</div>
              <div style={{ fontSize: '12px', color: 'var(--text-subtle)', marginTop: '4px' }}>domains monitored 24/7</div>
            </div>

            <div className="glass-card" style={{ padding: '20px' }}>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '4px' }}>Avg Health Score</div>
              <div style={{ fontSize: '28px', fontWeight: 700, color: scoreColor(summary?.avg_health_score) }}>
                {summary?.avg_health_score ?? '—'} <span style={{ fontSize: '14px', color: 'var(--text-muted)' }}>/100</span>
              </div>
              <div style={{ fontSize: '12px', color: 'var(--text-subtle)', marginTop: '4px' }}>portfolio average</div>
            </div>

            <div className="glass-card" style={{ padding: '20px' }}>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '4px' }}>Pages Scanned</div>
              <div style={{ fontSize: '28px', fontWeight: 700, color: '#818cf8' }}>{summary?.total_pages_scanned}</div>
              <div style={{ fontSize: '12px', color: 'var(--text-subtle)', marginTop: '4px' }}>{summary?.total_scans} crawl runs</div>
            </div>

            <div className="glass-card" style={{ padding: '20px' }}>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '4px' }}>Open Issues</div>
              <div style={{ fontSize: '28px', fontWeight: 700, color: '#f59e0b' }}>{summary?.open_issues}</div>
              <div style={{ fontSize: '12px', color: '#f43f5e', marginTop: '4px' }}>
                {summary?.critical_issues} critical • {summary?.warning_issues} warning
              </div>
            </div>

            <div className="glass-card" style={{ padding: '20px' }}>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '4px' }}>Fixes Deployed</div>
              <div style={{ fontSize: '28px', fontWeight: 700, color: '#10b981' }}>{summary?.approved_fixes}</div>
              <div style={{ fontSize: '12px', color: 'var(--text-subtle)', marginTop: '4px' }}>approved AI fixes live</div>
            </div>

            <div className="glass-card" style={{ padding: '20px' }}>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '4px' }}>Leads Captured</div>
              <div style={{ fontSize: '28px', fontWeight: 700, color: '#06b6d4' }}>{summary?.leads_captured}</div>
              <div style={{ fontSize: '12px', color: 'var(--text-subtle)', marginTop: '4px' }}>attributed inquiries</div>
            </div>
          </div>

          {/* Per-Site Report Table */}
          <div className="glass-card" style={{ overflow: 'hidden' }}>
            <div style={{ padding: '20px 24px', borderBottom: '1px solid var(--border-card)', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <TrendingUp color="#10b981" size={20} />
              <h3 style={{ fontSize: '18px', fontWeight: 700 }}>Portfolio Reports</h3>
            </div>

            {data.sites.length === 0 ? (
              <div style={{ padding: '48px', textAlign: 'center', color: 'var(--text-muted)' }}>
                <Globe size={40} color="#64748b" style={{ marginBottom: '12px' }} />
                <p style={{ fontWeight: 600, color: 'var(--text-main)' }}>No websites tracked yet</p>
                <p style={{ fontSize: '13px', marginTop: '4px' }}>Add a website from the dashboard to generate its first report.</p>
              </div>
            ) : (
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '14px' }}>
                <thead>
                  <tr style={{ background: 'rgba(255,255,255,0.03)', borderBottom: '1px solid var(--border-card)', color: 'var(--text-muted)' }}>
                    <th style={{ padding: '14px 24px' }}>Domain</th>
                    <th style={{ padding: '14px' }}>Health Score</th>
                    <th style={{ padding: '14px' }}>Trend</th>
                    <th style={{ padding: '14px' }}>Pages</th>
                    <th style={{ padding: '14px' }}>Issues</th>
                    <th style={{ padding: '14px' }}>Fixes</th>
                    <th style={{ padding: '14px' }}>Leads</th>
                    <th style={{ padding: '14px' }}>Last Scan</th>
                    <th style={{ padding: '14px 24px' }}></th>
                  </tr>
                </thead>
                <tbody>
                  {data.sites.map((site: ReportSiteSnapshot) => (
                    <tr
                      key={site.id}
                      style={{ borderBottom: '1px solid rgba(255,255,255,0.04)', cursor: 'pointer' }}
                      onClick={() => router.push(`/reports/${site.id}`)}
                    >
                      <td style={{ padding: '16px 24px', fontWeight: 600, color: '#fff' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <Globe size={15} color="#06b6d4" />
                          {site.domain}
                        </div>
                        {site.industry && (
                          <div style={{ fontSize: '11px', color: 'var(--text-subtle)', marginTop: '2px', fontWeight: 400 }}>{site.industry}</div>
                        )}
                      </td>
                      <td style={{ padding: '16px' }}>
                        <span className={`badge ${site.current_score && site.current_score > 80 ? 'badge-healthy' : site.current_score && site.current_score > 60 ? 'badge-warning' : 'badge-critical'}`} style={{ fontSize: '13px' }}>
                          {site.current_score ?? 'N/A'} / 100
                        </span>
                      </td>
                      <td style={{ padding: '16px' }}><DeltaBadge delta={site.score_delta} /></td>
                      <td style={{ padding: '16px', color: 'var(--text-muted)' }}>{site.pages_count}</td>
                      <td style={{ padding: '16px' }}>
                        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', color: site.open_issues > 0 ? '#f59e0b' : '#10b981' }}>
                          <AlertTriangle size={13} /> {site.open_issues}
                          {site.critical_issues > 0 && <span style={{ color: '#f43f5e', fontSize: '12px' }}>({site.critical_issues} crit)</span>}
                        </span>
                      </td>
                      <td style={{ padding: '16px', color: '#10b981' }}>{site.approved_fixes}</td>
                      <td style={{ padding: '16px', color: '#06b6d4' }}>{site.leads_captured}</td>
                      <td style={{ padding: '16px', fontSize: '13px', color: 'var(--text-muted)' }}>{formatDate(site.last_scan_at)}</td>
                      <td style={{ padding: '16px 24px' }}>
                        <button className="btn-secondary" style={{ padding: '6px 12px', fontSize: '12px' }} onClick={(e) => { e.stopPropagation(); router.push(`/reports/${site.id}`); }}>
                          View Report <ArrowRight size={13} />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

          <div style={{ marginTop: '20px', display: 'flex', gap: '12px', alignItems: 'center', fontSize: '13px', color: 'var(--text-muted)' }}>
            <FileDown size={14} color="#818cf8" />
            Open a site report to download the full CSV export or generate a shareable client link.
          </div>
        </>
      ) : null}
    </div>
  );
}
