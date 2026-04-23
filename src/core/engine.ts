// ============================================================
// ROSTR Agent Framework — Brain Engine
// PGLite embedded PostgreSQL with zero infrastructure
// ============================================================

import { PGlite } from '@electric-sql/pglite';
import { vector } from '@electric-sql/pglite/vector';
import { readFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { mkdirSync, existsSync } from 'fs';

const __dirname = dirname(fileURLToPath(import.meta.url));

export interface Page {
  slug: string;
  title: string;
  type: string;
  content: string;
  compiled_truth: string;
  timeline: string;
  tags: string[];
  metadata: Record<string, unknown>;
  word_count: number;
  version: number;
  created_at: Date;
  updated_at: Date;
}

export interface BrainStats {
  total_pages: number;
  total_embeddings: number;
  total_links: number;
  total_sessions: number;
  total_tasks: number;
  page_types: Record<string, number>;
}

export class BrainEngine {
  private db: PGlite | null = null;
  private dataPath: string;

  constructor(dataPath?: string) {
    this.dataPath = dataPath || join(process.cwd(), '.rostr-data');
  }

  async init(): Promise<void> {
    if (this.db) return;

    // Ensure data directory exists
    if (!existsSync(this.dataPath)) {
      mkdirSync(this.dataPath, { recursive: true });
    }

    const dbPath = join(this.dataPath, 'brain.pglite');
    this.db = new PGlite(dbPath, { extensions: { vector } });

    // Enable vector extension
    try {
      await this.db.exec('CREATE EXTENSION IF NOT EXISTS vector;');
    } catch {
      // Extension may already be loaded via JS
    }

    // Apply schema as a single block
    const schemaPath = join(__dirname, 'schema.sql');
    const schema = readFileSync(schemaPath, 'utf-8');

    try {
      await this.db.exec(schema);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      if (!msg.includes('already exists') && !msg.includes('duplicate')) {
        // Try statement by statement as fallback
        const statements = schema
          .split(/;\s*$/m)
          .map(s => s.trim())
          .filter(s => s.length > 0 && !s.startsWith('--'));

        for (const stmt of statements) {
          try {
            await this.db.exec(stmt + ';');
          } catch (e: unknown) {
            const m = e instanceof Error ? e.message : String(e);
            if (!m.includes('already exists') && !m.includes('duplicate')) {
              // Silently skip non-critical schema errors
            }
          }
        }
      }
    }
  }

  getDb(): PGlite {
    if (!this.db) throw new Error('Brain not initialized. Run engine.init() first.');
    return this.db;
  }

  // ── Page Operations ─────────────────────────────────────

  async getPage(slug: string): Promise<Page | null> {
    const db = this.getDb();
    const result = await db.query<Page>(
      `SELECT * FROM pages WHERE slug = $1`,
      [slug]
    );
    return result.rows[0] || null;
  }

  async putPage(page: Partial<Page> & { slug: string; title: string }): Promise<Page> {
    const db = this.getDb();
    const existing = await this.getPage(page.slug);

    const content = page.content || '';
    const wordCount = content.split(/\s+/).filter(Boolean).length;

    // Parse compiled truth and timeline from content
    const parts = content.split(/^---$/m);
    const compiledTruth = parts.length > 1 ? parts[0].trim() : content;
    const timeline = parts.length > 2 ? parts.slice(1).join('---').trim() : '';

    if (existing) {
      // Update existing page
      const result = await db.query<Page>(
        `UPDATE pages SET
          title = $2,
          type = COALESCE($3, type),
          content = $4,
          compiled_truth = $5,
          timeline = $6,
          tags = COALESCE($7, tags),
          metadata = COALESCE($8, metadata),
          word_count = $9,
          version = version + 1,
          updated_at = NOW()
        WHERE slug = $1
        RETURNING *`,
        [
          page.slug,
          page.title,
          page.type || existing.type,
          content,
          compiledTruth,
          timeline,
          page.tags || existing.tags,
          JSON.stringify(page.metadata || existing.metadata),
          wordCount,
        ]
      );
      return result.rows[0];
    } else {
      // Insert new page
      const result = await db.query<Page>(
        `INSERT INTO pages (slug, title, type, content, compiled_truth, timeline, tags, metadata, word_count)
         VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
         RETURNING *`,
        [
          page.slug,
          page.title,
          page.type || 'note',
          content,
          compiledTruth,
          timeline,
          page.tags || [],
          JSON.stringify(page.metadata || {}),
          wordCount,
        ]
      );
      return result.rows[0];
    }
  }

  async deletePage(slug: string): Promise<boolean> {
    const db = this.getDb();
    const result = await db.query(
      `DELETE FROM pages WHERE slug = $1`,
      [slug]
    );
    return (result.affectedRows || 0) > 0;
  }

  async listPages(options?: {
    type?: string;
    tag?: string;
    limit?: number;
    offset?: number;
  }): Promise<Page[]> {
    const db = this.getDb();
    let query = 'SELECT * FROM pages WHERE 1=1';
    const params: unknown[] = [];
    let paramIdx = 1;

    if (options?.type) {
      query += ` AND type = $${paramIdx++}`;
      params.push(options.type);
    }

    if (options?.tag) {
      query += ` AND $${paramIdx++} = ANY(tags)`;
      params.push(options.tag);
    }

    query += ' ORDER BY updated_at DESC';

    if (options?.limit) {
      query += ` LIMIT $${paramIdx++}`;
      params.push(options.limit);
    }

    if (options?.offset) {
      query += ` OFFSET $${paramIdx++}`;
      params.push(options.offset);
    }

    const result = await db.query<Page>(query, params);
    return result.rows;
  }

  // ── Stats ───────────────────────────────────────────────

  async getStats(): Promise<BrainStats> {
    const db = this.getDb();

    const [pages, embeddings, links, sessions, tasks, types] = await Promise.all([
      db.query<{ count: string }>('SELECT COUNT(*) as count FROM pages'),
      db.query<{ count: string }>('SELECT COUNT(*) as count FROM embeddings'),
      db.query<{ count: string }>('SELECT COUNT(*) as count FROM links'),
      db.query<{ count: string }>('SELECT COUNT(*) as count FROM sessions'),
      db.query<{ count: string }>('SELECT COUNT(*) as count FROM tasks'),
      db.query<{ type: string; count: string }>(
        'SELECT type, COUNT(*) as count FROM pages GROUP BY type'
      ),
    ]);

    const pageTypes: Record<string, number> = {};
    for (const row of types.rows) {
      pageTypes[row.type] = parseInt(row.count, 10);
    }

    return {
      total_pages: parseInt(pages.rows[0]?.count || '0', 10),
      total_embeddings: parseInt(embeddings.rows[0]?.count || '0', 10),
      total_links: parseInt(links.rows[0]?.count || '0', 10),
      total_sessions: parseInt(sessions.rows[0]?.count || '0', 10),
      total_tasks: parseInt(tasks.rows[0]?.count || '0', 10),
      page_types: pageTypes,
    };
  }

  // ── Activity Log ────────────────────────────────────────

  async logActivity(action: string, details: Record<string, unknown> = {}): Promise<void> {
    const db = this.getDb();
    await db.query(
      `INSERT INTO activity_log (action, details) VALUES ($1, $2)`,
      [action, JSON.stringify(details)]
    );
  }

  async getRecentActivity(limit = 20): Promise<Array<{ action: string; details: Record<string, unknown>; created_at: Date }>> {
    const db = this.getDb();
    const result = await db.query<{ action: string; details: Record<string, unknown>; created_at: Date }>(
      `SELECT action, details, created_at FROM activity_log ORDER BY created_at DESC LIMIT $1`,
      [limit]
    );
    return result.rows;
  }

  // ── Config ──────────────────────────────────────────────

  async getConfig(key: string): Promise<unknown> {
    const db = this.getDb();
    const result = await db.query<{ value: unknown }>(
      `SELECT value FROM config WHERE key = $1`,
      [key]
    );
    return result.rows[0]?.value;
  }

  async setConfig(key: string, value: unknown): Promise<void> {
    const db = this.getDb();
    await db.query(
      `INSERT INTO config (key, value, updated_at) VALUES ($1, $2, NOW())
       ON CONFLICT (key) DO UPDATE SET value = $2, updated_at = NOW()`,
      [key, JSON.stringify(value)]
    );
  }

  async close(): Promise<void> {
    if (this.db) {
      await this.db.close();
      this.db = null;
    }
  }
}

// Singleton
let _engine: BrainEngine | null = null;

export function getBrainEngine(dataPath?: string): BrainEngine {
  if (!_engine) {
    _engine = new BrainEngine(dataPath);
  }
  return _engine;
}
