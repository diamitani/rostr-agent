// ============================================================
// ROSTR Agent Framework — Hybrid Search Engine
// Vector + Keyword + RRF Fusion (inspired by gBrain)
// ============================================================

import { getBrainEngine } from './engine.js';
import { getEmbedder } from './embeddings.js';

export interface SearchResult {
  slug: string;
  title: string;
  type: string;
  snippet: string;
  score: number;
  method: 'vector' | 'keyword' | 'hybrid';
}

export async function hybridSearch(query: string, limit = 10): Promise<SearchResult[]> {
  const [vectorResults, keywordResults] = await Promise.all([
    vectorSearch(query, limit * 2),
    keywordSearch(query, limit * 2),
  ]);

  // RRF fusion: score = sum(1 / (60 + rank))
  const scores = new Map<string, { score: number; result: SearchResult }>();
  const k = 60;

  vectorResults.forEach((r, i) => {
    const rrf = 1 / (k + i);
    const existing = scores.get(r.slug);
    if (existing) {
      existing.score += rrf;
      existing.result.method = 'hybrid';
    } else {
      scores.set(r.slug, { score: rrf, result: { ...r, method: 'vector' } });
    }
  });

  keywordResults.forEach((r, i) => {
    const rrf = 1 / (k + i);
    const existing = scores.get(r.slug);
    if (existing) {
      existing.score += rrf;
      existing.result.method = 'hybrid';
    } else {
      scores.set(r.slug, { score: rrf, result: { ...r, method: 'keyword' } });
    }
  });

  // Compiled truth boost: pages with compiled_truth rank higher
  const engine = getBrainEngine();
  for (const [slug, entry] of scores) {
    const page = await engine.getPage(slug);
    if (page?.compiled_truth && page.compiled_truth.length > 50) {
      entry.score *= 1.15; // 15% boost for pages with compiled truth
    }
  }

  return Array.from(scores.values())
    .sort((a, b) => b.score - a.score)
    .slice(0, limit)
    .map(e => ({ ...e.result, score: parseFloat(e.score.toFixed(4)) }));
}

async function vectorSearch(query: string, limit: number): Promise<SearchResult[]> {
  try {
    const embedder = getEmbedder();
    const [queryVec] = await embedder.embed([query]);
    const vecStr = `[${queryVec.join(',')}]`;

    const db = getBrainEngine().getDb();
    const result = await db.query<{
      page_slug: string;
      chunk_text: string;
      distance: number;
      title: string;
      type: string;
    }>(
      `SELECT e.page_slug, e.chunk_text, 
              1 - (e.embedding <=> $1::vector) as distance,
              p.title, p.type
       FROM embeddings e
       JOIN pages p ON p.slug = e.page_slug
       ORDER BY e.embedding <=> $1::vector
       LIMIT $2`,
      [vecStr, limit]
    );

    // Deduplicate by page slug (keep best chunk)
    const seen = new Set<string>();
    return result.rows
      .filter(r => { if (seen.has(r.page_slug)) return false; seen.add(r.page_slug); return true; })
      .map(r => ({
        slug: r.page_slug,
        title: r.title,
        type: r.type,
        snippet: r.chunk_text.slice(0, 200),
        score: r.distance,
        method: 'vector' as const,
      }));
  } catch {
    return []; // No embeddings yet
  }
}

async function keywordSearch(query: string, limit: number): Promise<SearchResult[]> {
  const db = getBrainEngine().getDb();
  try {
    const result = await db.query<{
      slug: string;
      title: string;
      type: string;
      content: string;
      rank: number;
    }>(
      `SELECT slug, title, type, content,
              ts_rank(tsv, websearch_to_tsquery('english', $1)) as rank
       FROM pages
       WHERE tsv @@ websearch_to_tsquery('english', $1)
       ORDER BY rank DESC
       LIMIT $2`,
      [query, limit]
    );

    return result.rows.map(r => ({
      slug: r.slug,
      title: r.title,
      type: r.type,
      snippet: r.content.slice(0, 200),
      score: r.rank,
      method: 'keyword' as const,
    }));
  } catch {
    // Fallback to LIKE search
    const result = await db.query<{ slug: string; title: string; type: string; content: string }>(
      `SELECT slug, title, type, content FROM pages WHERE content ILIKE $1 OR title ILIKE $1 LIMIT $2`,
      [`%${query}%`, limit]
    );
    return result.rows.map(r => ({
      slug: r.slug, title: r.title, type: r.type,
      snippet: r.content.slice(0, 200), score: 0.5, method: 'keyword' as const,
    }));
  }
}

export { vectorSearch, keywordSearch };
