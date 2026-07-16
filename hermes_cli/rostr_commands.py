#!/usr/bin/env python3
"""
ROSTR CLI Commands — PAL, NPAO, RAG DAL, and Rostr Hub from the terminal.

Usage:
    hermes pal compile "Build a REST API for user management"
    hermes pal compile --context '{"project": "myapp"}' "Research vector DBs"

    hermes npao classify "Fix the authentication bug"
    hermes npao classify --domain debug --blocked 3 --revenue "Fix auth bug"

    hermes ragdal search "What are the best practices for RAG pipelines?"
    hermes ragdal search --tier tier1 "Latest research on attention mechanisms"

    hermes hub register --name "Builder Agent" --type builder --phases Development
    hermes hub list
    hermes hub decide --context "Chose PostgreSQL" --decision "Use PG17" --rationale "JSONB support"
    hermes hub learn --context "Deploy" --insight "Always verify staging first"
    hermes hub compound
    hermes hub search "deploy failure"

Author: Patrick Diamitani
License: MIT
"""

import argparse
import json
import sys


def _check_rostr():
    """Verify rostr is importable. Print error and exit 1 if not."""
    try:
        import rostr  # noqa: F401
    except ImportError:
        print("Error: ROSTR package not installed.", file=sys.stderr)
        print("Install with: pip install rostr-core", file=sys.stderr)
        print("Or: git clone https://github.com/diamitani/rostr-agent && cd rostr-agent && pip install -e .", file=sys.stderr)
        sys.exit(1)


# ── PAL Subcommand ────────────────────────────────────────────────

def _cmd_pal(args):
    """hermes pal compile [--context JSON] INTENT"""
    _check_rostr()
    from rostr import PALCompiler

    context = None
    if args.context:
        try:
            context = json.loads(args.context)
        except json.JSONDecodeError:
            print(f"Warning: Could not parse context JSON: {args.context}", file=sys.stderr)

    pal = PALCompiler()
    intent, enhanced, manifest, phase = pal.compile_intent(args.intent, context)

    print(f"Domain:       {intent.domain.value}")
    print(f"Agent Type:   {manifest.agent_type.value}")
    print(f"Model:        {manifest.model}")
    print(f"Phase:        {phase}")
    print(f"Urgency:      {intent.urgency.value}")
    print(f"Ambiguity:    {intent.ambiguity_score:.2f}")
    print(f"Temperature:  {manifest.temperature}")
    print(f"Timeout:      {manifest.timeout_seconds}s")
    print()
    print("Manifest (YAML):")
    print(manifest.to_yaml())

    if args.json:
        print()
        print(json.dumps(manifest.to_dict(), indent=2))


def _setup_pal_parser(subparsers):
    pal_parser = subparsers.add_parser("pal", help="PAL — Prompt Abstraction Layer compiler")
    pal_sub = pal_parser.add_subparsers(dest="pal_action")

    compile_parser = pal_sub.add_parser("compile", help="Compile natural language into an agent manifest")
    compile_parser.add_argument("intent", help="Natural language task description")
    compile_parser.add_argument("--context", "-c", help="Optional JSON context payload")
    compile_parser.add_argument("--json", "-j", action="store_true", help="Also output raw JSON manifest")
    compile_parser.set_defaults(func=_cmd_pal)


# ── NPAO Subcommand ───────────────────────────────────────────────

def _cmd_npao(args):
    """hermes npao classify [--domain X] [--blocked N] [--revenue] [--user] [--hours H] TASK"""
    _check_rostr()
    from rostr import NPAO

    npao = NPAO()
    result = npao.process(
        args.task,
        domain=args.domain or "",
        blocked_tasks=args.blocked,
        revenue_impact=args.revenue,
        user_impact=args.user,
        team_impact=args.team,
        estimated_hours=args.hours,
    )

    print(f"Phase:        {result['phase']} (index {result['phase_index']})")
    print(f"Priority:     {result['priority']['composite']:.1f}/10 → {result['priority']['status'].upper()}")
    print(f"Orchestration: {result['orchestration']}")
    print()
    print("Priority Breakdown:")
    for k, v in result["priority"]["breakdown"].items():
        print(f"  {k}: {v:.1f}")
    print()
    print("Phase Completion Criteria:")
    for c in result["criteria"]:
        print(f"  - {c}")

    if args.json:
        print()
        print(json.dumps(result, indent=2))


