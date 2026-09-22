"""PAL compiler with System One on stages 1 and 3 (classification / scoring).

Stage 3 semantic enhancement remains a System Two LLM when confidence is low.
Context injection, sandbox gates, and persistence stay deterministic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from .client import SystemOneClient
from .engine import PHASE_SCORES, PHASE_SUBAGENTS, SystemOneResponse


@dataclass
class StageResult:
    stage_number: int
    stage_name: str
    output: Any
    latency_ms: float
    owner: str = "system-one"


@dataclass
class PALCompilation:
    raw_prompt: str
    intent: str
    domain: str
    phase: str
    npao_category: str
    priority_score: float
    selected_subagents: list[str]
    allowed_tools: list[str]
    approval_required: list[str]
    stages: list[StageResult] = field(default_factory=list)
    answers: dict = field(default_factory=dict)
    backend: str = "local"
    confidence: float = 0.0
    escalate_to_llm: bool = False

    def to_dict(self) -> dict:
        return {
            "raw_prompt": self.raw_prompt,
            "intent": self.intent,
            "domain": self.domain,
            "phase": self.phase,
            "npao_category": self.npao_category,
            "priority_score": self.priority_score,
            "selected_subagents": self.selected_subagents,
            "allowed_tools": self.allowed_tools,
            "approval_required": self.approval_required,
            "backend": self.backend,
            "confidence": self.confidence,
            "escalate_to_llm": self.escalate_to_llm,
            "answers": self.answers,
        }


def compile_pal(user_prompt: str, client: Optional[SystemOneClient] = None) -> PALCompilation:
    response: SystemOneResponse = (client or SystemOneClient()).evaluate(user_prompt)
    answers = response.answers
    phase = answers["phase"]["choice"]
    if phase not in PHASE_SCORES:
        phase = "PreD"
    domain = answers["domain"]["choice"]
    domain_map = {"debug": "code", "deploy": "ops"}
    domain = domain_map.get(domain, domain)

    phase_val = PHASE_SCORES[phase]
    dep_val = float(answers["dependency_impact"]["value"])
    biz_val = float(answers["business_impact"]["value"])
    res_val = float(answers["resource_efficiency"]["value"])
    priority = round(phase_val * 0.35 + dep_val * 0.30 + biz_val * 0.25 + res_val * 0.10, 2)

    phase_agents = PHASE_SUBAGENTS[phase]
    primary = answers["agent"]["choice"]
    if primary not in phase_agents:
        primary = phase_agents[0]
    subagents = [primary] + [a for a in phase_agents if a != primary]
    subagents = subagents[:3]

    approval: list[str] = []
    if answers["requires_approval"]["noul"] >= 0.55 or phase == "Deploy":
        approval.append("production_deploy")
    prompt_l = user_prompt.lower()
    if (
        answers["production_risk"]["noul"] >= 0.55
        or "auth" in prompt_l
        or "secret" in prompt_l
        or "key" in prompt_l
    ):
        approval.append("security_boundary_check")

    tools = ["file_read", "file_write", "memory_query", "sandbox_eval"]
    if phase == "Deploy":
        tools.append("cloud_cli")
    if answers["needs_research"]["noul"] >= 0.5:
        tools.append("rag_dal")

    confidence = float(answers["phase"]["confidence"])
    escalate = confidence < 0.38 or float(answers["ambiguity"]["value"]) >= 0.65

    stages = [
        StageResult(
            1,
            "Intent Decomposition",
            {"intent": user_prompt.strip(), "phase": phase, "probabilities": answers["phase"]["probabilities"]},
            response.latency_ms,
            "system-one",
        ),
        StageResult(2, "Dependency Analysis", {"needs_research": answers["needs_research"]["noul"]}, 0.4, "deterministic"),
        StageResult(
            3,
            "Context Assembly",
            {"priority": priority, "escalate_to_llm": escalate, "soul_loaded": True, "assembled_tokens": 1420},
            0.6,
            "system-two" if escalate else "system-one",
        ),
        StageResult(4, "Sandboxed Verification", {"sandbox_ready": True, "approval_gates": approval}, 0.3, "deterministic"),
        StageResult(5, "State Persistence", {"target_namespace": "rostr_decisions"}, 0.2, "deterministic"),
    ]

    return PALCompilation(
        raw_prompt=user_prompt,
        intent=user_prompt.strip(),
        domain=domain,
        phase=phase,
        npao_category=str(answers["npao"]["choice"]),
        priority_score=priority,
        selected_subagents=subagents,
        allowed_tools=tools,
        approval_required=approval,
        stages=stages,
        answers=answers,
        backend=response.backend,
        confidence=confidence,
        escalate_to_llm=escalate,
    )
