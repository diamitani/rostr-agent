// ============================================================
// ROSTR — ContextEngine (Persistent Session Memory)
// 5 modes: CACHE, RETRIEVE, REPORT, QUERY, SCHEDULE
// ============================================================

import { getBrainEngine } from '../core/engine.js';

export interface SessionRecord {
  session_id: string;
  project: string;
  summary: string;
  duration_estimate: string;
  tools_used: string[];
  files_created: string[];
  files_modified: string[];
  skills_invoked: string[];
  what_worked: string[];
  what_failed: string[];
  decisions_made: string[];
  open_questions: string[];
  next_steps: string[];
  blockers: string[];
  tags: string[];
  created_at: Date;
}

function sessionId(): string {
  const now = new Date();
  return now.toISOString().replace(/[-:T]/g, '').slice(0, 15);
}

// ── CACHE — Save Session ────────────────────────────────

export async function cacheSession(record: Partial<SessionRecord>): Promise<SessionRecord> {
  const engine = getBrainEngine();
  const db = engine.getDb();

  const id = record.session_id || sessionId();
  const result = await db.query<SessionRecord>(
    `INSERT INTO sessions (session_id, project, summary, duration_estimate, tools_used, files_created, files_modified, skills_invoked, what_worked, what_failed, decisions_made, open_questions, next_steps, blockers, tags)
     VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15)
     RETURNING *`,
    [
      id,
      record.project || process.cwd().split('/').pop() || 'default',
      record.summary || '',
      record.duration_estimate || 'medium',
      record.tools_used || [],
      record.files_created || [],
      record.files_modified || [],
      record.skills_invoked || [],
      record.what_worked || [],
      record.what_failed || [],
      record.decisions_made || [],
      record.open_questions || [],
      record.next_steps || [],
      record.blockers || [],
      record.tags || [],
    ]
  );

  await engine.logActivity('session_cached', { session_id: id });
  return result.rows[0];
}

// ── RETRIEVE — Context Flash ────────────────────────────

export async function retrieveContext(count = 5): Promise<{
  last_session: SessionRecord | null;
  recent: SessionRecord[];
  recommended_start: string;
}> {
  const db = getBrainEngine().getDb();
  const result = await db.query<SessionRecord>(
    `SELECT * FROM sessions ORDER BY created_at DESC LIMIT $1`,
    [count]
  );

  const last = result.rows[0] || null;
  let recommended = 'No previous sessions found. Start fresh!';

  if (last) {
    if (last.blockers.length > 0) {
      recommended = `Resume by addressing blocker: ${last.blockers[0]}`;
    } else if (last.next_steps.length > 0) {
      recommended = `Continue with: ${last.next_steps[0]}`;
    } else {
      recommended = `Last session: ${last.summary}`;
    }
  }

  return { last_session: last, recent: result.rows, recommended_start: recommended };
}

// ── REPORT — Progress Report ────────────────────────────

export async function generateReport(opts?: { since?: string; tags?: string[] }): Promise<string> {
  const db = getBrainEngine().getDb();
  let query = `SELECT * FROM sessions WHERE 1=1`;
  const params: unknown[] = [];
  let idx = 1;

  if (opts?.since) {
    query += ` AND created_at >= $${idx++}`;
    params.push(opts.since);
  }

  query += ` ORDER BY created_at DESC`;
  const result = await db.query<SessionRecord>(query, params);
  const sessions = result.rows;

  if (sessions.length === 0) return '# Progress Report\n\nNo sessions found for the specified period.';

  const allWorked = sessions.flatMap(s => s.what_worked);
  const allFailed = sessions.flatMap(s => s.what_failed);
  const allDecisions = sessions.flatMap(s => s.decisions_made);
  const allBlockers = sessions.flatMap(s => s.blockers);
  const allNextSteps = sessions.flatMap(s => s.next_steps);

  const report = [
    `# Progress Report`,
    `*Generated: ${new Date().toISOString()}*`,
    `*Sessions covered: ${sessions.length}*`,
    '',
    '## Executive Summary',
    sessions[0]?.summary || 'No summary available.',
    '',
    '## What Worked',
    ...allWorked.map(w => `- ${w}`),
    '',
    '## What Failed',
    ...allFailed.map(f => `- ${f}`),
    '',
    '## Key Decisions',
    ...allDecisions.map(d => `- ${d}`),
    '',
    '## Active Blockers',
    allBlockers.length ? allBlockers.map(b => `- ⚠️ ${b}`).join('\n') : '- None',
    '',
    '## Next Steps',
    ...allNextSteps.map((n, i) => `${i + 1}. ${n}`),
    '',
    '## Session Timeline',
    ...sessions.map(s => `- **${s.session_id}** — ${s.summary}`),
  ];

  return report.join('\n');
}

// ── QUERY — Search History ──────────────────────────────

export async function queryHistory(search: string): Promise<SessionRecord[]> {
  const db = getBrainEngine().getDb();
  const result = await db.query<SessionRecord>(
    `SELECT * FROM sessions
     WHERE summary ILIKE $1
        OR $1 = ANY(tags)
        OR EXISTS (SELECT 1 FROM unnest(what_worked) w WHERE w ILIKE $1)
        OR EXISTS (SELECT 1 FROM unnest(what_failed) f WHERE f ILIKE $1)
        OR EXISTS (SELECT 1 FROM unnest(decisions_made) d WHERE d ILIKE $1)
     ORDER BY created_at DESC
     LIMIT 20`,
    [`%${search}%`]
  );
  return result.rows;
}

export async function getSessionCount(): Promise<number> {
  const db = getBrainEngine().getDb();
  const result = await db.query<{ count: string }>('SELECT COUNT(*) as count FROM sessions');
  return parseInt(result.rows[0]?.count || '0', 10);
}
