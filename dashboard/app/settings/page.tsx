'use client';
import { useEffect, useState } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001';

interface Settings {
  agent_name: string; agent_model: string; embedding_model: string;
  providers: Array<{ name: string; available: boolean }>;
}

export default function SettingsPage() {
  const [settings, setSettings] = useState<Settings | null>(null);

  useEffect(() => {
    fetch(`${API}/api/settings`).then(r => r.json()).then(setSettings).catch(() => {});
  }, []);

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">⚙️ Settings</h1>
        <p className="page-subtitle">Configure your ROSTR agent</p>
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-title">Agent Configuration</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div>
              <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)', display: 'block', marginBottom: 6 }}>Agent Name</label>
              <input className="chat-input" value={settings?.agent_name || 'ROSTR'} readOnly style={{ width: '100%' }} />
            </div>
            <div>
              <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)', display: 'block', marginBottom: 6 }}>Chat Model</label>
              <input className="chat-input" value={settings?.agent_model || 'gpt-4o-mini'} readOnly style={{ width: '100%' }} />
            </div>
            <div>
              <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)', display: 'block', marginBottom: 6 }}>Embedding Model</label>
              <input className="chat-input" value={settings?.embedding_model || 'text-embedding-3-small'} readOnly style={{ width: '100%' }} />
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-title">LLM Providers</div>
          <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 16 }}>
            BYOK (Bring Your Own Keys). Configure in <code>.env</code> file.
          </p>
          {settings?.providers.map(p => (
            <div key={p.name} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 0', borderBottom: '1px solid var(--border)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <span className={`status-dot ${p.available ? 'online' : 'offline'}`} />
                <span style={{ fontWeight: 500, textTransform: 'capitalize' }}>{p.name}</span>
              </div>
              <span style={{ fontSize: 12, color: p.available ? 'var(--success)' : 'var(--text-muted)' }}>
                {p.available ? 'Configured' : 'Not set'}
              </span>
            </div>
          ))}
        </div>

        <div className="card" style={{ gridColumn: '1 / -1' }}>
          <div className="card-title">Environment Variables</div>
          <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 12 }}>
            Edit the <code>.env</code> file in the project root to change these settings.
          </p>
          <pre style={{ background: 'var(--bg)', padding: 16, borderRadius: 8, fontSize: 12, color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)', lineHeight: 1.8 }}>
{`# LLM Providers (add at least one)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
DEEPSEEK_API_KEY=...
GROQ_API_KEY=gsk_...

# Agent
AGENT_NAME=${settings?.agent_name || 'ROSTR'}
AGENT_MODEL=${settings?.agent_model || 'gpt-4o-mini'}
EMBEDDING_MODEL=${settings?.embedding_model || 'text-embedding-3-small'}

# Server
GATEWAY_PORT=3001
DASHBOARD_PORT=3000`}
          </pre>
        </div>
      </div>
    </div>
  );
}
