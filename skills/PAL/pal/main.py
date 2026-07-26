#!/usr/bin/env python3
"""
PAL — Prompt Abstraction Layer

5-stage compilation pipeline:
1. Intent Extraction — Parse raw input for goal, domain, subject, constraints
2. Context Injection — Pull relevant context (CLAUDE.md, prefs, codebase, memory)
3. Prompt Enhancement — Rewrite with precision, inject knowledge
4. Compilation — Generate typed AgentManifest JSON
5. Routing — Route to appropriate LLM + MCPs

Usage:
    pal = PAL(claude_md_path=".claude/CLAUDE.md", memory_path=".claude/projects/memory.md")
    manifest = pal.compile("make a basketball site for my school")
    print(json.dumps(manifest, indent=2))
"""

import json
import os
import re
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
import logging

try:
    from pydantic import BaseModel, Field
except ImportError:
    BaseModel = object
    Field = lambda **kwargs: None

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Domain(str, Enum):
    CODE = "code"
    DESIGN = "design"
    CONTENT = "content"
    SALES = "sales"
    OPS = "ops"
    IDEA = "idea"
    DEBUG = "debug"
    DEPLOY = "deploy"


class Model(str, Enum):
    CLAUDE_OPUS = "claude-opus"
    CLAUDE_SONNET = "claude-sonnet"
    CLAUDE_HAIKU = "claude-haiku"
    GPT_4 = "gpt-4"
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_3_5_TURBO = "gpt-3.5-turbo"
    OLLAMA_LOCAL = "ollama-local"


class Behavior(str, Enum):
    AUTO_APPROVE = "auto-approve"
    ASK = "ask"
    REPORT_ONLY = "report-only"
    GUARD = "guard"


# Intent routing table from CLAUDE.md (order matters - most specific first)
INTENT_ROUTING = [
    # Signals → (domain, suggested_model, suggested_tools)
    (r"review my code|check the diff|pre-pr|code review", Domain.CODE, Model.CLAUDE_OPUS, ["review"]),
    (r"why is.*failing|debug|investigate|root cause", Domain.DEBUG, Model.CLAUDE_OPUS, ["investigate"]),
    (r"find and fix bugs|qa|test this|broken|doesn't work|find issues", Domain.DEBUG, Model.CLAUDE_SONNET, ["qa"]),
    (r"ship|push|create pr|deploy and verify|deploy to", Domain.DEPLOY, Model.CLAUDE_SONNET, ["ship"]),
    (r"merge|land|deploy", Domain.DEPLOY, Model.CLAUDE_SONNET, ["land-and-deploy"]),
    (r"build.*website|build.*site|make.*site|basketball site", Domain.DESIGN, Model.CLAUDE_OPUS, ["design-html"]),
    (r"build the page|finalize the design|make it real|html|css", Domain.DESIGN, Model.CLAUDE_SONNET, ["design-html"]),
    (r"design consultation|brand system|design language|show me options", Domain.DESIGN, Model.CLAUDE_OPUS, ["design-shotgun"]),
    (r"verify|inspect|looking at|checking|open|go to|what does.*look like", Domain.DESIGN, Model.CLAUDE_HAIKU, ["browse"]),
    (r"does this look right|visual bugs|spacing issues", Domain.DESIGN, Model.CLAUDE_SONNET, ["design-review"]),
    (r"audit only|just report|don't fix|what's wrong with", Domain.DEBUG, Model.CLAUDE_HAIKU, ["qa-only"]),
    (r"architecture|engineering lens|plan review", Domain.CODE, Model.CLAUDE_OPUS, ["plan-eng-review"]),
    (r"think bigger|10x version|ceo lens|strategic", Domain.IDEA, Model.CLAUDE_OPUS, ["plan-ceo-review"]),
    (r"idea|what do you think|help me think|brainstorm", Domain.IDEA, Model.CLAUDE_OPUS, ["office-hours"]),
    (r"performance|how fast|page speed|load time", Domain.CODE, Model.CLAUDE_SONNET, ["benchmark"]),
    (r"security|vulnerabilities|pentest", Domain.CODE, Model.CLAUDE_OPUS, ["cso"]),
    (r"health check|how clean|quality score|codebase", Domain.CODE, Model.CLAUDE_SONNET, ["health"]),
    (r"retro|what did we ship|weekly review", Domain.OPS, Model.CLAUDE_SONNET, ["retro"]),
    (r"update the docs|sync docs|documentation", Domain.CONTENT, Model.CLAUDE_SONNET, ["document-release"]),
    (r"prospect|outreach|sales|email|cold call|atlas|eor|hiring", Domain.SALES, Model.CLAUDE_SONNET, ["rfp-answer-retriever"]),
    (r"content|blog|social|copy|marketing|write", Domain.CONTENT, Model.CLAUDE_SONNET, ["design-html"]),
]

