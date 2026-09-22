"""Local System One engine.

Same question schema as TypeSafe Jev (Choice / Noul / Score). Used when no
TYPESAFE_API_KEY is present. Not Jev — a calibrated-ish evidence scorer so
the harness is typed even offline.
"""

from __future__ import annotations

import math
import re
import time
from dataclasses import dataclass
from typing import Dict, List, Tuple


PHASES = ("PreD", "Design", "Development", "Deploy", "Debugging")
DOMAINS = ("code", "design", "research", "ops", "sales", "content", "deploy", "debug")
NPAO = ("Necessity", "Anxiety", "Priority", "Opportunity")
URGENCY = ("immediate", "queued", "scheduled")

PHASE_SUBAGENTS = {
    "PreD": ["product-architect", "jtbd-npao-planner"],
    "Design": ["product-architect", "experience-engineer", "agent-runtime-engineer"],
    "Development": ["application-engineer", "agent-runtime-engineer", "quality-engineer"],
    "Deploy": ["devops-release-engineer", "identity-commerce-qa", "quality-engineer"],
    "Debugging": ["application-engineer", "security-reviewer", "quality-engineer"],
}

PHASE_SCORES = {
    "Debugging": 10.0,
    "Deploy": 8.0,
    "Development": 6.0,
    "Design": 4.0,
    "PreD": 2.0,
}


def _clamp(n: float) -> float:
    return max(0.0, min(1.0, n))


def _softmax(weights: Dict[str, float], temperature: float = 0.72) -> Dict[str, float]:
    if not weights:
        return {}
    mx = max(weights.values())
    exps = {k: math.exp((v - mx) / temperature) for k, v in weights.items()}
    total = sum(exps.values()) or 1.0
    return {k: v / total for k, v in exps.items()}


def _hits(text: str, patterns: List[Tuple[str, float]]) -> float:
    score = 0.08
    for pattern, weight in patterns:
        found = re.findall(pattern, text, flags=re.I)
        if found:
            score += weight * min(len(found), 3)
    return score


def _dist(weights: Dict[str, float]) -> Dict[str, object]:
    probs = _softmax(weights)
    ranked = sorted(probs.items(), key=lambda kv: kv[1], reverse=True)
    choice = ranked[0][0]
    top = ranked[0][1]
    second = ranked[1][1] if len(ranked) > 1 else 0.0
    mass = sum(weights.values())
    confidence = _clamp((top - second) * 1.65 + min(mass / 8.0, 0.22))
    return {"choice": choice, "probabilities": probs, "confidence": round(confidence, 4)}


def _noul(text: str, yes: List[Tuple[str, float]], no: List[Tuple[str, float]] | None = None) -> Dict[str, object]:
    y = _hits(text, yes)
    n = _hits(text, no or []) + 0.35
    p = _clamp(y / (y + n))
    return {"noul": round(p, 3), "label": "yes" if p >= 0.5 else "no"}


