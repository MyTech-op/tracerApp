'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api, Website } from '@/lib/api';
import { Globe, Plus, Play, Trash2, ArrowRight, ShieldCheck, Activity, LogOut, Settings, BarChart3, CreditCard } from 'lucide-react';

export default function Dashboard() {
  const router = useRouter();
  const [websites, setWebsites] = useState<Website[]>([]);
  const [newDomain, setNewDomain] = useState('');
  const [loading, setLoading] = useState(true);
  const [adding, setAdding] = useState(false);
  const [showModal, setShowModal] = useState(false);

  useEffect(() => {
    fetchWebsites();
  }, []);

  const fetchWebsites = async () => {
    try {
      const res = await api.get('/website');
      setWebsites(res.data);
    } catch (err) {
      console.error(err);
      router.push('/');
    } finally {
      setLoading(false);
    }
  };

  const handleAddWebsite = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newDomain.trim()) return;
    setAdding(true);
    try {
      const res = await api.post('/website', { domain: newDomain });
      setNewDomain('');
      setShowModal(false);
      if (res.data && res.data.id) {
        router.push(`/website/${res.data.id}`);
      } else {
        fetchWebsites();
      }
    } catch (err) {
      alert('Failed to add website');
    } finally {
      setAdding(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to remove this website?')) return;
    try {
      await api.delete(`/website/${id}`);
      fetchWebsites();
    } catch (err) {
      alert('Failed to delete website');
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    router.push('/');
  };

  return (
    <div style={{ minHeight: '100vh', padding: '32px', maxWidth: '1200px', margin: '0 auto' }}>
      {/* Top Navbar */}
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px', paddingBottom: '20px', borderBottom: '1px solid var(--border-card)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ padding: '8px', background: 'rgba(99,102,241,0.2)', borderRadius: '12px' }}>
            <Activity color="#6366f1" size={24} />
          </div>
          <div>
            <h1 style={{ fontSize: '24px', fontWeight: 700 }}>SEOOps Workspace</h1>
            <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>Continuous Monitoring & Autonomous AI Fixes</p>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '12px' }}>
          <button className="btn-primary" onClick={() => router.push('/reports')}>
            <BarChart3 size={16} /> Reports
          </button>
          <button className="btn-secondary" onClick={() => router.push('/settings')}>
            <Settings size={16} /> Agency Settings
          </button>
          <button className="btn-secondary" onClick={() => router.push('/billing')}>
            <CreditCard size={16} /> Billing
          </button>
          <button className="btn-primary" onClick={() => setShowModal(true)}>
            <Plus size={16} /> Add Website
          </button>
          <button className="btn-secondary" onClick={handleLogout}>
            <LogOut size={16} />
          </button>
        </div>
      </header>

      {/* Main Content */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '60px', color: 'var(--text-muted)' }}>Loading workspace domains...</div>
      ) : websites.length === 0 ? (
        <div className="glass-card" style={{ padding: '60px', textAlign: 'center' }}>
          <Globe size={48} color="#64748b" style={{ marginBottom: '16px' }} />
          <h2 style={{ fontSize: '20px', fontWeight: 600, marginBottom: '8px' }}>No Websites Tracked Yet</h2>
          <p style={{ fontSize: '14px', color: 'var(--text-muted)', marginBottom: '24px' }}>
            Add your domain to start continuous SEO monitoring, incremental crawling, and automated fix recommendations.
          </p>
          <button className="btn-primary" onClick={() => setShowModal(true)}>
            <Plus size={16} /> Add Your First Website
          </button>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: '20px' }}>
          {websites.map((site) => (
            <div key={site.id} className="glass-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <Globe size={20} color="#06b6d4" />
                    <h3 style={{ fontSize: '18px', fontWeight: 600 }}>{site.domain}</h3>
                  </div>
                  <span className={`badge ${site.status === 'scanning' ? 'badge-warning' : 'badge-healthy'}`}>
                    {site.status}
                  </span>
                </div>

                <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '20px' }}>
                  Last scan: {site.last_scan_at ? new Date(site.last_scan_at.endsWith('Z') ? site.last_scan_at : site.last_scan_at + 'Z').toLocaleString('en-US', { timeZone: 'Asia/Kathmandu', month: 'short', day: 'numeric', year: 'numeric', hour: 'numeric', minute: '2-digit', hour12: true }) : 'Never scanned'}
                </p>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '16px', borderTop: '1px solid rgba(255,255,255,0.06)' }}>
                <button
                  className="btn-secondary"
                  style={{ color: '#f43f5e', padding: '8px 12px' }}
                  onClick={() => handleDelete(site.id)}
                >
                  <Trash2 size={14} />
                </button>

                <button
                  className="btn-primary"
                  style={{ padding: '8px 16px', fontSize: '13px' }}
                  onClick={() => router.push(`/website/${site.id}`)}
                >
                  View Details <ArrowRight size={14} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Add Website Modal */}
      {showModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(4px)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 100 }}>
          <div className="glass-card" style={{ width: '100%', maxWidth: '450px', padding: '32px' }}>
            <h2 style={{ fontSize: '20px', fontWeight: 600, marginBottom: '8px' }}>Add Website to Track</h2>
            <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '20px' }}>Enter domain (e.g. example.com or travelnepal.com)</p>

            <form onSubmit={handleAddWebsite}>
              <input
                type="text"
                className="glass-input"
                placeholder="example.com"
                value={newDomain}
                onChange={(e) => setNewDomain(e.target.value)}
                autoFocus
                required
                style={{ marginBottom: '20px' }}
              />

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
                <button type="button" className="btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
                <button type="submit" className="btn-primary" disabled={adding}>
                  {adding ? 'Adding...' : 'Add & Start Crawl'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
