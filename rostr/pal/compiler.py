"""
PAL Compiler — Production-Grade Prompt Abstraction Layer
=========================================================

Deterministic compilation pipeline: Natural Language -> Versioned AgentManifest.

Five modular stages:
  1. IntentExtractor   — keyword + heuristic parse into typed Intent
  2. ContextResolver   — merge session/project/org/agent context
  3. SemanticEnhancer  — expand verbs, add precision, decompose compounds
  4. ManifestCompiler  — assemble fully-typed AgentManifest
  5. ModelRouter       — select model tier based on domain/risk/urgency

No external LLM calls required. Fully deterministic and testable.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ════════════════════════════════════════════════════════════════════════════════
# SCHEMAS
# ════════════════════════════════════════════════════════════════════════════════


class Intent(BaseModel):
    """Structured intent extracted from raw natural language input."""

    primary_goal: str
    domain: str = "code"  # code, design, content, sales, debug, deploy, ops, idea
    secondary_domains: list[str] = Field(default_factory=list)
    task_type: str = "action"  # query, action, analysis, creation, modification
    subject: str = ""
    inputs: dict[str, Any] = Field(default_factory=dict)
    constraints: list[str] = Field(default_factory=list)
    desired_outputs: list[str] = Field(default_factory=list)
    target_systems: list[str] = Field(default_factory=list)
    urgency: str = "normal"  # low, normal, high, critical
    risk_level: str = "low"  # low, medium, high, critical
    ambiguity_score: float = 0.0
    field_confidence: dict[str, float] = Field(default_factory=dict)
    missing_information: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)


class ResolvedContext(BaseModel):
    """Context resolved from all available sources."""

    session_context: dict[str, Any] = Field(default_factory=dict)
    project_context: dict[str, Any] = Field(default_factory=dict)
    organization_context: dict[str, Any] = Field(default_factory=dict)
    agent_context: dict[str, Any] = Field(default_factory=dict)
    prior_decisions: list[dict[str, Any]] = Field(default_factory=list)
    prior_learnings: list[dict[str, Any]] = Field(default_factory=list)
    available_tools: list[str] = Field(default_factory=list)
    budget_limits: dict[str, Any] = Field(default_factory=dict)
    runtime_environment: str = "local"


class ModelPolicy(BaseModel):
    """Model selection and configuration policy."""

    provider: str = "anthropic"  # openai, anthropic, ollama, etc
    model: str = "claude-sonnet-4-6"
    temperature: float = 0.7
    max_tokens: int = 2048
    fallback_models: list[str] = Field(default_factory=list)
    cost_ceiling: float = 0.0  # 0 = unlimited
    latency_target_ms: int = 0  # 0 = no constraint


class ToolPolicy(BaseModel):
    """Policy governing a single tool's access and constraints."""

    tool_id: str
    allowed: bool = True
    resource_scope: list[str] = Field(default_factory=list)
    environment: str = "development"
    requires_approval: bool = False
    max_calls: int = 0  # 0 = unlimited


class AgentManifest(BaseModel):
    """Fully compiled agent runtime manifest — the output of PAL compilation."""

    manifest_version: str = "1.0"
    task_id: str = ""
    intent: Intent
    runtime: str = "local"  # local, cloud, hybrid
    model_policy: ModelPolicy = Field(default_factory=ModelPolicy)
    tool_policies: list[ToolPolicy] = Field(default_factory=list)
    memory_policy: str = "session"  # none, session, project, persistent
    execution_policy: str = "auto"  # auto, supervised, manual
    approval_policy: str = "auto"  # auto, ask, require
    output_contract: str = "markdown"  # markdown, json, code, action, structured_report
    completion_criteria: list[str] = Field(default_factory=list)
    context_sources: list[str] = Field(default_factory=list)
    budget: dict[str, Any] = Field(default_factory=dict)
    timeouts: dict[str, Any] = Field(default_factory=lambda: {"total_ms": 60000})
    retry_policy: dict[str, Any] = Field(
        default_factory=lambda: {"max_retries": 2, "backoff_ms": 1000}
    )
    observability: dict[str, Any] = Field(default_factory=lambda: {"log_level": "info"})
    routing: dict[str, Any] = Field(default_factory=dict)

    def to_json(self, indent: int = 2) -> str:
        """Serialize manifest to JSON."""
        return self.model_dump_json(indent=indent)

    def to_yaml(self) -> str:
        """Serialize manifest to YAML-like format (no PyYAML dependency)."""
        return _dict_to_yaml(self.model_dump())

    def to_dict(self) -> dict[str, Any]:
        """Serialize manifest to plain dict."""
        return self.model_dump()


# ════════════════════════════════════════════════════════════════════════════════
# STAGE 1: INTENT EXTRACTOR
# ════════════════════════════════════════════════════════════════════════════════

# Domain keyword signals (ordered by specificity)
_DOMAIN_SIGNALS: dict[str, list[str]] = {
    "deploy": [
        "deploy", "ship", "release", "publish", "launch", "push to prod",
        "go live", "roll out", "rollout", "ci/cd", "pipeline", "staging",
    ],
    "debug": [
        "bug", "fix", "error", "broken", "crash", "issue", "traceback",
        "exception", "failing", "doesn't work", "not working", "investigate",
        "root cause", "debug", "stack trace",
    ],
    "design": [
        "design", "wireframe", "ui", "ux", "layout", "style", "css",
        "figma", "mockup", "prototype", "visual", "brand", "color scheme",
        "typography", "responsive",
    ],
    "idea": [
        "brainstorm", "what if", "idea", "explore", "concept", "think about",
        "what do you think", "strategy", "vision", "blue sky",
    ],
    "content": [
        "write", "blog", "article", "content", "copy", "email", "draft",
        "newsletter", "social post", "linkedin", "twitter", "seo",
        "headline", "subject line",
    ],
    "sales": [
        "prospect", "lead", "pipeline", "outreach", "cold email", "crm",
        "hubspot", "salesforce", "deal", "close", "quota", "revenue",
        "customer", "account", "sales",
    ],
    "ops": [
        "monitor", "alert", "backup", "schedule", "cron", "infra",
        "terraform", "kubernetes", "docker", "devops", "sre", "uptime",
        "observability", "log", "metric",
    ],
    "code": [
        "code", "implement", "build", "api", "function", "class", "app",
        "refactor", "test", "module", "library", "sdk", "endpoint",
        "database", "schema", "migration", "typescript", "python", "react",
        "component", "service",
    ],
}

