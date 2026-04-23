// ============================================================
// ROSTR — PAL (Prompt Abstraction Layer)
// 5-stage prompt compilation pipeline
// ============================================================

import { classifyNPAO, detectPhase, type NPAOCategory, type Phase } from './npao.js';
import { retrieveContext } from './context-engine.js';
import { hybridSearch } from '../core/search.js';

export interface TaskSpec {
  primary_intent: string;
  domain: string;
  constraints: string[];
  desired_output: string;
  success_criteria: string[];
  sub_tasks: string[];
  npao_category: NPAOCategory;
  phase: Phase;
  context_injected: string[];
  enhanced_prompt: string;
}

// Stage 1: Intent Extraction
function extractIntent(input: string): { intent: string; domain: string; constraints: string[]; output: string } {
  const lower = input.toLowerCase();
  const domains = ['engineering', 'design', 'research', 'business', 'marketing', 'sales', 'legal', 'operations'];
  const domain = domains.find(d => lower.includes(d)) || 'general';

  // Extract constraints (quoted text, numbers, deadlines)
  const constraints: string[] = [];
  const quoted = input.match(/"([^"]+)"/g);
  if (quoted) constraints.push(...quoted.map(q => q.replace(/"/g, '')));
  const deadlines = input.match(/(?:by|before|deadline|due)\s+([^,.]+)/gi);
  if (deadlines) constraints.push(...deadlines);

  return {
    intent: input.replace(/"[^"]+"/g, '').trim(),
    domain,
    constraints,
    output: lower.includes('report') ? 'report' : lower.includes('code') ? 'code' : lower.includes('design') ? 'design' : 'action',
  };
}

// Stage 2: Context Injection
async function injectContext(intent: string): Promise<string[]> {
  const contextItems: string[] = [];
  try {
    // Pull relevant prior context from ContextEngine
    const ctx = await retrieveContext(3);
    if (ctx.last_session) {
      if (ctx.last_session.what_failed.length > 0) {
        contextItems.push(`Previous failure: ${ctx.last_session.what_failed[0]}`);
      }
      if (ctx.last_session.decisions_made.length > 0) {
        contextItems.push(`Prior decision: ${ctx.last_session.decisions_made[0]}`);
      }
    }

    // Pull relevant brain knowledge
    const searchResults = await hybridSearch(intent, 3);
    for (const r of searchResults) {
      if (r.score > 0.01) {
        contextItems.push(`Brain: ${r.title} — ${r.snippet.slice(0, 100)}`);
      }
    }
  } catch {
    // Context injection is best-effort
  }
  return contextItems;
}

// Stage 3: Semantic Enhancement
function enhance(intent: string, constraints: string[]): { criteria: string[]; subTasks: string[] } {
  const criteria: string[] = [];
  const subTasks: string[] = [];

  // Add success criteria based on output type
  if (intent.toLowerCase().includes('build') || intent.toLowerCase().includes('create')) {
    criteria.push('Implementation compiles/runs without errors');
    criteria.push('All edge cases handled');
    subTasks.push('Define requirements', 'Implement core logic', 'Test edge cases', 'Document');
  } else if (intent.toLowerCase().includes('fix') || intent.toLowerCase().includes('debug')) {
    criteria.push('Root cause identified');
    criteria.push('Fix verified — original issue no longer reproduces');
    subTasks.push('Reproduce the issue', 'Identify root cause', 'Implement fix', 'Verify fix');
  } else if (intent.toLowerCase().includes('research') || intent.toLowerCase().includes('investigate')) {
    criteria.push('At least 2 credible sources confirm core claim');
    criteria.push('Gaps marked as UNCERTAIN');
    subTasks.push('Define research questions', 'Gather sources', 'Synthesize findings', 'Document conclusions');
  } else {
    criteria.push('Task completed as specified');
    subTasks.push('Understand requirements', 'Execute', 'Verify');
  }

  return { criteria, subTasks };
}

// Stage 4 & 5: Runtime Compilation + Output Routing
export async function compilePAL(userInput: string): Promise<TaskSpec> {
  // Stage 1: Intent Extraction
  const { intent, domain, constraints, output } = extractIntent(userInput);

  // Stage 2: Context Injection
  const contextItems = await injectContext(intent);

  // Stage 3: Semantic Enhancement
  const { criteria, subTasks } = enhance(intent, constraints);

  // Stage 4: Runtime Compilation (NPAO classification)
  const category = classifyNPAO(userInput);
  const phase = detectPhase(userInput);

  // Stage 5: Build enhanced prompt
  const contextBlock = contextItems.length > 0
    ? `\n\nRelevant context:\n${contextItems.map(c => `- ${c}`).join('\n')}`
    : '';

  const constraintBlock = constraints.length > 0
    ? `\n\nConstraints:\n${constraints.map(c => `- ${c}`).join('\n')}`
    : '';

  const enhanced = `${intent}${constraintBlock}${contextBlock}\n\nSuccess criteria:\n${criteria.map(c => `- ${c}`).join('\n')}`;

  return {
    primary_intent: intent,
    domain,
    constraints,
    desired_output: output,
    success_criteria: criteria,
    sub_tasks: subTasks,
    npao_category: category,
    phase,
    context_injected: contextItems,
    enhanced_prompt: enhanced,
  };
}
