/**
 * ROSTR / PAL compiler — compatibility facade over System One.
 *
 * Stages 1 and 3 (phase / NPAO) are typed probabilistic decisions from
 * `lib/jev`. The first-regex-wins classifier and hardcoded 5.5 / 6.5 / 7.0
 * weights live in `lib/jev/keyword.ts` only as a comparison baseline.
 */

import { compilePAL } from "../jev/pal";
import { PHASE_SCORES, PHASE_SUBAGENTS } from "../jev/types";
import type { Domain, Phase } from "../jev/types";

export type PhaseType = Phase;
export type DomainType = "code" | "design" | "research" | "ops" | "security";

export interface PALStageResult {
  stageNumber: number;
  stageName: string;
  description: string;
  latencyMs: number;
  metadata: Record<string, unknown>;
}

export interface PALCompilation {
  rawPrompt: string;
  intent: string;
  domain: DomainType;
  phase: PhaseType;
  priorityScore: number;
  priorityBreakdown: {
    phaseWeight: number;
    dependencyWeight: number;
    businessWeight: number;
    resourceWeight: number;
    formula: string;
  };
  subAgents: string[];
  allowedTools: string[];
  approvalGates: string[];
  episodicNamespace: string;
  stages: PALStageResult[];
  timestamp: string;
  npaoCategory?: string;
  confidence?: number;
  backend?: string;
  escalateToLlm?: boolean;
}

export interface NPAOWeights {
  dependencyScore?: number;
  businessScore?: number;
  resourceScore?: number;
}

function mapDomain(domain: Domain): DomainType {
  if (domain === "design" || domain === "content") return "design";
  if (domain === "research") return "research";
  if (domain === "code" || domain === "debug") return "code";
  return "ops";
}

export function detectPhase(prompt: string): { phase: PhaseType; domain: DomainType } {
  const compiled = compilePAL(prompt);
  return { phase: compiled.phase, domain: mapDomain(compiled.domain) };
}

export function calculateNPAOPriority(
  phase: PhaseType,
  weights: NPAOWeights = {},
): {
  score: number;
  breakdown: PALCompilation["priorityBreakdown"];
} {
  const phaseVal = PHASE_SCORES[phase] || 4.0;
  const depVal = weights.dependencyScore ?? 5.5;
  const bizVal = weights.businessScore ?? 6.5;
  const resVal = weights.resourceScore ?? 7.0;
  const score = phaseVal * 0.35 + depVal * 0.3 + bizVal * 0.25 + resVal * 0.1;

  return {
    score: Number(score.toFixed(2)),
    breakdown: {
      phaseWeight: Number((phaseVal * 0.35).toFixed(2)),
      dependencyWeight: Number((depVal * 0.3).toFixed(2)),
      businessWeight: Number((bizVal * 0.25).toFixed(2)),
      resourceWeight: Number((resVal * 0.1).toFixed(2)),
      formula: `(${phaseVal} × 0.35) + (${depVal} × 0.30) + (${bizVal} × 0.25) + (${resVal} × 0.10)`,
    },
  };
}

export function compilePALIntent(
  userPrompt: string,
  customWeights?: NPAOWeights,
): PALCompilation {
  const compiled = compilePAL(userPrompt);
  const scored = customWeights
    ? calculateNPAOPriority(compiled.phase, customWeights)
    : { score: compiled.priorityScore, breakdown: compiled.priorityBreakdown };

  return {
    rawPrompt: compiled.rawPrompt,
    intent: compiled.intent,
    domain: mapDomain(compiled.domain),
    phase: compiled.phase,
    priorityScore: scored.score,
    priorityBreakdown: scored.breakdown,
    subAgents: compiled.subAgents,
    allowedTools: compiled.allowedTools,
    approvalGates: compiled.approvalGates,
    episodicNamespace: compiled.episodicNamespace,
    stages: compiled.stages.map((stage) => ({
      stageNumber: stage.stageNumber,
      stageName: stage.stageName,
      description: stage.description,
      latencyMs: stage.latencyMs,
      metadata: { ...stage.metadata, owner: stage.owner },
    })),
    timestamp: compiled.timestamp,
    npaoCategory: compiled.npaoCategory,
    confidence: compiled.confidence,
    backend: compiled.backend,
    escalateToLlm: compiled.escalateToLlm,
  };
}

export { PHASE_SCORES, PHASE_SUBAGENTS };