# Task type detection
_TASK_TYPE_SIGNALS: dict[str, list[str]] = {
    "query": [
        "what is", "how does", "explain", "describe", "tell me", "show me",
        "list", "where is", "who", "when", "why",
    ],
    "analysis": [
        "analyze", "compare", "evaluate", "assess", "audit", "review",
        "benchmark", "profile", "measure", "investigate",
    ],
    "creation": [
        "create", "build", "make", "generate", "write", "design", "draft",
        "compose", "produce", "new",
    ],
    "modification": [
        "update", "change", "modify", "edit", "refactor", "improve",
        "optimize", "enhance", "upgrade", "migrate",
    ],
    "action": [
        "deploy", "ship", "run", "execute", "send", "push", "install",
        "configure", "setup", "connect",
    ],
}

# Urgency detection
_URGENCY_SIGNALS: dict[str, list[str]] = {
    "critical": ["critical", "emergency", "p0", "production down", "outage"],
    "high": ["asap", "urgent", "immediately", "now", "right now", "blocking"],
    "normal": ["today", "soon", "when you can", "this sprint"],
    "low": ["eventually", "backlog", "nice to have", "low priority", "whenever"],
}

# Risk escalation signals
_RISK_SIGNALS: dict[str, list[str]] = {
    "critical": [
        "production", "customer data", "pii", "credentials", "secrets",
        "database migration", "delete", "drop table", "force push",
    ],
    "high": [
        "deploy", "release", "payment", "billing", "auth", "security",
        "compliance", "gdpr", "hipaa",
    ],
    "medium": [
        "refactor", "migration", "schema change", "api change", "breaking",
        "dependency update",
    ],
    "low": [
        "test", "docs", "readme", "comment", "style", "format", "lint",
        "research", "analyze",
    ],
}

# Output format detection
_OUTPUT_SIGNALS: dict[str, list[str]] = {
    "code": ["code", "implement", "function", "class", "component", "script"],
    "json": ["json", "api response", "structured data", "schema"],
    "markdown": ["report", "summary", "documentation", "readme", "blog"],
    "action": ["deploy", "ship", "send", "execute", "run", "install"],
    "structured_report": ["audit", "analysis", "comparison", "benchmark"],
}

# Desired output detection
_DESIRED_OUTPUT_SIGNALS: dict[str, list[str]] = {
    "working implementation": ["build", "implement", "create", "make"],
    "deployed feature": ["deploy", "ship", "release", "launch"],
    "research report": ["research", "analyze", "investigate", "find out"],
    "bug fix": ["fix", "debug", "resolve", "patch"],
    "design artifact": ["design", "wireframe", "mockup", "prototype"],
    "written content": ["write", "draft", "compose", "blog"],
    "configuration": ["configure", "setup", "install", "connect"],
}

# Target system detection
_TARGET_SYSTEM_SIGNALS: dict[str, list[str]] = {
    "git": ["git", "commit", "branch", "merge", "pr", "pull request"],
    "ci_cd": ["ci", "cd", "pipeline", "github actions", "vercel"],
    "database": ["database", "db", "postgres", "mysql", "mongo", "redis"],
    "cloud": ["aws", "gcp", "azure", "cloud", "s3", "lambda"],
    "crm": ["hubspot", "salesforce", "crm", "pipeline"],
    "web": ["website", "page", "frontend", "browser", "dom"],
    "api": ["api", "endpoint", "rest", "graphql", "webhook"],
}


