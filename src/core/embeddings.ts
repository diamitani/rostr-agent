// ============================================================
// ROSTR Agent Framework — Embedding System
// ============================================================

import { getBrainEngine } from './engine.js';

interface EmbeddingProvider {
  embed(texts: string[]): Promise<number[][]>;
  dimension: number;
}

class OpenAIEmbedder implements EmbeddingProvider {
  dimension = 1536;
  private apiKey: string;
  private model: string;

  constructor(apiKey: string, model = 'text-embedding-3-small') {
    this.apiKey = apiKey;
    this.model = model;
  }

  async embed(texts: string[]): Promise<number[][]> {
    const res = await fetch('https://api.openai.com/v1/embeddings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${this.apiKey}` },
      body: JSON.stringify({ model: this.model, input: texts }),
    });
    if (!res.ok) throw new Error(`OpenAI embedding failed: ${res.statusText}`);
    const data = await res.json() as { data: Array<{ embedding: number[] }> };
    return data.data.map(d => d.embedding);
  }
}

class LocalEmbedder implements EmbeddingProvider {
  dimension = 1536;
  async embed(texts: string[]): Promise<number[][]> {
    return texts.map(text => {
      const vec = new Array(this.dimension).fill(0);
      const words = text.toLowerCase().split(/\s+/);
      for (let i = 0; i < words.length; i++) {
        let hash = 5381;
        for (const ch of words[i]) hash = ((hash << 5) + hash) + ch.charCodeAt(0);
        hash = Math.abs(hash & hash);
        for (let j = 0; j < 8; j++) vec[Math.abs((hash + j * 7919) % this.dimension)] += 1 / Math.sqrt(words.length);
      }
      const norm = Math.sqrt(vec.reduce((s: number, v: number) => s + v * v, 0));
      if (norm > 0) for (let i = 0; i < vec.length; i++) vec[i] /= norm;
      return vec;
    });
  }
}

function getEmbedder(): EmbeddingProvider {
  const key = process.env.OPENAI_API_KEY;
  if (key && key !== 'sk-...') return new OpenAIEmbedder(key, process.env.EMBEDDING_MODEL || 'text-embedding-3-small');
  return new LocalEmbedder();
}

export function chunkText(text: string, max = 500): string[] {
  if (!text) return [];
  const chunks: string[] = [];
  const sections = text.split(/\n#{1,3}\s/);
  for (const sec of sections) {
    if (sec.length <= max) { if (sec.trim().length > 20) chunks.push(sec.trim()); }
    else {
      let cur = '';
      for (const p of sec.split(/\n\n+/)) {
        if ((cur + '\n\n' + p).length > max && cur) { chunks.push(cur.trim()); cur = p; }
        else cur = cur ? cur + '\n\n' + p : p;
      }
      if (cur.trim().length > 20) chunks.push(cur.trim());
    }
  }
  return chunks.length > 0 ? chunks : [text.slice(0, max)];
}

export async function embedPage(slug: string): Promise<number> {
  const engine = getBrainEngine();
  const db = engine.getDb();
  const page = await engine.getPage(slug);
  if (!page) throw new Error(`Page not found: ${slug}`);
  await db.query('DELETE FROM embeddings WHERE page_slug = $1', [slug]);
  const chunks = chunkText(`${page.title}\n\n${page.compiled_truth || page.content}`);
  if (!chunks.length) return 0;
  const vecs = await getEmbedder().embed(chunks);
  for (let i = 0; i < chunks.length; i++) {
    await db.query(
      `INSERT INTO embeddings (page_slug, chunk_index, chunk_text, embedding) VALUES ($1,$2,$3,$4::vector)`,
      [slug, i, chunks[i], `[${vecs[i].join(',')}]`]
    );
  }
  return chunks.length;
}

export async function embedAllStale(): Promise<{ embedded: number; chunks: number }> {
  const engine = getBrainEngine();
  const result = await engine.getDb().query<{ slug: string }>(
    `SELECT p.slug FROM pages p LEFT JOIN embeddings e ON p.slug = e.page_slug WHERE e.id IS NULL OR p.updated_at > e.created_at GROUP BY p.slug`
  );
  let total = 0;
  for (const r of result.rows) total += await embedPage(r.slug);
  return { embedded: result.rows.length, chunks: total };
}

export { getEmbedder, type EmbeddingProvider };
