'use client';
import { useEffect, useState } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001';

interface Status {
  agent: string; model: string; uptime: number;
  providers: Array<{ name: string; available: boolean }>;
  brain: { total_pages: number; total_embeddings: number; total_links: number; total_sessions: number; total_tasks: number };
}

interface Activity { action: string; details: Record<string, unknown>; created_at: string; }

export default function Home() {
  const [status, setStatus] = useState<Status | null>(null);
  const [activity, setActivity] = useState<Activity[]>([]);
  const [error, setError] = useState('');

  useEffect(() => {
    fetch(`${API}/api/status`).then(r => r.json()).then(setStatus).catch(() => setError('Cannot reach gateway. Run: npx tsx src/cli/index.ts serve'));
    fetch(`${API}/api/activity?limit=10`).then(r => r.json()).then(setActivity).catch(() => {});
  }, []);

  if (error) return (
    <div>
      <div className="page-header"><h1 className="page-title">ROSTR Dashboard</h1></div>
      <div className="card" style={{ borderColor: 'var(--danger)' }}>
        <p style={{ color: 'var(--danger)' }}>⚠️ {error}</p>
        <p style={{ color: 'var(--text-muted)', marginTop: 8 }}>Start the gateway: <code>npx tsx src/cli/index.ts serve</code></p>
      </div>
    </div>
  );

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Welcome to <span style={{ color: 'var(--gold)' }}>ROSTR</span></h1>
        <p className="page-subtitle">
          {status ? <><span className="status-dot online" />Agent online • {status.model} • {Math.floor(status.uptime)}s uptime</> : 'Loading...'}
        </p>
      </div>

      {status && (
        <>
          <div className="grid-4">
            <div className="card">
              <div className="card-title">Pages</div>
              <div className="card-value gold">{status.brain.total_pages}</div>
            </div>
            <div className="card">
              <div className="card-title">Embeddings</div>
              <div className="card-value">{status.brain.total_embeddings}</div>
            </div>
            <div className="card">
              <div className="card-title">Links</div>
              <div className="card-value">{status.brain.total_links}</div>
            </div>
            <div className="card">
              <div className="card-title">Sessions</div>
              <div className="card-value">{status.brain.total_sessions}</div>
            </div>
          </div>

          <div className="grid-2">
            <div className="card">
              <div className="card-title">LLM Providers</div>
              {status.providers.map(p => (
                <div key={p.name} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '6px 0' }}>
                  <span className={`status-dot ${p.available ? 'online' : 'offline'}`} />
                  <span style={{ color: p.available ? 'var(--text)' : 'var(--text-muted)' }}>{p.name}</span>
                </div>
              ))}
            </div>

            <div className="card">
              <div className="card-title">Quick Actions</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                <a href="/chat" className="btn btn-gold" style={{ textAlign: 'center' }}>💬 Chat with Agent</a>
                <a href="/brain" className="btn" style={{ textAlign: 'center' }}>🧠 Search Brain</a>
                <a href="/tasks" className="btn" style={{ textAlign: 'center' }}>📋 View Tasks</a>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card-title">Recent Activity</div>
            {activity.length === 0 ? (
              <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>No activity yet. Start chatting!</p>
            ) : (
              activity.map((a, i) => (
                <div key={i} className="activity-item">
                  <div className="activity-icon">
                    {a.action === 'chat' ? '💬' : a.action === 'task_created' ? '📋' : a.action === 'session_cached' ? '💾' : '⚡'}
                  </div>
                  <div className="activity-text">{a.action}{a.details && typeof a.details === 'object' && 'title' in a.details ? `: ${a.details.title}` : ''}</div>
                  <div className="activity-time">{new Date(a.created_at).toLocaleTimeString()}</div>
                </div>
              ))
            )}
          </div>
        </>
      )}
    </div>
  );
}
