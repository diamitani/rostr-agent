"""
NPAO — Navigate, Prioritize, Allocate, Orchestrate
=====================================================
The Decision Engine: Phase-aware, priority-scored agent orchestration.

5D Phase Taxonomy:
  PreD (0) — Research: "Is this worth building?"
  Design (1) — Plan: "What exactly are we building?"
  Development (2) — Build: "Does it work?"
  Deployment (3) — Ship: "Is it safe to ship?"
  Debugging (4) — Fix: "What broke, why, how do we prevent it?"

4D Priority Scoring:
  Priority = (Phase_Urgency × 0.35) + (Dependency_Impact × 0.30)
           + (Business_Impact × 0.25) + (Resource_Efficiency × 0.10)

  Thresholds: ≥7.0: Immediate | 4.0-6.9: Queued | <4.0: Backlog
"""

from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Optional
import json


class PhaseType(IntEnum):
    """5D Phase Taxonomy — ordered by workflow lifecycle."""
    PRED = 0        # Pre-Development: Research & Feasibility
    DESIGN = 1       # Design: Architecture & Planning
    DEVELOPMENT = 2  # Development: Implementation & Testing
    DEPLOYMENT = 3   # Deployment: Shipping & Monitoring
    DEBUGGING = 4    # Debugging: Investigation & Fix


class OrchestrationPattern(str, Enum):
    SEQUENTIAL = "sequential"        # A → B → C
    PARALLEL_FAN_OUT = "parallel"    # A → [B, C, D]
    AGGREGATION_FAN_IN = "aggregate" # [A, B, C] → E
    CONDITIONAL_BRANCH = "conditional" # A → decision → B or C


class AllocationStatus(str, Enum):
    IMMEDIATE = "immediate"  # ≥7.0
    QUEUED = "queued"        # 4.0-6.9
    BACKLOG = "backlog"      # <4.0


# ── Phase Urgency Base Scores ──────────────────────────────────

PHASE_URGENCY_BASE: dict[PhaseType, float] = {
    PhaseType.DEBUGGING: 10.0,     # P0 production issues
    PhaseType.DEPLOYMENT: 8.0,     # Active release
    PhaseType.DEVELOPMENT: 6.0,    # Blocked sprint
    PhaseType.DESIGN: 4.0,         # Pre-development
    PhaseType.PRED: 2.0,           # Research
}


# ── Phase Completion Criteria ──────────────────────────────────

PHASE_CRITERIA: dict[PhaseType, list[str]] = {
    PhaseType.PRED: [
        "Problem stated in one sentence",
        "Target user identified",
        "≥3 alternatives considered and rejected",
        "Success criteria defined (measurable)",
        "Known unknowns documented",
        "Decision: build now / later / don't build",
    ],
    PhaseType.DESIGN: [
        "Architecture diagram exists",
        "User flows documented",
        "Data models defined",
        "Interfaces specified",
        "Tech choices made with rationale",
        "Edge cases identified",
    ],
    PhaseType.DEVELOPMENT: [
        "All features implemented",
        "Test coverage ≥ threshold",
        "Code review passed",
        "No blocking bugs",
        "Documentation updated",
    ],
    PhaseType.DEPLOYMENT: [
        "Staging QA passed",
        "Performance benchmarks met",
        "Security audit passed",
        "Monitoring active",
        "Rollback procedure tested",
        "Production deploy verified",
    ],
    PhaseType.DEBUGGING: [
        "Bug reproduced reliably",
        "Root cause identified (not just symptom)",
        "Fix implemented and tested",
        "Regression test added",
        "Post-mortem written (if P0/P1)",
    ],
}


@dataclass
class PriorityScore:
    """4D priority scoring for a task."""
    phase_urgency: float
    dependency_impact: float
    business_impact: float
    resource_efficiency: float
    composite: float = 0.0

    def __post_init__(self):
        self.composite = (
            self.phase_urgency * 0.35
            + self.dependency_impact * 0.30
            + self.business_impact * 0.25
            + self.resource_efficiency * 0.10
        )

    @property
    def status(self) -> AllocationStatus:
        if self.composite >= 7.0:
            return AllocationStatus.IMMEDIATE
        elif self.composite >= 4.0:
            return AllocationStatus.QUEUED
        return AllocationStatus.BACKLOG


