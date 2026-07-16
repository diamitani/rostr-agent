#!/usr/bin/env python3
"""
ROSTR Tools — PAL Compiler, NPAO Orchestrator, RAG DAL Knowledge Engine, Rostr Hub.

ROSTR (Runtime, Orchestration, State, Tools, Reference) is a unified architecture
for production-grade multi-agent systems. These tools give the agent first-class
access to all four ROSTR pillars.

Author: Patrick Diamitani
License: MIT
"""

import json
import os
from typing import Optional


# ── Shared helpers ────────────────────────────────────────────────

def _get_rostr_module():
    """Lazy-import the ROSTR package. Returns None if not installed."""
    try:
        import rostr
        return rostr
    except ImportError:
        return None


# ── PAL Compiler Tool ─────────────────────────────────────────────

def pal_compile_tool(
    intent: str,
    context: Optional[str] = None,
) -> str:
    """
    Compile natural language intent into a structured agent manifest via PAL.

    The PAL (Prompt Abstraction Layer) runs a 5-stage compilation pipeline:
      1. Intent Extraction — parse raw input
      2. Context Injection  — load relevant state
      3. Semantic Enhancement — expand verbs, add precision
      4. Runtime Compilation — produce typed agent manifest
      5. Output Routing     — determine workflow phase

    Args:
        intent: Natural language description of what needs to be done
        context: Optional JSON context payload (project state, decisions, etc.)

    Returns:
        JSON with intent, enhanced_instruction, manifest, and routing_phase
    """
    rostr = _get_rostr_module()
    if rostr is None:
        return json.dumps({"error": "ROSTR package not installed. Run: pip install rostr-core"})

    hub_context = None
    if context:
        try:
            hub_context = json.loads(context)
        except json.JSONDecodeError:
            pass

    try:
        pal = rostr.PALCompiler()
        intent_obj, enhanced, manifest, phase = pal.compile_intent(intent, hub_context)

        return json.dumps({
            "intent": intent_obj.to_dict(),
            "enhanced_instruction": enhanced,
            "manifest": manifest.to_dict(),
            "manifest_yaml": manifest.to_yaml(),
            "routing_phase": phase,
            "domain": intent_obj.domain.value,
            "agent_type": manifest.agent_type.value,
            "model": manifest.model,
            "urgency": intent_obj.urgency.value,
            "ambiguity_score": intent_obj.ambiguity_score,
        }, indent=2, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"PAL compilation failed: {e}"})


def check_pal_requirements() -> bool:
    return _get_rostr_module() is not None


PAL_COMPILE_SCHEMA = {
    "name": "pal_compile",
    "description": (
        "Compile a natural language task description into a structured ROSTR agent "
        "manifest using PAL (Prompt Abstraction Layer). Runs a 5-stage pipeline: "
        "intent extraction → context injection → semantic enhancement → runtime "
        "compilation → output routing. Returns the agent type, model, tools, "
        "behavior profile, domain, and workflow phase. Use this BEFORE delegating "
        "complex tasks — the manifest guides downstream tool selection and agent "
        "allocation."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "intent": {
                "type": "string",
                "description": "Natural language description of the task to compile (e.g. 'Research top 3 vector database solutions for a production RAG pipeline')",
            },
            "context": {
                "type": "string",
                "description": "Optional JSON context payload with project state, prior decisions, org constraints",
            },
        },
        "required": ["intent"],
    },
}


# ── NPAO Classify Tool ────────────────────────────────────────────

def npao_classify_tool(
    task_description: str,
    domain: str = "",
    blocked_tasks: int = 0,
    revenue_impact: bool = False,
    user_impact: bool = False,
    team_impact: bool = False,
    estimated_hours: float = 4.0,
) -> str:
    """
    Classify a task through the NPAO decision engine.

    NPAO (Navigate, Prioritize, Allocate, Orchestrate) uses:
      - 5D Phase Taxonomy (PreD → Design → Development → Deployment → Debugging)
      - 4D Priority Scoring (Phase × 0.35 + Dependency × 0.30 + Business × 0.25 + Resource × 0.10)

    Args:
        task_description: What the task involves
        domain: Optional hint (code, research, design, deploy, debug)
        blocked_tasks: How many tasks are blocked waiting on this one
        revenue_impact: Does this directly affect revenue?
        user_impact: Does this affect user experience?
        team_impact: Does this affect team productivity?
        estimated_hours: Estimated completion time

    Returns:
        JSON with phase, priority score, allocation, and orchestration pattern
    """
    rostr = _get_rostr_module()
    if rostr is None:
        return json.dumps({"error": "ROSTR package not installed. Run: pip install rostr-core"})

    try:
        npao = rostr.NPAO()
        result = npao.process(
            task_description,
            domain=domain,
            blocked_tasks=blocked_tasks,
            revenue_impact=revenue_impact,
            user_impact=user_impact,
            team_impact=team_impact,
            estimated_hours=estimated_hours,
        )

        return json.dumps(result, indent=2, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"NPAO classification failed: {e}"})


