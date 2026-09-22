import type {
  BackendKind,
  Distribution,
  Domain,
  NoulAnswer,
  NpaoCategory,
  Phase,
  ScoreAnswer,
  SubAgent,
  SystemOneAnswers,
  SystemOneResponse,
  Urgency,
} from "./types";
import { PHASE_SUBAGENTS } from "./types";

type Evidence = { pattern: RegExp; weight: number };

function clamp01(n: number) {
  return Math.max(0, Math.min(1, n));
}

function softmax(weights: Record<string, number>, temperature = 0.72): Record<string, number> {
  const keys = Object.keys(weights);
  const max = Math.max(...keys.map((k) => weights[k] ?? 0), 0);
  const exps = keys.map((k) => Math.exp(((weights[k] ?? 0) - max) / temperature));
  const sum = exps.reduce((a, b) => a + b, 0) || 1;
  const out: Record<string, number> = {};
  keys.forEach((k, i) => {
    out[k] = exps[i] / sum;
  });
  return out;
}

function hitScore(text: string, evidence: Evidence[]): number {
  let score = 0.08;
  for (const { pattern, weight } of evidence) {
    const matches = text.match(pattern);
    if (matches) score += weight * Math.min(matches.length, 3);
  }
  return score;
}

function distribution(weights: Record<string, number>): Distribution {
  const probabilities = softmax(weights);
  const ranked = Object.entries(probabilities).sort((a, b) => b[1] - a[1]);
  const choice = ranked[0]?.[0] ?? Object.keys(weights)[0];
  const top = ranked[0]?.[1] ?? 0;
  const second = ranked[1]?.[1] ?? 0;
  const mass = Object.values(weights).reduce((a, b) => a + b, 0);
  const confidence = clamp01((top - second) * 1.65 + Math.min(mass / 8, 0.22));
  return { probabilities, choice, confidence };
}

function noul(text: string, yes: Evidence[], no: Evidence[] = []): NoulAnswer {
  const y = hitScore(text, yes);
  const n = hitScore(text, no) + 0.35;
  const p = clamp01(y / (y + n));
  return { noul: Number(p.toFixed(3)), label: p >= 0.5 ? "yes" : "no" };
}

function scoreAnswer(
  text: string,
  criteria: Record<string, Evidence[]>,
  numeric: Record<string, number>,
): ScoreAnswer {
  const weights: Record<string, number> = {};
  const keys = Object.keys(criteria);
  for (const key of keys) {
    weights[key] = hitScore(text, criteria[key] ?? []);
  }
  // Weak prior toward typical sprint work so empty axes don't collapse to the first key.
  if (keys.length >= 2) {
    const mid = keys[Math.floor((keys.length - 1) / 2)] ?? keys[1];
    const mid2 = keys[Math.min(keys.length - 2, Math.floor(keys.length / 2) + 1)];
    if (mid) weights[mid] += 0.55;
    if (mid2 && mid2 !== mid) weights[mid2] += 0.25;
  }
  const dist = distribution(weights);
  return {
    score: dist.choice,
    value: numeric[dist.choice] ?? 5,
    probabilities: dist.probabilities,
    confidence: dist.confidence,
  };
}

const PHASE_EVIDENCE: Record<Phase, Evidence[]> = {
  Debugging: [
    { pattern: /\b(fix|hotfix|bug|crash|broken|repro|regression|stack\s*trace|exception|outage|incident)\b/gi, weight: 3.3 },
    { pattern: /\berror\s*\d{3}\b/gi, weight: 3.6 },
    { pattern: /\bdebug(ging)?\b/gi, weight: 2.8 },
    { pattern: /\broot\s*cause\b/gi, weight: 2.6 },
    { pattern: /\bnot working\b/gi, weight: 2.4 },
  ],
  Deploy: [
    { pattern: /\b(deploy|rollout|release|publish|ci\/cd|github actions|production rollout)\b/gi, weight: 3.4 },
    { pattern: /\bship( it| to prod| to production)?\b/gi, weight: 3.1 },
    { pattern: /\b(prod(uction)?|vercel|aws)\b/gi, weight: 1.4 },
  ],
  Design: [
    { pattern: /\b(wireframe|figma|design tokens?|palette|typography|mock(up)?s?)\b/gi, weight: 3.4 },
    { pattern: /\b(ux spec|ui spec|user flow|information architecture)\b/gi, weight: 3.2 },
    { pattern: /\b(design|ux|ui)\b/gi, weight: 1.7 },
  ],
  Development: [
    { pattern: /\b(implement|scaffold|endpoint|api route|integration|codebase|typescript|next\.js)\b/gi, weight: 3.2 },
    { pattern: /\b(build|create|add|make|develop|write code)\b/gi, weight: 1.5 },
    { pattern: /\b(frontend|backend|full-?stack)\b/gi, weight: 1.8 },
  ],
  PreD: [
    { pattern: /\b(research|feasib|literature|best practices|should we|whether to|go\/no-go|discover)\b/gi, weight: 3.6 },
    { pattern: /\b(plan|prd|compare|evaluate|is this worth)\b/gi, weight: 2.3 },
    { pattern: /\b(brainstorm|explore|investigate)\b/gi, weight: 2.0 },
  ],
};