SKILL_MAPPINGS = {
    "browse": ["web-search"],
    "qa": ["browser-automation"],
    "qa-only": ["browser-automation"],
    "review": ["code-analysis"],
    "ship": ["git-commands"],
    "land-and-deploy": ["git-commands", "deployment"],
    "investigate": ["debugging-tools"],
    "office-hours": ["reasoning"],
    "plan-ceo-review": ["reasoning"],
    "plan-eng-review": ["code-analysis"],
    "design-review": ["visual-analysis"],
    "design-shotgun": ["generative-design"],
    "design-html": ["code-generation"],
    "design-consultation": ["design-reasoning"],
    "benchmark": ["performance-analysis"],
    "cso": ["security-analysis"],
    "health": ["code-analysis"],
    "retro": ["analytics"],
    "document-release": ["code-generation"],
    "rfp-answer-retriever": ["semantic-search"],
}

TEMPERATURE_BY_TASK = {
    Domain.CODE: 0.1,  # Deterministic
    Domain.DEBUG: 0.1,  # Deterministic
    Domain.DESIGN: 0.7,  # Creative
    Domain.CONTENT: 0.8,  # Creative
    Domain.SALES: 0.6,  # Balanced
    Domain.OPS: 0.3,  # Analytical
    Domain.IDEA: 0.9,  # Very creative
    Domain.DEPLOY: 0.1,  # Deterministic
}


class Intent:
    """Stage 1: Extract intent from raw request."""

    def __init__(self, raw_request: str):
        self.raw = raw_request
        self.goal = None
        self.domain = None
        self.subject = None
        self.constraints = []
        self.output_format = None

    def extract(self) -> Dict[str, Any]:
        """Extract intent from raw request using NLP heuristics."""
        text = self.raw.lower()

        # Extract constraints
        if "no fix" in text or "report only" in text or "audit only" in text:
            self.constraints.append("report-only")
        if "just" in text and ("frontend" in text or "backend" in text):
            self.constraints.append(f"scope-limited-{self._extract_scope()}")
        if "don't break" in text or "be careful" in text:
            self.constraints.append("safety-mode")

        # Extract output format (check specific patterns first)
        if "screenshot" in text or "show me what" in text or "what it looks like" in text:
            self.output_format = "screenshot"
        elif "pr" in text or "pull request" in text or "create pr" in text:
            self.output_format = "pr"
        elif "file" in text or "page" in text and ("write" in text or "build" in text):
            self.output_format = "file"
        elif "analysis" in text or "report" in text:
            self.output_format = "analysis"
        elif "draft" in text:
            self.output_format = "draft"
        elif "plan" in text or "planning" in text:
            self.output_format = "plan"
        elif "code" in text or "write" in text:
            self.output_format = "file"

        # Route to domain using intent table
        self.domain = self._route_domain(text)
        self.goal = self.raw  # Use raw as goal until enhancement stage

        # Extract subject
        self.subject = self._extract_subject(text)

        return {
            "goal": self.goal,
            "domain": self.domain,
            "subject": self.subject,
            "constraints": self.constraints,
            "output_format": self.output_format,
        }

    def _route_domain(self, text: str) -> str:
        """Match text against intent routing table."""
        for pattern, domain, _, _ in INTENT_ROUTING:
            if re.search(pattern, text):
                return domain

        # Default fallback
        if any(x in text for x in ["build", "make", "create", "write"]):
            return Domain.CODE
        return Domain.IDEA

    def _extract_subject(self, text: str) -> str:
        """Extract what's being acted upon."""
        words = text.split()
        if len(words) > 3:
            return " ".join(words[-3:])
        return text

    def _extract_scope(self) -> str:
        """Extract scope constraint."""
        if "frontend" in self.raw.lower():
            return "frontend"
        if "backend" in self.raw.lower():
            return "backend"
        return "partial"