def _score(text: str, criteria: Dict[str, List[Tuple[str, float]]], numeric: Dict[str, float]) -> Dict[str, object]:
    keys = list(criteria.keys())
    weights = {k: _hits(text, criteria[k]) for k in keys}
    if len(keys) >= 2:
        mid = keys[(len(keys) - 1) // 2]
        mid2 = keys[min(len(keys) - 2, len(keys) // 2 + 1)]
        weights[mid] = weights.get(mid, 0.0) + 0.55
        if mid2 != mid:
            weights[mid2] = weights.get(mid2, 0.0) + 0.25
    dist = _dist(weights)
    choice = str(dist["choice"])
    return {
        "score": choice,
        "value": numeric.get(choice, 5.0),
        "probabilities": dist["probabilities"],
        "confidence": dist["confidence"],
    }


PHASE_EVIDENCE = {
    "Debugging": [
        (r"\b(fix|hotfix|bug|crash|broken|repro|regression|stack\s*trace|exception|outage|incident)\b", 3.3),
        (r"\berror\s*\d{3}\b", 3.6),
        (r"\bdebug(ging)?\b", 2.8),
        (r"\broot\s*cause\b", 2.6),
        (r"\bnot working\b", 2.4),
    ],
    "Deploy": [
        (r"\b(deploy|rollout|release|publish|ci/cd|github actions|production rollout)\b", 3.4),
        (r"\bship( it| to prod| to production)?\b", 3.1),
        (r"\b(prod(uction)?|vercel|aws)\b", 1.4),
    ],
    "Design": [
        (r"\b(wireframe|figma|design tokens?|palette|typography|mock(up)?s?)\b", 3.4),
        (r"\b(ux spec|ui spec|user flow|information architecture)\b", 3.2),
        (r"\b(design|ux|ui)\b", 1.7),
    ],
    "Development": [
        (r"\b(implement|scaffold|endpoint|api route|integration|codebase|typescript|next\.js)\b", 3.2),
        (r"\b(build|create|add|make|develop|write code)\b", 1.5),
        (r"\b(frontend|backend|full-?stack)\b", 1.8),
    ],
    "PreD": [
        (r"\b(research|feasib|literature|best practices|should we|whether to|go/no-go|discover)\b", 3.6),
        (r"\b(plan|prd|compare|evaluate|is this worth)\b", 2.3),
        (r"\b(brainstorm|explore|investigate)\b", 2.0),
    ],
}

DOMAIN_EVIDENCE = {
    "debug": [(r"\b(bug|crash|error|hotfix|exception|debug)\b", 3.2)],
    "deploy": [(r"\b(deploy|release|rollout|ci/cd|prod)\b", 3.0)],
    "design": [
        (r"\b(ux|ui|wireframe|figma|palette|typography|visual|design)\b", 3.1),
        (r"\b(icon|icons|layout|mock(up)?s?)\b", 1.8),
    ],
    "code": [(r"\b(code|api|endpoint|implement|typescript|python|next\.js|scaffold)\b", 2.8)],
    "ops": [(r"\b(infra|devops|aws|vercel|kubernetes|terraform|ci/cd)\b", 2.9)],
    "research": [(r"\b(research|literature|survey|compare|feasib|best practices)\b", 3.2)],
    "sales": [(r"\b(email|outreach|prospect|icp|fintech guy|cold|pipeline|gtm)\b", 3.3)],
    "content": [(r"\b(copy|blog|landing page copy|docs page|changelog)\b", 2.4)],
}

NPAO_EVIDENCE = {
    "Necessity": [
        (r"\b(blocker|blocked|outage|down|sev[0-1]|p0|can't proceed|cannot ship|prod is)\b", 3.8),
        (r"\b(security breach|secret leak|data loss|payment failing)\b", 3.6),
    ],
    "Anxiety": [
        (r"\b(unclear|messy|confusing|friction|worried|anxious|vague|doesn't look right)\b", 3.2),
        (r"\b(cleanup|debt|inconsistent|noisy)\b", 2.4),
    ],
    "Priority": [
        (r"\b(must|need to|mission|this sprint|revenue|customer|ship|deadline|today)\b", 2.2),
        (r"\b(implement|deploy|fix|release|build)\b", 1.4),
    ],
    "Opportunity": [
        (r"\b(nice to have|explore|growth|experiment|could|maybe|later|optional)\b", 3.2),
        (r"\b(research|brainstorm)\b", 1.6),
    ],
}

URGENCY_EVIDENCE = {
    "immediate": [
        (r"\b(now|asap|today|p0|sev0|outage|hotfix|prod down|immediately)\b", 3.5),
        (r"\b(fix error|crash|broken)\b", 1.6),
    ],
    "queued": [(r"\b(this sprint|this week|need to|must|ship|implement|deploy)\b", 2.0)],
    "scheduled": [
        (r"\b(later|next quarter|backlog|someday|when we can|roadmap)\b", 3.2),
        (r"\b(research|explore|brainstorm)\b", 1.3),
    ],
}

AGENT_EVIDENCE = {
    "product-architect": [(r"\b(prd|architecture|plan|domain boundar|spec)\b", 2.8)],
    "jtbd-npao-planner": [(r"\b(priorit|npao|rank|sequence|jtbd|jobs.to.be.done)\b", 3.2)],
    "experience-engineer": [(r"\b(ux|ui|wireframe|accessibility|wcag|interaction)\b", 3.1)],
    "application-engineer": [(r"\b(implement|api|code|frontend|backend|scaffold|next\.js)\b", 2.7)],
    "agent-runtime-engineer": [(r"\b(agent|skill|mcp|soul\.md|runtime|harness|pydantic)\b", 3.3)],
    "identity-commerce-qa": [(r"\b(oauth|auth|stripe|checkout|payment|identity)\b", 3.4)],
    "quality-engineer": [(r"\b(test|qa|e2e|benchmark|regression|coverage)\b", 3.0)],
    "devops-release-engineer": [(r"\b(deploy|ci/cd|infra|rollback|vercel|aws)\b", 3.2)],
    "security-reviewer": [(r"\b(security|threat|secret|audit|vulnerability|jailbreak)\b", 3.4)],
}


@dataclass
class SystemOneResponse:
    backend: str
    model: str
    latency_ms: float
    answers: dict

    def to_dict(self) -> dict:
        return {
            "backend": self.backend,
            "model": self.model,
            "latency_ms": self.latency_ms,
            "answers": self.answers,
        }


def evaluate_local(state: str, backend: str = "local", model: str = "rostr-local-s1") -> SystemOneResponse:
    t0 = time.perf_counter()
    text = state.strip()

    phase_w = {k: _hits(text, v) for k, v in PHASE_EVIDENCE.items()}
    if re.search(r"\b(research|should we|whether to|feasib|is this worth)\b", text, re.I):
        phase_w["PreD"] += 2.4
    phase = _dist(phase_w)

    domain = _dist({k: _hits(text, v) for k, v in DOMAIN_EVIDENCE.items()})
    npao = _dist({k: _hits(text, v) for k, v in NPAO_EVIDENCE.items()})
    urgency = _dist({k: _hits(text, v) for k, v in URGENCY_EVIDENCE.items()})

    chosen_phase = phase["choice"] if phase["choice"] in PHASE_SUBAGENTS else "Development"
    eligible = PHASE_SUBAGENTS[chosen_phase]
    agent = _dist({aid: _hits(text, AGENT_EVIDENCE[aid]) + 0.4 for aid in eligible})

    answers = {
        "phase": phase,
        "domain": domain,
        "npao": npao,
        "urgency": urgency,
        "agent": agent,
        "ambiguity": _score(
            text,
            {
                "crystal": [(r"\b(exact|specific|named|error\s*\d{3}|file|route|endpoint)\b", 2.4)],
                "usable": [(r"\b(implement|deploy|design|fix|build)\b", 1.6)],
                "vague": [(r"\b(the thing|it|better|stuff|somehow|maybe)\b", 3.2)],
                "incoherent": [(r"\b(idk|whatever|lol|asdf)\b", 4.0)],
            },
            {"crystal": 0.1, "usable": 0.32, "vague": 0.68, "incoherent": 0.92},
        ),
        "business_impact": _score(
            text,
            {
                "internal": [(r"\b(internal|tooling|refactor|docs)\b", 2.2)],
                "team": [
                    (r"\b(team|productivity|harness|runtime)\b", 2.0),
                    (r"\b(workflow|ci/?cd|github actions)\b", 1.6),
                ],
                "ux": [(r"\b(ux|ui|landing|customer experience|icons?)\b", 2.4)],
                "revenue": [(r"\b(revenue|stripe|checkout|customer|prod|billing|gtm)\b", 3.0)],
            },
            {"internal": 3.0, "team": 5.0, "ux": 7.0, "revenue": 9.2},
        ),
        "dependency_impact": _score(
            text,
            {
                "none": [(r"\b(docs|copy|palette|research only)\b", 2.0)],
                "few": [(r"\b(component|page|endpoint|handler)\b", 1.8)],
                "several": [
                    (r"\b(auth|payments|runtime|harness|multi-agent)\b", 2.6),
                    (r"\b(error|crash|regression|fix)\b", 1.7),
                ],
                "critical_path": [
                    (r"\b(prod|deploys?|outage|blocker|secret|stripe|release|ci/?cd|github actions)\b", 3.2)
                ],
            },
            {"none": 1.0, "few": 3.5, "several": 6.4, "critical_path": 9.5},
        ),
        "resource_efficiency": _score(
            text,
            {
                "multi_day": [(r"\b(platform|rewrite|architecture|migration|strategies)\b", 2.8)],
                "full_day": [(r"\b(harness|workflow|integration)\b", 2.2)],
                "hours": [(r"\b(implement|page|endpoint|design|handler)\b", 1.8)],
                "sub_hour": [(r"\b(typo|copy|hotfix|one line|ship it)\b", 3.0)],
            },
            {"multi_day": 2.0, "full_day": 4.0, "hours": 7.0, "sub_hour": 9.5},
        ),
        "requires_approval": _noul(
            text, [(r"\b(prod(uction)?|deploy|release|secret|oauth|stripe|dns|delete|payment)\b", 2.8)]
        ),
        "production_risk": _noul(
            text, [(r"\b(prod(uction)?|live|customer data|secret|private key|webhook|dns)\b", 3.2)]
        ),
        "needs_research": _noul(
            text, [(r"\b(research|unknown|best practices|compare|should we|feasib)\b", 3.4)]
        ),
        "mixed_intent": _noul(text, [(r"\b(then|and then|also|plus)\b", 2.6)]),
    }

    return SystemOneResponse(
        backend=backend,
        model=model,
        latency_ms=round((time.perf_counter() - t0) * 1000, 2),
        answers=answers,
    )


def pal_questions(state: str) -> dict:
    """The actual Jev payload. Same questions whether backend is Jev or adapter."""
    return {
        "state": {"task": state},
        "questions": {
            "phase": {
                "type": "choice",
                "instructions": "Which 5D lifecycle phase is this task in?",
                "criteria": {
                    "PreD": "Determine whether to build; research, feasibility, go/no-go.",
                    "Design": "Define what to build: specs, UX, architecture, contracts.",
                    "Development": "Implement working, tested software.",
                    "Deploy": "Ship safely to production or staging.",
                    "Debugging": "Reproduce, root-cause, and fix a defect.",
                },
            },
            "npao": {
                "type": "choice",
                "instructions": "Which NPAO category?",
                "criteria": {
                    "Necessity": "Hard blocker; nothing else can proceed.",
                    "Anxiety": "Cognitive friction degrading other work.",
                    "Priority": "Mission-critical planned work.",
                    "Opportunity": "Growth or optional improvement.",
                },
            },
            "requires_approval": {
                "type": "noul",
                "instructions": "Does executing this require a named human approval gate?",
            },
            "production_risk": {
                "type": "noul",
                "instructions": "Would this mutate production, auth, payments, or DNS?",
            },
        },
    }
