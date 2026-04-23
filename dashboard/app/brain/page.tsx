'use client';
import { useState } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001';

interface SearchResult { slug: string; title: string; type: string; snippet: string; score: number; method: string; }
interface Page { slug: string; title: string; type: string; content: string; compiled_truth: string; tags: string[]; backlinks: Array<{ source_slug: string; link_type: string }>; }

export default function BrainPage() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [selected, setSelected] = useState<Page | null>(null);
  const [searching, setSearching] = useState(false);

  const search = async () => {
    if (!query.trim()) return;
    setSearching(true);
    const res = await fetch(`${API}/api/brain/search?q=${encodeURIComponent(query)}`);
    setResults(await res.json());
    setSearching(false);
    setSelected(null);
  };

  const selectPage = async (slug: string) => {
    const res = await fetch(`${API}/api/brain/page/${slug}`);
    if (res.ok) setSelected(await res.json());
  };

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">🧠 Brain</h1>
        <p className="page-subtitle">Search and browse your knowledge graph</p>
      </div>

      <div style={{ display: 'flex', gap: 12, marginBottom: 24 }}>
        <input className="search-bar" style={{ marginBottom: 0 }} value={query} onChange={e => setQuery(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && search()} placeholder="Search your brain..." />
        <button className="btn btn-gold" onClick={search} disabled={searching}>{searching ? '...' : 'Search'}</button>
      </div>

      <div className="grid-2">
        <div className="card" style={{ maxHeight: 'calc(100vh - 250px)', overflowY: 'auto' }}>
          <div className="card-title">Results {results.length > 0 && `(${results.length})`}</div>
          {results.length === 0 ? (
            <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>Search to find knowledge pages</p>
          ) : results.map(r => (
            <div key={r.slug} className="search-result" onClick={() => selectPage(r.slug)}>
              <div className="search-result-title">{r.title}</div>
              <div className="search-result-snippet">{r.snippet}</div>
              <div className="search-result-meta">{r.type} • {r.method} • score: {r.score}</div>
            </div>
          ))}
        </div>

        <div className="card" style={{ maxHeight: 'calc(100vh - 250px)', overflowY: 'auto' }}>
          <div className="card-title">Page Detail</div>
          {!selected ? (
            <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>Select a page to view details</p>
          ) : (
            <div>
              <h3 style={{ fontSize: 18, fontWeight: 700, marginBottom: 8 }}>{selected.title}</h3>
              <div style={{ display: 'flex', gap: 6, marginBottom: 12 }}>
                <span className="npao-badge npao-priority">{selected.type}</span>
                {selected.tags?.map(t => <span key={t} className="npao-badge npao-opportunity">{t}</span>)}
              </div>
              {selected.compiled_truth && (
                <div style={{ marginBottom: 16 }}>
                  <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--gold)', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 6 }}>Compiled Truth</div>
                  <div style={{ fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.7, whiteSpace: 'pre-wrap' }}>{selected.compiled_truth}</div>
                </div>
              )}
              <div style={{ fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.7, whiteSpace: 'pre-wrap' }}>{selected.content}</div>
              {selected.backlinks?.length > 0 && (
                <div style={{ marginTop: 16 }}>
                  <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', marginBottom: 6 }}>BACKLINKS</div>
                  {selected.backlinks.map((bl, i) => (
                    <div key={i} style={{ fontSize: 13, color: 'var(--text-secondary)', padding: '4px 0', cursor: 'pointer' }}
                      onClick={() => selectPage(bl.source_slug)}>
                      ← {bl.source_slug} ({bl.link_type})
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