class IntentExtractor:
    """
    Stage 1: Deterministic intent extraction using keyword patterns and heuristics.

    No LLM required. Uses weighted signal matching for domain classification,
    regex patterns for constraint extraction, and heuristic rules for confidence
    scoring.
    """

    def extract(self, raw_input: str) -> Intent:
        """Extract structured intent from raw natural language."""
        text = raw_input.strip()
        text_lower = text.lower()

        domain = self._classify_domain(text_lower)
        secondary_domains = self._find_secondary_domains(text_lower, domain)
        task_type = self._classify_task_type(text_lower)
        subject = self._extract_subject(text, text_lower)
        primary_goal = self._extract_primary_goal(text, text_lower, task_type)
        constraints = self._extract_constraints(text_lower)
        desired_outputs = self._detect_desired_outputs(text_lower)
        target_systems = self._detect_target_systems(text_lower)
        urgency = self._classify_urgency(text_lower)
        risk_level = self._classify_risk(text_lower, domain)
        inputs = self._extract_inputs(text)
        field_confidence = self._compute_field_confidence(
            text_lower, domain, subject, constraints, desired_outputs,
            target_systems, primary_goal
        )
        ambiguity_score = self._compute_ambiguity(field_confidence)
        missing_info = self._identify_missing_info(field_confidence)
        assumptions = self._generate_assumptions(
            text_lower, domain, subject, missing_info
        )

        return Intent(
            primary_goal=primary_goal,
            domain=domain,
            secondary_domains=secondary_domains,
            task_type=task_type,
            subject=subject,
            inputs=inputs,
            constraints=constraints,
            desired_outputs=desired_outputs,
            target_systems=target_systems,
            urgency=urgency,
            risk_level=risk_level,
            ambiguity_score=ambiguity_score,
            field_confidence=field_confidence,
            missing_information=missing_info,
            assumptions=assumptions,
        )

    def _classify_domain(self, text: str) -> str:
        """Classify primary domain using weighted keyword matching."""
        scores: dict[str, float] = {}
        for domain, signals in _DOMAIN_SIGNALS.items():
            score = 0.0
            for signal in signals:
                if signal in text:
                    # Multi-word signals get higher weight
                    weight = 1.0 + (signal.count(" ") * 0.5)
                    score += weight
            scores[domain] = score

        best_domain = max(scores, key=lambda k: scores[k])
        if scores[best_domain] == 0:
            return "code"  # Default domain
        return best_domain

    def _find_secondary_domains(self, text: str, primary: str) -> list[str]:
        """Find secondary domains with non-trivial signal presence."""
        secondary = []
        for domain, signals in _DOMAIN_SIGNALS.items():
            if domain == primary:
                continue
            hits = sum(1 for s in signals if s in text)
            if hits >= 2:
                secondary.append(domain)
        return secondary

    def _classify_task_type(self, text: str) -> str:
        """Classify the type of task being requested."""
        scores: dict[str, int] = {}
        for task_type, signals in _TASK_TYPE_SIGNALS.items():
            scores[task_type] = sum(1 for s in signals if s in text)
        best = max(scores, key=lambda k: scores[k])
        return best if scores[best] > 0 else "action"

    def _extract_subject(self, text: str, text_lower: str) -> str:
        """Extract the subject/object of the request."""
        # Try to extract the object after action verbs
        action_verbs = [
            "build", "create", "make", "write", "design", "fix", "debug",
            "deploy", "ship", "analyze", "research", "implement", "refactor",
            "update", "add", "remove", "configure", "setup", "test",
        ]
        for verb in action_verbs:
            # Match "verb <object>" or "verb a/an/the <object>"
            pattern = rf"\b{verb}\s+(?:a\s+|an\s+|the\s+)?(.+?)(?:\s+(?:using|with|for|in|on|to|from|that|which|and)\b|[.,;]|$)"
            match = re.search(pattern, text_lower)
            if match:
                subject = match.group(1).strip()
                if len(subject) > 2 and len(subject) < 100:
                    return subject

        # Fallback: use the core noun phrase after cleaning
        cleaned = re.sub(
            r"\b(please|can you|could you|i need|i want|help me|let's)\b",
            "", text_lower
        ).strip()
        # Take up to first 8 words after cleaning
        words = cleaned.split()[:8]
        return " ".join(words) if words else text[:50]

    def _extract_primary_goal(
        self, text: str, text_lower: str, task_type: str
    ) -> str:
        """Extract the primary goal as a concise action statement."""
        # Remove filler phrases
        goal = re.sub(
            r"^(please|can you|could you|i need you to|i want you to|help me|let's)\s+",
            "", text_lower
        ).strip()
        # Capitalize first letter
        if goal:
            goal = goal[0].upper() + goal[1:]
        # Truncate to reasonable length
        if len(goal) > 200:
            goal = goal[:200].rsplit(" ", 1)[0] + "..."
        return goal or text[:100]

    def _extract_constraints(self, text: str) -> list[str]:
        """Extract explicit and implicit constraints from the text."""
        constraints = []

        # Language/framework constraints
        techs = [
            "python", "typescript", "javascript", "react", "vue", "angular",
            "rust", "go", "java", "ruby", "swift", "kotlin", "c#", "c++",
            "node", "deno", "bun", "next.js", "nuxt", "svelte", "django",
            "flask", "fastapi", "express", "rails",
        ]
        for tech in techs:
            if tech in text:
                constraints.append(f"use {tech}")

        # Quality constraints
        if any(w in text for w in ["production", "prod-grade", "production-grade"]):
            constraints.append("production-grade")
        if any(w in text for w in ["test", "tested", "with tests"]):
            constraints.append("include tests")
        if any(w in text for w in ["fast", "quick", "minimal", "lightweight"]):
            constraints.append("keep lightweight")
        if any(w in text for w in ["secure", "security"]):
            constraints.append("security-first")
        if any(w in text for w in ["no dependencies", "zero dep"]):
            constraints.append("no external dependencies")
        if "backwards compatible" in text or "backward compatible" in text:
            constraints.append("backwards compatible")
        if any(w in text for w in ["don't break", "non-breaking"]):
            constraints.append("non-breaking change")

        # Negative constraints (things NOT to do)
        not_patterns = re.findall(r"(?:don'?t|do not|no|without|avoid)\s+(\w+(?:\s+\w+)?)", text)
        for match in not_patterns:
            if match not in ["worry", "need", "have"]:
                constraints.append(f"avoid {match}")

        return constraints

    def _detect_desired_outputs(self, text: str) -> list[str]:
        """Detect the desired output types."""
        outputs = []
        for output_type, signals in _DESIRED_OUTPUT_SIGNALS.items():
            if any(s in text for s in signals):
                outputs.append(output_type)
        return outputs if outputs else ["completed task"]

    def _detect_target_systems(self, text: str) -> list[str]:
        """Detect target systems mentioned in the text."""
        systems = []
        for system, signals in _TARGET_SYSTEM_SIGNALS.items():
            if any(s in text for s in signals):
                systems.append(system)
        return systems

    def _classify_urgency(self, text: str) -> str:
        """Classify urgency level from temporal/priority signals."""
        for level in ["critical", "high", "normal", "low"]:
            signals = _URGENCY_SIGNALS[level]
            if any(s in text for s in signals):
                return level
        return "normal"

    def _classify_risk(self, text: str, domain: str) -> str:
        """Classify risk level based on signals and domain."""
        for level in ["critical", "high", "medium", "low"]:
            signals = _RISK_SIGNALS[level]
            if any(s in text for s in signals):
                return level

        # Domain-based defaults
        domain_risk = {
            "deploy": "medium",
            "debug": "medium",
            "ops": "medium",
            "code": "low",
            "design": "low",
            "content": "low",
            "sales": "low",
            "idea": "low",
        }
        return domain_risk.get(domain, "low")

    def _extract_inputs(self, text: str) -> dict[str, Any]:
        """Extract structured inputs like file paths, URLs, names."""
        inputs: dict[str, Any] = {}

        # URLs
        urls = re.findall(r"https?://[^\s,)]+", text)
        if urls:
            inputs["urls"] = urls

        # File paths
        paths = re.findall(r"(?:/[\w./-]+|\w+/[\w./-]+)", text)
        paths = [p for p in paths if "." in p or p.count("/") > 1]
        if paths:
            inputs["paths"] = paths

        # Quoted strings (likely identifiers or names)
        quoted = re.findall(r'["\']([^"\']+)["\']', text)
        if quoted:
            inputs["references"] = quoted

        # Numbers that might be parameters
        numbers = re.findall(r"\b(\d+(?:\.\d+)?)\s*(?:ms|sec|min|mb|gb|%)", text)
        if numbers:
            inputs["numeric_params"] = numbers

        return inputs

    def _compute_field_confidence(
        self,
        text: str,
        domain: str,
        subject: str,
        constraints: list[str],
        desired_outputs: list[str],
        target_systems: list[str],
        primary_goal: str,
    ) -> dict[str, float]:
        """
        Compute confidence for each extracted field.
        Score 0.0-1.0 based on signal strength and specificity.
        """
        confidence: dict[str, float] = {}

        # Goal confidence: based on action verb clarity
        goal_verbs = [
            "build", "create", "fix", "deploy", "write", "design",
            "analyze", "research", "configure", "test",
        ]
        has_clear_verb = any(v in text for v in goal_verbs)
        confidence["goal"] = 0.9 if has_clear_verb else 0.4

        # Domain confidence: based on signal count
        domain_signals = _DOMAIN_SIGNALS.get(domain, [])
        domain_hits = sum(1 for s in domain_signals if s in text)
        confidence["scope"] = min(1.0, domain_hits * 0.3)

        # Subject confidence
        confidence["inputs"] = 0.8 if len(subject) > 5 else 0.3

        # Constraints confidence
        confidence["constraints"] = min(1.0, len(constraints) * 0.3) if constraints else 0.2

        # Output confidence
        confidence["output"] = 0.8 if desired_outputs != ["completed task"] else 0.3

        # Target system confidence
        confidence["target_system"] = 0.9 if target_systems else 0.2

        # Completion criteria (inferred from specificity of request)
        word_count = len(text.split())
        confidence["completion_criteria"] = min(1.0, word_count / 30.0)

        # Risk confidence (always moderately confident since we have heuristics)
        confidence["risk"] = 0.7

        # Approval confidence
        confidence["approval"] = 0.6

        return confidence

    def _compute_ambiguity(self, field_confidence: dict[str, float]) -> float:
        """
        Compute overall ambiguity score as inverse of mean field confidence.
        0.0 = perfectly clear, 1.0 = maximally ambiguous.
        """
        if not field_confidence:
            return 1.0
        mean_confidence = sum(field_confidence.values()) / len(field_confidence)
        return round(1.0 - mean_confidence, 3)

    def _identify_missing_info(
        self, field_confidence: dict[str, float]
    ) -> list[str]:
        """Identify fields with low confidence that indicate missing info."""
        missing = []
        labels = {
            "goal": "clear primary goal",
            "scope": "specific scope/domain",
            "inputs": "input data or references",
            "constraints": "explicit constraints or requirements",
            "output": "expected output format",
            "target_system": "target system or platform",
            "completion_criteria": "success/completion criteria",
            "risk": "risk assessment context",
            "approval": "approval requirements",
        }
        for field_name, conf in field_confidence.items():
            if conf < 0.4:
                label = labels.get(field_name, field_name)
                missing.append(label)
        return missing

    def _generate_assumptions(
        self, text: str, domain: str, subject: str, missing: list[str]
    ) -> list[str]:
        """Generate explicit assumptions for missing information."""
        assumptions = []
        if "clear primary goal" in missing:
            assumptions.append(f"Assumed domain: {domain}")
        if "input data or references" in missing:
            assumptions.append(f"Assumed subject refers to: {subject}")
        if "explicit constraints or requirements" in missing:
            assumptions.append("Assumed no special constraints apply")
        if "target system or platform" in missing:
            assumptions.append("Assumed local development environment")
        return assumptions


