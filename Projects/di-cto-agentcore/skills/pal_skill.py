"""
PAL (Prompt Abstraction Layer) skill implementation for DI-CTO AgentCore.

Stages 1 and 3 classification/scoring go through System One (Jev when a
TypeSafe key is present, otherwise the local typed engine). Semantic
enhancement still belongs to a System Two LLM when confidence is low.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_TOOLS = Path(__file__).resolve().parents[3] / "Tools"
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from system_one.pal import compile_pal  # noqa: E402


@dataclass
class StageResult:
    stage_number: int
    stage_name: str
    output: Any
    latency_ms: float


@dataclass
class CompiledPAL:
    raw_prompt: str
    intent: str
    domain: str
    phase: str
    priority_score: float
    selected_subagents: list[str]
    allowed_tools: list[str]
    approval_required: list[str]
    stages: list[StageResult] = field(default_factory=list)
    npao_category: str = "Priority"
    backend: str = "local"
    confidence: float = 0.0
    escalate_to_llm: bool = False


class PALSkill:
    SKILL_ID = "di-cto-pal-compiler"
    VERSION = "1.1.0"

    def __init__(self, agent_context: dict[str, Any] | None = None):
        self.context = agent_context or {}

    def compile(self, user_prompt: str) -> CompiledPAL:
        compiled = compile_pal(user_prompt)
        stages = [
            StageResult(s.stage_number, s.stage_name, s.output, s.latency_ms)
            for s in compiled.stages
        ]
        return CompiledPAL(
            raw_prompt=compiled.raw_prompt,
            intent=compiled.intent,
            domain=compiled.domain,
            phase=compiled.phase,
            priority_score=compiled.priority_score,
            selected_subagents=compiled.selected_subagents,
            allowed_tools=compiled.allowed_tools,
            approval_required=compiled.approval_required,
            stages=stages,
            npao_category=compiled.npao_category,
            backend=compiled.backend,
            confidence=compiled.confidence,
            escalate_to_llm=compiled.escalate_to_llm,
        )
