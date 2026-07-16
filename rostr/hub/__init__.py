"""
Rostr Hub — Persistent Reference Architecture
===============================================
The Agent Operating System: Multi-namespace state management,
agent registry, and knowledge compounding.

4-Level State Management:
  L1: Session State (ephemeral) — Active tasks, in-progress work
  L2: Project State (persistent) — Decisions, artifacts, learnings, history
  L3: Organization State (evolving) — Identity, ICP, positioning, team structure
  L4: Agent State (portable) — Skills, preferences, calibration, performance

Namespaces:
  projects/{id}/ — Per-project knowledge and state
  orgs/{id}/    — Organization-level shared context
  teams/{id}/   — Team conventions and shared knowledge
  global/       — Public shared templates and knowledge
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import json
import time
import uuid


class StateLevel(str, Enum):
    SESSION = "session"
    PROJECT = "project"
    ORGANIZATION = "organization"
    AGENT = "agent"


class Namespace(str, Enum):
    PROJECTS = "projects"
    ORGS = "orgs"
    TEAMS = "teams"
    GLOBAL = "global"


@dataclass
class AgentRegistration:
    """Agent registration entry in the Rostr Hub registry."""
    agent_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    agent_type: str = ""  # builder, researcher, reviewer, designer, deployer, debugger
    capabilities: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    phases: list[str] = field(default_factory=list)
    model: str = "claude-sonnet-4-6"
    max_parallel_tasks: int = 3
    performance_stats: dict = field(default_factory=lambda: {
        "tasks_completed": 0,
        "avg_completion_time_minutes": 0,
        "success_rate": 0.0,
    })

    def to_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "type": self.agent_type,
            "capabilities": self.capabilities,
            "tools": self.tools,
            "phases": self.phases,
            "model": self.model,
            "max_parallel_tasks": self.max_parallel_tasks,
            "performance_stats": self.performance_stats,
        }


@dataclass
class Decision:
    """A key decision logged to the reference hub."""
    decision_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    context: str = ""
    decision: str = ""
    rationale: str = ""
    alternatives_considered: list[str] = field(default_factory=list)
    namespace: str = ""


@dataclass
class Learning:
    """An insight learned during agent execution."""
    learning_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    context: str = ""
    insight: str = ""
    outcome: str = ""  # success, failure, observation
    source: str = ""   # agent_id or session_id
    tags: list[str] = field(default_factory=list)


class RostrHub:
    """
    Rostr Hub — the persistent reference architecture.

    Provides:
      - Agent registration and discovery
      - Multi-namespace state management
      - Decision and learning logging
      - Knowledge compounding across sessions
      - Cross-namespace access control
    """

    def __init__(self, base_path: str = ".rostr"):
        self.base_path = base_path
        self.agents: dict[str, AgentRegistration] = {}
        self.decisions: list[Decision] = []
        self.learnings: list[Learning] = []
        self.state: dict = {
            "session": {},
            "project": {},
            "organization": {},
            "agent": {},
        }
        self.namespaces: dict[str, dict] = {
            "projects": {},
            "orgs": {},
            "teams": {},
            "global": {},
        }

    # ── Agent Registry ──────────────────────────────────────────

    def register_agent(self, agent: AgentRegistration) -> AgentRegistration:
        """Register an agent in the hub."""
        self.agents[agent.agent_id] = agent
        return agent

    def get_agent(self, agent_id: str) -> Optional[AgentRegistration]:
        """Retrieve an agent by ID."""
        return self.agents.get(agent_id)

    def list_agents_by_type(self, agent_type: str) -> list[AgentRegistration]:
        """List all agents of a given type."""
        return [a for a in self.agents.values() if a.agent_type == agent_type]

    def list_agents_by_phase(self, phase: str) -> list[AgentRegistration]:
        """List all agents that can operate in a given phase."""
        return [a for a in self.agents.values() if phase in a.phases]

    # ── Decisions ───────────────────────────────────────────────

    def log_decision(
        self,
        context: str,
        decision: str,
        rationale: str,
        alternatives: Optional[list[str]] = None,
        namespace: str = "",
    ) -> Decision:
        """Log a key decision to the hub."""
        d = Decision(
            context=context,
            decision=decision,
            rationale=rationale,
            alternatives_considered=alternatives or [],
            namespace=namespace,
        )
        self.decisions.append(d)
        return d

    def get_decisions(self, namespace: str = "", limit: int = 20) -> list[Decision]:
        """Retrieve recent decisions, optionally filtered by namespace."""
        if namespace:
            filtered = [d for d in self.decisions if d.namespace == namespace]
            return filtered[-limit:]
        return self.decisions[-limit:]

    # ── Learnings ───────────────────────────────────────────────

    def log_learning(
        self,
        context: str,
        insight: str,
        outcome: str = "observation",
        source: str = "",
        tags: Optional[list[str]] = None,
    ) -> Learning:
        """Log an agent learning to the hub for knowledge compounding."""
        l = Learning(
            context=context,
            insight=insight,
            outcome=outcome,
            source=source,
            tags=tags or [],
        )
        self.learnings.append(l)
        return l

    def get_learnings(self, limit: int = 20, tags: Optional[list[str]] = None) -> list[Learning]:
        """Retrieve recent learnings, optionally filtered by tags."""
        results = self.learnings
        if tags:
            results = [l for l in results if any(t in l.tags for t in tags)]
        return results[-limit:]

    def search_learnings(self, query: str) -> list[Learning]:
        """
        Search learnings by keyword.
        Production: use semantic/vector search, not simple keyword matching.
        """
        query_lower = query.lower()
        results = []
        for l in self.learnings:
            score = 0
            if query_lower in l.context.lower():
                score += 3
            if query_lower in l.insight.lower():
                score += 5
            if query_lower in " ".join(l.tags).lower():
                score += 2
            if score > 0:
                results.append((score, l))
        results.sort(key=lambda x: x[0], reverse=True)
        return [l for _, l in results[:10]]

    # ── State Management ────────────────────────────────────────

    def set_state(self, level: StateLevel, key: str, value):
        """Set state at a given level."""
        self.state[level.value][key] = value

    def get_state(self, level: StateLevel, key: str, default=None):
        """Get state at a given level."""
        return self.state[level.value].get(key, default)

    def snapshot_session(self) -> dict:
        """Take a snapshot of current session state."""
        return {
            "timestamp": time.time(),
            "decisions_count": len(self.decisions),
            "learnings_count": len(self.learnings),
            "agents_registered": len(self.agents),
            "session_state_keys": list(self.state["session"].keys()),
        }

    # ── Namespace Management ────────────────────────────────────

    def ensure_namespace(self, ns_type: Namespace, ns_id: str) -> dict:
        """Ensure a namespace exists and return it."""
        if ns_id not in self.namespaces[ns_type.value]:
            self.namespaces[ns_type.value][ns_id] = {
                "created_at": time.time(),
                "decisions": [],
                "learnings": [],
                "knowledge_entries": [],
                "state": {},
            }
        return self.namespaces[ns_type.value][ns_id]

    def get_namespace(self, ns_type: Namespace, ns_id: str) -> Optional[dict]:
        """Get a namespace if it exists."""
        return self.namespaces[ns_type.value].get(ns_id)

    # ── Hub Structure ───────────────────────────────────────────

    def generate_structure(self) -> dict:
        """Generate the canonical rostr-hub directory structure."""
        return {
            "rostr-hub": {
                "projects": {
                    "{project-id}": [
                        "README.md",
                        "goals.md",
                        "decisions.md",
                        "architecture.md",
                        "knowledge-base/",
                        "learnings.jsonl",
                        "timeline.jsonl",
                        "checkpoints/",
                    ]
                },
                "orgs": {
                    "{org-id}": [
                        "identity.md",
                        "icp.md",
                        "positioning.md",
                        "playbooks/",
                        "knowledge-base/",
                    ]
                },
                "teams": {
                    "{team-id}": [
                        "agents.md",
                        "conventions.md",
                        "shared-context/",
                    ]
                },
                "global": [
                    "knowledge-base/",
                    "agent-templates/",
                ],
            }
        }

    # ── Knowledge Compounding ───────────────────────────────────

    def compound(self) -> dict:
        """Produce a knowledge compounding report."""
        return {
            "total_decisions": len(self.decisions),
            "total_learnings": len(self.learnings),
            "total_agents": len(self.agents),
            "recent_decisions": [d.decision for d in self.decisions[-5:]],
            "recent_learnings": [l.insight for l in self.learnings[-5:]],
            "agent_summary": {
                agent_id: {
                    "tasks_completed": a.performance_stats["tasks_completed"],
                    "success_rate": a.performance_stats["success_rate"],
                }
                for agent_id, a in self.agents.items()
            },
        }

    def to_json(self) -> str:
        """Serialize the hub state to JSON."""
        return json.dumps({
            "agents": {aid: a.to_dict() for aid, a in self.agents.items()},
            "decisions_count": len(self.decisions),
            "learnings_count": len(self.learnings),
        }, indent=2)
