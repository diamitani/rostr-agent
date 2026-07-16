# 🧠 ROSTR Agent — The Self-Improving Multi-Agent Framework

**Runtime · Orchestration · State · Tools · Reference**

<div align="center">

[![PyPI](https://img.shields.io/badge/pypi-rostr--agent-a78bfa?style=for-the-badge)](https://pypi.org/project/rostr-agent)
[![License: MIT](https://img.shields.io/badge/license-MIT-34d399?style=for-the-badge)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-a78bfa?style=for-the-badge)](https://python.org)
[![GitHub](https://img.shields.io/badge/github-diamitani/rostr--agent-22d3ee?style=for-the-badge)](https://github.com/diamitani/rostr-agent)

</div>

---

## What Is ROSTR Agent?

ROSTR Agent is a **production-grade multi-agent framework** that fuses the power of the Hermes Agent runtime with the **ROSTR architecture** — a unified system for agent orchestration, knowledge retrieval, and persistent state management.

It's the same self-improving AI agent you know (skills from experience, persistent memory, 20+ messaging platforms, any LLM provider), now with **first-class multi-agent orchestration built in**.

### What makes ROSTR Agent different

- **ROSTR built-in** — PAL (Prompt Abstraction Layer), NPAO (Navigate/Prioritize/Allocate/Orchestrate), RAG DAL (Dynamic Acquisition Layer), and Rostr Hub (persistent state) are first-class CLI commands and agent tools
- **Self-improving through skills** — learns from experience by saving reusable procedures as skills
- **Persistent memory across sessions** — remembers who you are, your preferences, and lessons learned
- **Multi-platform gateway** — same agent on Telegram, Discord, Slack, WhatsApp, iMessage, Signal, and 15+ more
- **Provider-agnostic** — swap models and providers mid-workflow with 20+ providers supported
- **Extensible** — plugins, MCP servers, custom tools, webhook triggers, cron scheduling

---

## The ROSTR Architecture

ROSTR Agent ships with four integrated pillars:

| Component | Role | CLI | Agent Tool |
|-----------|------|-----|------------|
| **PAL** — Prompt Abstraction Layer | Compiles NL → typed Agent Manifest | `hermes pal compile` | `pal_compile` |
| **NPAO** — Decision Engine | 5D phase + 4D priority scoring | `hermes npao classify` | `npao_classify` |
| **RAG DAL** — Knowledge Engine | 3-tier multi-pass retrieval | `hermes ragdal search` | `ragdal_search` |
| **Rostr Hub** — Agent OS | 4-level state + knowledge compounding | `hermes hub {register,list,decide,learn,compound,search}` | `rostr_hub` |

```
User Input → PAL (Compiler) → NPAO (Orchestrator) → Agents + RAG DAL + Hub → Output
```

---

## Quick Start

```bash
# Clone
git clone https://github.com/diamitani/rostr-agent.git
cd rostr-agent

# Install
pip install -e .

# Run
rostr-agent

# Or use the ROSTR CLI directly
rostr-agent pal compile "Research best RAG architectures for production"
rostr-agent npao classify --revenue "Fix the auth bug in production"
rostr-agent ragdal search "Latest advances in multi-agent orchestration"
rostr-agent hub register --name "Builder Agent" --type builder
```

---

## ROSTR CLI Reference

### PAL — Prompt Abstraction Layer

```bash
# Compile natural language into an agent manifest
hermes pal compile "Build a Python REST API for user management"
hermes pal compile --context '{"project":"myapp"}' "Research vector DBs"
hermes pal compile --json "Analyze competitor GTM strategies"
```

Output: domain, agent type, model, phase, urgency, ambiguity score, full YAML manifest.

### NPAO — Navigate, Prioritize, Allocate, Orchestrate

```bash
# Classify a task through the 5D phase + 4D priority system
hermes npao classify "Fix the authentication bug"
hermes npao classify --domain debug --blocked 3 --revenue "Fix auth bug"
hermes npao classify --hours 1.5 --user "Add dark mode toggle"
```

Output: workflow phase, 4D priority score, allocation status, completion criteria, orchestration pattern.

### RAG DAL — Dynamic Acquisition Layer

```bash
# Multi-pass knowledge retrieval with credibility scoring
hermes ragdal search "What are best practices for RAG pipelines?"
hermes ragdal search --tier tier1 "Attention mechanisms survey"
```

Output: sub-topics, confidence per topic, sources used, passes completed, knowledge gaps.

### Rostr Hub — Persistent Reference Architecture

```bash
# Register an agent
hermes hub register --name "Research Agent" --type researcher --phases PreD

# List all agents
hermes hub list
hermes hub list --type builder

# Log a key decision
hermes hub decide --context "Database choice" --decision "PostgreSQL 17" --rationale "JSONB + vector support"

# Log a learning
hermes hub learn --context "Deploy pipeline" --insight "Always run staging smoke tests" --tags deploy,testing

# Knowledge compounding report
hermes hub compound

# Search past learnings
hermes hub search "deployment"
```

---

## Agent Tools

ROSTR Agent exposes five new tools that agents can call during conversations:

| Tool | What it does |
|------|-------------|
| `pal_compile` | Compile NL intent → typed agent manifest with domain, model, tools, behavior |
| `npao_classify` | Classify task into 5D phase + compute 4D priority score |
| `ragdal_search` | Multi-pass knowledge retrieval with 3-tier source credibility |
| `rostr_hub` | Register agents, log decisions/learnings, compound knowledge |
| `rostr_pipeline` | Full PAL → NPAO pipeline in one call |

---

## Architecture

```
rostr-agent/
├── rostr/                     # ROSTR core (PAL, NPAO, RAG DAL, Hub)
├── tools/
│   └── rostr_tools.py         # ROSTR tool registration
├── hermes_cli/
│   ├── main.py                # CLI entry point (+ ROSTR subcommands)
│   └── rostr_commands.py      # ROSTR CLI implementations
├── agent/                     # Agent core (prompt builder, memory, routing)
├── gateway/                   # Multi-platform messaging gateway
├── toolsets.py                # Toolset definitions (ROSTR tools included)
├── cli.py                     # Interactive CLI loop
├── run_agent.py               # Core conversation loop
└── tools/                     # 60+ built-in tools
```

---

## Research

**"ROSTR: A Unified Architecture for Production-Grade Multi-Agent Systems with Phase-Aware Orchestration and Persistent Knowledge Compounding"**

Patrick Diamitani · April 2026 · 22,000 words · 27 references

- **arXiv**: [2604.XXXXX](https://arxiv.org/abs/2604.XXXXX)
- **Keywords**: multi-agent systems, agent orchestration, RAG, prompt engineering, knowledge management, workflow automation

---

## The ROSTR Ecosystem

| Site | URL | Stack |
|------|-----|-------|
| ROSTR Agent (this repo) | `github.com/diamitani/rostr-agent` | Python, Hermes + ROSTR |
| SaaS Landing | `rostr-framework.vercel.app` | HTML, ethereal glass |
| Platform Dashboard | `platform-virid-psi.vercel.app` | Next.js 15 |
| PAL Docs | `pal-site-three.vercel.app` | Docusaurus 3 |

---

## License

MIT © Patrick Diamitani, 2026

Built on [Hermes Agent](https://github.com/NousResearch/hermes-agent) by Nous Research. ROSTR architecture and multi-agent orchestration by Patrick Diamitani.