def check_npao_requirements() -> bool:
    return _get_rostr_module() is not None


NPAO_CLASSIFY_SCHEMA = {
    "name": "npao_classify",
    "description": (
        "Classify a task through the NPAO (Navigate, Prioritize, Allocate, "
        "Orchestrate) decision engine. Returns the 5D workflow phase (PreD, "
        "Design, Development, Deployment, Debugging), a 4D priority score "
        "(0-10 composite), allocation status (immediate/queued/backlog), "
        "completion criteria for the phase, and the recommended orchestration "
        "pattern. Use this to understand where a task fits in the workflow "
        "lifecycle and how urgently it should be handled."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "task_description": {
                "type": "string",
                "description": "Description of the task to classify",
            },
            "domain": {
                "type": "string",
                "description": "Optional domain hint: code, research, design, deploy, debug",
            },
            "blocked_tasks": {
                "type": "integer",
                "description": "Number of tasks blocked by this one (default: 0)",
            },
            "revenue_impact": {
                "type": "boolean",
                "description": "Does this directly affect revenue? (default: false)",
            },
            "user_impact": {
                "type": "boolean",
                "description": "Does this affect user experience? (default: false)",
            },
            "team_impact": {
                "type": "boolean",
                "description": "Does this affect team productivity? (default: false)",
            },
            "estimated_hours": {
                "type": "number",
                "description": "Estimated completion time in hours (default: 4.0)",
            },
        },
        "required": ["task_description"],
    },
}


# ── RAG DAL Search Tool ───────────────────────────────────────────

def ragdal_search_tool(
    query: str,
    tier_filter: Optional[str] = None,
) -> str:
    """
    Execute multi-pass knowledge retrieval with source credibility scoring.

    RAG DAL (Dynamic Acquisition Layer) uses:
      - Three-tier source credibility (Tier 1: academic 1.0, Tier 2: editorial 0.75, Tier 3: community 0.40)
      - Multi-pass algorithm with gap detection and targeted re-search
      - Confidence formula: (source_count × 0.35) + (consistency × 0.30) + (tier_distribution × 0.25) + (recency × 0.10)

    Args:
        query: What to research
        tier_filter: Optional: 'tier1', 'tier2', 'tier3' to filter sources

    Returns:
        JSON coverage report with confidence scores and knowledge entries
    """
    rostr = _get_rostr_module()
    if rostr is None:
        return json.dumps({"error": "ROSTR package not installed. Run: pip install rostr-core"})

    try:
        ragdal = rostr.RAGDAL()
        report = ragdal.multi_pass_retrieve(query)

        return json.dumps({
            "query": query,
            "sub_topics": report.sub_topics,
            "confidence_per_topic": report.confidence_per_topic,
            "sources_used": report.sources_used,
            "passes_completed": report.passes_completed,
            "is_complete": report.is_complete,
            "gaps": report.gaps,
            "knowledge_entries": [
                e.to_dict() for e in ragdal.knowledge_base[-10:]
            ],
        }, indent=2, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"RAG DAL search failed: {e}"})


def check_ragdal_requirements() -> bool:
    return _get_rostr_module() is not None


RAGDAL_SEARCH_SCHEMA = {
    "name": "ragdal_search",
    "description": (
        "Execute multi-pass knowledge retrieval with the RAG DAL (Dynamic "
        "Acquisition Layer) knowledge engine. Decomposes the query into "
        "sub-topics, runs up to 4 passes of targeted search across 3 tiers "
        "of source credibility (academic → editorial → community), computes "
        "confidence scores per topic, and identifies knowledge gaps. Use this "
        "for deep research tasks that require source validation and coverage "
        "assessment."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Research query to investigate",
            },
            "tier_filter": {
                "type": "string",
                "description": "Optional: restrict to 'tier1', 'tier2', or 'tier3' sources",
            },
        },
        "required": ["query"],
    },
}