def _setup_npao_parser(subparsers):
    npao_parser = subparsers.add_parser("npao", help="NPAO — Navigate, Prioritize, Allocate, Orchestrate")
    npao_sub = npao_parser.add_subparsers(dest="npao_action")

    classify_parser = npao_sub.add_parser("classify", help="Classify a task through the 5D phase + 4D priority system")
    classify_parser.add_argument("task", help="Task description")
    classify_parser.add_argument("--domain", "-d", help="Domain hint: code, research, design, deploy, debug")
    classify_parser.add_argument("--blocked", "-b", type=int, default=0, help="Number of blocked tasks")
    classify_parser.add_argument("--revenue", "-r", action="store_true", help="Revenue-impacting")
    classify_parser.add_argument("--user", "-u", action="store_true", help="User-experience impacting")
    classify_parser.add_argument("--team", "-t", action="store_true", help="Team-productivity impacting")
    classify_parser.add_argument("--hours", type=float, default=4.0, help="Estimated hours")
    classify_parser.add_argument("--json", "-j", action="store_true", help="Also output raw JSON")
    classify_parser.set_defaults(func=_cmd_npao)


# ── RAG DAL Subcommand ────────────────────────────────────────────

def _cmd_ragdal(args):
    """hermes ragdal search [--tier X] QUERY"""
    _check_rostr()
    from rostr import RAGDAL

    ragdal = RAGDAL()
    report = ragdal.multi_pass_retrieve(args.query)

    print(f"Query:        {args.query}")
    print(f"Passes:       {report.passes_completed}")
    print(f"Sources:      {report.sources_used}")
    print(f"Complete:     {'Yes' if report.is_complete else 'No'}")
    if report.gaps:
        print(f"Gaps:         {', '.join(report.gaps)}")
    print()
    print("Sub-Topic Confidence:")
    for topic, conf in report.confidence_per_topic.items():
        bar = "█" * int(conf * 10) + "░" * (10 - int(conf * 10))
        print(f"  [{bar}] {conf:.2f} — {topic}")

    if args.json:
        print()
        print(json.dumps({
            "sub_topics": report.sub_topics,
            "confidence_per_topic": report.confidence_per_topic,
            "sources_used": report.sources_used,
            "passes_completed": report.passes_completed,
            "is_complete": report.is_complete,
            "gaps": report.gaps,
        }, indent=2))


def _setup_ragdal_parser(subparsers):
    ragdal_parser = subparsers.add_parser("ragdal", help="RAG DAL — Dynamic Acquisition Layer knowledge engine")
    ragdal_sub = ragdal_parser.add_subparsers(dest="ragdal_action")

    search_parser = ragdal_sub.add_parser("search", help="Multi-pass knowledge retrieval with credibility scoring")
    search_parser.add_argument("query", help="Research query")
    search_parser.add_argument("--tier", choices=["tier1", "tier2", "tier3"], help="Restrict to source tier")
    search_parser.add_argument("--json", "-j", action="store_true", help="Also output raw JSON")
    search_parser.set_defaults(func=_cmd_ragdal)


# ── Rostr Hub Subcommand ──────────────────────────────────────────

