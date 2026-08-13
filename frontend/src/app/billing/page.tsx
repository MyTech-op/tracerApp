'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api, BillingStatus } from '@/lib/api';
import { ArrowLeft, CreditCard, Check, Crown, Zap, Rocket, Clock, Globe, AlertTriangle } from 'lucide-react';

export default function BillingPage() {
  const router = useRouter();
  const [status, setStatus] = useState<BillingStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    fetchStatus();
    const checkout = typeof window !== 'undefined'
      ? new URLSearchParams(window.location.search).get('checkout')
      : null;
    if (checkout === 'success') {
      setNotice('✅ Payment successful — your plan is now active.');
      router.replace('/billing');
    } else if (checkout === 'cancelled') {
      setNotice('Checkout was cancelled. No charge was made.');
      router.replace('/billing');
    }
  }, []);

  const fetchStatus = async () => {
    try {
      const res = await api.get('/billing/status');
      setStatus(res.data);
    } catch (err) {
      console.error('Failed to load billing status', err);
    } finally {
      setLoading(false);
    }
  };

  const handleUpgrade = async (planId: string) => {
    if (planId === 'free') return;
    setBusy(planId);
    try {
      const res = await api.post('/billing/checkout', { plan: planId });
      if (res.data?.url) {
        window.location.href = res.data.url;
      } else {
        alert('Could not start checkout');
      }
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      if (typeof detail === 'string') {
        alert(detail);
      } else {
        alert('Billing is not configured on the server yet. Set STRIPE_SECRET_KEY to activate payments.');
      }
    } finally {
      setBusy(null);
    }
  };

  const handleManage = async () => {
    setBusy('manage');
    try {
      const res = await api.post('/billing/portal');
      if (res.data?.url) {
        window.location.href = res.data.url;
      } else {
        alert('No active subscription to manage');
      }
    } catch (err) {
      alert('Could not open the billing portal');
    } finally {
      setBusy(null);
    }
  };

  const planIcons: Record<string, React.ReactNode> = {
    free: <Globe size={20} color="#94a3b8" />,
    starter: <Zap size={20} color="#38bdf8" />,
    growth: <Rocket size={20} color="#a78bfa" />,
    agency: <Crown size={20} color="#fbbf24" />,
  };

  const planOrder = ['free', 'starter', 'growth', 'agency'];

  const usageMeter = (used: number, max: number) => {
    const pct = Math.min(100, Math.round((used / Math.max(1, max)) * 100));
    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div style={{ flex: 1, height: '8px', borderRadius: '99px', background: 'rgba(255,255,255,0.08)', overflow: 'hidden' }}>
          <div
            style={{
              width: `${pct}%`,
              height: '100%',
              borderRadius: '99px',
              background: pct >= 100 ? '#f43f5e' : '#6366f1',
              transition: 'width 0.3s',
            }}
          />
        </div>
        <span style={{ fontSize: '13px', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
          {used} / {max}
        </span>
      </div>
    );
  };

  return (
    <div style={{ minHeight: '100vh', padding: '32px', maxWidth: '1100px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <button className="btn-secondary" onClick={() => router.push('/dashboard')}>
          <ArrowLeft size={16} /> Back to Dashboard
        </button>
      </div>

      <div className="glass-card" style={{ padding: '28px', marginBottom: '32px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
          <CreditCard size={24} color="#818cf8" />
          <h1 style={{ fontSize: '24px', fontWeight: 700 }}>Billing & Plans</h1>
        </div>
        <p style={{ fontSize: '14px', color: 'var(--text-muted)' }}>
          Agency pricing for SEOOps — pay per client-site capacity. Limits are enforced automatically on sites, pages per scan, and scan frequency.
        </p>
      </div>

      {notice && (
        <div style={{ background: 'rgba(16, 185, 129, 0.15)', border: '1px solid rgba(16, 185, 129, 0.3)', padding: '14px 18px', borderRadius: '12px', color: '#34d399', marginBottom: '24px' }}>
          {notice}
        </div>
      )}

      {!status?.billing_configured && (
        <div style={{ background: 'rgba(245, 158, 11, 0.12)', border: '1px solid rgba(245, 158, 11, 0.3)', padding: '14px 18px', borderRadius: '12px', color: '#fbbf24', marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px' }}>
          <AlertTriangle size={16} /> Payments are not configured on the server yet (STRIPE_SECRET_KEY not set). The Free plan is fully functional; upgrade buttons will appear once billing is enabled.
        </div>
      )}

      {loading ? (
        <div style={{ textAlign: 'center', padding: '60px', color: 'var(--text-muted)' }}>Loading billing status...</div>
      ) : status && (
        <>
          {/* Current plan + usage */}
          <div className="glass-card" style={{ padding: '24px', marginBottom: '32px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                {planIcons[status.plan] || <Globe size={20} color="#94a3b8" />}
                <div>
                  <h2 style={{ fontSize: '18px', fontWeight: 700 }}>{status.plan_name} Plan</h2>
                  <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
                    {status.subscription_status !== 'none' ? (
                      <>Subscription {status.subscription_status}
                        {status.current_period_end ? ` · renews ${new Date(status.current_period_end.endsWith('Z') ? status.current_period_end : status.current_period_end + 'Z').toLocaleDateString()}` : ''}
                      </>
                    ) : (
                      'No active subscription'
                    )}
                  </p>
                </div>
              </div>
              {status.subscription_status === 'active' || status.subscription_status === 'trialing' ? (
                <button className="btn-secondary" onClick={handleManage} disabled={busy === 'manage'}>
                  <CreditCard size={16} /> {busy === 'manage' ? 'Opening...' : 'Manage Billing'}
                </button>
              ) : status.billing_configured && (
                <button className="btn-primary" onClick={() => handleUpgrade(status.next_plan || 'starter')} disabled={!!busy}>
                  Upgrade
                </button>
              )}
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '24px' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
                  <Globe size={14} color="#06b6d4" />
                  <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>Tracked websites</span>
                </div>
                {usageMeter(status.sites_used, status.max_sites)}
                <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '6px' }}>
                  {status.sites_remaining > 0 ? `${status.sites_remaining} slots remaining` : 'Limit reached — upgrade to add more'}
                </p>
              </div>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
                  <Zap size={14} color="#a78bfa" />
                  <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>Pages per scan</span>
                </div>
                <p style={{ fontSize: '22px', fontWeight: 700 }}>{status.max_pages_per_scan}</p>
                <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Max pages crawled per scan</p>
              </div>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
                  <Clock size={14} color="#fbbf24" />
                  <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>Scan frequency</span>
                </div>
                <p style={{ fontSize: '22px', fontWeight: 700 }}>
                  {status.scan_interval_hours >= 24 ? 'Daily' : `Every ${status.scan_interval_hours}h`}
                </p>
                <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Minimum interval between scans per site</p>
              </div>
            </div>
          </div>

          {/* Plan cards */}
          <h3 style={{ fontSize: '18px', fontWeight: 700, marginBottom: '16px' }}>Compare Plans</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(230px, 1fr))', gap: '20px' }}>
            {planOrder.map((pid) => {
              const p = status.plans[pid];
              if (!p) return null;
              const isCurrent = pid === status.plan;
              const isUpgrade = planOrder.indexOf(pid) > planOrder.indexOf(status.plan);
              return (
                <div
                  key={pid}
                  className="glass-card"
                  style={{
                    padding: '24px',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between',
                    border: isCurrent ? '1px solid rgba(129, 140, 248, 0.6)' : undefined,
                  }}
                >
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
                      {planIcons[pid]}
                      <h3 style={{ fontSize: '18px', fontWeight: 700 }}>{p.name}</h3>
                    </div>
                    <p style={{ fontSize: '28px', fontWeight: 800, marginBottom: '4px' }}>
                      {p.price_monthly_usd === 0 ? '$0' : `$${p.price_monthly_usd}`}
                      <span style={{ fontSize: '13px', fontWeight: 400, color: 'var(--text-muted)' }}>/mo</span>
                    </p>
                    <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '16px' }}>{p.description}</p>
                    <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '13px' }}>
                      <li style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                        <Check size={14} color="#34d399" /> {p.max_sites} tracked {p.max_sites === 1 ? 'site' : 'sites'}
                      </li>
                      <li style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                        <Check size={14} color="#34d399" /> {p.max_pages_per_scan} pages per scan
                      </li>
                      <li style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                        <Check size={14} color="#34d399" />{' '}
                        {p.scan_interval_hours >= 24 ? 'Daily scans' : `Scan every ${p.scan_interval_hours}h`}
                      </li>
                    </ul>
                  </div>

                  <div style={{ marginTop: '20px' }}>
                    {isCurrent ? (
                      <span className="badge badge-healthy" style={{ width: '100%', textAlign: 'center', padding: '10px' }}>
                        Current Plan
                      </span>
                    ) : isUpgrade ? (
                      <button
                        className="btn-primary"
                        style={{ width: '100%' }}
                        disabled={!!busy}
                        onClick={() => handleUpgrade(pid)}
                      >
                        {busy === pid ? 'Redirecting...' : `Upgrade to ${p.name}`}
                      </button>
                    ) : (
                      <span className="badge" style={{ width: '100%', textAlign: 'center', padding: '10px', background: 'rgba(148, 163, 184, 0.15)', color: '#94a3b8' }}>
                        Downgrade via Manage Billing
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}
