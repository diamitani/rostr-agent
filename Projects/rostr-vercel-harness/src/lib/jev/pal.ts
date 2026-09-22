import { evaluateSystemOne } from "./engine";
import { detectPhaseKeyword, keywordPriority } from "./keyword";
import type {
  Domain,
  NpaoCategory,
  PALCompilation,
  Phase,
  SubAgent,
  SystemOneResponse,
  Urgency,
} from "./types";
import { PHASE_SCORES, PHASE_SUBAGENTS } from "./types";

function asPhase(value: string): Phase {
  if (value in PHASE_SCORES) return value as Phase;
  return "PreD";
}

function asDomain(value: string): Domain {
  const allowed: Domain[] = [
    "code",
    "design",
    "research",
    "ops",
    "sales",
    "content",
    "deploy",
    "debug",
  ];
  return allowed.includes(value as Domain) ? (value as Domain) : "research";
}

export function compilePAL(
  userPrompt: string,
  response?: SystemOneResponse,
): PALCompilation {
  const evaluated = response ?? evaluateSystemOne(userPrompt);
  const { answers } = evaluated;
  const phase = asPhase(answers.phase.choice);
  const domain = asDomain(answers.domain.choice);
  const npaoCategory = answers.npao.choice as NpaoCategory;
  const urgency = answers.urgency.choice as Urgency;

  const phaseVal = PHASE_SCORES[phase];
  const depVal = answers.dependencyImpact.value;
  const bizVal = answers.businessImpact.value;
  const resVal = answers.resourceEfficiency.value;
  const score = Number((phaseVal * 0.35 + depVal * 0.3 + bizVal * 0.25 + resVal * 0.1).toFixed(2));

  const phaseAgents = PHASE_SUBAGENTS[phase];
  const primary = phaseAgents.includes(answers.agent.choice as SubAgent)
    ? (answers.agent.choice as SubAgent)
    : phaseAgents[0];
  const subAgents = [primary, ...phaseAgents.filter((a) => a !== primary)].slice(0, 3);

  const approvalGates: string[] = [];
  if (answers.requiresApproval.noul >= 0.55 || phase === "Deploy") {
    approvalGates.push("production_deploy");
  }
  if (answers.productionRisk.noul >= 0.55 || /(auth|secret|credential|jwt|stripe|payment|private key)/i.test(userPrompt)) {
    approvalGates.push("security_boundary_audit");
  }

  const allowedTools = ["file_read", "file_write", "memory_query", "sandbox_eval"];
  if (phase === "Deploy") allowedTools.push("cloud_cli", "vercel_deploy");
  if (phase === "Debugging") allowedTools.push("log_analyzer", "git_blame");
  if (answers.needsResearch.noul >= 0.5) allowedTools.push("rag_dal");

  const escalateToLlm = answers.phase.confidence < 0.38 || answers.ambiguity.value >= 0.65;

  const stages = [
    {
      stageNumber: 1,
      stageName: "Intent Decomposition",
      description: `System One classified phase [${phase}] domain [${domain}] NPAO [${npaoCategory}]`,
      owner: "system-one" as const,
      latencyMs: evaluated.latencyMs,
      metadata: {
        probabilities: answers.phase.probabilities,
        confidence: answers.phase.confidence,
      },
    },
    {
      stageNumber: 2,
      stageName: "Dependency Analysis",
      description: "Mapped workspace references, soul principles, and retrieval need",
      owner: "deterministic" as const,
      latencyMs: 0.4,
      metadata: {
        needsResearch: answers.needsResearch.noul,
        references: ["soul.md", "sub-agent-registry.yaml"],
      },
    },
    {
      stageNumber: 3,
      stageName: "Context Assembly",
      description: escalateToLlm
        ? "Ambiguous — escalate semantic enhancement to a System Two LLM"
        : "NPAO 4D scores assembled from calibrated System One answers",
      owner: escalateToLlm ? ("system-two" as const) : ("system-one" as const),
      latencyMs: 0.6,
      metadata: { priority: score, escalateToLlm },
    },
    {
      stageNumber: 4,
      stageName: "Sandboxed Verification",
      description: `Tool boundaries and ${approvalGates.length} approval gate(s)`,
      owner: "deterministic" as const,
      latencyMs: 0.3,
      metadata: { approvalGates, allowedTools },
    },
    {
      stageNumber: 5,
      stageName: "State Persistence",
      description: "Queue session trajectory in rostr_decisions",
      owner: "deterministic" as const,
      latencyMs: 0.2,
      metadata: { namespace: "rostr_decisions" },
    },
  ];

  return {
    rawPrompt: userPrompt,
    intent: userPrompt.trim(),
    domain,
    phase,
    npaoCategory,
    urgency,
    ambiguityScore: answers.ambiguity.value,
    priorityScore: score,
    priorityBreakdown: {
      phaseWeight: Number((phaseVal * 0.35).toFixed(2)),
      dependencyWeight: Number((depVal * 0.3).toFixed(2)),
      businessWeight: Number((bizVal * 0.25).toFixed(2)),
      resourceWeight: Number((resVal * 0.1).toFixed(2)),
      formula: `(${phaseVal} × 0.35) + (${depVal} × 0.30) + (${bizVal} × 0.25) + (${resVal} × 0.10)`,
    },
    subAgents,
    primaryAgent: primary,
    allowedTools,
    approvalGates,
    episodicNamespace: "rostr_decisions",
    stages,
    answers,
    backend: evaluated.backend,
    model: evaluated.model,
    confidence: answers.phase.confidence,
    escalateToLlm,
    timestamp: new Date().toISOString(),
  };
}

export function compileKeyword(userPrompt: string) {
  const { phase, domain } = detectPhaseKeyword(userPrompt);
  const { score, formula, fakeWeights } = keywordPriority(phase);
  return {
    phase,
    domain,
    priorityScore: score,
    formula,
    fakeWeights,
    subAgents: PHASE_SUBAGENTS[phase],
  };
}