def _cmd_hub(args):
    """hermes hub {register,list,decide,learn,compound,search} ..."""
    _check_rostr()
    from rostr import RostrHub, AgentRegistration

    hub = RostrHub()

    if args.hub_action == "register":
        if not args.name:
            print("Error: --name is required for register", file=sys.stderr)
            sys.exit(1)
        caps = [c.strip() for c in (args.capabilities or "").split(",") if c.strip()]
        phases = [p.strip() for p in (args.phases or "Development").split(",") if p.strip()]
        agent = AgentRegistration(
            name=args.name,
            agent_type=args.type or "builder",
            capabilities=caps,
            tools=["web_search", "file_system:read"],
            phases=phases,
        )
        registered = hub.register_agent(agent)
        print(f"Agent registered: {registered.agent_id}")
        print(f"  Name: {registered.name}")
        print(f"  Type: {registered.agent_type}")
        print(f"  Phases: {registered.phases}")

    elif args.hub_action == "list":
        if args.type_filter:
            agents = hub.list_agents_by_type(args.type_filter)
        else:
            agents = list(hub.agents.values())
        print(f"Agents ({len(agents)}):")
        for a in agents:
            print(f"  {a.agent_id[:8]}…  {a.name:20s}  {a.agent_type:12s}  phases={a.phases}")

    elif args.hub_action == "decide":
        if not all([args.context, args.decision, args.rationale]):
            print("Error: --context, --decision, and --rationale are required", file=sys.stderr)
            sys.exit(1)
        d = hub.log_decision(
            context=args.context,
            decision=args.decision,
            rationale=args.rationale,
            namespace=args.namespace or "",
        )
        print(f"Decision logged: {d.decision_id}")

    elif args.hub_action == "learn":
        if not all([args.context, args.insight]):
            print("Error: --context and --insight are required", file=sys.stderr)
            sys.exit(1)
        tags = [t.strip() for t in (args.tags or "").split(",") if t.strip()]
        l = hub.log_learning(
            context=args.context,
            insight=args.insight,
            outcome=args.outcome or "observation",
            tags=tags,
        )
        print(f"Learning logged: {l.learning_id}")

    elif args.hub_action == "compound":
        report = hub.compound()
        print(f"Knowledge Compounding Report:")
        print(f"  Decisions: {report['total_decisions']}")
        print(f"  Learnings: {report['total_learnings']}")
        print(f"  Agents:    {report['total_agents']}")
        if report["recent_learnings"]:
            print(f"\nRecent Learnings:")
            for insight in report["recent_learnings"]:
                print(f"  • {insight}")

    elif args.hub_action == "search":
        if not args.query:
            print("Error: search query required", file=sys.stderr)
            sys.exit(1)
        results = hub.search_learnings(args.query)
        print(f"Results for '{args.query}' ({len(results)}):")
        for r in results:
            print(f"  [{', '.join(r.tags)}] {r.insight}")

    else:
        print(f"Unknown hub action: {args.hub_action}", file=sys.stderr)
        sys.exit(1)

    if args.json and args.hub_action in ("list", "compound", "search"):
        if args.hub_action == "list":
            data = [a.to_dict() for a in hub.agents.values()]
        elif args.hub_action == "compound":
            data = hub.compound()
        else:
            data = [{"insight": r.insight, "tags": r.tags} for r in hub.search_learnings(args.query)]
        print()
        print(json.dumps(data, indent=2))


def _setup_hub_parser(subparsers):
    hub_parser = subparsers.add_parser("hub", help="Rostr Hub — persistent reference architecture")
    hub_sub = hub_parser.add_subparsers(dest="hub_action")

    # register
    reg = hub_sub.add_parser("register", help="Register a new agent")
    reg.add_argument("--name", "-n", required=True, help="Agent name")
    reg.add_argument("--type", "-t", default="builder", help="Agent type (builder, researcher, etc.)")
    reg.add_argument("--capabilities", "-c", help="Comma-separated capabilities")
    reg.add_argument("--phases", "-p", default="Development", help="Comma-separated phases")
    reg.add_argument("--json", "-j", action="store_true")
    reg.set_defaults(func=_cmd_hub)

    # list
    lst = hub_sub.add_parser("list", help="List registered agents")
    lst.add_argument("--type", "-t", dest="type_filter", help="Filter by agent type")
    lst.add_argument("--json", "-j", action="store_true")
    lst.set_defaults(func=_cmd_hub)

    # decide
    decide = hub_sub.add_parser("decide", help="Log a key decision")
    decide.add_argument("--context", "-c", required=True, help="Decision context")
    decide.add_argument("--decision", "-d", required=True, help="The decision")
    decide.add_argument("--rationale", "-r", required=True, help="Why this decision")
    decide.add_argument("--namespace", "-n", help="Namespace (projects/{id})")
    decide.add_argument("--json", "-j", action="store_true")
    decide.set_defaults(func=_cmd_hub)

    # learn
    learn = hub_sub.add_parser("learn", help="Log a learning/insight")
    learn.add_argument("--context", "-c", required=True, help="Learning context")
    learn.add_argument("--insight", "-i", required=True, help="What was learned")
    learn.add_argument("--outcome", "-o", default="observation", help="success, failure, observation")
    learn.add_argument("--tags", "-t", help="Comma-separated tags")
    learn.add_argument("--json", "-j", action="store_true")
    learn.set_defaults(func=_cmd_hub)

    # compound
    compound = hub_sub.add_parser("compound", help="Knowledge compounding report")
    compound.add_argument("--json", "-j", action="store_true")
    compound.set_defaults(func=_cmd_hub)

    # search
    search = hub_sub.add_parser("search", help="Search past learnings")
    search.add_argument("query", help="Search query")
    search.add_argument("--json", "-j", action="store_true")
    search.set_defaults(func=_cmd_hub)


# ── Register with main CLI ────────────────────────────────────────

def register_rostr_commands(subparsers):
    """Register all ROSTR subcommands on an argparse subparsers object."""
    _setup_pal_parser(subparsers)
    _setup_npao_parser(subparsers)
    _setup_ragdal_parser(subparsers)
    _setup_hub_parser(subparsers)
