// ============================================================
// ROSTR — NPAO Task Classification Engine
// Necessity → Anxiety → Priority → Opportunity
// Created by Patrick Diamitani
// ============================================================

import { getBrainEngine } from '../core/engine.js';
import { v4 as uuid } from 'uuid';

export type NPAOCategory = 'necessity' | 'priority' | 'anxiety' | 'opportunity';
export type Phase = 'pre_d' | 'design' | 'development' | 'deployment' | 'debugging';
export type TaskStatus = 'open' | 'in_progress' | 'blocked' | 'done' | 'cancelled';

export interface Task {
  id: string;
  title: string;
  description: string;
  npao_category: NPAOCategory;
  phase: Phase;
  urgency_score: number;
  dependency_score: number;
  business_score: number;
  resource_score: number;
  priority_score: number;
  status: TaskStatus;
  dependencies: string[];
  assigned_agent: string;
  tags: string[];
  metadata: Record<string, unknown>;
  created_at: Date;
  updated_at: Date;
  completed_at: Date | null;
}

// NPAO keyword signals for classification
const NPAO_SIGNALS: Record<NPAOCategory, string[]> = {
  necessity: ['must', 'broken', 'down', 'critical', 'blocker', 'crash', 'urgent', 'emergency', 'fix immediately', 'blocking', 'cannot', 'impossible', 'deadline today'],
  anxiety: ['worried', 'anxious', 'uneasy', 'peace', 'nagging', 'bothering', 'can\'t stop thinking', 'stress', 'concerned', 'friction', 'annoying', 'messy', 'disorganized'],
  priority: ['need', 'important', 'should', 'mission-critical', 'key', 'core', 'essential', 'required', 'roadmap', 'milestone', 'deliver', 'ship'],
  opportunity: ['could', 'might', 'nice to have', 'explore', 'experiment', 'idea', 'growth', 'potential', 'optimization', 'improvement', 'bonus', 'stretch'],
};

// Phase detection keywords
const PHASE_SIGNALS: Record<Phase, string[]> = {
  pre_d: ['research', 'investigate', 'evaluate', 'assess', 'explore', 'plan', 'feasibility', 'worth building'],
  design: ['design', 'architect', 'wireframe', 'spec', 'prototype', 'blueprint', 'schema', 'structure'],
  development: ['build', 'implement', 'code', 'develop', 'create', 'integrate', 'write', 'add feature'],
  deployment: ['deploy', 'ship', 'release', 'launch', 'publish', 'push to production', 'go live'],
  debugging: ['fix', 'bug', 'error', 'broken', 'crash', 'debug', 'investigate', 'failing', 'not working'],
};

export function classifyNPAO(text: string): NPAOCategory {
  const lower = text.toLowerCase();
  const scores: Record<NPAOCategory, number> = { necessity: 0, anxiety: 0, priority: 0, opportunity: 0 };

  for (const [category, keywords] of Object.entries(NPAO_SIGNALS)) {
    for (const kw of keywords) {
      if (lower.includes(kw)) scores[category as NPAOCategory] += 1;
    }
  }

  // Necessity wins ties — execution order is N → A → P → O
  const sorted = Object.entries(scores).sort((a, b) => b[1] - a[1]);
  if (sorted[0][1] === 0) return 'priority'; // default
  return sorted[0][0] as NPAOCategory;
}

export function detectPhase(text: string): Phase {
  const lower = text.toLowerCase();
  const scores: Record<Phase, number> = { pre_d: 0, design: 0, development: 0, deployment: 0, debugging: 0 };

  for (const [phase, keywords] of Object.entries(PHASE_SIGNALS)) {
    for (const kw of keywords) {
      if (lower.includes(kw)) scores[phase as Phase] += 1;
    }
  }

  // Debugging always overrides
  if (scores.debugging > 0) return 'debugging';

  const sorted = Object.entries(scores).sort((a, b) => b[1] - a[1]);
  if (sorted[0][1] === 0) return 'development'; // default
  return sorted[0][0] as Phase;
}

export function calculatePriorityScore(urgency: number, dependencies: number, business: number, resource: number): number {
  // Score = (Urgency×0.35) + (Dependencies×0.30) + (Business×0.25) + (Resource×0.10)
  return parseFloat(((urgency * 0.35) + (dependencies * 0.30) + (business * 0.25) + (resource * 0.10)).toFixed(2));
}

const PHASE_URGENCY: Record<Phase, number> = {
  pre_d: 2, design: 4, development: 6, deployment: 8, debugging: 10,
};

export async function createTask(title: string, description = ''): Promise<Task> {
  const engine = getBrainEngine();
  const db = engine.getDb();

  const fullText = `${title} ${description}`;
  const category = classifyNPAO(fullText);
  const phase = detectPhase(fullText);
  const urgency = PHASE_URGENCY[phase] / 10;
  const priority = calculatePriorityScore(urgency, 0.5, 0.5, 0.5);

  const id = uuid().slice(0, 8);

  const result = await db.query<Task>(
    `INSERT INTO tasks (id, title, description, npao_category, phase, urgency_score, dependency_score, business_score, resource_score, priority_score)
     VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
     RETURNING *`,
    [id, title, description, category, phase, urgency, 0.5, 0.5, 0.5, priority]
  );

  await engine.logActivity('task_created', { id, title, category, phase, priority });
  return result.rows[0];
}

export async function listTasks(status?: TaskStatus): Promise<Task[]> {
  const db = getBrainEngine().getDb();
  let query = `SELECT * FROM tasks`;
  const params: unknown[] = [];

  if (status) {
    query += ` WHERE status = $1`;
    params.push(status);
  }

  // NPAO execution order: N → A → P → O, then by priority_score DESC
  query += ` ORDER BY
    CASE npao_category
      WHEN 'necessity' THEN 0
      WHEN 'anxiety' THEN 1
      WHEN 'priority' THEN 2
      WHEN 'opportunity' THEN 3
    END,
    priority_score DESC`;

  const result = await db.query<Task>(query, params);
  return result.rows;
}

export async function updateTask(id: string, updates: Partial<Task>): Promise<Task | null> {
  const db = getBrainEngine().getDb();
  const setClauses: string[] = [];
  const params: unknown[] = [];
  let idx = 1;

  for (const [key, value] of Object.entries(updates)) {
    if (['id', 'created_at'].includes(key)) continue;
    setClauses.push(`${key} = $${idx++}`);
    params.push(key === 'metadata' ? JSON.stringify(value) : value);
  }

  if (updates.status === 'done') {
    setClauses.push(`completed_at = NOW()`);
  }

  setClauses.push('updated_at = NOW()');
  params.push(id);

  const result = await db.query<Task>(
    `UPDATE tasks SET ${setClauses.join(', ')} WHERE id = $${idx} RETURNING *`,
    params
  );
  return result.rows[0] || null;
}

export const NPAO_LABELS: Record<NPAOCategory, { label: string; signal: string; color: string }> = {
  necessity: { label: 'Necessity', signal: 'I MUST...', color: '#D4AF37' },
  anxiety: { label: 'Anxiety', signal: "Won't have peace until...", color: '#f87171' },
  priority: { label: 'Priority', signal: 'I NEED to...', color: '#60a5fa' },
  opportunity: { label: 'Opportunity', signal: 'I CAN...', color: '#34d399' },
};