# ════════════════════════════════════════════════════════════════════════════════
# STAGE 2: CONTEXT RESOLVER
# ════════════════════════════════════════════════════════════════════════════════


class ContextResolver:
    """
    Stage 2: Resolve and merge context from all available sources.

    Sources (priority order):
      1. Session context (current conversation state)
      2. Project context (CLAUDE.md, package.json, etc.)
      3. Organization context (team, tools, policies)
      4. Agent context (capabilities, history)
    """

    def __init__(
        self,
        session_context: Optional[dict[str, Any]] = None,
        project_context: Optional[dict[str, Any]] = None,
        organization_context: Optional[dict[str, Any]] = None,
        agent_context: Optional[dict[str, Any]] = None,
    ):
        self._session = session_context or {}
        self._project = project_context or {}
        self._organization = organization_context or {}
        self._agent = agent_context or {}

    def resolve(self, intent: Intent) -> ResolvedContext:
        """Resolve context relevant to the given intent."""
        available_tools = self._resolve_tools(intent)
        budget_limits = self._resolve_budget(intent)
        runtime = self._resolve_runtime(intent)

        return ResolvedContext(
            session_context=self._session,
            project_context=self._project,
            organization_context=self._organization,
            agent_context=self._agent,
            prior_decisions=self._session.get("prior_decisions", []),
            prior_learnings=self._session.get("prior_learnings", []),
            available_tools=available_tools,
            budget_limits=budget_limits,
            runtime_environment=runtime,
        )

    def _resolve_tools(self, intent: Intent) -> list[str]:
        """Determine which tools are available for this intent's domain."""
        base_tools = ["web_search", "file_read"]
        domain_tools: dict[str, list[str]] = {
            "code": ["code_execution", "file_write", "git", "test_runner"],
            "deploy": ["code_execution", "file_write", "git", "deploy_api", "monitoring"],
            "debug": ["code_execution", "file_read", "git", "test_runner", "profiler"],
            "design": ["file_write", "browser", "screenshot"],
            "ops": ["code_execution", "monitoring", "alerting", "infra_api"],
            "content": ["file_write", "web_search"],
            "sales": ["crm_api", "web_search", "email_api"],
            "idea": ["web_search", "file_write"],
        }
        extra = domain_tools.get(intent.domain, [])
        return base_tools + extra

    def _resolve_budget(self, intent: Intent) -> dict[str, Any]:
        """Resolve budget constraints based on context."""
        org_budget = self._organization.get("budget", {})
        if org_budget:
            return org_budget
        # Default budget tiers
        if intent.risk_level in ("critical", "high"):
            return {"max_cost_usd": 5.0, "max_tokens": 100000}
        return {"max_cost_usd": 1.0, "max_tokens": 50000}

    def _resolve_runtime(self, intent: Intent) -> str:
        """Determine runtime environment."""
        if intent.domain == "deploy":
            return "cloud"
        if intent.risk_level == "critical":
            return "hybrid"
        return self._project.get("runtime", "local")


