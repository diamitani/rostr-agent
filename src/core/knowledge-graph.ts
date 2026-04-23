// ============================================================
// ROSTR — Knowledge Graph (auto-linking, zero LLM calls)
// ============================================================

import { getBrainEngine } from './engine.js';

const LINK_PATTERNS: Array<{ type: string; patterns: RegExp[] }> = [
  { type: 'works_at', patterns: [/(?:works?\s+at|employed\s+(?:at|by)|(?:CEO|CTO|VP|Director|Manager|Engineer)\s+(?:at|of))\s+([A-Z][\w\s]+)/gi] },
  { type: 'founded', patterns: [/(?:founded|co-?founded|started|created)\s+([A-Z][\w\s]+)/gi] },
  { type: 'invested_in', patterns: [/(?:invested\s+in|backed|funded)\s+([A-Z][\w\s]+)/gi] },
  { type: 'advises', patterns: [/(?:advises?|advisor\s+(?:to|at|for))\s+([A-Z][\w\s]+)/gi] },
  { type: 'attended', patterns: [/(?:attended|present\s+at|joined)\s+([A-Z][\w\s]+)/gi] },
];

export interface Link {
  source_slug: string;
  target_slug: string;
  link_type: string;
  context: string;
}

function slugify(text: string): string {
  return text.toLowerCase().trim().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
}

// Extract wiki-style links: [[slug]] or [[slug|display]]
function extractWikiLinks(content: string): Array<{ slug: string; context: string }> {
  const links: Array<{ slug: string; context: string }> = [];
  const re = /\[\[([^\]|]+)(?:\|[^\]]+)?\]\]/g;
  let match;
  while ((match = re.exec(content)) !== null) {
    links.push({ slug: slugify(match[1]), context: match[0] });
  }
  return links;
}

// Extract typed relationship links from content patterns
function extractTypedLinks(content: string, sourceSlug: string): Link[] {
  const links: Link[] = [];
  for (const { type, patterns } of LINK_PATTERNS) {
    for (const pattern of patterns) {
      let match;
      const re = new RegExp(pattern.source, pattern.flags);
      while ((match = re.exec(content)) !== null) {
        const target = match[1]?.trim();
        if (target && target.length > 2 && target.length < 60) {
          links.push({
            source_slug: sourceSlug,
            target_slug: slugify(target),
            link_type: type,
            context: match[0].trim().slice(0, 200),
          });
        }
      }
    }
  }
  return links;
}

export async function extractAndSaveLinks(slug: string): Promise<number> {
  const engine = getBrainEngine();
  const db = engine.getDb();
  const page = await engine.getPage(slug);
  if (!page) return 0;

  // Remove old links from this source
  await db.query('DELETE FROM links WHERE source_slug = $1', [slug]);

  const allLinks: Link[] = [];

  // Wiki-style links
  for (const wl of extractWikiLinks(page.content)) {
    allLinks.push({ source_slug: slug, target_slug: wl.slug, link_type: 'mentions', context: wl.context });
  }

  // Typed relationship links
  allLinks.push(...extractTypedLinks(page.content, slug));

  // Deduplicate by (source, target, type)
  const seen = new Set<string>();
  const unique = allLinks.filter(l => {
    const key = `${l.source_slug}|${l.target_slug}|${l.link_type}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return l.source_slug !== l.target_slug; // no self-links
  });

  // Insert links
  for (const link of unique) {
    await db.query(
      `INSERT INTO links (source_slug, target_slug, link_type, context)
       VALUES ($1, $2, $3, $4)
       ON CONFLICT (source_slug, target_slug, link_type) DO UPDATE SET context = $4`,
      [link.source_slug, link.target_slug, link.link_type, link.context]
    );
  }

  return unique.length;
}

export async function getBacklinks(slug: string): Promise<Link[]> {
  const db = getBrainEngine().getDb();
  const result = await db.query<Link>(
    `SELECT source_slug, target_slug, link_type, context FROM links WHERE target_slug = $1`,
    [slug]
  );
  return result.rows;
}

export async function getOutlinks(slug: string): Promise<Link[]> {
  const db = getBrainEngine().getDb();
  const result = await db.query<Link>(
    `SELECT source_slug, target_slug, link_type, context FROM links WHERE source_slug = $1`,
    [slug]
  );
  return result.rows;
}

export async function graphTraversal(slug: string, opts?: { type?: string; depth?: number; direction?: 'in' | 'out' | 'both' }): Promise<Link[]> {
  const db = getBrainEngine().getDb();
  const depth = Math.min(opts?.depth || 2, 5);
  const direction = opts?.direction || 'both';

  let dirClause = '(source_slug = $1 OR target_slug = $1)';
  if (direction === 'out') dirClause = 'source_slug = $1';
  if (direction === 'in') dirClause = 'target_slug = $1';

  let query = `SELECT source_slug, target_slug, link_type, context FROM links WHERE ${dirClause}`;
  const params: unknown[] = [slug];

  if (opts?.type) {
    query += ` AND link_type = $2`;
    params.push(opts.type);
  }

  // For depth > 1, do iterative expansion (simplified)
  const allLinks: Link[] = [];
  const visited = new Set<string>([slug]);
  let frontier = [slug];

  for (let d = 0; d < depth && frontier.length > 0; d++) {
    const nextFrontier: string[] = [];
    for (const node of frontier) {
      params[0] = node;
      const result = await db.query<Link>(query, params);
      for (const link of result.rows) {
        allLinks.push(link);
        const neighbor = link.source_slug === node ? link.target_slug : link.source_slug;
        if (!visited.has(neighbor)) {
          visited.add(neighbor);
          nextFrontier.push(neighbor);
        }
      }
    }
    frontier = nextFrontier;
  }

  return allLinks;
}