# ── Rostr Hub Tool ─────────────────────────────────────────────────

def rostr_hub_tool(
    action: str,
    agent_id: Optional[str] = None,
    agent_name: Optional[str] = None,
    agent_type: Optional[str] = None,
    agent_capabilities: Optional[str] = None,
    agent_phases: Optional[str] = None,
    context: Optional[str] = None,
    decision: Optional[str] = None,
    rationale: Optional[str] = None,
    insight: Optional[str] = None,
    outcome: str = "observation",
    namespace: str = "",
    tags: Optional[str] = None,
    limit: int = 20,
) -> str:
    """
    Interact with the Rostr Hub — the persistent reference architecture.

    Actions:
      - 'register_agent': Register a new agent in the hub
      - 'list_agents': List all registered agents
      - 'log_decision': Record a key decision with rationale
      - 'log_learning': Record an insight learned during execution
      - 'compound': Get knowledge compounding report
      - 'search_learnings': Search past learnings by keyword

    Args:
        action: What to do (register_agent, list_agents, log_decision, log_learning, compound, search_learnings)
        agent_id: Agent identifier (for register)
        agent_name: Human-readable agent name
        agent_type: builder, researcher, reviewer, designer, deployer, debugger
        agent_capabilities: Comma-separated capability list
        agent_phases: Comma-separated phase list (PreD, Design, Development, Deployment, Debugging)
        context: Context for the decision/learning/insight
        decision: The decision that was made
        rationale: Why the decision was made
        insight: What was learned
        outcome: success, failure, or observation
        namespace: projects/{id}, orgs/{id}, teams/{id}, or global
        tags: Comma-separated tags for learnings
        limit: Max results (default 20)

    Returns:
        JSON response
    """
    rostr = _get_rostr_module()
    if rostr is None:
        return json.dumps({"error": "ROSTR package not installed. Run: pip install rostr-core"})

    try:
        hub = rostr.RostrHub()

        if action == "register_agent":
            if not agent_name:
                return json.dumps({"error": "agent_name is required for register_agent"})
            caps = [c.strip() for c in (agent_capabilities or "").split(",") if c.strip()]
            phases = [p.strip() for p in (agent_phases or "Development").split(",") if p.strip()]
            agent = rostr.AgentRegistration(
                agent_id=agent_id or "",
                name=agent_name,
                agent_type=agent_type or "builder",
                capabilities=caps,
                tools=["web_search", "file_system:read"],
                phases=phases,
            )
            registered = hub.register_agent(agent)
            return json.dumps({
                "action": "register_agent",
                "agent": registered.to_dict(),
            }, indent=2)

        elif action == "list_agents":
            agents = [
                {"id": aid, "name": a.name, "type": a.agent_type, "phases": a.phases}
                for aid, a in hub.agents.items()
            ]
            return json.dumps({
                "action": "list_agents",
                "count": len(agents),
                "agents": agents,
            }, indent=2)

        elif action == "log_decision":
            if not context or not decision or not rationale:
                return json.dumps({"error": "context, decision, and rationale are required"})
            d = hub.log_decision(
                context=context,
                decision=decision,
                rationale=rationale,
                namespace=namespace,
            )
            return json.dumps({
                "action": "log_decision",
                "decision_id": d.decision_id,
                "timestamp": d.timestamp,
            }, indent=2)

        elif action == "log_learning":
            if not context or not insight:
                return json.dumps({"error": "context and insight are required"})
            tag_list = [t.strip() for t in (tags or "").split(",") if t.strip()]
            l = hub.log_learning(
                context=context,
                insight=insight,
                outcome=outcome,
                tags=tag_list,
            )
            return json.dumps({
                "action": "log_learning",
                "learning_id": l.learning_id,
                "timestamp": l.timestamp,
            }, indent=2)

        elif action == "compound":
            report = hub.compound()
            return json.dumps({
                "action": "compound",
                "report": report,
            }, indent=2)

        elif action == "search_learnings":
            if not insight:
                return json.dumps({"error": "insight (search query) is required"})
            results = hub.search_learnings(insight)
            return json.dumps({
                "action": "search_learnings",
                "query": insight,
                "count": len(results),
                "results": [
                    {"id": l.learning_id, "insight": l.insight, "context": l.context, "tags": l.tags}
                    for l in results[:limit]
                ],
            }, indent=2)

        else:
            return json.dumps({
                "error": f"Unknown action: {action}. Valid: register_agent, list_agents, log_decision, log_learning, compound, search_learnings"
            })

    except Exception as e:
        return json.dumps({"error": f"Rostr Hub operation failed: {e}"})


