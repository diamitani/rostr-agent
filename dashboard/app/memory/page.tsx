'use client';
import { useEffect, useState } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001';

interface Session {
  session_id: string; summary: string; what_worked: string[];
  what_failed: string[]; next_steps: string[]; blockers: string[]; created_at: string;
}

export default function MemoryPage() {
  const [context, setContext] = useState<{ last_session: Session | null; recent: Session[]; recommended_start: string } | null>(null);
  const [report, setReport] = useState('');

  useEffect(() => {
    fetch(`${API}/api/context/flash`).then(r => r.json()).then(setContext).catch(() => {});
  }, []);

  const genReport = async () => {
    const res = await fetch(`${API}/api/context/report`);
    const data = await res.json();
    setReport(data.report);
  };

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">💾 Memory</h1>
        <p className="page-subtitle">ContextEngine — persistent session memory</p>
      </div>

      {context && (
        <div className="card" style={{ marginBottom: 24, borderLeft: '3px solid var(--gold)' }}>
          <div className="card-title">Context Flash</div>
          <p style={{ fontSize: 16, fontWeight: 600, color: 'var(--gold)', marginBottom: 8 }}>{context.recommended_start}</p>
          {context.last_session && (
            <p style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Last session: {context.last_session.session_id} — {context.last_session.summary}</p>
          )}
        </div>
      )}

      <div className="grid-2">
        <div>
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <div className="card-title" style={{ marginBottom: 0 }}>Sessions</div>
              <button className="btn" onClick={genReport}>Generate Report</button>
            </div>
            {!context?.recent?.length ? (
              <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>No sessions yet. Use &quot;rostr context save&quot; to cache sessions.</p>
            ) : context.recent.map(s => (
              <div key={s.session_id} style={{ padding: '12px 0', borderBottom: '1px solid var(--border)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ fontWeight: 600, fontSize: 14, fontFamily: 'var(--font-mono)' }}>{s.session_id}</span>
                  <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{new Date(s.created_at).toLocaleDateString()}</span>
                </div>
                <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 4 }}>{s.summary}</p>
                {s.blockers?.length > 0 && <p style={{ fontSize: 12, color: 'var(--danger)', marginTop: 4 }}>⚠️ Blocker: {s.blockers[0]}</p>}
                {s.next_steps?.length > 0 && <p style={{ fontSize: 12, color: 'var(--success)', marginTop: 4 }}>→ Next: {s.next_steps[0]}</p>}
              </div>
            ))}
          </div>
        </div>

        <div className="card">
          <div className="card-title">Progress Report</div>
          {report ? (
            <pre style={{ fontSize: 13, color: 'var(--text-secondary)', whiteSpace: 'pre-wrap', lineHeight: 1.7, fontFamily: 'var(--font-sans)' }}>{report}</pre>
          ) : (
            <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>Click &quot;Generate Report&quot; to create a progress summary.</p>
          )}
        </div>
      </div>
    </div>
  );
}
