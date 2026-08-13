'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api, UserSettings } from '@/lib/api';
import { ArrowLeft, Save, Key, Building, CheckCircle2, Sparkles, Shield } from 'lucide-react';

export default function SettingsPage() {
  const router = useRouter();
  const [agencyName, setAgencyName] = useState('');
  const [semrushKey, setSemrushKey] = useState('');
  const [ahrefsKey, setAhrefsKey] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);
  const [settingsStatus, setSettingsStatus] = useState<UserSettings | null>(null);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const res = await api.get('/settings');
      setSettingsStatus(res.data);
      setAgencyName(res.data.agency_name || '');
    } catch (err) {
      console.error('Failed to load settings', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSavedSuccess(false);
    try {
      const payload: any = { agency_name: agencyName };
      if (semrushKey.trim()) payload.semrush_api_key = semrushKey.trim();
      if (ahrefsKey.trim()) payload.ahrefs_api_key = ahrefsKey.trim();

      const res = await api.patch('/settings', payload);
      setSettingsStatus(res.data);
      setSemrushKey('');
      setAhrefsKey('');
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 3000);
    } catch (err) {
      alert('Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', padding: '32px', maxWidth: '800px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <button className="btn-secondary" onClick={() => router.push('/dashboard')}>
          <ArrowLeft size={16} /> Back to Dashboard
        </button>
      </div>

      <div className="glass-card" style={{ padding: '28px', marginBottom: '32px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
          <Building size={24} color="#818cf8" />
          <h1 style={{ fontSize: '24px', fontWeight: 700 }}>Agency Settings & BYOK Integrations</h1>
        </div>
        <p style={{ fontSize: '14px', color: 'var(--text-muted)' }}>
          Configure your whitelabel agency branding and optionally plug in your own SEMrush or Ahrefs API keys for live 3rd-party data integration.
        </p>
      </div>

      {savedSuccess && (
        <div style={{ background: 'rgba(16, 185, 129, 0.15)', border: '1px solid rgba(16, 185, 129, 0.3)', padding: '14px 18px', borderRadius: '12px', color: '#34d399', marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <CheckCircle2 size={18} /> Settings saved successfully!
        </div>
      )}

      <form onSubmit={handleSave} style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
        {/* Section 1: Whitelabel Agency Branding */}
        <div className="glass-card" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
            <Sparkles size={18} color="#818cf8" />
            <h3 style={{ fontSize: '16px', fontWeight: 600 }}>Whitelabel Agency Branding</h3>
          </div>
          <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '16px' }}>
            This name will be displayed at the top of your shareable live Client Portals (`/portal/[id]`).
          </p>

          <div>
            <label style={{ fontSize: '13px', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>
              Agency Name
            </label>
            <input
              type="text"
              className="glass-input"
              placeholder="e.g. Acme Growth Marketing Agency"
              value={agencyName}
              onChange={(e) => setAgencyName(e.target.value)}
              style={{ width: '100%' }}
            />
          </div>
        </div>

        {/* Section 2: BYOK External API Integrations */}
        <div className="glass-card" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
            <Key size={18} color="#10b981" />
            <h3 style={{ fontSize: '16px', fontWeight: 600 }}>Bring Your Own Key (BYOK) Paid Integrations</h3>
          </div>
          <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '16px' }}>
            By default, SEOOps uses internal crawling + AI models for backlink profiles and search intent volume estimates. If you have paid SEMrush or Ahrefs subscriptions, enter your API keys below to fetch exact 3rd-party index data.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                <label style={{ fontSize: '13px', color: 'var(--text-muted)' }}>SEMrush API Key</label>
                {settingsStatus?.semrush_api_key_set ? (
                  <span className="badge badge-healthy" style={{ fontSize: '11px' }}>✓ Connected</span>
                ) : (
                  <span className="badge" style={{ fontSize: '11px', background: 'rgba(148, 163, 184, 0.2)', color: '#94a3b8' }}>Optional (AI Estimate Active)</span>
                )}
              </div>
              <input
                type="password"
                className="glass-input"
                placeholder={settingsStatus?.semrush_api_key_set ? '••••••••••••••••' : 'Enter SEMrush API Key'}
                value={semrushKey}
                onChange={(e) => setSemrushKey(e.target.value)}
                style={{ width: '100%' }}
              />
            </div>

            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                <label style={{ fontSize: '13px', color: 'var(--text-muted)' }}>Ahrefs API Key</label>
                {settingsStatus?.ahrefs_api_key_set ? (
                  <span className="badge badge-healthy" style={{ fontSize: '11px' }}>✓ Connected</span>
                ) : (
                  <span className="badge" style={{ fontSize: '11px', background: 'rgba(148, 163, 184, 0.2)', color: '#94a3b8' }}>Optional (AI Estimate Active)</span>
                )}
              </div>
              <input
                type="password"
                className="glass-input"
                placeholder={settingsStatus?.ahrefs_api_key_set ? '••••••••••••••••' : 'Enter Ahrefs API Key'}
                value={ahrefsKey}
                onChange={(e) => setAhrefsKey(e.target.value)}
                style={{ width: '100%' }}
              />
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <button className="btn-primary" type="submit" disabled={saving} style={{ background: '#10b981', padding: '10px 24px' }}>
            <Save size={16} /> {saving ? 'Saving Settings...' : 'Save Settings'}
          </button>
        </div>
      </form>
    </div>
  );
}