def check_hub_requirements() -> bool:
    return _get_rostr_module() is not None


ROSTR_HUB_SCHEMA = {
    "name": "rostr_hub",
    "description": (
        "Interact with the Rostr Hub — the persistent reference architecture "
        "for multi-agent systems. Supports: registering agents, listing agents, "
        "logging decisions with rationale, logging learnings for knowledge "
        "compounding, getting a compounding report, and searching past learnings. "
        "Use this to persist state across sessions, track agent performance, and "
        "build a compounding knowledge base."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "description": "Action: register_agent, list_agents, log_decision, log_learning, compound, search_learnings",
                "enum": ["register_agent", "list_agents", "log_decision", "log_learning", "compound", "search_learnings"],
            },
            "agent_id": {"type": "string", "description": "Agent ID (for register)"},
            "agent_name": {"type": "string", "description": "Agent name (for register)"},
            "agent_type": {"type": "string", "description": "builder, researcher, reviewer, designer, deployer, debugger"},
            "agent_capabilities": {"type": "string", "description": "Comma-separated capabilities"},
            "agent_phases": {"type": "string", "description": "Comma-separated phases"},
            "context": {"type": "string", "description": "Decision/learning context"},
            "decision": {"type": "string", "description": "The decision made"},
            "rationale": {"type": "string", "description": "Why this decision"},
            "insight": {"type": "string", "description": "What was learned / search query"},
            "outcome": {"type": "string", "description": "success, failure, observation (default: observation)"},
            "namespace": {"type": "string", "description": "projects/{id}, orgs/{id}, teams/{id}"},
            "tags": {"type": "string", "description": "Comma-separated tags"},
            "limit": {"type": "integer", "description": "Max results (default: 20)"},
        },
        "required": ["action"],
    },
}


# ── ROSTR Pipeline Tool (Full Integration) ────────────────────────

def rostr_pipeline_tool(
    intent: str,
    context: Optional[str] = None,
    blocked_tasks: int = 0,
    revenue_impact: bool = False,
    user_impact: bool = False,
    estimated_hours: float = 4.0,
) -> str:
    """
    Run the full ROSTR pipeline: PAL → NPAO → (optionally) RAG DAL.

    This is the all-in-one entry point that:
      1. Compiles intent via PAL (5-stage)
      2. Classifies via NPAO (phase + priority)
      3. Optionally triggers RAG DAL for research tasks

    Args:
        intent: Natural language task description
        context: Optional JSON context
        blocked_tasks: Tasks blocked by this one
        revenue_impact: Revenue-affecting?
        user_impact: User-facing?
        estimated_hours: Time estimate

    Returns:
        Full pipeline output: PAL manifest + NPAO classification + orchestration
    """
    rostr = _get_rostr_module()
    if rostr is None:
        return json.dumps({"error": "ROSTR package not installed. Run: pip install rostr-core"})

    try:
        # PAL: Compile intent
        hub_context = None
        if context:
            try:
                hub_context = json.loads(context)
            except json.JSONDecodeError:
                pass

        pal = rostr.PALCompiler()
        intent_obj, enhanced, manifest, phase = pal.compile_intent(intent, hub_context)

        # NPAO: Classify
        npao = rostr.NPAO()
        npao_result = npao.process(
            enhanced,
            domain=intent_obj.domain.value,
            blocked_tasks=blocked_tasks,
            revenue_impact=revenue_impact,
            user_impact=user_impact,
            estimated_hours=estimated_hours,
        )

        # RAG DAL: Trigger for research tasks
        ragdal_result = None
        if intent_obj.domain.value == "research":
            ragdal = rostr.RAGDAL()
            report = ragdal.multi_pass_retrieve(intent)
            ragdal_result = {
                "sub_topics": report.sub_topics,
                "passes": report.passes_completed,
                "complete": report.is_complete,
            }

        return json.dumps({
            "pal": {
                "domain": intent_obj.domain.value,
                "agent_type": manifest.agent_type.value,
                "model": manifest.model,
                "manifest": manifest.to_dict(),
            },
            "npao": npao_result,
            "ragdal": ragdal_result,
            "pipeline_summary": f"Domain={intent_obj.domain.value} → Phase={npao_result['phase']} → Priority={npao_result['priority']['composite']:.1f}/10 → Agent={manifest.agent_type.value}",
        }, indent=2, ensure_ascii=False)

    except Exception as e:
        return json.dumps({"error": f"ROSTR pipeline failed: {e}"})


