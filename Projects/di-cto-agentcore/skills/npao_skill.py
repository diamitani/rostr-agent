"""
NPAO skill. Deterministic 4D formula is unchanged.

When a prompt is supplied, axis scores come from System One instead of the
caller inventing 5.5 / 6.5 / 7.0.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

_TOOLS = Path(__file__).resolve().parents[3] / "Tools"
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from system_one.npao import score_npao  # noqa: E402


@dataclass
class NPAOResult:
    task_id: str
    phase: str
    phase_score: float
    dependency_score: float
    business_score: float
    resource_score: float
    final_priority: float
    queue_rank: int
    assigned_subagents: list[str]
    rationale: str
    category: str = "Priority"


class NPAOSkill:
    SKILL_ID = "di-cto-npao-orchestrator"
    VERSION = "1.1.0"

    PHASE_SCORES = {
        "Debugging": 10.0,
        "Deploy": 8.0,
        "Development": 6.0,
        "Design": 4.0,
        "PreD": 2.0,
    }

    def calculate_priority(
        self,
        task_id: str,
        phase: str,
        dependency_score: float = 5.0,
        business_score: float = 6.0,
        resource_score: float = 7.0,
        prompt: Optional[str] = None,
    ) -> NPAOResult:
        if prompt:
            live = score_npao(task_id, prompt, phase=phase)
            return NPAOResult(
                task_id=live.task_id,
                phase=live.phase,
                phase_score=live.phase_score,
                dependency_score=live.dependency_score,
                business_score=live.business_score,
                resource_score=live.resource_score,
                final_priority=live.final_priority,
                queue_rank=1 if live.final_priority >= 7.0 else (2 if live.final_priority >= 5.0 else 3),
                assigned_subagents=live.assigned_subagents,
                rationale=live.rationale,
                category=live.category,
            )

        phase_score = self.PHASE_SCORES.get(phase, 4.0)
        score = (
            (phase_score * 0.35)
            + (dependency_score * 0.30)
            + (business_score * 0.25)
            + (resource_score * 0.10)
        )
        rationale = (
            f"Phase [{phase}] contributes {phase_score * 0.35:.2f} (35%), "
            f"Dependency [{dependency_score}] contributes {dependency_score * 0.30:.2f} (30%), "
            f"Business [{business_score}] contributes {business_score * 0.25:.2f} (25%), "
            f"Resource [{resource_score}] contributes {resource_score * 0.10:.2f} (10%)."
        )
        subagent_map = {
            "PreD": ["product-architect", "jtbd-npao-planner"],
            "Design": ["product-architect", "experience-engineer", "agent-runtime-engineer"],
            "Development": ["application-engineer", "agent-runtime-engineer", "quality-engineer"],
            "Deploy": ["devops-release-engineer", "identity-commerce-qa"],
            "Debugging": ["application-engineer", "security-reviewer"],
        }
        return NPAOResult(
            task_id=task_id,
            phase=phase,
            phase_score=phase_score,
            dependency_score=dependency_score,
            business_score=business_score,
            resource_score=resource_score,
            final_priority=round(score, 2),
            queue_rank=1 if score >= 7.0 else (2 if score >= 5.0 else 3),
            assigned_subagents=subagent_map.get(phase, ["application-engineer"]),
            rationale=rationale,
        )