class ContextInjector:
    """Stage 2: Inject context from CLAUDE.md, project memory, etc."""

    def __init__(self, claude_md_path: Optional[str] = None, memory_path: Optional[str] = None):
        self.claude_md = self._load_file(claude_md_path) if claude_md_path else ""
        self.memory = self._load_file(memory_path) if memory_path else ""
        self.user_prefs = {
            "preferred_model": Model.CLAUDE_OPUS,
            "preferred_tools": ["browse", "review"],
            "safety_mode": False,
        }

    def _load_file(self, path: str) -> str:
        """Load file contents safely."""
        try:
            if os.path.exists(path):
                with open(path, "r") as f:
                    return f.read()
        except Exception as e:
            logger.warning(f"Failed to load {path}: {e}")
        return ""

    def inject(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        """Inject context into intent."""
        context = {
            "claude_md_summary": self._summarize_claude_md(),
            "project_memory": self._summarize_memory(),
            "user_prefs": self.user_prefs,
            "domain_specific_context": self._get_domain_context(intent.get("domain")),
        }
        return {**intent, "context": context}

    def _summarize_claude_md(self) -> str:
        """Extract key context from CLAUDE.md."""
        if not self.claude_md:
            return ""
        lines = self.claude_md.split("\n")[:50]
        return "\n".join(lines)

    def _summarize_memory(self) -> str:
        """Extract key context from project memory."""
        if not self.memory:
            return ""
        lines = self.memory.split("\n")[:30]
        return "\n".join(lines)

    def _get_domain_context(self, domain: str) -> Dict[str, str]:
        """Get domain-specific context."""
        contexts = {
            Domain.SALES: "Atlas HXM (EOR platform, 160+ countries), Competitors: Deel/Remote/Rippling",
            Domain.CODE: "Modern web stack, Next.js, TypeScript, focus on performance",
            Domain.DESIGN: "Mobile-first responsive design, accessibility-first, design system thinking",
            Domain.DEBUG: "Root cause analysis, systematic debugging, verify fixes",
            Domain.DEPLOY: "Test before merge, staging verification, monitoring post-deploy",
            Domain.CONTENT: "Clear, concise, rep/marketer-friendly (50+ users at scale)",
            Domain.OPS: "Data-driven, scalable, practical for non-technical end users",
            Domain.IDEA: "Think bigger, 10x version, strategic lens",
        }
        return {"summary": contexts.get(domain, "General purpose")}


class PromptEnhancer:
    """Stage 3: Enhance the request with precision, structure, and context."""

    def enhance(
        self,
        raw_request: str,
        intent: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Rewrite request with full context and structure."""
        subtasks = self._break_into_subtasks(raw_request, intent)
        rewritten = self._rewrite_prompt(raw_request, intent, context, subtasks)
        knowledge_injected = self._identify_injected_knowledge(context)

        return {
            "original": raw_request,
            "rewritten": rewritten,
            "subtasks": subtasks,
            "knowledge_injected": knowledge_injected,
        }

    def _break_into_subtasks(self, raw: str, intent: Dict[str, Any]) -> List[str]:
        """Break multi-step tasks into sub-steps."""
        text = raw.lower()
        subtasks = []

        # Domain-specific sub-task detection
        if "and" in text:
            parts = re.split(r"\band\b", text)
            subtasks = [p.strip() for p in parts if p.strip()]

        # Implicit subtasks for certain domains
        if intent.get("domain") == Domain.DEPLOY:
            subtasks.extend(["Test locally", "Create PR", "Merge to main", "Verify in production"])
        elif intent.get("domain") == Domain.DEBUG:
            subtasks.extend(["Reproduce issue", "Identify root cause", "Apply fix", "Verify fix"])

        return subtasks or [raw]

    def _rewrite_prompt(
        self,
        raw: str,
        intent: Dict[str, Any],
        context: Dict[str, Any],
        subtasks: List[str],
    ) -> str:
        """Rewrite prompt with precision and injected context."""
        domain = intent.get("domain")
        subject = intent.get("subject")
        constraints = intent.get("constraints", [])

        parts = [f"Task: {raw}"]

        # Add domain-specific context
        domain_context = context.get("context", {}).get("domain_specific_context", {})
        if domain_context.get("summary"):
            parts.append(f"Context: {domain_context['summary']}")

        # Add subtasks
        if subtasks and len(subtasks) > 1:
            parts.append(f"Subtasks: {', '.join(subtasks)}")

        # Add constraints
        if constraints:
            parts.append(f"Constraints: {', '.join(constraints)}")

        # Add output format if specified
        if intent.get("output_format"):
            parts.append(f"Output format: {intent['output_format']}")

        return "\n".join(parts)

    def _identify_injected_knowledge(self, context: Dict[str, Any]) -> List[str]:
        """Identify what knowledge was injected."""
        injected = []
        if context.get("context", {}).get("claude_md_summary"):
            injected.append("CLAUDE.md (project rules)")
        if context.get("context", {}).get("project_memory"):
            injected.append("Project memory (session context)")
        if context.get("context", {}).get("domain_specific_context"):
            injected.append("Domain-specific best practices")
        return injected


class Compiler:
    """Stage 4: Compile into typed AgentManifest JSON."""

    def compile(
        self,
        intent: Dict[str, Any],
        enhanced: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Compile all data into AgentManifest."""
        domain = intent.get("domain")
        model = self._select_model(domain, intent)
        temperature = TEMPERATURE_BY_TASK.get(domain, 0.5)
        tools = self._select_tools(domain, intent, enhanced)
        behavior = self._select_behavior(intent)

        manifest = {
            "domain": domain,
            "model": model,
            "temperature": temperature,
            "tools": tools,
            "behavior": behavior,
            "enhanced_prompt": enhanced.get("rewritten"),
            "routing_reason": self._generate_routing_reason(domain, model, tools),
            "estimated_complexity": self._estimate_complexity(
                intent.get("subject"), enhanced.get("subtasks")
            ),
            "metadata": {
                "original_request": intent.get("goal"),
                "constraints": intent.get("constraints", []),
                "output_format": intent.get("output_format"),
                "knowledge_injected": enhanced.get("knowledge_injected", []),
            },
        }

        return manifest

    def _select_model(self, domain: str, intent: Dict[str, Any]) -> str:
        """Select model based on domain and complexity."""
        # Check for multi-step or complex tasks
        if len(intent.get("constraints", [])) > 1 or "and" in intent.get("goal", "").lower():
            return Model.CLAUDE_OPUS

        # Default by domain
        defaults = {
            Domain.CODE: Model.CLAUDE_OPUS,
            Domain.DEBUG: Model.CLAUDE_SONNET,
            Domain.DEPLOY: Model.CLAUDE_SONNET,
            Domain.DESIGN: Model.CLAUDE_OPUS,
            Domain.CONTENT: Model.CLAUDE_SONNET,
            Domain.SALES: Model.CLAUDE_SONNET,
            Domain.OPS: Model.CLAUDE_SONNET,
            Domain.IDEA: Model.CLAUDE_OPUS,
        }

        return defaults.get(domain, Model.CLAUDE_SONNET)

    def _select_tools(self, domain: str, intent: Dict[str, Any], enhanced: Dict[str, Any]) -> List[str]:
        """Select tools/MCPs based on domain and task."""
        tools = []

        # Use intent routing table to find initial tools
        text = intent.get("goal", "").lower()
        for pattern, _, _, pattern_tools in INTENT_ROUTING:
            if re.search(pattern, text):
                tools.extend(pattern_tools)
                break

        # Add domain-specific defaults
        if not tools:
            domain_defaults = {
                Domain.CODE: ["review", "test"],
                Domain.DESIGN: ["design-html"],
                Domain.DEBUG: ["investigate"],
                Domain.DEPLOY: ["ship"],
                Domain.SALES: ["rfp-answer-retriever"],
                Domain.CONTENT: ["design-html"],
            }
            tools = domain_defaults.get(domain, ["browse"])

        # Expand tools to MCPs
        expanded = set()
        for tool in tools:
            if tool in SKILL_MAPPINGS:
                expanded.update(SKILL_MAPPINGS[tool])
            else:
                expanded.add(tool)

        return list(expanded)[:5]  # Limit to 5 tools

    def _select_behavior(self, intent: Dict[str, Any]) -> str:
        """Select execution behavior based on constraints."""
        constraints = intent.get("constraints", [])

        if "report-only" in constraints:
            return Behavior.REPORT_ONLY
        if "safety-mode" in constraints:
            return Behavior.GUARD
        if "ask" in constraints:
            return Behavior.ASK

        return Behavior.AUTO_APPROVE

    def _generate_routing_reason(self, domain: str, model: str, tools: List[str]) -> str:
        """Generate explanation of routing decision."""
        reason_parts = [f"Domain '{domain}' mapped to {model}"]

        if len(tools) > 0:
            reason_parts.append(f"Tools: {', '.join(tools[:3])}")

        if model == Model.CLAUDE_OPUS:
            reason_parts.append("(Opus for multi-stage reasoning, creative work, or complex tasks)")
        elif model == Model.CLAUDE_SONNET:
            reason_parts.append("(Sonnet for balanced speed and capability)")
        elif model == Model.CLAUDE_HAIKU:
            reason_parts.append("(Haiku for simple, fast routing)")

        return "; ".join(reason_parts)

    def _estimate_complexity(self, subject: str, subtasks: List[str]) -> str:
        """Estimate task complexity."""
        if len(subtasks) > 3:
            return "high"
        elif len(subtasks) > 1:
            return "medium"
        return "low"


class Router:
    """Stage 5: Route to appropriate LLM + MCPs."""

    def route(self, manifest: Dict[str, Any]) -> Dict[str, Any]:
        """Generate routing instructions."""
        return {
            **manifest,
            "routing_instructions": {
                "mcp_endpoints": self._get_mcp_endpoints(manifest.get("tools", [])),
                "execution_flags": self._get_execution_flags(manifest),
                "fallback_model": Model.CLAUDE_SONNET,
            },
        }

    def _get_mcp_endpoints(self, tools: List[str]) -> Dict[str, str]:
        """Map tools to MCP endpoints."""
        endpoints = {
            "web-search": "webrtc://duckduckgo",
            "code-analysis": "mcp://code-analyzer",
            "browser-automation": "mcp://browser-control",
            "git-commands": "mcp://git-ops",
            "semantic-search": "mcp://embeddings",
        }
        return {tool: endpoints.get(tool, f"mcp://{tool}") for tool in tools if tool in endpoints}

    def _get_execution_flags(self, manifest: Dict[str, Any]) -> Dict[str, bool]:
        """Generate execution flags based on manifest."""
        behavior = manifest.get("behavior")
        return {
            "auto_approve": behavior == Behavior.AUTO_APPROVE,
            "ask_for_confirmation": behavior == Behavior.ASK,
            "report_only": behavior == Behavior.REPORT_ONLY,
            "safety_mode": behavior == Behavior.GUARD,
            "streaming_enabled": manifest.get("temperature", 0.5) > 0.5,
        }


class PAL:
    """Main Prompt Abstraction Layer orchestrator."""

    def __init__(
        self,
        claude_md_path: Optional[str] = None,
        memory_path: Optional[str] = None,
        verbose: bool = False,
    ):
        self.claude_md_path = claude_md_path
        self.memory_path = memory_path
        self.verbose = verbose

        self.intent_extractor = Intent
        self.context_injector = ContextInjector(claude_md_path, memory_path)
        self.prompt_enhancer = PromptEnhancer()
        self.compiler = Compiler()
        self.router = Router()

    def compile(self, raw_request: str, context_override: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute full 5-stage pipeline.

        Args:
            raw_request: Natural language request
            context_override: Optional context to override auto-detected

        Returns:
            AgentManifest JSON with domain, model, temperature, tools, behavior
        """
        if self.verbose:
            logger.info(f"[PAL] Stage 1: Extracting intent from: {raw_request[:50]}...")

        # Stage 1: Intent Extraction
        intent_extractor = self.intent_extractor(raw_request)
        intent = intent_extractor.extract()

        if self.verbose:
            logger.info(f"[PAL] Stage 1 result: domain={intent.get('domain')}")

        # Stage 2: Context Injection
        if self.verbose:
            logger.info("[PAL] Stage 2: Injecting context...")
        context = self.context_injector.inject(intent)

        if context_override:
            context.update(context_override)

        # Stage 3: Prompt Enhancement
        if self.verbose:
            logger.info("[PAL] Stage 3: Enhancing prompt...")
        enhanced = self.prompt_enhancer.enhance(raw_request, intent, context)

        # Stage 4: Compilation
        if self.verbose:
            logger.info("[PAL] Stage 4: Compiling into AgentManifest...")
        manifest = self.compiler.compile(intent, enhanced)

        # Stage 5: Routing
        if self.verbose:
            logger.info("[PAL] Stage 5: Generating routing instructions...")
        routed = self.router.route(manifest)

        if self.verbose:
            logger.info(f"[PAL] Complete. Model={routed.get('model')}, Tools={routed.get('tools')}")

        return routed


def main():
    """CLI interface."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python main.py '<request>'")
        print("Example: python main.py 'make a basketball site for my school'")
        sys.exit(1)

    request = sys.argv[1]
    pal = PAL(verbose=True)
    manifest = pal.compile(request)
    print(json.dumps(manifest, indent=2, default=str))


if __name__ == "__main__":
    main()