# ════════════════════════════════════════════════════════════════════════════════
# STAGE 3: SEMANTIC ENHANCER
# ════════════════════════════════════════════════════════════════════════════════


class SemanticEnhancer:
    """
    Stage 3: Enhance the extracted intent with precision and specificity.

    Applies deterministic transformation rules:
      1. Expand ambiguous verbs into precise action sequences
      2. Decompose compound goals into ordered subtasks
      3. Remove hedging language
      4. Inject domain best practices
      5. Add completion criteria when missing
    """

    # Verb expansion rules
    _VERB_EXPANSIONS: dict[str, str] = {
        "improve": "identify top issues by severity, propose specific fix for each, implement",
        "check": "verify correctness, flag anomalies, report status with evidence",
        "review": "audit against best practices, score each criterion, recommend actionable fixes",
        "optimize": "profile performance, identify bottlenecks, implement targeted improvements, measure impact",
        "clean up": "identify dead code and inconsistencies, refactor for clarity, verify behavior unchanged",
        "look at": "inspect current state, identify issues, report findings",
        "handle": "implement complete error handling, edge cases, and recovery paths",
        "set up": "install dependencies, configure environment, verify connectivity, document setup",
    }

    # Domain best practices injection
    _DOMAIN_PRACTICES: dict[str, list[str]] = {
        "code": [
            "follow existing code conventions",
            "include unit tests",
            "update relevant documentation",
            "ensure backwards compatibility where possible",
        ],
        "deploy": [
            "verify in staging first",
            "check performance benchmarks",
            "ensure rollback procedure exists",
            "monitor post-deploy metrics",
        ],
        "debug": [
            "reproduce the issue first",
            "identify root cause (not just symptoms)",
            "verify fix doesn't introduce regressions",
            "add test to prevent recurrence",
        ],
        "design": [
            "consider accessibility (WCAG 2.1 AA)",
            "ensure responsive behavior",
            "maintain visual consistency with existing system",
            "document design decisions",
        ],
        "content": [
            "match brand voice and tone",
            "optimize for target audience",
            "include clear call-to-action",
            "verify factual accuracy",
        ],
        "sales": [
            "personalize to prospect's context",
            "lead with value, not features",
            "include social proof where possible",
            "clear next step / CTA",
        ],
    }

    # Hedging phrases to remove
    _HEDGES: list[str] = [
        "maybe", "perhaps", "if you have time", "it would be nice",
        "whenever you get a chance", "no rush", "if possible",
        "kind of", "sort of", "I think", "I guess",
    ]

    def enhance(self, intent: Intent, context: ResolvedContext) -> Intent:
        """Apply all enhancement rules to the intent."""
        enhanced = intent.model_copy(deep=True)

        # Rule 1: Expand ambiguous verbs in primary goal
        enhanced.primary_goal = self._expand_verbs(enhanced.primary_goal)

        # Rule 2: Decompose compound goals
        if self._is_compound(enhanced.primary_goal):
            enhanced.primary_goal = self._decompose_compound(enhanced.primary_goal)

        # Rule 3: Remove hedging
        enhanced.primary_goal = self._remove_hedging(enhanced.primary_goal)

        # Rule 4: Inject domain best practices into constraints
        practices = self._DOMAIN_PRACTICES.get(enhanced.domain, [])
        for practice in practices:
            if practice not in enhanced.constraints:
                enhanced.constraints.append(practice)

        # Rule 5: Add completion criteria if outputs are generic
        if enhanced.desired_outputs == ["completed task"]:
            enhanced.desired_outputs = self._infer_outputs(enhanced.domain, enhanced.task_type)

        return enhanced

    def _expand_verbs(self, text: str) -> str:
        """Expand ambiguous verbs into precise instructions."""
        text_lower = text.lower()
        for vague, precise in self._VERB_EXPANSIONS.items():
            if vague in text_lower:
                # Replace the vague verb with the expansion
                text = re.sub(
                    rf"\b{re.escape(vague)}\b",
                    precise,
                    text,
                    count=1,
                    flags=re.IGNORECASE,
                )
        return text

    def _is_compound(self, text: str) -> bool:
        """Detect if a goal contains multiple independent tasks."""
        compound_signals = [" and ", " then ", " also ", " plus ", " as well as "]
        return any(s in text.lower() for s in compound_signals)

    def _decompose_compound(self, text: str) -> str:
        """Decompose compound goal into ordered phases."""
        # Split on compound connectors
        parts = re.split(
            r"\s+(?:and then|then|and also|and|plus|as well as)\s+",
            text,
            flags=re.IGNORECASE,
        )
        if len(parts) <= 1:
            return text
        steps = [f"Phase {i+1}: {p.strip()}" for i, p in enumerate(parts)]
        return " -> ".join(steps)

    def _remove_hedging(self, text: str) -> str:
        """Remove hedging language for directness."""
        for hedge in self._HEDGES:
            text = re.sub(
                rf"\b{re.escape(hedge)}\b,?\s*",
                "",
                text,
                flags=re.IGNORECASE,
            )
        return text.strip()

    def _infer_outputs(self, domain: str, task_type: str) -> list[str]:
        """Infer desired outputs from domain and task type."""
        outputs_map: dict[str, dict[str, list[str]]] = {
            "code": {
                "creation": ["working implementation", "passing tests"],
                "modification": ["updated code", "passing tests"],
                "analysis": ["code analysis report"],
                "action": ["executed action", "verification"],
            },
            "deploy": {
                "action": ["successful deployment", "health check passing"],
            },
            "debug": {
                "action": ["bug fix", "regression test"],
                "analysis": ["root cause analysis"],
            },
            "design": {
                "creation": ["design artifact", "documentation"],
            },
            "content": {
                "creation": ["written content", "review-ready draft"],
            },
            "sales": {
                "creation": ["outreach copy", "personalized messaging"],
                "analysis": ["prospect research report"],
            },
        }
        domain_outputs = outputs_map.get(domain, {})
        return domain_outputs.get(task_type, ["completed task"])