const DOMAIN_EVIDENCE: Record<Domain, Evidence[]> = {
  debug: [{ pattern: /\b(bug|crash|error|hotfix|exception|debug)\b/gi, weight: 3.2 }],
  deploy: [{ pattern: /\b(deploy|release|rollout|ci\/cd|prod)\b/gi, weight: 3.0 }],
  design: [
    { pattern: /\b(ux|ui|wireframe|figma|palette|typography|visual|design)\b/gi, weight: 3.1 },
    { pattern: /\b(icon|icons|layout|mock(up)?s?)\b/gi, weight: 1.8 },
  ],
  code: [{ pattern: /\b(code|api|endpoint|implement|typescript|python|next\.js|scaffold)\b/gi, weight: 2.8 }],
  ops: [{ pattern: /\b(infra|devops|aws|vercel|kubernetes|terraform|ci\/cd)\b/gi, weight: 2.9 }],
  research: [{ pattern: /\b(research|literature|survey|compare|feasib|best practices)\b/gi, weight: 3.2 }],
  sales: [{ pattern: /\b(email|outreach|prospect|icp|fintech guy|cold|pipeline|gtm)\b/gi, weight: 3.3 }],
  content: [{ pattern: /\b(copy|blog|landing page copy|docs page|changelog)\b/gi, weight: 2.4 }],
};

