'use client';
import { useState, useRef, useEffect } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001';

interface Message { role: 'user' | 'assistant'; content: string; model?: string; sources?: Array<{ slug: string; title: string }>; }

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  const send = async () => {
    if (!input.trim() || loading) return;
    const userMsg: Message = { role: 'user', content: input };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const res = await fetch(`${API}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: input, history: messages.slice(-10) }),
      });
      const data = await res.json();
      setMessages(prev => [...prev, { role: 'assistant', content: data.message, model: data.model, sources: data.sources }]);
    } catch {
      setMessages(prev => [...prev, { role: 'assistant', content: '⚠️ Failed to reach gateway.' }]);
    }
    setLoading(false);
  };

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">💬 Chat</h1>
        <p className="page-subtitle">Talk to your ROSTR agent</p>
      </div>

      <div className="chat-container">
        <div className="chat-messages">
          {messages.length === 0 && (
            <div style={{ textAlign: 'center', padding: '60px 0', color: 'var(--text-muted)' }}>
              <p style={{ fontSize: 40, marginBottom: 16 }}>🤖</p>
              <p>Start a conversation with your ROSTR agent.</p>
              <p style={{ fontSize: 13, marginTop: 8 }}>Try: &quot;What can you do?&quot; or &quot;Search my brain for...&quot;</p>
            </div>
          )}
          {messages.map((msg, i) => (
            <div key={i} className={`message message-${msg.role}`}>
              <div className="message-bubble">
                {msg.content.split('\n').map((line, j) => <p key={j} style={{ margin: '4px 0', color: 'var(--text-secondary)' }}>{line}</p>)}
              </div>
              {msg.model && <div className="message-meta">{msg.model}{msg.sources?.length ? ` • Sources: ${msg.sources.map(s => s.title).join(', ')}` : ''}</div>}
            </div>
          ))}
          {loading && <div className="message message-assistant"><div className="message-bubble" style={{ color: 'var(--gold)' }}>Thinking...</div></div>}
          <div ref={endRef} />
        </div>

        <div className="chat-input-bar">
          <input
            className="chat-input"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && send()}
            placeholder="Type a message..."
            disabled={loading}
          />
          <button className="chat-send" onClick={send} disabled={loading}>Send</button>
        </div>
      </div>
    </div>
  );
}
