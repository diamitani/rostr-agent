export type Phase =
  | "PreD"
  | "Design"
  | "Development"
  | "Deploy"
  | "Debugging";

export type Domain =
  | "code"
  | "design"
  | "research"
  | "ops"
  | "sales"
  | "content"
  | "deploy"
  | "debug";

export type NpaoCategory = "Necessity" | "Anxiety" | "Priority" | "Opportunity";

export type Urgency = "immediate" | "queued" | "scheduled";

export type SubAgent =
  | "product-architect"
  | "jtbd-npao-planner"
  | "experience-engineer"
  | "application-engineer"
  | "agent-runtime-engineer"
  | "identity-commerce-qa"
  | "quality-engineer"
  | "devops-release-engineer"
  | "security-reviewer";

export type BackendKind = "jev" | "gateway" | "openrouter" | "adapter" | "local";

export interface Distribution {
  probabilities: Record<string, number>;
  choice: string;
  confidence: number;
}

export interface NoulAnswer {
  noul: number;
  label: string;
}

export interface ScoreAnswer {
  score: string;
  value: number;
  probabilities: Record<string, number>;
  confidence: number;
}

export interface SystemOneAnswers {
  phase: Distribution;
  domain: Distribution;
  npao: Distribution;
  urgency: Distribution;
  agent: Distribution;
  ambiguity: ScoreAnswer;
  businessImpact: ScoreAnswer;
  dependencyImpact: ScoreAnswer;
  resourceEfficiency: ScoreAnswer;
  requiresApproval: NoulAnswer;
  productionRisk: NoulAnswer;
  needsResearch: NoulAnswer;
  mixedIntent: NoulAnswer;
}

export interface SystemOneResponse {
  backend: BackendKind;
  model: string;
  latencyMs: number;
  answers: SystemOneAnswers;
}

export interface PALStage {
  stageNumber: number;
  stageName: string;
  description: string;
  owner: "system-one" | "deterministic" | "system-two";
  latencyMs: number;
  metadata: Record<string, unknown>;
}

export interface PALCompilation {
  rawPrompt: string;
  intent: string;
  domain: Domain;
  phase: Phase;
  npaoCategory: NpaoCategory;
  urgency: Urgency;
  ambiguityScore: number;
  priorityScore: number;
  priorityBreakdown: {
    phaseWeight: number;
    dependencyWeight: number;
    businessWeight: number;
    resourceWeight: number;
    formula: string;
  };
  subAgents: SubAgent[];
  primaryAgent: SubAgent;
  allowedTools: string[];
  approvalGates: string[];
  episodicNamespace: string;
  stages: PALStage[];
  answers: SystemOneAnswers;
  backend: BackendKind;
  model: string;
  confidence: number;
  escalateToLlm: boolean;
  timestamp: string;
}

export const PHASE_SCORES: Record<Phase, number> = {
  Debugging: 10,
  Deploy: 8,
  Development: 6,
  Design: 4,
  PreD: 2,
};

export const PHASE_SUBAGENTS: Record<Phase, SubAgent[]> = {
  PreD: ["product-architect", "jtbd-npao-planner"],
  Design: ["product-architect", "experience-engineer", "agent-runtime-engineer"],
  Development: ["application-engineer", "agent-runtime-engineer", "quality-engineer"],
  Deploy: ["devops-release-engineer", "identity-commerce-qa", "quality-engineer"],
  Debugging: ["application-engineer", "security-reviewer", "quality-engineer"],
};

export const NPAO_ORDER: NpaoCategory[] = [
  "Necessity",
  "Anxiety",
  "Priority",
  "Opportunity",
];