const NPAO_EVIDENCE: Record<NpaoCategory, Evidence[]> = {
  Necessity: [
    { pattern: /\b(blocker|blocked|outage|down|sev[0-1]|p0|can't proceed|cannot ship|prod is)\b/gi, weight: 3.8 },
    { pattern: /\b(security breach|secret leak|data loss|payment failing)\b/gi, weight: 3.6 },
  ],
  Anxiety: [
    { pattern: /\b(unclear|messy|confusing|friction|worried|anxious|vague|doesn't look right)\b/gi, weight: 3.2 },
    { pattern: /\b(cleanup|debt|inconsistent|noisy)\b/gi, weight: 2.4 },
  ],
  Priority: [
    { pattern: /\b(must|need to|mission|this sprint|revenue|customer|ship|deadline|today)\b/gi, weight: 2.2 },
    { pattern: /\b(implement|deploy|fix|release|build)\b/gi, weight: 1.4 },
  ],
  Opportunity: [
    { pattern: /\b(nice to have|explore|growth|experiment|could|maybe|later|optional)\b/gi, weight: 3.2 },
    { pattern: /\b(research|brainstorm)\b/gi, weight: 1.6 },
  ],
};

const URGENCY_EVIDENCE: Record<Urgency, Evidence[]> = {
  immediate: [
    { pattern: /\b(now|asap|today|p0|sev0|outage|hotfix|prod down|immediately)\b/gi, weight: 3.5 },
    { pattern: /\b(fix error|crash|broken)\b/gi, weight: 1.6 },
  ],
  queued: [
    { pattern: /\b(this sprint|this week|need to|must|ship|implement|deploy)\b/gi, weight: 2.0 },
  ],
  scheduled: [
    { pattern: /\b(later|next quarter|backlog|someday|when we can|roadmap)\b/gi, weight: 3.2 },
    { pattern: /\b(research|explore|brainstorm)\b/gi, weight: 1.3 },
  ],
};

const AGENT_EVIDENCE: Record<SubAgent, Evidence[]> = {
  "product-architect": [{ pattern: /\b(prd|architecture|plan|domain boundar|spec)\b/gi, weight: 2.8 }],
  "jtbd-npao-planner": [{ pattern: /\b(priorit|npao|rank|sequence|jtbd|jobs.to.be.done)\b/gi, weight: 3.2 }],
  "experience-engineer": [{ pattern: /\b(ux|ui|wireframe|accessibility|wcag|interaction)\b/gi, weight: 3.1 }],
  "application-engineer": [{ pattern: /\b(implement|api|code|frontend|backend|scaffold|next\.js)\b/gi, weight: 2.7 }],
  "agent-runtime-engineer": [{ pattern: /\b(agent|skill|mcp|soul\.md|runtime|harness|pydantic)\b/gi, weight: 3.3 }],
  "identity-commerce-qa": [{ pattern: /\b(oauth|auth|stripe|checkout|payment|identity)\b/gi, weight: 3.4 }],
  "quality-engineer": [{ pattern: /\b(test|qa|e2e|benchmark|regression|coverage)\b/gi, weight: 3.0 }],
  "devops-release-engineer": [{ pattern: /\b(deploy|ci\/cd|infra|rollback|vercel|aws)\b/gi, weight: 3.2 }],
  "security-reviewer": [{ pattern: /\b(security|threat|secret|audit|vulnerability|jailbreak)\b/gi, weight: 3.4 }],
};

export function evaluateSystemOne(
  state: string,
  backend: BackendKind = "local",
  model = "rostr-local-s1",
): SystemOneResponse {
  const t0 = performance.now();
  const text = state.trim();

  const phaseWeights: Record<string, number> = {
    PreD: hitScore(text, PHASE_EVIDENCE.PreD),
    Design: hitScore(text, PHASE_EVIDENCE.Design),
    Development: hitScore(text, PHASE_EVIDENCE.Development),
    Deploy: hitScore(text, PHASE_EVIDENCE.Deploy),
    Debugging: hitScore(text, PHASE_EVIDENCE.Debugging),
  };

  // Research framing beats incidental "build/fix" verbs.
  if (/\b(research|should we|whether to|feasib|is this worth)\b/i.test(text)) {
    phaseWeights.PreD += 2.4;
  }

  const phase = distribution(phaseWeights);
  const domain = distribution({
    code: hitScore(text, DOMAIN_EVIDENCE.code),
    design: hitScore(text, DOMAIN_EVIDENCE.design),
    research: hitScore(text, DOMAIN_EVIDENCE.research),
    ops: hitScore(text, DOMAIN_EVIDENCE.ops),
    sales: hitScore(text, DOMAIN_EVIDENCE.sales),
    content: hitScore(text, DOMAIN_EVIDENCE.content),
    deploy: hitScore(text, DOMAIN_EVIDENCE.deploy),
    debug: hitScore(text, DOMAIN_EVIDENCE.debug),
  });

  const npao = distribution({
    Necessity: hitScore(text, NPAO_EVIDENCE.Necessity),
    Anxiety: hitScore(text, NPAO_EVIDENCE.Anxiety),
    Priority: hitScore(text, NPAO_EVIDENCE.Priority),
    Opportunity: hitScore(text, NPAO_EVIDENCE.Opportunity),
  });

  const urgency = distribution({
    immediate: hitScore(text, URGENCY_EVIDENCE.immediate),
    queued: hitScore(text, URGENCY_EVIDENCE.queued),
    scheduled: hitScore(text, URGENCY_EVIDENCE.scheduled),
  });

  const chosenPhase = (phase.choice as Phase) in PHASE_SUBAGENTS
    ? (phase.choice as Phase)
    : "Development";
  const eligible = PHASE_SUBAGENTS[chosenPhase];
  const agentWeights: Record<string, number> = {};
  for (const id of eligible) {
    agentWeights[id] = hitScore(text, AGENT_EVIDENCE[id]) + 0.4;
  }
  const agent = distribution(agentWeights);

  const answers: SystemOneAnswers = {
    phase,
    domain,
    npao,
    urgency,
    agent,
    ambiguity: scoreAnswer(
      text,
      {
        crystal: [{ pattern: /\b(exact|specific|named|error\s*\d{3}|file|route|endpoint)\b/gi, weight: 2.4 }],
        usable: [{ pattern: /\b(implement|deploy|design|fix|build)\b/gi, weight: 1.6 }],
        vague: [{ pattern: /\b(the thing|it|better|stuff|somehow|maybe)\b/gi, weight: 3.2 }],
        incoherent: [{ pattern: /\b(idk|whatever|lol|asdf)\b/gi, weight: 4.0 }],
      },
      { crystal: 0.1, usable: 0.32, vague: 0.68, incoherent: 0.92 },
    ),
    businessImpact: scoreAnswer(
      text,
      {
        internal: [{ pattern: /\b(internal|tooling|refactor|docs)\b/gi, weight: 2.2 }],
        team: [
          { pattern: /\b(team|productivity|harness|runtime)\b/gi, weight: 2.0 },
          { pattern: /\b(workflow|ci\/?cd|github actions)\b/gi, weight: 1.6 },
        ],
        ux: [{ pattern: /\b(ux|ui|landing|customer experience|icons?)\b/gi, weight: 2.4 }],
        revenue: [{ pattern: /\b(revenue|stripe|checkout|customer|prod|billing|gtm)\b/gi, weight: 3.0 }],
      },
      { internal: 3, team: 5, ux: 7, revenue: 9.2 },
    ),
    dependencyImpact: scoreAnswer(
      text,
      {
        none: [{ pattern: /\b(docs|copy|palette|research only)\b/gi, weight: 2.0 }],
        few: [{ pattern: /\b(component|page|endpoint|handler)\b/gi, weight: 1.8 }],
        several: [
          { pattern: /\b(auth|payments|runtime|harness|multi-agent)\b/gi, weight: 2.6 },
          { pattern: /\b(error|crash|regression|fix)\b/gi, weight: 1.7 },
        ],
        critical_path: [
          { pattern: /\b(prod|deploys?|outage|blocker|secret|stripe|release|ci\/?cd|github actions)\b/gi, weight: 3.2 },
        ],
      },
      { none: 1, few: 3.5, several: 6.4, critical_path: 9.5 },
    ),
    resourceEfficiency: scoreAnswer(
      text,
      {
        multi_day: [{ pattern: /\b(platform|rewrite|architecture|migration|strategies)\b/gi, weight: 2.8 }],
        full_day: [{ pattern: /\b(harness|workflow|integration)\b/gi, weight: 2.2 }],
        hours: [{ pattern: /\b(implement|page|endpoint|design|handler)\b/gi, weight: 1.8 }],
        sub_hour: [{ pattern: /\b(typo|copy|hotfix|one line|ship it)\b/gi, weight: 3.0 }],
      },
      { multi_day: 2, full_day: 4, hours: 7, sub_hour: 9.5 },
    ),
    requiresApproval: noul(text, [
      { pattern: /\b(prod(uction)?|deploy|release|secret|oauth|stripe|dns|delete|payment)\b/gi, weight: 2.8 },
    ]),
    productionRisk: noul(text, [
      { pattern: /\b(prod(uction)?|live|customer data|secret|private key|webhook|dns)\b/gi, weight: 3.2 },
    ]),
    needsResearch: noul(text, [
      { pattern: /\b(research|unknown|best practices|compare|should we|feasib)\b/gi, weight: 3.4 },
    ]),
    mixedIntent: noul(text, [
      { pattern: /\b(then|and then|also|plus)\b/gi, weight: 2.6 },
    ]),
  };

  return {
    backend,
    model,
    latencyMs: Number((performance.now() - t0).toFixed(2)),
    answers,
  };
}

export function questionsFor(state: string) {
  return {
    state,
    questions: {
      phase: {
        type: "choice",
        instructions: "Which 5D lifecycle phase is this task in?",
        criteria: {
          PreD: "Determine whether to build; research, feasibility, go/no-go.",
          Design: "Define what to build: specs, UX, architecture, contracts.",
          Development: "Implement working, tested software.",
          Deploy: "Ship safely to production or staging.",
          Debugging: "Reproduce, root-cause, and fix a defect.",
        },
      },
      domain: {
        type: "choice",
        instructions: "Which work domain is primary?",
        criteria: {
          code: "Software implementation",
          design: "UX/UI specification",
          research: "Investigation before building",
          ops: "Infrastructure and deployment",
          sales: "GTM / outreach",
          content: "Writing",
          deploy: "Shipping",
          debug: "Defect repair",
        },
      },
      npao: {
        type: "choice",
        instructions: "Which NPAO category?",
        criteria: {
          Necessity: "Hard blocker; nothing else can proceed.",
          Anxiety: "Cognitive friction degrading other work.",
          Priority: "Mission-critical planned work.",
          Opportunity: "Growth or optional improvement.",
        },
      },
      urgency: {
        type: "choice",
        instructions: "When should this run?",
        criteria: {
          immediate: "Now / today / incident",
          queued: "Current sprint",
          scheduled: "Later / backlog",
        },
      },
      requires_approval: {
        type: "noul",
        instructions: "Does executing this require a named human approval gate?",
      },
      production_risk: {
        type: "noul",
        instructions: "Would this mutate production, auth, payments, or DNS?",
      },
    },
  };
}
