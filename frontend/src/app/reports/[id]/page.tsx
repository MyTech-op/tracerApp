'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { api, WebsiteReport, ScorePoint } from '@/lib/api';
import {
  ArrowLeft,
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  FileDown,
  Printer,
  Share2,
  RefreshCw,
  Globe,
  BarChart3,
  FileSpreadsheet,
  Link2,
  Activity,
  Users,
  Sparkles,
  Plug,
  Unplug
} from 'lucide-react';

const formatDate = (dateStr?: string) => {
  if (!dateStr) return 'N/A';
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

function ScoreTrendChart({ history, baseline }: { history: ScorePoint[]; baseline?: number }) {
  const W = 640;
  const H = 240;
  const PAD = { top: 18, right: 18, bottom: 28, left: 34 };

  if (!history || history.length === 0) {
    return (
      <div style={{ height: H, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', gap: '8px' }}>
        <TrendingUp size={30} />
        <p style={{ fontSize: '13px' }}>No completed scans with a recorded score yet.</p>
        <p style={{ fontSize: '12px', color: 'var(--text-subtle)' }}>Run a website scan — each scan adds a point to this trend.</p>
      </div>
    );
  }

  const min = Math.min(0, ...history.map((p) => p.score), baseline ?? 100);
  const max = Math.max(100, ...history.map((p) => p.score), baseline ?? 0);
  const range = max - min || 1;

  const x = (i: number) => PAD.left + (i * (W - PAD.left - PAD.right)) / Math.max(history.length - 1, 1);
  const y = (v: number) => PAD.top + ((max - v) / range) * (H - PAD.top - PAD.bottom);

  const linePath = history.map((p, i) => `${i === 0 ? 'M' : 'L'}${x(i).toFixed(1)},${y(p.score).toFixed(1)}`).join(' ');
  const areaPath = `${linePath} L${x(history.length - 1).toFixed(1)},${(H - PAD.bottom).toFixed(1)} L${x(0).toFixed(1)},${(H - PAD.bottom).toFixed(1)} Z`;

  const gridLines = [0, 25, 50, 75, 100].filter((v) => v >= min && v <= max);

  return (
    <svg viewBox={`0 0 ${W} ${H}`} style={{ width: '100%', height: 'auto', display: 'block' }}>
      {/* Gridlines */}
      {gridLines.map((v) => (
        <g key={v}>
          <line x1={PAD.left} x2={W - PAD.right} y1={y(v)} y2={y(v)} stroke="rgba(255,255,255,0.07)" strokeWidth="1" />
          <text x={PAD.left - 6} y={y(v) + 3} textAnchor="end" fontSize="10" fill="#64748b">{v}</text>
        </g>
      ))}

      {/* Baseline */}
      {baseline !== undefined && baseline !== null && (
        <g>
          <line x1={PAD.left} x2={W - PAD.right} y1={y(baseline)} y2={y(baseline)} stroke="#818cf8" strokeWidth="1.5" strokeDasharray="6 4" />
          <text x={W - PAD.right} y={y(baseline) - 5} textAnchor="end" fontSize="10" fill="#818cf8">baseline {baseline}</text>
        </g>
      )}

      {/* Area + line */}
      <path d={areaPath} fill="rgba(99,102,241,0.12)" stroke="none" />
      <path d={linePath} fill="none" stroke="#6366f1" strokeWidth="2.5" strokeLinejoin="round" strokeLinecap="round" />

      {/* Points */}
      {history.map((p, i) => (
        <g key={i}>
          <circle cx={x(i)} cy={y(p.score)} r="4" fill={scoreColor(p.score)} stroke="#0f172a" strokeWidth="1.5">
            <title>{`${formatDate(p.date)} — Score ${p.score}/100, ${p.issues} issues, ${p.pages} pages`}</title>
          </circle>
          {history.length <= 8 && (
            <text x={x(i)} y={y(p.score) - 8} textAnchor="middle" fontSize="10" fill="#94a3b8">{p.score}</text>
          )}
        </g>
      ))}

      {/* X labels */}
      {history.length > 1 && history.map((p, i) => {
        if (history.length > 8 && i % 2 !== 0 && i !== history.length - 1) return null;
        const label = (() => {
          try {
            const iso = p.date.endsWith('Z') ? p.date : p.date + 'Z';
            return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
          } catch { return ''; }
        })();
        return (
          <text key={`x${i}`} x={x(i)} y={H - 8} textAnchor="middle" fontSize="10" fill="#64748b">{label}</text>
        );
      })}
    </svg>
  );
}

function TrendAreaChart({ data, label, color }: { data: { date: string; value: number }[]; label: string; color: string }) {
  const W = 560;
  const H = 180;
  const PAD = { top: 16, right: 14, bottom: 24, left: 42 };

  if (!data || data.length === 0) {
    return (
      <div style={{ height: H, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: '12px' }}>
        No {label} data yet.
      </div>
    );
  }

  const max = Math.max(1, ...data.map((d) => d.value));
  const range = max || 1;
  const x = (i: number) => PAD.left + (i * (W - PAD.left - PAD.right)) / Math.max(data.length - 1, 1);
  const y = (v: number) => PAD.top + ((max - v) / range) * (H - PAD.top - PAD.bottom);
  const line = data.map((d, i) => `${i === 0 ? 'M' : 'L'}${x(i).toFixed(1)},${y(d.value).toFixed(1)}`).join(' ');
  const area = `${line} L${x(data.length - 1).toFixed(1)},${(H - PAD.bottom).toFixed(1)} L${x(0).toFixed(1)},${(H - PAD.bottom).toFixed(1)} Z`;
  const ticks = Array.from(new Set([0, Math.round(max / 2), Math.round(max)]));

  return (
    <svg viewBox={`0 0 ${W} ${H}`} style={{ width: '100%', height: 'auto', display: 'block' }}>
      {ticks.map((v) => (
        <g key={v}>
          <line x1={PAD.left} x2={W - PAD.right} y1={y(v)} y2={y(v)} stroke="rgba(255,255,255,0.07)" strokeWidth="1" />
          <text x={PAD.left - 6} y={y(v) + 3} textAnchor="end" fontSize="10" fill="#64748b">{v}</text>
        </g>
      ))}
      <path d={area} fill={`${color}22`} stroke="none" />
      <path d={line} fill="none" stroke={color} strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" />
      {data.map((d, i) => (
        <circle key={i} cx={x(i)} cy={y(d.value)} r="3" fill={color} stroke="#0f172a" strokeWidth="1">
          <title>{`${d.date} — ${d.value} ${label}`}</title>
        </circle>
      ))}
      {data.length > 1 && data.map((d, i) => {
        if (data.length > 10 && i % 4 !== 0 && i !== data.length - 1) return null;
        return <text key={`x${i}`} x={x(i)} y={H - 7} textAnchor="middle" fontSize="9" fill="#64748b">{d.date.slice(5)}</text>;
      })}
    </svg>
  );
}

function SeverityBar({ severity }: { severity: { critical: number; warning: number; info: number } }) {
  const total = severity.critical + severity.warning + severity.info;
  if (total === 0) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', color: '#10b981' }}>
        <CheckCircle2 size={16} /> No open issues — site is clean.
      </div>
    );
  }
  const pct = (v: number) => (v / total) * 100;
  return (
    <div>
      <div style={{ display: 'flex', height: '14px', borderRadius: '7px', overflow: 'hidden', background: 'rgba(255,255,255,0.06)', marginBottom: '10px' }}>
        {severity.critical > 0 && <div style={{ width: `${pct(severity.critical)}%`, background: '#f43f5e' }} title={`${severity.critical} critical`} />}
        {severity.warning > 0 && <div style={{ width: `${pct(severity.warning)}%`, background: '#f59e0b' }} title={`${severity.warning} warning`} />}
        {severity.info > 0 && <div style={{ width: `${pct(severity.info)}%`, background: '#06b6d4' }} title={`${severity.info} info`} />}
      </div>
      <div style={{ display: 'flex', gap: '18px', fontSize: '12px', flexWrap: 'wrap' }}>
        <span style={{ color: '#f43f5e' }}>● Critical {severity.critical}</span>
        <span style={{ color: '#f59e0b' }}>● Warning {severity.warning}</span>
        <span style={{ color: '#06b6d4' }}>● Info {severity.info}</span>
      </div>
    </div>
  );
}

export default function WebsiteReportPage({ params }: { params: { id: string } | Promise<{ id: string }> }) {
  const router = useRouter();
  const [report, setReport] = useState<WebsiteReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [pdfExporting, setPdfExporting] = useState(false);
  const [syncingGsc, setSyncingGsc] = useState(false);
  const [gscError, setGscError] = useState('');
  const [gscNotice, setGscNotice] = useState('');

  const fetchReport = useCallback(async (id: string) => {
    setLoading(true);
    try {
      const res = await api.get(`/reports/website/${id}`);
      setReport(res.data);
    } catch (err: any) {
      if (err.response?.status === 401) {
        router.push('/');
      } else {
        alert('Failed to load report');
      }
    } finally {
      setLoading(false);
    }
  }, [router]);

  useEffect(() => {
    Promise.resolve(params).then((p) => {
      if (p && p.id) fetchReport(p.id);
    });
  }, [params, fetchReport]);

  useEffect(() => {
    const q = new URLSearchParams(window.location.search);
    const gscParam = q.get('gsc');
    if (gscParam === 'connected') setGscNotice('Google Search Console connected — syncing data now.');
    if (gscParam === 'error') setGscNotice('Google Search Console connection failed. Check the property and try again.');
  }, []);

  const handleConnectGsc = async () => {
    if (!report) return;
    setGscError('');
    try {
      const res = await api.get(`/gsc/auth-url?website_id=${report.id}`);
      window.location.href = res.data.url;
    } catch (err: any) {
      setGscError(err.response?.data?.detail || 'Failed to start Google connection.');
    }
  };

  const handleSyncGsc = async () => {
    if (!report) return;
    setSyncingGsc(true);
    setGscError('');
    try {
      await api.post(`/gsc/sync/${report.id}`);
      await fetchReport(String(report.id));
    } catch (err) {
      setGscError('Sync failed. Try again in a moment.');
    } finally {
      setSyncingGsc(false);
    }
  };

  const handleDisconnectGsc = async () => {
    if (!report) return;
    if (!window.confirm('Disconnect Google Search Console from this site?')) return;
    try {
      await api.post(`/gsc/disconnect/${report.id}`);
      await fetchReport(String(report.id));
    } catch (err) {
      setGscError('Failed to disconnect.');
    }
  };

  const handleExportCsv = async () => {
    if (!report) return;
    setExporting(true);
    try {
      const res = await api.get(`/reports/website/${report.id}/export`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement('a');
      a.href = url;
      a.download = `seoops_report_${report.domain.replace(/\./g, '_')}.csv`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert('CSV export failed');
    } finally {
      setExporting(false);
    }
  };

  const handleExportPdf = async () => {
    if (!report) return;
    setPdfExporting(true);
    try {
      const res = await api.get(`/reports/website/${report.id}/pdf`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }));
      const a = document.createElement('a');
      a.href = url;
      a.download = `seoops_report_${report.domain.replace(/\./g, '_')}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert('PDF export failed');
    } finally {
      setPdfExporting(false);
    }
  };

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', justifyContent: 'center', alignItems: 'center', background: 'var(--bg-main)', color: '#fff' }}>
        <div style={{ textAlign: 'center' }}>
          <RefreshCw size={30} className="spin" style={{ marginBottom: '12px' }} />
          <p style={{ fontSize: '15px', fontWeight: 600 }}>Building report...</p>
        </div>
      </div>
    );
  }

  if (!report) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', justifyContent: 'center', alignItems: 'center', background: 'var(--bg-main)', color: '#f43f5e' }}>
        Report not found.
      </div>
    );
  }

  const delta = report.score_delta;

  return (
    <div style={{ minHeight: '100vh', padding: '32px', maxWidth: '1200px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', flexWrap: 'wrap', gap: '12px' }}>
        <button className="btn-secondary" onClick={() => router.push('/reports')}>
          <ArrowLeft size={16} /> All Reports
        </button>

        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          <button className="btn-secondary" onClick={() => window.open(`/portal/${report.id}`, '_blank')} style={{ color: '#818cf8' }}>
            <Share2 size={15} /> Share Client Link
          </button>
          <button className="btn-secondary" onClick={handleExportCsv} disabled={exporting}>
            {exporting ? <RefreshCw size={15} className="spin" /> : <FileDown size={15} />}
            {exporting ? 'Exporting...' : 'Export CSV'}
          </button>
          <button className="btn-primary" onClick={handleExportPdf} disabled={pdfExporting}>
            {pdfExporting ? <RefreshCw size={15} className="spin" /> : <FileSpreadsheet size={15} />}
            {pdfExporting ? 'Generating...' : 'Download PDF'}
          </button>
          <button className="btn-secondary" onClick={() => window.print()}>
            <Printer size={15} /> Print View
          </button>
          <button className="btn-secondary" onClick={() => router.push(`/website/${report.id}`)}>
            <Activity size={15} /> Live Workspace
          </button>
        </div>
      </div>

      {/* Report Title */}
      <div className="glass-card" style={{ padding: '28px', marginBottom: '24px', background: 'linear-gradient(135deg, rgba(99,102,241,0.18) 0%, rgba(15,23,42,0.85) 100%)', border: '1px solid rgba(99,102,241,0.3)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '20px' }}>
          <div>
            <span style={{ fontSize: '12px', color: '#818cf8', textTransform: 'uppercase', letterSpacing: '1px', fontWeight: 700 }}>SEO Performance Report</span>
            <h1 style={{ fontSize: '30px', fontWeight: 700, marginTop: '6px', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Globe size={26} color="#06b6d4" /> {report.domain}
            </h1>
            <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '6px' }}>
              {report.industry ? `${report.industry} • ` : ''}Generated {formatDate(new Date().toISOString())} • {report.total_scans} scans completed
            </p>
          </div>

          <div style={{ display: 'flex', gap: '24px', alignItems: 'center', padding: '16px 24px', background: 'rgba(15,23,42,0.7)', border: '1px solid var(--border-card)', borderRadius: '14px', flexWrap: 'wrap' }}>
            <div>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Current Health Score</div>
              <div style={{ fontSize: '34px', fontWeight: 700, color: scoreColor(report.current_score) }}>
                {report.current_score ?? '—'} <span style={{ fontSize: '16px', color: 'var(--text-muted)' }}>/100</span>
              </div>
            </div>
            <div style={{ width: '1px', height: '40px', background: 'var(--border-card)' }} />
            <div>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Baseline</div>
              <div style={{ fontSize: '24px', fontWeight: 700, color: '#818cf8' }}>{report.baseline_score ?? '—'}</div>
            </div>
            <div style={{ width: '1px', height: '40px', background: 'var(--border-card)' }} />
            <div>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Improvement</div>
              <div style={{ fontSize: '24px', fontWeight: 700, color: delta !== undefined && delta !== null && delta >= 0 ? '#10b981' : '#f43f5e' }}>
                {delta !== undefined && delta !== null ? `${delta >= 0 ? '+' : ''}${delta}` : '—'} pts
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* KPI Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '14px', marginBottom: '24px' }}>
        <div className="glass-card" style={{ padding: '16px 18px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Pages Monitored</div>
          <div style={{ fontSize: '24px', fontWeight: 700, color: '#818cf8' }}>{report.pages_count}</div>
        </div>
        <div className="glass-card" style={{ padding: '16px 18px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Open Issues</div>
          <div style={{ fontSize: '24px', fontWeight: 700, color: report.open_issues > 0 ? '#f59e0b' : '#10b981' }}>{report.open_issues}</div>
        </div>
        <div className="glass-card" style={{ padding: '16px 18px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Fixes Deployed</div>
          <div style={{ fontSize: '24px', fontWeight: 700, color: '#10b981' }}>{report.approved_fixes}</div>
        </div>
        <div className="glass-card" style={{ padding: '16px 18px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Content Changes</div>
          <div style={{ fontSize: '24px', fontWeight: 700, color: '#06b6d4' }}>{report.changes_detected}</div>
        </div>
        <div className="glass-card" style={{ padding: '16px 18px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Leads Captured</div>
          <div style={{ fontSize: '24px', fontWeight: 700, color: '#06b6d4' }}>{report.leads_captured}</div>
        </div>
        <div className="glass-card" style={{ padding: '16px 18px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Rollback Versions</div>
          <div style={{ fontSize: '24px', fontWeight: 700, color: '#a78bfa' }}>{report.versions_deployed}</div>
        </div>
      </div>

      {/* Score Trend */}
      <div className="glass-card" style={{ padding: '24px', marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
          <TrendingUp color="#6366f1" size={20} />
          <h3 style={{ fontSize: '18px', fontWeight: 700 }}>SEO Health Score Trend</h3>
        </div>
        <p style={{ fontSize: '12px', color: 'var(--text-subtle)', marginBottom: '16px' }}>
          One point per completed crawl — watch fixes move the score over time.
        </p>
        <ScoreTrendChart history={report.score_history} baseline={report.baseline_score ?? undefined} />
      </div>

      {/* Google Search Console — real search performance */}
      <div className="glass-card" style={{ padding: '24px', marginBottom: '24px', border: report.gsc.connected ? '1px solid rgba(16,185,129,0.35)' : '1px solid var(--border-card)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px', marginBottom: '6px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Link2 color="#10b981" size={20} />
            <h3 style={{ fontSize: '18px', fontWeight: 700 }}>Google Search Console — Real Search Performance</h3>
          </div>

          {report.gsc.connected ? (
            <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
              <button className="btn-secondary" style={{ padding: '6px 12px', fontSize: '12px' }} onClick={handleSyncGsc} disabled={syncingGsc}>
                <RefreshCw size={13} className={syncingGsc ? 'spin' : ''} /> {syncingGsc ? 'Syncing...' : 'Sync Now'}
              </button>
              <button className="btn-secondary" style={{ padding: '6px 12px', fontSize: '12px', color: '#f43f5e' }} onClick={handleDisconnectGsc}>
                <Unplug size={13} /> Disconnect
              </button>
            </div>
          ) : (
            <button className="btn-primary" style={{ background: '#10b981', fontSize: '13px' }} onClick={handleConnectGsc}>
              <Plug size={14} /> Connect Google Search Console
            </button>
          )}
        </div>

        {gscNotice && (
          <div style={{ marginBottom: '14px', padding: '10px 14px', borderRadius: '8px', fontSize: '13px', background: 'rgba(16,185,129,0.12)', border: '1px solid rgba(16,185,129,0.3)', color: '#34d399' }}>
            {gscNotice}
          </div>
        )}
        {gscError && (
          <div style={{ marginBottom: '14px', padding: '10px 14px', borderRadius: '8px', fontSize: '13px', background: 'rgba(244,63,94,0.12)', border: '1px solid rgba(244,63,94,0.3)', color: '#f43f5e' }}>
            {gscError}
          </div>
        )}

        {!report.gsc.connected ? (
          <div style={{ padding: '12px 0 4px', fontSize: '13px', color: 'var(--text-muted)', lineHeight: 1.6 }}>
            {report.gsc.status === 'error' && report.gsc.error_message ? (
              <p style={{ color: '#f59e0b', marginBottom: '8px' }}>⚠️ {report.gsc.error_message}</p>
            ) : null}
            <p>
              Connect Google Search Console to show <strong style={{ color: '#e2e8f0' }}>real clicks, impressions, and average position</strong> from Google —
              the actual business impact of your SEO work, not just a health score. You'll be asked to verify that you own this domain
              (free with Google).
            </p>
          </div>
        ) : (
          <>
            <p style={{ fontSize: '12px', color: 'var(--text-subtle)', marginBottom: '16px' }}>
              Property: <strong style={{ color: '#a5b4fc' }}>{report.gsc.site_url}</strong>
              {report.gsc.last_sync_at ? ` • Last synced ${formatDate(report.gsc.last_sync_at)}` : ''}
              {report.gsc.status === 'error' && report.gsc.error_message ? ` • ⚠️ ${report.gsc.error_message}` : ''}
            </p>

            {report.gsc.metrics.length > 0 ? (
              <>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '12px', marginBottom: '20px' }}>
                  {(() => {
                    const m = report.gsc.metrics;
                    const totalClicks = m.reduce((a, r) => a + r.clicks, 0);
                    const totalImpressions = m.reduce((a, r) => a + r.impressions, 0);
                    const avgPosition = m.reduce((a, r) => a + r.position, 0) / m.length;
                    const avgCtr = m.reduce((a, r) => a + r.ctr, 0) / m.length;
                    return (
                      <>
                        <div className="glass-card" style={{ padding: '14px 16px' }}>
                          <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Clicks (30d)</div>
                          <div style={{ fontSize: '22px', fontWeight: 700, color: '#10b981' }}>{totalClicks}</div>
                        </div>
                        <div className="glass-card" style={{ padding: '14px 16px' }}>
                          <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Impressions (30d)</div>
                          <div style={{ fontSize: '22px', fontWeight: 700, color: '#818cf8' }}>{totalImpressions}</div>
                        </div>
                        <div className="glass-card" style={{ padding: '14px 16px' }}>
                          <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Avg Position</div>
                          <div style={{ fontSize: '22px', fontWeight: 700, color: '#06b6d4' }}>{avgPosition.toFixed(1)}</div>
                        </div>
                        <div className="glass-card" style={{ padding: '14px 16px' }}>
                          <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Avg CTR</div>
                          <div style={{ fontSize: '22px', fontWeight: 700, color: '#a78bfa' }}>{(avgCtr * 100).toFixed(1)}%</div>
                        </div>
                      </>
                    );
                  })()}
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '20px' }}>
                  <div>
                    <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '8px' }}>Daily Impressions</div>
                    <TrendAreaChart
                      data={report.gsc.metrics.map((m) => ({ date: m.date, value: m.impressions }))}
                      label="impressions"
                      color="#818cf8"
                    />
                  </div>
                  <div>
                    <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '8px' }}>Daily Clicks</div>
                    <TrendAreaChart
                      data={report.gsc.metrics.map((m) => ({ date: m.date, value: m.clicks }))}
                      label="clicks"
                      color="#10b981"
                    />
                  </div>
                </div>
              </>
            ) : (
              <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
                Connected, but no data yet — click <strong>Sync Now</strong> or wait for the daily sync.
              </p>
            )}

            {report.gsc.top_queries.length > 0 && (
              <div style={{ overflowX: 'auto' }}>
                <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '8px' }}>TOP SEARCH QUERIES (snapshot)</div>
                <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
                  <thead>
                    <tr style={{ background: 'rgba(255,255,255,0.03)', borderBottom: '1px solid var(--border-card)', color: 'var(--text-muted)' }}>
                      <th style={{ padding: '10px 12px' }}>Query</th>
                      <th style={{ padding: '10px 12px' }}>Clicks</th>
                      <th style={{ padding: '10px 12px' }}>Impressions</th>
                      <th style={{ padding: '10px 12px' }}>Position</th>
                      <th style={{ padding: '10px 12px' }}>CTR</th>
                    </tr>
                  </thead>
                  <tbody>
                    {report.gsc.top_queries.map((q, i) => (
                      <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                        <td style={{ padding: '10px 12px', color: '#e2e8f0', fontWeight: 600 }}>{q.query}</td>
                        <td style={{ padding: '10px 12px', color: '#10b981' }}>{q.clicks}</td>
                        <td style={{ padding: '10px 12px' }}>{q.impressions}</td>
                        <td style={{ padding: '10px 12px', color: q.position <= 10 ? '#10b981' : 'var(--text-main)' }}>{q.position.toFixed(1)}</td>
                        <td style={{ padding: '10px 12px' }}>{(q.ctr * 100).toFixed(1)}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '24px' }}>
        {/* Severity + Issue breakdown */}
        <div className="glass-card" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
            <AlertTriangle color="#f59e0b" size={20} />
            <h3 style={{ fontSize: '17px', fontWeight: 700 }}>Open Issue Severity</h3>
          </div>
          <SeverityBar severity={report.severity_breakdown} />

          <div style={{ marginTop: '22px', fontSize: '12px', color: 'var(--text-subtle)', fontWeight: 600, marginBottom: '8px' }}>
            MOST COMMON ISSUE TYPES
          </div>
          {report.issue_breakdown.length === 0 ? (
            <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>No open issues to report.</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {report.issue_breakdown.slice(0, 8).map((row) => (
                <div key={row.issue_type} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px' }}>
                  <span style={{ fontSize: '13px', color: 'var(--text-muted)', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{row.issue_type}</span>
                  <div style={{ width: '120px', height: '6px', borderRadius: '3px', background: 'rgba(255,255,255,0.06)', overflow: 'hidden', flexShrink: 0 }}>
                    <div
                      style={{
                        width: `${Math.min(100, (row.count / report.issue_breakdown[0].count) * 100)}%`,
                        height: '100%',
                        background: row.severity === 'critical' ? '#f43f5e' : row.severity === 'warning' ? '#f59e0b' : '#06b6d4'
                      }}
                    />
                  </div>
                  <span style={{ fontSize: '13px', fontWeight: 600, width: '24px', textAlign: 'right' }}>{row.count}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Leads by source */}
        <div className="glass-card" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
            <Users color="#10b981" size={20} />
            <h3 style={{ fontSize: '17px', fontWeight: 700 }}>Lead Attribution by Source</h3>
          </div>
          {report.leads_by_source.length === 0 ? (
            <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>No leads captured yet — seed sample leads from the workspace or install the tracking snippet.</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {report.leads_by_source.map((row) => {
                const total = report.leads_by_source.reduce((a, r) => a + r.count, 0);
                const isAi = ['chatgpt', 'perplexity', 'claude', 'gemini'].includes(row.source.toLowerCase());
                return (
                  <div key={row.source} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px' }}>
                    <span style={{ fontSize: '13px', color: 'var(--text-muted)', display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
                      {isAi ? <Sparkles size={13} color="#818cf8" /> : <Link2 size={13} color="#06b6d4" />}
                      {row.source.replace(/_/g, ' ')}
                    </span>
                    <div style={{ width: '120px', height: '6px', borderRadius: '3px', background: 'rgba(255,255,255,0.06)', overflow: 'hidden', flexShrink: 0 }}>
                      <div style={{ width: `${(row.count / total) * 100}%`, height: '100%', background: isAi ? '#818cf8' : '#06b6d4' }} />
                    </div>
                    <span style={{ fontSize: '13px', fontWeight: 600 }}>{row.count}</span>
                  </div>
                );
              })}
            </div>
          )}

          <div style={{ marginTop: '22px', fontSize: '12px', color: 'var(--text-subtle)', fontWeight: 600, marginBottom: '8px' }}>
            RECENTLY DEPLOYED FIXES
          </div>
          {report.fixes_timeline.length === 0 ? (
            <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>No fixes deployed yet.</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '180px', overflowY: 'auto' }}>
              {report.fixes_timeline.slice(0, 10).map((fix) => (
                <div key={fix.id} style={{ background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.2)', borderRadius: '8px', padding: '10px 12px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', gap: '10px', alignItems: 'center' }}>
                    <span style={{ fontSize: '12px', fontWeight: 600, color: '#34d399', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      <CheckCircle2 size={12} style={{ verticalAlign: '-2px', marginRight: '4px' }} />{fix.issue_type}
                    </span>
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)', flexShrink: 0 }}>{formatDate(fix.approved_at)}</span>
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--text-subtle)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{fix.page_url}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Worst Pages */}
      <div className="glass-card" style={{ overflow: 'hidden', marginBottom: '24px' }}>
        <div style={{ padding: '20px 24px', borderBottom: '1px solid var(--border-card)', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <BarChart3 color="#f43f5e" size={20} />
          <h3 style={{ fontSize: '17px', fontWeight: 700 }}>Priority Pages — Lowest SEO Scores</h3>
        </div>
        {report.top_pages.length === 0 ? (
          <div style={{ padding: '32px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '13px' }}>
            No pages crawled yet.
          </div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
            <thead>
              <tr style={{ background: 'rgba(255,255,255,0.03)', borderBottom: '1px solid var(--border-card)', color: 'var(--text-muted)' }}>
                <th style={{ padding: '14px 24px' }}>Page URL</th>
                <th style={{ padding: '14px' }}>Title</th>
                <th style={{ padding: '14px' }}>Words</th>
                <th style={{ padding: '14px' }}>Missing Alt</th>
                <th style={{ padding: '14px 24px' }}>Score</th>
              </tr>
            </thead>
            <tbody>
              {report.top_pages.map((p) => (
                <tr key={p.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                  <td style={{ padding: '14px 24px', maxWidth: '280px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    <a href={p.url} target="_blank" rel="noreferrer" style={{ color: '#818cf8' }}>{p.url}</a>
                  </td>
                  <td style={{ padding: '14px', maxWidth: '220px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', color: p.title ? 'var(--text-main)' : '#f43f5e' }}>
                    {p.title || 'Missing Title'}
                  </td>
                  <td style={{ padding: '14px' }}>{p.word_count}</td>
                  <td style={{ padding: '14px', color: p.missing_alt_count > 0 ? '#f59e0b' : 'var(--text-main)' }}>{p.missing_alt_count}</td>
                  <td style={{ padding: '14px 24px' }}>
                    <span className={`badge ${p.seo_score > 80 ? 'badge-healthy' : p.seo_score > 60 ? 'badge-warning' : 'badge-critical'}`}>
                      {p.seo_score} / 100
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Export footer */}
      <div style={{ display: 'flex', gap: '12px', alignItems: 'center', justifyContent: 'center', padding: '12px', fontSize: '13px', color: 'var(--text-muted)' }}>
        <FileSpreadsheet size={16} color="#10b981" />
        Download the full CSV (summary, all pages, all open issues) for client attachments or further analysis.
      </div>
    </div>
  );
}