# ════════════════════════════════════════════════════════════════════════════════
# STAGE 4: MANIFEST COMPILER
# ════════════════════════════════════════════════════════════════════════════════


class ManifestCompiler:
    """
    Stage 4: Compile enhanced intent + context into a versioned AgentManifest.
    """

    def compile(
        self,
        intent: Intent,
        context: ResolvedContext,
        model_policy: ModelPolicy,
    ) -> AgentManifest:
        """Compile all inputs into a final AgentManifest."""
        task_id = self._generate_task_id(intent)
        tool_policies = self._generate_tool_policies(intent, context)
        memory_policy = self._select_memory_policy(intent)
        execution_policy = self._select_execution_policy(intent)
        approval_policy = self._select_approval_policy(intent)
        output_contract = self._select_output_contract(intent)
        completion_criteria = self._generate_completion_criteria(intent)
        timeouts = self._compute_timeouts(intent)
        routing = self._compute_routing(intent)

        return AgentManifest(
            manifest_version="1.0",
            task_id=task_id,
            intent=intent,
            runtime=context.runtime_environment,
            model_policy=model_policy,
            tool_policies=tool_policies,
            memory_policy=memory_policy,
            execution_policy=execution_policy,
            approval_policy=approval_policy,
            output_contract=output_contract,
            completion_criteria=completion_criteria,
            context_sources=self._determine_context_sources(intent, context),
            budget=context.budget_limits,
            timeouts=timeouts,
            retry_policy=self._compute_retry_policy(intent),
            observability=self._compute_observability(intent),
            routing=routing,
        )

    def _generate_task_id(self, intent: Intent) -> str:
        """Generate a deterministic task ID from intent content."""
        content = f"{intent.domain}:{intent.primary_goal}:{intent.subject}"
        hash_val = hashlib.sha256(content.encode()).hexdigest()[:12]
        return f"pal-{intent.domain}-{hash_val}"

    def _generate_tool_policies(
        self, intent: Intent, context: ResolvedContext
    ) -> list[ToolPolicy]:
        """Generate tool policies based on intent and context."""
        policies: list[ToolPolicy] = []
        available = context.available_tools

        for tool_id in available:
            requires_approval = False
            environment = "development"

            # High-risk tools need approval in certain contexts
            if intent.risk_level in ("critical", "high"):
                if tool_id in ("deploy_api", "infra_api", "file_write"):
                    requires_approval = True

            # Deploy domain uses production environment
            if intent.domain == "deploy":
                environment = "production"

            # Restrict write tools for analysis/query tasks
            allowed = True
            if intent.task_type in ("query", "analysis"):
                if tool_id in ("file_write", "deploy_api", "infra_api"):
                    allowed = False

            policies.append(
                ToolPolicy(
                    tool_id=tool_id,
                    allowed=allowed,
                    resource_scope=self._tool_resource_scope(tool_id, intent),
                    environment=environment,
                    requires_approval=requires_approval,
                    max_calls=0,  # unlimited by default
                )
            )

        return policies

    def _tool_resource_scope(self, tool_id: str, intent: Intent) -> list[str]:
        """Determine resource scope for a given tool."""
        if tool_id == "file_write":
            # Scope writes to project directory only
            return ["project_root/**"]
        if tool_id == "git":
            return ["current_branch"]
        if tool_id == "deploy_api":
            if intent.risk_level == "critical":
                return ["staging_only"]
            return ["staging", "production"]
        return ["*"]

    def _select_memory_policy(self, intent: Intent) -> str:
        """Select memory policy based on task scope."""
        if intent.domain in ("idea", "content"):
            return "session"
        if intent.risk_level in ("critical", "high"):
            return "persistent"
        if intent.domain in ("code", "deploy", "debug"):
            return "project"
        return "session"

    def _select_execution_policy(self, intent: Intent) -> str:
        """Select execution policy based on risk and urgency."""
        if intent.risk_level == "critical":
            return "supervised"
        if intent.risk_level == "high" and intent.urgency != "critical":
            return "supervised"
        return "auto"

    def _select_approval_policy(self, intent: Intent) -> str:
        """Select approval policy based on risk level."""
        if intent.risk_level == "critical":
            return "require"
        if intent.risk_level == "high":
            return "ask"
        return "auto"

    def _select_output_contract(self, intent: Intent) -> str:
        """Select output format based on intent signals."""
        text = intent.primary_goal.lower()
        for format_type, signals in _OUTPUT_SIGNALS.items():
            if any(s in text for s in signals):
                return format_type
        # Domain-based defaults
        domain_defaults = {
            "code": "code",
            "deploy": "action",
            "debug": "code",
            "design": "markdown",
            "content": "markdown",
            "sales": "markdown",
            "ops": "action",
            "idea": "markdown",
        }
        return domain_defaults.get(intent.domain, "markdown")

    def _generate_completion_criteria(self, intent: Intent) -> list[str]:
        """Generate explicit completion criteria."""
        criteria: list[str] = []

        domain_criteria: dict[str, list[str]] = {
            "code": ["Implementation complete", "Tests passing", "No lint errors"],
            "deploy": ["Deployment successful", "Health checks passing", "Monitoring active"],
            "debug": ["Root cause identified", "Fix implemented", "Regression test added"],
            "design": ["Design artifact produced", "Accessibility verified", "Responsive behavior confirmed"],
            "content": ["Content drafted", "Tone and voice consistent", "CTA present"],
            "sales": ["Personalized to prospect", "Value proposition clear", "CTA included"],
            "ops": ["Configuration applied", "Health verified", "Alerts configured"],
            "idea": ["Concept articulated", "Feasibility assessed", "Next steps identified"],
        }
        criteria = domain_criteria.get(intent.domain, ["Task completed"])

        # Add risk-specific criteria
        if intent.risk_level in ("critical", "high"):
            criteria.append("Rollback plan documented")
            criteria.append("Peer review completed")

        return criteria

    def _compute_timeouts(self, intent: Intent) -> dict[str, Any]:
        """Compute timeout configuration."""
        base_ms = 60000  # 1 minute default

        if intent.urgency == "critical":
            base_ms = 30000
        elif intent.urgency == "high":
            base_ms = 45000
        elif intent.domain in ("code", "deploy"):
            base_ms = 120000  # 2 minutes for complex tasks
        elif intent.domain == "idea":
            base_ms = 180000  # 3 minutes for exploration

        return {
            "total_ms": base_ms,
            "per_tool_ms": min(base_ms // 2, 30000),
            "idle_ms": 10000,
        }

    def _compute_retry_policy(self, intent: Intent) -> dict[str, Any]:
        """Compute retry policy based on risk and urgency."""
        if intent.risk_level == "critical":
            return {"max_retries": 1, "backoff_ms": 2000}
        if intent.urgency in ("critical", "high"):
            return {"max_retries": 3, "backoff_ms": 500}
        return {"max_retries": 2, "backoff_ms": 1000}

    def _compute_observability(self, intent: Intent) -> dict[str, Any]:
        """Compute observability settings."""
        if intent.risk_level in ("critical", "high"):
            return {"log_level": "debug", "trace": True, "metrics": True}
        return {"log_level": "info", "trace": False, "metrics": False}

    def _compute_routing(self, intent: Intent) -> dict[str, Any]:
        """Compute routing metadata for downstream orchestrators."""
        phase_map = {
            "idea": "pre-development",
            "design": "design",
            "code": "development",
            "debug": "development",
            "deploy": "deployment",
            "ops": "operations",
            "content": "pre-development",
            "sales": "pre-development",
        }
        return {
            "phase": phase_map.get(intent.domain, "development"),
            "domain": intent.domain,
            "priority": _urgency_to_priority(intent.urgency),
        }

    def _determine_context_sources(
        self, intent: Intent, context: ResolvedContext
    ) -> list[str]:
        """Determine which context sources to include in the manifest."""
        sources = []
        if context.session_context:
            sources.append("session")
        if context.project_context:
            sources.append("project")
        if context.organization_context:
            sources.append("organization")
        if context.prior_decisions:
            sources.append("prior_decisions")
        if context.prior_learnings:
            sources.append("prior_learnings")
        return sources


# ════════════════════════════════════════════════════════════════════════════════
# STAGE 5: MODEL ROUTER
# ════════════════════════════════════════════════════════════════════════════════


class ModelRouter:
    """
    Stage 5: Select optimal model configuration based on domain, complexity,
    risk, and urgency.

    Routing rules:
      - code/debug + high risk       -> opus tier, temp 0.1
      - design/idea                  -> opus tier, temp 0.7-0.9
      - content/sales                -> sonnet tier, temp 0.6-0.8
      - ops/deploy + low risk        -> haiku tier, temp 0.1-0.3
      - High urgency                 -> fastest available model
    """

    # Model tier definitions
    OPUS_TIER = "claude-opus-4"
    SONNET_TIER = "claude-sonnet-4-6"
    HAIKU_TIER = "claude-haiku-3-5"

    # Fallback chains
    _FALLBACK_CHAINS: dict[str, list[str]] = {
        OPUS_TIER: ["claude-sonnet-4-6", "claude-haiku-3-5"],
        SONNET_TIER: ["claude-haiku-3-5", "claude-opus-4"],
        HAIKU_TIER: ["claude-sonnet-4-6", "claude-opus-4"],
    }

    def route(self, intent: Intent, context: ResolvedContext) -> ModelPolicy:
        """Select model policy based on intent characteristics."""
        model, temperature = self._select_model_and_temp(intent)
        max_tokens = self._select_max_tokens(intent)
        fallbacks = self._FALLBACK_CHAINS.get(model, [])
        cost_ceiling = self._compute_cost_ceiling(intent, context)
        latency_target = self._compute_latency_target(intent)

        return ModelPolicy(
            provider="anthropic",
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            fallback_models=fallbacks,
            cost_ceiling=cost_ceiling,
            latency_target_ms=latency_target,
        )

    def _select_model_and_temp(self, intent: Intent) -> tuple[str, float]:
        """Core routing logic: domain + risk + urgency -> model + temperature."""

        # Rule: High urgency -> fastest model regardless of other factors
        if intent.urgency == "critical":
            return self.HAIKU_TIER, 0.2

        # Rule: code/debug + high/critical risk -> opus, low temp
        if intent.domain in ("code", "debug") and intent.risk_level in ("critical", "high"):
            return self.OPUS_TIER, 0.1

        # Rule: design/idea -> opus, high temp (creative)
        if intent.domain in ("design", "idea"):
            temp = 0.9 if intent.domain == "idea" else 0.7
            return self.OPUS_TIER, temp

        # Rule: content/sales -> sonnet, moderate temp
        if intent.domain in ("content", "sales"):
            temp = 0.7 if intent.domain == "content" else 0.6
            return self.SONNET_TIER, temp

        # Rule: ops/deploy + low risk -> haiku, low temp
        if intent.domain in ("ops", "deploy") and intent.risk_level == "low":
            return self.HAIKU_TIER, 0.2

        # Rule: ops/deploy + medium/high risk -> sonnet, low temp
        if intent.domain in ("ops", "deploy"):
            return self.SONNET_TIER, 0.2

        # Rule: code/debug + low/medium risk -> sonnet
        if intent.domain in ("code", "debug"):
            return self.SONNET_TIER, 0.2

        # Default: sonnet tier
        return self.SONNET_TIER, 0.5

    def _select_max_tokens(self, intent: Intent) -> int:
        """Select max tokens based on expected output size."""
        if intent.domain in ("code", "debug"):
            return 4096
        if intent.domain in ("content", "sales"):
            return 2048
        if intent.domain in ("idea", "design"):
            return 3072
        if intent.domain in ("ops", "deploy"):
            return 1024
        return 2048

    def _compute_cost_ceiling(
        self, intent: Intent, context: ResolvedContext
    ) -> float:
        """Compute cost ceiling from context budget limits."""
        budget = context.budget_limits
        if "max_cost_usd" in budget:
            return budget["max_cost_usd"]
        # Default ceilings by risk
        risk_ceilings = {
            "critical": 10.0,
            "high": 5.0,
            "medium": 2.0,
            "low": 1.0,
        }
        return risk_ceilings.get(intent.risk_level, 1.0)

    def _compute_latency_target(self, intent: Intent) -> int:
        """Compute latency target in ms."""
        if intent.urgency == "critical":
            return 5000
        if intent.urgency == "high":
            return 10000
        if intent.urgency == "normal":
            return 30000
        return 0  # No constraint for low urgency


# ════════════════════════════════════════════════════════════════════════════════
# PAL COMPILER (FULL PIPELINE)
# ════════════════════════════════════════════════════════════════════════════════


class PALCompiler:
    """
    PAL — Prompt Abstraction Layer Compiler.

    Orchestrates the five-stage compilation pipeline:
      1. IntentExtractor   -> Intent
      2. ContextResolver   -> ResolvedContext
      3. SemanticEnhancer  -> Enhanced Intent
      4. ModelRouter       -> ModelPolicy
      5. ManifestCompiler  -> AgentManifest

    Usage:
        compiler = PALCompiler()
        manifest = compiler.compile("Build a REST API with authentication")
        print(manifest.to_json())
    """

    def __init__(
        self,
        session_context: Optional[dict[str, Any]] = None,
        project_context: Optional[dict[str, Any]] = None,
        organization_context: Optional[dict[str, Any]] = None,
        agent_context: Optional[dict[str, Any]] = None,
    ):
        self.extractor = IntentExtractor()
        self.context_resolver = ContextResolver(
            session_context=session_context,
            project_context=project_context,
            organization_context=organization_context,
            agent_context=agent_context,
        )
        self.enhancer = SemanticEnhancer()
        self.router = ModelRouter()
        self.manifest_compiler = ManifestCompiler()

    def compile(self, raw_input: str) -> AgentManifest:
        """
        Full compilation pipeline: raw text -> AgentManifest.

        This is the primary entry point for the PAL compiler.
        """
        # Stage 1: Extract intent
        intent = self.extractor.extract(raw_input)

        # Stage 2: Resolve context
        context = self.context_resolver.resolve(intent)

        # Stage 3: Semantic enhancement
        enhanced_intent = self.enhancer.enhance(intent, context)

        # Stage 4: Model routing
        model_policy = self.router.route(enhanced_intent, context)

        # Stage 5: Compile manifest
        manifest = self.manifest_compiler.compile(
            enhanced_intent, context, model_policy
        )

        return manifest

    def compile_with_stages(
        self, raw_input: str
    ) -> tuple[Intent, ResolvedContext, Intent, ModelPolicy, AgentManifest]:
        """
        Full pipeline returning all intermediate stages for debugging/inspection.

        Returns:
            (raw_intent, context, enhanced_intent, model_policy, manifest)
        """
        # Stage 1
        intent = self.extractor.extract(raw_input)

        # Stage 2
        context = self.context_resolver.resolve(intent)

        # Stage 3
        enhanced_intent = self.enhancer.enhance(intent, context)

        # Stage 4
        model_policy = self.router.route(enhanced_intent, context)

        # Stage 5
        manifest = self.manifest_compiler.compile(
            enhanced_intent, context, model_policy
        )

        return intent, context, enhanced_intent, model_policy, manifest


# ════════════════════════════════════════════════════════════════════════════════
# UTILITIES
# ════════════════════════════════════════════════════════════════════════════════


def _urgency_to_priority(urgency: str) -> int:
    """Convert urgency string to numeric priority (lower = higher priority)."""
    mapping = {"critical": 0, "high": 1, "normal": 2, "low": 3}
    return mapping.get(urgency, 2)


def _dict_to_yaml(d: dict[str, Any], indent: int = 0) -> str:
    """Simple YAML serializer (no PyYAML dependency required)."""
    lines: list[str] = []
    prefix = "  " * indent
    for key, value in d.items():
        if isinstance(value, dict):
            if value:
                lines.append(f"{prefix}{key}:")
                lines.append(_dict_to_yaml(value, indent + 1))
            else:
                lines.append(f"{prefix}{key}: {{}}")
        elif isinstance(value, list):
            if value:
                lines.append(f"{prefix}{key}:")
                for item in value:
                    if isinstance(item, dict):
                        lines.append(f"{prefix}  -")
                        lines.append(_dict_to_yaml(item, indent + 2))
                    else:
                        lines.append(f"{prefix}  - {item}")
            else:
                lines.append(f"{prefix}{key}: []")
        elif isinstance(value, bool):
            lines.append(f"{prefix}{key}: {str(value).lower()}")
        elif value is None:
            lines.append(f"{prefix}{key}: null")
        elif isinstance(value, (int, float)):
            lines.append(f"{prefix}{key}: {value}")
        else:
            # String value — quote if it contains special chars
            val_str = str(value)
            if any(c in val_str for c in ":#{}[]|>&*!%@"):
                lines.append(f'{prefix}{key}: "{val_str}"')
            else:
                lines.append(f"{prefix}{key}: {val_str}")
    return "\n".join(lines)