def check_pipeline_requirements() -> bool:
    return _get_rostr_module() is not None


ROSTR_PIPELINE_SCHEMA = {
    "name": "rostr_pipeline",
    "description": (
        "Run the full ROSTR pipeline (PAL → NPAO) on a task. Compiles natural "
        "language into a typed agent manifest, classifies the workflow phase, "
        "computes a 4D priority score, and optionally triggers RAG DAL knowledge "
        "retrieval for research tasks. Use this as a one-stop classification and "
        "routing step before executing complex multi-agent workflows."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "intent": {
                "type": "string",
                "description": "Natural language task description",
            },
            "context": {
                "type": "string",
                "description": "Optional JSON context payload",
            },
            "blocked_tasks": {
                "type": "integer",
                "description": "Number of tasks blocked by this one",
            },
            "revenue_impact": {
                "type": "boolean",
                "description": "Does this directly affect revenue?",
            },
            "user_impact": {
                "type": "boolean",
                "description": "Does this affect user experience?",
            },
            "estimated_hours": {
                "type": "number",
                "description": "Estimated completion time in hours",
            },
        },
        "required": ["intent"],
    },
}


# ── Registry ──────────────────────────────────────────────────────

from tools.registry import registry, tool_error

registry.register(
    name="pal_compile",
    toolset="rostr",
    schema=PAL_COMPILE_SCHEMA,
    handler=lambda args, **kw: pal_compile_tool(
        intent=args.get("intent", ""),
        context=args.get("context"),
    ),
    check_fn=check_pal_requirements,
)

registry.register(
    name="npao_classify",
    toolset="rostr",
    schema=NPAO_CLASSIFY_SCHEMA,
    handler=lambda args, **kw: npao_classify_tool(
        task_description=args.get("task_description", ""),
        domain=args.get("domain", ""),
        blocked_tasks=args.get("blocked_tasks", 0),
        revenue_impact=args.get("revenue_impact", False),
        user_impact=args.get("user_impact", False),
        team_impact=args.get("team_impact", False),
        estimated_hours=args.get("estimated_hours", 4.0),
    ),
    check_fn=check_npao_requirements,
)

registry.register(
    name="ragdal_search",
    toolset="rostr",
    schema=RAGDAL_SEARCH_SCHEMA,
    handler=lambda args, **kw: ragdal_search_tool(
        query=args.get("query", ""),
        tier_filter=args.get("tier_filter"),
    ),
    check_fn=check_ragdal_requirements,
)

registry.register(
    name="rostr_hub",
    toolset="rostr",
    schema=ROSTR_HUB_SCHEMA,
    handler=lambda args, **kw: rostr_hub_tool(
        action=args.get("action", ""),
        agent_id=args.get("agent_id"),
        agent_name=args.get("agent_name"),
        agent_type=args.get("agent_type"),
        agent_capabilities=args.get("agent_capabilities"),
        agent_phases=args.get("agent_phases"),
        context=args.get("context"),
        decision=args.get("decision"),
        rationale=args.get("rationale"),
        insight=args.get("insight"),
        outcome=args.get("outcome", "observation"),
        namespace=args.get("namespace", ""),
        tags=args.get("tags"),
        limit=args.get("limit", 20),
    ),
    check_fn=check_hub_requirements,
)

registry.register(
    name="rostr_pipeline",
    toolset="rostr",
    schema=ROSTR_PIPELINE_SCHEMA,
    handler=lambda args, **kw: rostr_pipeline_tool(
        intent=args.get("intent", ""),
        context=args.get("context"),
        blocked_tasks=args.get("blocked_tasks", 0),
        revenue_impact=args.get("revenue_impact", False),
        user_impact=args.get("user_impact", False),
        estimated_hours=args.get("estimated_hours", 4.0),
    ),
    check_fn=check_pipeline_requirements,
)
