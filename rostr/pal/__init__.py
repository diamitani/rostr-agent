"""
PAL — Prompt Abstraction Layer
================================
The LLM Compiler: Natural Language → Typed Agent Manifest

Five-Stage Compilation Pipeline:
  1. Intent Extraction  — Parse raw input → structured intent object
  2. Context Injection  — Load session/project/org state from reference hub
  3. Semantic Enhancement — Expand verbs, decompose goals, inject precision
  4. Runtime Compilation — Compile enhanced intent → agent runtime manifest
  5. Output Routing     — Route manifest to NPAO by domain/phase

Analogy:
  Source Code (NL) → AST (Intent) → Optimization (Enhancement)
  → Binary (Manifest) → Target Architecture (Agent Type)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Any
import json


class Domain(str, Enum):
    CODE = "code"
    DESIGN = "design"
    RESEARCH = "research"
    OPS = "ops"
    SALES = "sales"
    CONTENT = "content"
    DEPLOY = "deploy"
    DEBUG = "debug"


class Urgency(str, Enum):
    IMMEDIATE = "immediate"
    QUEUED = "queued"
    SCHEDULED = "scheduled"


class AgentType(str, Enum):
    BUILDER = "builder"
    RESEARCHER = "researcher"
    REVIEWER = "reviewer"
    DESIGNER = "designer"
    DEPLOYER = "deployer"
    DEBUGGER = "debugger"


class BehaviorProfile(str, Enum):
    ANALYTICAL = "analytical"
    CREATIVE = "creative"
    OPERATIONAL = "operational"
    INVESTIGATIVE = "investigative"


class EscalationPolicy(str, Enum):
    AUTO_PROCEED = "auto-proceed"
    REQUIRE_APPROVAL = "require-approval"
    HUMAN_IN_LOOP = "human-in-loop"


class MemoryMode(str, Enum):
    SESSION = "session"
    PROJECT = "project"
    PERSISTENT = "persistent"


class OutputFormat(str, Enum):
    MARKDOWN = "markdown"
    JSON = "json"
    CODE = "code"
    ACTION = "action"


class VerificationMode(str, Enum):
    NONE = "none"
    TEST = "test"
    HUMAN_REVIEW = "human-review"


@dataclass
class Intent:
    """Structured intent extracted from raw natural language input."""

    primary_intent: str
    domain: Domain
    subject: str
    constraints: list[str] = field(default_factory=list)
    desired_output: str = ""
    urgency: Urgency = Urgency.QUEUED
    ambiguity_score: float = 0.0
    context_payload: Optional[dict[str, Any]] = None

    def to_dict(self) -> dict:
        return {
            "primary_intent": self.primary_intent,
            "domain": self.domain.value,
            "subject": self.subject,
            "constraints": self.constraints,
            "desired_output": self.desired_output,
            "urgency": self.urgency.value,
            "ambiguity_score": self.ambiguity_score,
        }


@dataclass
class AgentManifest:
    """Compiled agent runtime manifest — the 'binary' of PAL compilation."""

    agent_type: AgentType
    model: str = "claude-sonnet-4-6"
    temperature: float = 0.2
    max_parallel_tasks: int = 1
    timeout_seconds: int = 600
    behavior_profile: BehaviorProfile = BehaviorProfile.OPERATIONAL
    task_description: str = ""
    completion_criteria: list[str] = field(default_factory=list)
    escalation_policy: EscalationPolicy = EscalationPolicy.AUTO_PROCEED
    tools_allow: list[str] = field(default_factory=list)
    tools_deny: list[str] = field(default_factory=list)
    memory_mode: MemoryMode = MemoryMode.SESSION
    context_sources: list[str] = field(default_factory=list)
    save_triggers: list[str] = field(default_factory=lambda: ["decisions", "learnings", "artifacts"])
    output_format: OutputFormat = OutputFormat.MARKDOWN
    output_destination: str = "return"
    verification: VerificationMode = VerificationMode.NONE
    routing_phase: Optional[str] = None  # Set by NPAO after classification

    def to_dict(self) -> dict:
        return {
            "runtime": {
                "agent_type": self.agent_type.value,
                "model": self.model,
                "temperature": self.temperature,
                "max_parallel_tasks": self.max_parallel_tasks,
                "timeout_seconds": self.timeout_seconds,
            },
            "instructions": {
                "behavior_profile": self.behavior_profile.value,
                "task_description": self.task_description,
                "completion_criteria": self.completion_criteria,
                "escalation_policy": self.escalation_policy.value,
            },
            "tools_enabled": {
                "allow": self.tools_allow,
                "deny": self.tools_deny,
            },
            "memory": {
                "mode": self.memory_mode.value,
                "context_sources": self.context_sources,
                "save_triggers": self.save_triggers,
            },
            "output": {
                "format": self.output_format.value,
                "destination": self.output_destination,
                "verification": self.verification.value,
            },
        }

    def to_yaml(self) -> str:
        """Serialize manifest to YAML string."""
        d = self.to_dict()
        return _dict_to_yaml(d)


class PALCompiler:
    """
    PAL — Prompt Abstraction Layer Compiler.

    Five-stage pipeline that transforms raw natural language intent
    into a strictly-typed agent runtime manifest.

    Stage 1: Intent Extraction
    Stage 2: Context Injection (from reference hub)
    Stage 3: Semantic Enhancement
    Stage 4: Runtime Compilation
    Stage 5: Output Routing
    """

    def __init__(self, context_budget: int = 5500):
        self.context_budget = context_budget

    # ── Stage 1: Intent Extraction ──────────────────────────────

    def extract_intent(self, raw_input: str) -> Intent:
        """
        Parse raw natural language input into a structured Intent object.

        Algorithm:
          1. Parse for imperative verbs (build, research, fix, deploy, analyze)
          2. Extract domain signals from keywords
          3. Identify explicit and implicit constraints
          4. Classify urgency from time signals
          5. Compute ambiguity score: 1.0 - (explicit_params / required_params)
        """
        intent = Intent(
            primary_intent=self._extract_primary(raw_input),
            domain=self._classify_domain(raw_input),
            subject=self._extract_subject(raw_input),
            constraints=self._extract_constraints(raw_input),
            desired_output=self._infer_output(raw_input),
            urgency=self._classify_urgency(raw_input),
            ambiguity_score=self._compute_ambiguity(raw_input),
        )
        return intent

    def _extract_primary(self, text: str) -> str:
        verbs = {
            "build": "create",
            "make": "create",
            "research": "research",
            "fix": "fix",
            "debug": "debug",
            "deploy": "deploy",
            "ship": "deploy",
            "analyze": "analyze",
            "design": "design",
            "write": "write",
        }
        text_lower = text.lower()
        for trigger, verb in verbs.items():
            if trigger in text_lower:
                return f"{verb} {self._extract_object(text, trigger)}"
        return text.strip()

    def _extract_object(self, text: str, verb: str) -> str:
        """Extract the object after the verb."""
        parts = text.lower().split(verb, 1)
        if len(parts) > 1:
            return parts[1].strip().rstrip(".")
        return ""

    def _classify_domain(self, text: str) -> Domain:
        signals = {
            Domain.CODE: ["code", "implement", "build", "api", "function", "class", "app"],
            Domain.DESIGN: ["design", "wireframe", "ui", "ux", "layout", "style", "css"],
            Domain.RESEARCH: ["research", "analyze", "find", "search", "report", "investigate"],
            Domain.DEPLOY: ["deploy", "ship", "release", "publish", "launch"],
            Domain.DEBUG: ["bug", "fix", "error", "broken", "crash", "issue"],
            Domain.SALES: ["customer", "lead", "prospect", "sales", "outreach", "pipeline"],
            Domain.CONTENT: ["write", "blog", "article", "content", "copy", "email"],
            Domain.OPS: ["monitor", "alert", "backup", "schedule", "cron"],
        }
        text_lower = text.lower()
        scores = {domain: sum(1 for s in sig if s in text_lower) for domain, sig in signals.items()}
        best = max(scores, key=scores.get)
        return best if scores[best] > 0 else Domain.RESEARCH

    def _extract_subject(self, text: str) -> str:
        text_lower = text.lower()
        for verb in ["build", "make", "research", "fix", "debug", "deploy", "ship", "analyze", "design", "write"]:
            if verb in text_lower:
                obj = self._extract_object(text, verb)
                return obj if obj else text.strip()
        return text.strip()

    def _extract_constraints(self, text: str) -> list[str]:
        constraints = []
        if "python" in text.lower():
            constraints.append("use Python")
        if "test" in text.lower():
            constraints.append("include tests")
        if "fast" in text.lower() or "quick" in text.lower():
            constraints.append("time-sensitive")
        if "production" in text.lower():
            constraints.append("production-grade")
        return constraints

    def _classify_urgency(self, text: str) -> Urgency:
        if any(w in text.lower() for w in ["now", "asap", "urgent", "immediately", "critical"]):
            return Urgency.IMMEDIATE
        if any(w in text.lower() for w in ["today", "tonight", "by end of day"]):
            return Urgency.QUEUED
        return Urgency.SCHEDULED

    def _infer_output(self, text: str) -> str:
        if "deploy" in text.lower() or "ship" in text.lower():
            return "deployed feature"
        if "research" in text.lower() or "analyze" in text.lower():
            return "research report"
        if "build" in text.lower() or "make" in text.lower():
            return "working implementation"
        return "completed task"

    def _compute_ambiguity(self, text: str) -> float:
        words = len(text.split())
        has_domain = self._classify_domain(text) != Domain.RESEARCH
        has_output = any(w in text.lower() for w in ["deploy", "publish", "write", "build in"])
        has_tool = any(w in text.lower() for w in ["python", "react", "api", "cli"])
        explicit = sum([has_domain, has_output, has_tool])
        return max(0.0, 1.0 - (explicit / 4.0))

    # ── Stage 2: Context Injection ──────────────────────────────

    def inject_context(self, intent: Intent, hub_context: Optional[dict] = None) -> Intent:
        """
        Inject relevant context from the reference hub into the intent.

        Loads: session state, project context, org context, team context,
        and vector-search retrieves top-k relevant prior decisions/learnings.
        """
        if hub_context:
            intent.context_payload = hub_context
        return intent

    # ── Stage 3: Semantic Enhancement ──────────────────────────

    def enhance(self, intent: Intent) -> str:
        """
        Apply semantic enhancement rules to produce a precise instruction string.

        Rules:
          1. Expand ambiguous verbs
          2. Add missing precision (success criteria, output format)
          3. Decompose compound goals into phase sequence
          4. Remove hedging
          5. Inject domain best practices
        """
        rules_applied = []

        # Rule 1: Expand ambiguous verbs
        expansion = {
            "improve": "identify top 3 issues by severity, propose specific fix for each",
            "check": "verify correctness, flag anomalies, report status",
            "review": "audit against best practices, score each criterion, recommend fixes",
            "optimize": "profile performance, identify bottlenecks, implement targeted improvements",
        }
        enhanced = intent.primary_intent
        for vague, precise in expansion.items():
            if vague in enhanced.lower():
                enhanced = precise
                rules_applied.append(f"expanded '{vague}' → '{precise}'")

        # Rule 2: Add missing precision
        if not intent.desired_output:
            enhanced += "\n\nSuccess criteria: task completed, verified, documented."

        # Rule 4: Remove hedging
        hedges = ["maybe", "perhaps", "if you have time", "it would be nice", "whenever"]
        for h in hedges:
            if h in enhanced.lower():
                enhanced = enhanced.replace(h, "").replace("  ", " ")
                rules_applied.append(f"removed hedging: '{h}'")

        # Rule 5: Domain best practices
        domain_practices = {
            Domain.CODE: "\n\nBest practices: write tests, follow repo conventions, update documentation, commit with descriptive messages.",
            Domain.RESEARCH: "\n\nBest practices: cite sources, check multiple perspectives, note confidence level, identify knowledge gaps.",
            Domain.DEPLOY: "\n\nBest practices: verify staging, check benchmarks, ensure rollback procedure, monitor post-deploy.",
        }
        if intent.domain in domain_practices:
            enhanced += domain_practices[intent.domain]

        return enhanced

    # ── Stage 4: Runtime Compilation ───────────────────────────

    def compile(self, intent: Intent, enhanced_instruction: str) -> AgentManifest:
        """
        Compile enhanced intent into a strictly-typed agent runtime manifest.
        """
        agent_type = self._select_agent_type(intent)
        model = self._select_model(intent, enhanced_instruction)

        manifest = AgentManifest(
            agent_type=agent_type,
            model=model,
            temperature=0.2 if intent.domain != Domain.DESIGN else 0.7,
            max_parallel_tasks=3 if intent.domain == Domain.CODE else 1,
            timeout_seconds=300 if intent.urgency == Urgency.IMMEDIATE else 600,
            behavior_profile=self._select_behavior(intent),
            task_description=enhanced_instruction,
            completion_criteria=self._generate_criteria(intent),
            escalation_policy=EscalationPolicy.AUTO_PROCEED,
            tools_allow=self._default_tools(intent),
            tools_deny=["file_system:write:production"] if intent.domain != Domain.DEPLOY else [],
            memory_mode=MemoryMode.PROJECT,
            context_sources=[],
            output_format=OutputFormat.MARKDOWN,
            verification=VerificationMode.TEST if intent.domain == Domain.CODE else VerificationMode.NONE,
        )
        return manifest

    def _select_agent_type(self, intent: Intent) -> AgentType:
        mapping = {
            Domain.CODE: AgentType.BUILDER,
            Domain.RESEARCH: AgentType.RESEARCHER,
            Domain.DESIGN: AgentType.DESIGNER,
            Domain.DEPLOY: AgentType.DEPLOYER,
            Domain.DEBUG: AgentType.DEBUGGER,
            Domain.CONTENT: AgentType.BUILDER,
            Domain.SALES: AgentType.RESEARCHER,
            Domain.OPS: AgentType.DEPLOYER,
        }
        return mapping.get(intent.domain, AgentType.RESEARCHER)

    def _select_model(self, intent: Intent, enhanced: str) -> str:
        if intent.domain == Domain.RESEARCH and len(enhanced) > 2000:
            return "claude-opus-4"
        elif intent.domain == Domain.CODE and intent.urgency == Urgency.IMMEDIATE:
            return "claude-sonnet-4-6"
        elif intent.domain == Domain.DESIGN:
            return "claude-opus-4"
        return "claude-sonnet-4-6"

    def _select_behavior(self, intent: Intent) -> BehaviorProfile:
        mapping = {
            Domain.CODE: BehaviorProfile.OPERATIONAL,
            Domain.RESEARCH: BehaviorProfile.INVESTIGATIVE,
            Domain.DESIGN: BehaviorProfile.CREATIVE,
            Domain.DEBUG: BehaviorProfile.ANALYTICAL,
        }
        return mapping.get(intent.domain, BehaviorProfile.OPERATIONAL)

    def _generate_criteria(self, intent: Intent) -> list[str]:
        defaults = {
            Domain.CODE: ["All tests pass", "Code review approved", "Documentation updated"],
            Domain.RESEARCH: ["Sources cited", "Multiple perspectives considered", "Confidence levels noted"],
            Domain.DEPLOY: ["Staging verified", "Performance benchmarks met", "Monitoring active"],
        }
        return defaults.get(intent.domain, ["Task completed", "Output verified"])

    def _default_tools(self, intent: Intent) -> list[str]:
        base = ["web_search", "file_system:read"]
        if intent.domain == Domain.CODE:
            base.extend(["code_execution", "file_system:write"])
        elif intent.domain == Domain.DEPLOY:
            base.extend(["code_execution", "api:deploy"])
        return base

    # ── Stage 5: Output Routing ────────────────────────────────

    def route(self, manifest: AgentManifest) -> str:
        """
        Route the compiled manifest to the appropriate NPAO phase.

        Returns the phase name for downstream NPAO classification.
        """
        task_lower = manifest.task_description.lower()
        phase_keywords = {
            "PreD": ["research", "analyze", "investigate", "find", "explore"],
            "Design": ["design", "wireframe", "plan", "architect", "spec"],
            "Development": ["build", "implement", "code", "create", "make"],
            "Deployment": ["deploy", "ship", "release", "publish", "launch"],
            "Debugging": ["bug", "fix", "error", "broken", "crash", "debug"],
        }
        for phase, keywords in phase_keywords.items():
            if any(kw in task_lower for kw in keywords):
                manifest.routing_phase = phase
                return phase

        manifest.routing_phase = "PreD"  # Default: research first
        return "PreD"

    # ── Full Pipeline ──────────────────────────────────────────

    def compile_intent(
        self, raw_input: str, hub_context: Optional[dict] = None
    ) -> tuple[Intent, str, AgentManifest, str]:
        """
        Run the full PAL five-stage compilation pipeline.

        Returns: (Intent, EnhancedInstruction, AgentManifest, RoutedPhase)
        """
        # Stage 1: Extract
        intent = self.extract_intent(raw_input)

        # Stage 2: Inject context
        intent = self.inject_context(intent, hub_context)

        # Stage 3: Enhance
        enhanced = self.enhance(intent)

        # Stage 4: Compile
        manifest = self.compile(intent, enhanced)

        # Stage 5: Route
        phase = self.route(manifest)

        return intent, enhanced, manifest, phase


def _dict_to_yaml(d: dict, indent: int = 0) -> str:
    """Simple YAML serializer for agent manifests."""
    lines = []
    prefix = "  " * indent
    for key, value in d.items():
        if isinstance(value, dict):
            lines.append(f"{prefix}{key}:")
            lines.append(_dict_to_yaml(value, indent + 1))
        elif isinstance(value, list):
            if value:
                lines.append(f"{prefix}{key}:")
                for item in value:
                    lines.append(f"{prefix}  - {item}")
            else:
                lines.append(f"{prefix}{key}: []")
        elif isinstance(value, bool):
            lines.append(f"{prefix}{key}: {str(value).lower()}")
        else:
            lines.append(f"{prefix}{key}: {value}")
    return "\n".join(lines)