@dataclass
class AgentSpec:
    """Specification for an agent in the registry."""
    agent_id: str
    name: str
    agent_type: str  # builder, researcher, reviewer, designer, deployer, debugger
    capabilities: list[str]
    tools: list[str]
    phases: list[PhaseType]
    model: str = "claude-sonnet-4-6"
    max_parallel_tasks: int = 3
    current_tasks: int = 0
    performance_stats: dict = field(default_factory=lambda: {
        "tasks_completed": 0,
        "avg_completion_time_minutes": 0,
        "success_rate": 0.0,
    })


class NPAO:
    """
    NPAO — Navigate, Prioritize, Allocate, Orchestrate.

    The decision engine that classifies task phases, scores priority,
    allocates to capable agents, and selects orchestration patterns.
    """

    def __init__(self):
        self.agent_registry: list[AgentSpec] = []

    # ── Navigate: 5D Phase Classification ──────────────────────

    def classify_phase(self, task_description: str, domain: str = "") -> PhaseType:
        """
        Navigate: classify a task into the 5D phase taxonomy.

        Uses keyword heuristics; production would use LLM classification.
        """
        task_lower = task_description.lower()
        domain_lower = domain.lower()

        # Debugging signals (highest priority check)
        debug_keywords = ["bug", "fix", "error", "broken", "crash", "issue", "debug"]
        if any(kw in task_lower for kw in debug_keywords):
            return PhaseType.DEBUGGING

        # Deployment signals
        deploy_keywords = ["deploy", "ship", "release", "publish", "launch", "production"]
        if any(kw in task_lower for kw in deploy_keywords):
            return PhaseType.DEPLOYMENT

        # Development signals
        dev_keywords = ["build", "implement", "code", "create", "make", "develop"]
        if any(kw in task_lower for kw in dev_keywords):
            return PhaseType.DEVELOPMENT

        # Design signals
        design_keywords = ["design", "wireframe", "plan", "architect", "spec", "ui", "ux"]
        if any(kw in task_lower for kw in design_keywords):
            return PhaseType.DESIGN

        # Research signals
        research_keywords = ["research", "analyze", "investigate", "find", "explore", "report"]
        if any(kw in task_lower for kw in research_keywords):
            return PhaseType.PRED

        # Domain-based fallback
        domain_phase_map = {
            "code": PhaseType.DEVELOPMENT,
            "design": PhaseType.DESIGN,
            "research": PhaseType.PRED,
            "deploy": PhaseType.DEPLOYMENT,
            "debug": PhaseType.DEBUGGING,
        }
        if domain_lower in domain_phase_map:
            return domain_phase_map[domain_lower]

        # Default: start with research
        return PhaseType.PRED

    # ── Prioritize: 4D Priority Scoring ────────────────────────

    def score_priority(
        self,
        phase: PhaseType,
        blocked_tasks: int = 0,
        revenue_impact: bool = False,
        user_impact: bool = False,
        team_impact: bool = False,
        estimated_hours: float = 4.0,
    ) -> PriorityScore:
        """
        Prioritize: compute 4D priority score.

        Args:
            phase: Classified workflow phase
            blocked_tasks: Number of tasks blocked by this one
            revenue_impact: Directly affects revenue?
            user_impact: Affects user experience?
            team_impact: Affects team productivity?
            estimated_hours: Estimated completion time
        """
        # Dimension 1: Phase Urgency
        phase_urgency = PHASE_URGENCY_BASE.get(phase, 2.0)
        if phase == PhaseType.DEBUGGING:
            pass  # Already max priority
        elif phase == PhaseType.DEPLOYMENT and revenue_impact:
            phase_urgency += 2.0

        # Dimension 2: Dependency Impact
        if blocked_tasks >= 6:
            dependency_impact = 10.0
        elif blocked_tasks >= 3:
            dependency_impact = 6.0
        elif blocked_tasks >= 1:
            dependency_impact = 3.0
        else:
            dependency_impact = 0.0

        # Dimension 3: Business Impact
        if revenue_impact:
            business_impact = 9.0
        elif user_impact:
            business_impact = 7.0
        elif team_impact:
            business_impact = 5.0
        else:
            business_impact = 2.0

        # Dimension 4: Resource Efficiency
        if estimated_hours < 1:
            resource_efficiency = 10.0
        elif estimated_hours < 4:
            resource_efficiency = 7.0
        elif estimated_hours < 8:
            resource_efficiency = 4.0
        else:
            resource_efficiency = 2.0

        return PriorityScore(
            phase_urgency=phase_urgency,
            dependency_impact=dependency_impact,
            business_impact=business_impact,
            resource_efficiency=resource_efficiency,
        )

    # ── Allocate: Agent Allocation Algorithm ────────────────────

    def register_agent(self, agent: AgentSpec):
        """Register an agent in the registry."""
        self.agent_registry.append(agent)

    def allocate(
        self,
        phase: PhaseType,
        required_tools: list[str],
    ) -> Optional[AgentSpec]:
        """
        Allocate: find the best agent for a task.

        Algorithm:
          1. Filter eligible agents (phase match, tool match, capacity)
          2. Score each agent (context 0.50, specialization 0.35, load 0.15)
          3. Return highest scorer
        """
        # Filter eligible
        eligible = []
        for agent in self.agent_registry:
            if phase not in agent.phases:
                continue
            if not all(tool in agent.tools for tool in required_tools):
                continue
            if agent.current_tasks >= agent.max_parallel_tasks:
                continue
            eligible.append(agent)

        if not eligible:
            return None

        # Score each agent
        scored = []
        for agent in eligible:
            spec_score = self._capability_overlap(agent, phase)
            load_score = 1.0 - (agent.current_tasks / max(agent.max_parallel_tasks, 1))
            context_score = 0.5  # Default; real impl uses vector similarity

            total = context_score * 0.50 + spec_score * 0.35 + load_score * 0.15
            scored.append((total, agent))

        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[0][1]

    def _capability_overlap(self, agent: AgentSpec, phase: PhaseType) -> float:
        """Score how well this agent's capabilities match the task phase."""
        phase_agents = {
            PhaseType.PRED: ["researcher"],
            PhaseType.DESIGN: ["designer"],
            PhaseType.DEVELOPMENT: ["builder"],
            PhaseType.DEPLOYMENT: ["deployer"],
            PhaseType.DEBUGGING: ["debugger"],
        }
        preferred = phase_agents.get(phase, [])
        if agent.agent_type in preferred:
            return 1.0
        return 0.5

    # ── Orchestrate: Pattern Selection ─────────────────────────

    def select_pattern(
        self,
        task_count: int,
        has_dependencies: bool,
        needs_aggregation: bool,
        has_conditionals: bool,
    ) -> OrchestrationPattern:
        """
        Orchestrate: select the appropriate execution pattern.

        Sequential: A → B → C (dependencies, single path)
        Parallel Fan-Out: A → [B, C, D] (independent tasks)
        Aggregation Fan-In: [A, B, C] → E (synthesize results)
        Conditional Branch: A → decision → B or C
        """
        if has_conditionals:
            return OrchestrationPattern.CONDITIONAL_BRANCH
        if needs_aggregation:
            return OrchestrationPattern.AGGREGATION_FAN_IN
        if task_count > 1 and not has_dependencies:
            return OrchestrationPattern.PARALLEL_FAN_OUT
        return OrchestrationPattern.SEQUENTIAL

    # ── Full NPAO Pipeline ─────────────────────────────────────

    def process(
        self, task_description: str, domain: str = "", **priority_kwargs
    ) -> dict:
        """Run the full NPAO pipeline: Navigate → Prioritize → Allocate → Orchestrate."""
        # Navigate
        phase = self.classify_phase(task_description, domain)

        # Prioritize
        priority = self.score_priority(phase, **priority_kwargs)

        # Allocate
        required_tools = ["web_search", "file_system:read"]
        if phase == PhaseType.DEVELOPMENT:
            required_tools.append("code_execution")

        allocated_agent = self.allocate(phase, required_tools)

        # Orchestrate
        pattern = self.select_pattern(
            task_count=1,
            has_dependencies=False,
            needs_aggregation=False,
            has_conditionals=False,
        )

        return {
            "phase": phase.name,
            "phase_index": phase.value,
            "criteria": PHASE_CRITERIA[phase],
            "priority": {
                "composite": priority.composite,
                "status": priority.status.value,
                "breakdown": {
                    "phase_urgency": priority.phase_urgency,
                    "dependency_impact": priority.dependency_impact,
                    "business_impact": priority.business_impact,
                    "resource_efficiency": priority.resource_efficiency,
                },
            },
            "allocation": {
                "agent": allocated_agent.agent_id if allocated_agent else None,
                "agent_name": allocated_agent.name if allocated_agent else None,
            },
            "orchestration": pattern.value,
        }
