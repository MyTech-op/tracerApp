'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { ShieldCheck, Zap, Bot, Search, ArrowRight, CheckCircle2 } from 'lucide-react';

export default function Home() {
  const router = useRouter();
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('admin@seo.com');
  const [password, setPassword] = useState('admin@123');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      if (isRegister) {
        await api.post('/auth/register', { email, password });
      }

      const params = new URLSearchParams();
      params.append('username', email);
      params.append('password', password);

      const res = await api.post('/auth/login', params, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      });

      localStorage.setItem('token', res.data.access_token);
      localStorage.setItem('user', JSON.stringify(res.data.user));
      router.push('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Authentication failed. Please check credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', padding: '24px' }}>
      {/* Header Branding */}
      <div style={{ textAlign: 'center', maxWidth: '800px', marginBottom: '40px' }}>
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '6px 14px', background: 'rgba(99,102,241,0.15)', border: '1px solid rgba(99,102,241,0.3)', borderRadius: '20px', marginBottom: '20px' }}>
          <Zap size={16} color="#6366f1" />
          <span style={{ fontSize: '13px', fontWeight: 600, color: '#818cf8' }}>Next-Gen Incremental SEO Engine</span>
        </div>
        
        <h1 style={{ fontSize: '48px', fontWeight: 700, lineHeight: 1.1, marginBottom: '16px', background: 'linear-gradient(135deg, #ffffff 0%, #94a3b8 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
          Autonomous SEO Monitoring & AI Fixes
        </h1>
        
        <p style={{ fontSize: '18px', color: 'var(--text-muted)', lineHeight: 1.5 }}>
          Don't crawl everything. Only process what changed. Instant SHA-256 diff detection, zero-cost deterministic rules, and AI recommendations.
        </p>
      </div>

      {/* Feature Highlights Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px', width: '100%', maxWidth: '850px', marginBottom: '40px' }}>
        <div className="glass-card" style={{ padding: '20px' }}>
          <Search color="#06b6d4" style={{ marginBottom: '12px' }} />
          <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '6px' }}>Incremental Crawls</h3>
          <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>SHA-256 hashing skips un-modified pages for ultra-fast scans.</p>
        </div>
        <div className="glass-card" style={{ padding: '20px' }}>
          <ShieldCheck color="#10b981" style={{ marginBottom: '12px' }} />
          <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '6px' }}>Rules Engine</h3>
          <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>Instant zero-cost detection for missing titles, meta, and H1 tags.</p>
        </div>
        <div className="glass-card" style={{ padding: '20px' }}>
          <Bot color="#6366f1" style={{ marginBottom: '12px' }} />
          <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '6px' }}>AI Fix Suggestions</h3>
          <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>Gemini & OpenAI powered fixes ready for one-click approval.</p>
        </div>
      </div>

      {/* Auth Card */}
      <div className="glass-card" style={{ width: '100%', maxWidth: '420px', padding: '32px' }}>
        <h2 style={{ fontSize: '22px', fontWeight: 600, marginBottom: '8px', textAlign: 'center' }}>
          {isRegister ? 'Create Your Account' : 'Welcome Back'}
        </h2>
        <p style={{ fontSize: '14px', color: 'var(--text-muted)', marginBottom: '24px', textAlign: 'center' }}>
          {isRegister ? 'Start monitoring your website in seconds' : 'Sign in to access your SEO dashboard'}
        </p>

        {error && (
          <div style={{ padding: '12px', background: 'rgba(244, 63, 94, 0.15)', border: '1px solid rgba(244, 63, 94, 0.3)', borderRadius: '8px', color: '#f43f5e', fontSize: '13px', marginBottom: '16px' }}>
            {error}
          </div>
        )}

        <div style={{ padding: '10px 14px', background: 'rgba(99, 102, 241, 0.1)', border: '1px solid rgba(99, 102, 241, 0.25)', borderRadius: '8px', marginBottom: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: '12px', color: '#818cf8' }}>🔑 Default Admin Pre-filled</span>
          <button
            type="button"
            onClick={() => { setEmail('admin@seo.com'); setPassword('admin@123'); }}
            style={{ background: 'none', border: 'none', color: '#a5b4fc', fontSize: '12px', cursor: 'pointer', textDecoration: 'underline' }}
          >
            Reset
          </button>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <label style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '6px', display: 'block' }}>Email Address</label>
            <input
              type="email"
              className="glass-input"
              placeholder="user@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div>
            <label style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '6px', display: 'block' }}>Password</label>
            <input
              type="password"
              className="glass-input"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <button type="submit" className="btn-primary" disabled={loading} style={{ justifyContent: 'center', marginTop: '8px' }}>
            {loading ? 'Processing...' : (isRegister ? 'Register Account' : 'Sign In')}
            <ArrowRight size={16} />
          </button>
        </form>

        <div style={{ textAlign: 'center', marginTop: '20px' }}>
          <button
            type="button"
            onClick={() => setIsRegister(!isRegister)}
            style={{ background: 'none', border: 'none', color: 'var(--text-muted)', fontSize: '13px', cursor: 'pointer' }}
          >
            {isRegister ? 'Already have an account? Sign In' : "Don't have an account? Register"}
          </button>
        </div>
      </div>
    </main>
  );
}
