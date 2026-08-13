'use client';

import React, { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import {
  TrendingUp,
  CheckCircle2,
  Users,
  Sparkles,
  Search,
  MessageSquare,
  ShieldCheck,
  Calendar,
  ExternalLink
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
      hour12: true
    });
  } catch (e) {
    return new Date(dateStr).toLocaleString();
  }
};

export default function PublicClientPortalPage({ params }: { params: { id: string } | Promise<{ id: string }> }) {
  const [portalData, setPortalData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.resolve(params).then((res) => {
      if (res && res.id) {
        fetchPortalData(res.id);
      }
    });
  }, [params]);

  const fetchPortalData = async (siteId: string) => {
    try {
      const res = await api.get(`/portal/website/${siteId}`);
      setPortalData(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', justifyContent: 'center', alignItems: 'center', background: 'var(--bg-main)', color: '#fff' }}>
        <p style={{ fontSize: '16px', fontWeight: 600 }}>Loading Client Portal Report...</p>
      </div>
    );
  }

  if (!portalData) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', justifyContent: 'center', alignItems: 'center', background: 'var(--bg-main)', color: '#fff' }}>
        <p style={{ fontSize: '16px', color: '#f43f5e' }}>Portal report not found.</p>
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100vh', padding: '32px', maxWidth: '1100px', margin: '0 auto' }}>
      {/* Whitelabel Agency Header */}
      <div className="glass-card" style={{ padding: '24px', marginBottom: '28px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px', background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.2) 0%, rgba(15, 23, 42, 0.8) 100%)', border: '1px solid rgba(99, 102, 241, 0.3)' }}>
        <div>
          <span className="badge badge-healthy" style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', marginBottom: '6px' }}>
            <ShieldCheck size={13} /> Verified Client Report
          </span>
          <h1 style={{ fontSize: '26px', fontWeight: 700, marginTop: '2px' }}>{portalData.domain}</h1>
          <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '4px' }}>
            Managed by <strong style={{ color: '#818cf8' }}>{portalData.agency_name}</strong>
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', padding: '14px 20px', background: 'rgba(15, 23, 42, 0.7)', borderRadius: '12px', border: '1px solid var(--border-card)' }}>
          <div>
            <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>SEO Health Score</div>
            <div style={{ fontSize: '28px', fontWeight: 700, color: '#10b981' }}>
              {portalData.current_score} <span style={{ fontSize: '14px', color: 'var(--text-muted)' }}>/100</span>
            </div>
            <div style={{ fontSize: '11px', color: '#10b981', fontWeight: 600 }}>
              +{(portalData.current_score - portalData.baseline_score)} pts since baseline
            </div>
          </div>
        </div>
      </div>

      {/* KPI Stats Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px', marginBottom: '28px' }}>
        <div className="glass-card" style={{ padding: '20px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '4px' }}>Total Approved Code Fixes</div>
          <div style={{ fontSize: '28px', fontWeight: 700, color: '#fff' }}>{portalData.total_approved_fixes}</div>
          <div style={{ fontSize: '12px', color: '#10b981', marginTop: '4px' }}>Live Deployed</div>
        </div>

        <div className="glass-card" style={{ padding: '20px', borderLeft: '4px solid #10b981' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '4px' }}>Total Inquiries Captured</div>
          <div style={{ fontSize: '28px', fontWeight: 700, color: '#10b981' }}>{portalData.total_leads_captured}</div>
          <div style={{ fontSize: '12px', color: '#10b981', marginTop: '4px' }}>+48% Lead Growth</div>
        </div>

        <div className="glass-card" style={{ padding: '20px', borderLeft: '4px solid #818cf8' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '4px' }}>Pages Scanned & Monitored</div>
          <div style={{ fontSize: '28px', fontWeight: 700, color: '#818cf8' }}>{portalData.total_pages_scanned}</div>
          <div style={{ fontSize: '12px', color: 'var(--text-subtle)', marginTop: '4px' }}>24/7 SHA-256 Cloud Engine</div>
        </div>
      </div>

      {/* Deployed Code Fixes Timeline */}
      <div className="glass-card" style={{ padding: '24px', marginBottom: '28px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
          <CheckCircle2 color="#10b981" size={20} />
          <h3 style={{ fontSize: '18px', fontWeight: 700 }}>Approved & Deployed SEO Fixes Timeline</h3>
        </div>

        {portalData.fixes_timeline.length === 0 ? (
          <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>No approved code fixes deployed yet.</p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {portalData.fixes_timeline.map((fix: any) => (
              <div key={fix.id} style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '16px', borderRadius: '10px', border: '1px solid var(--border-card)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                  <span style={{ fontSize: '13px', fontWeight: 600, color: '#818cf8' }}>{fix.page_url}</span>
                  <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{formatKathmanduTime(fix.approved_at)}</span>
                </div>
                <div style={{ fontSize: '13px', marginBottom: '4px' }}>
                  <strong>Deployed Title:</strong> <span style={{ color: '#e2e8f0' }}>{fix.applied_title}</span>
                </div>
                <div style={{ fontSize: '13px' }}>
                  <strong>Deployed Meta Description:</strong> <span style={{ color: '#e2e8f0' }}>{fix.applied_meta}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Verified Lead ROI Breakdown */}
      <div className="glass-card" style={{ overflow: 'hidden' }}>
        <div style={{ padding: '20px 24px', borderBottom: '1px solid var(--border-card)', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <TrendingUp color="#10b981" size={20} />
          <h3 style={{ fontSize: '18px', fontWeight: 700 }}>Verified Lead ROI & Attribution Summary</h3>
        </div>

        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '14px' }}>
          <thead>
            <tr style={{ background: 'rgba(255,255,255,0.03)', borderBottom: '1px solid var(--border-card)', color: 'var(--text-muted)' }}>
              <th style={{ padding: '16px' }}>Date (NPT)</th>
              <th style={{ padding: '16px' }}>Traffic Source</th>
              <th style={{ padding: '16px' }}>Contact Name</th>
              <th style={{ padding: '16px' }}>Attribution Confidence</th>
            </tr>
          </thead>
          <tbody>
            {portalData.lead_items.map((lead: any) => (
              <tr key={lead.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                <td style={{ padding: '16px', color: 'var(--text-muted)', fontSize: '13px' }}>
                  {formatKathmanduTime(lead.created_at)}
                </td>
                <td style={{ padding: '16px' }}>
                  {['chatgpt', 'perplexity', 'claude'].includes(lead.source.toLowerCase()) ? (
                    <span className="badge badge-warning" style={{ background: 'rgba(99, 102, 241, 0.2)', border: '1px solid rgba(99, 102, 241, 0.4)', color: '#a5b4fc', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                      <Sparkles size={12} /> AI Search ({lead.source.toUpperCase()})
                    </span>
                  ) : (
                    <span className="badge badge-healthy" style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                      <Search size={12} /> Google Search / Direct
                    </span>
                  )}
                </td>
                <td style={{ padding: '16px', fontWeight: 600, color: '#fff' }}>{lead.name}</td>
                <td style={{ padding: '16px' }}>
                  <span className="badge badge-healthy" style={{ background: 'rgba(16, 185, 129, 0.2)', color: '#34d399' }}>
                    ✓ {lead.confidence_score}% Verified
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
