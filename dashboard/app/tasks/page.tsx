'use client';
import { useEffect, useState } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001';

interface Task {
  id: string; title: string; description: string;
  npao_category: string; phase: string; priority_score: number;
  status: string; created_at: string;
}

const NPAO_ORDER = ['necessity', 'anxiety', 'priority', 'opportunity'];
const NPAO_META: Record<string, { label: string; signal: string; cls: string }> = {
  necessity: { label: 'N', signal: 'I MUST...', cls: 'npao-necessity' },
  anxiety: { label: 'A', signal: "Won't have peace...", cls: 'npao-anxiety' },
  priority: { label: 'P', signal: 'I NEED to...', cls: 'npao-priority' },
  opportunity: { label: 'O', signal: 'I CAN...', cls: 'npao-opportunity' },
};

export default function TasksPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [newTitle, setNewTitle] = useState('');
  const [adding, setAdding] = useState(false);

  const load = () => fetch(`${API}/api/tasks`).then(r => r.json()).then(setTasks).catch(() => {});

  useEffect(() => { load(); }, []);

  const addTask = async () => {
    if (!newTitle.trim()) return;
    setAdding(true);
    await fetch(`${API}/api/tasks`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: newTitle }),
    });
    setNewTitle('');
    setAdding(false);
    load();
  };

  const toggleDone = async (id: string, currentStatus: string) => {
    await fetch(`${API}/api/tasks/${id}`, {
      method: 'PATCH', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: currentStatus === 'done' ? 'open' : 'done' }),
    });
    load();
  };

  const grouped = NPAO_ORDER.reduce((acc, cat) => {
    acc[cat] = tasks.filter(t => t.npao_category === cat);
    return acc;
  }, {} as Record<string, Task[]>);

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">📋 Tasks</h1>
        <p className="page-subtitle">NPAO execution order: Necessity → Anxiety → Priority → Opportunity</p>
      </div>

      <div style={{ display: 'flex', gap: 12, marginBottom: 24 }}>
        <input className="chat-input" value={newTitle} onChange={e => setNewTitle(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && addTask()} placeholder="Add a task (auto-classified with NPAO)..." />
        <button className="btn btn-gold" onClick={addTask} disabled={adding}>{adding ? '...' : 'Add'}</button>
      </div>

      <div className="grid-4" style={{ gridTemplateColumns: 'repeat(4, 1fr)' }}>
        {NPAO_ORDER.map(cat => {
          const meta = NPAO_META[cat];
          return (
            <div key={cat} className="card" style={{ minHeight: 200 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
                <span className={`npao-badge ${meta.cls}`} style={{ fontSize: 14, fontWeight: 800 }}>{meta.label}</span>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600 }}>{cat.charAt(0).toUpperCase() + cat.slice(1)}</div>
                  <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>{meta.signal}</div>
                </div>
              </div>
              {grouped[cat]?.length === 0 ? (
                <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>No tasks</p>
              ) : grouped[cat]?.map(task => (
                <div key={task.id} style={{
                  padding: '10px 12px', marginBottom: 8, borderRadius: 8,
                  background: 'var(--surface-2)', border: '1px solid var(--border)',
                  cursor: 'pointer', opacity: task.status === 'done' ? 0.5 : 1,
                }} onClick={() => toggleDone(task.id, task.status)}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ fontSize: 14 }}>{task.status === 'done' ? '✅' : '○'}</span>
                    <span style={{ fontSize: 13, fontWeight: 500, textDecoration: task.status === 'done' ? 'line-through' : 'none' }}>{task.title}</span>
                  </div>
                  <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 4, fontFamily: 'var(--font-mono)' }}>
                    {task.phase} • score: {task.priority_score}
                  </div>
                </div>
              ))}
            </div>
          );
        })}
      </div>
    </div>
  );
}
