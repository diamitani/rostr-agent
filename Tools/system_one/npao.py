"""NPAO scoring from System One answers instead of hardcoded 5.5/6.5/7.0."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .client import SystemOneClient
from .engine import PHASE_SCORES, PHASE_SUBAGENTS


@dataclass
class NPAOResult:
    task_id: str
    phase: str
    category: str
    phase_score: float
    dependency_score: float
    business_score: float
    resource_score: float
    final_priority: float
    queue_rank: int
    assigned_subagents: list[str]
    rationale: str
    confidence: float


def score_npao(
    task_id: str,
    prompt: str,
    phase: Optional[str] = None,
    client: Optional[SystemOneClient] = None,
) -> NPAOResult:
    response = (client or SystemOneClient()).evaluate(prompt)
    answers = response.answers
    resolved_phase = phase or str(answers["phase"]["choice"])
    if resolved_phase not in PHASE_SCORES:
        resolved_phase = "PreD"

    phase_score = PHASE_SCORES[resolved_phase]
    dependency_score = float(answers["dependency_impact"]["value"])
    business_score = float(answers["business_impact"]["value"])
    resource_score = float(answers["resource_efficiency"]["value"])
    final = round(
        phase_score * 0.35 + dependency_score * 0.30 + business_score * 0.25 + resource_score * 0.10,
        2,
    )
    category = str(answers["npao"]["choice"])
    order = {"Necessity": 0, "Anxiety": 1, "Priority": 2, "Opportunity": 3}
    queue_rank = order.get(category, 2) + (0 if final >= 7 else 1)

    return NPAOResult(
        task_id=task_id,
        phase=resolved_phase,
        category=category,
        phase_score=phase_score,
        dependency_score=dependency_score,
        business_score=business_score,
        resource_score=resource_score,
        final_priority=final,
        queue_rank=queue_rank,
        assigned_subagents=PHASE_SUBAGENTS.get(resolved_phase, ["application-engineer"]),
        rationale=(
            f"{category} in {resolved_phase}: "
            f"phase {phase_score * 0.35:.2f} + dep {dependency_score * 0.30:.2f} + "
            f"biz {business_score * 0.25:.2f} + res {resource_score * 0.10:.2f}."
        ),
        confidence=float(answers["phase"]["confidence"]),
    )
