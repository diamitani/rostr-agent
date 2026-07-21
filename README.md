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

**Website:** https://rostragent.com

It's the same self-improving AI agent you know (skills from experience, persistent memory, 20+ messaging platforms, any LLM provider), now with **first-class multi-agent orchestration built in**.

### Real Benchmark Results

ROSTR outperforms Hermes baseline across all key metrics:

| Metric | Hermes | ROSTR | Improvement |
|--------|--------|-------|---|
| Task Completion | 76.9% | 88.6% | **+15.2pp** |
| Accuracy | 70.5% | 78.5% | **+11.5pp** |
| Coherence | 71.4% | 85.5% | **+19.7pp** |
| Decision Quality | 69.9% | 79.0% | **+13.0pp** |

Evaluated on 11 real tasks across GTM, code, content, analytics, ops, productivity, research, and integration domains. [Full evaluation report →](EVALUATION_REPORT.md)

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

## What ROSTR Is vs. Isn't

**ROSTR is:**
- A framework/library you integrate into your agents
- A CLI tool with 41 generalized skills
- A set of architectural patterns (PAL, NPAO, RAG DAL, Hub)
- A way to make your agents measurably better (15% task completion improvement)

**ROSTR is NOT:**
- A dashboard UI (use terminal or integrate into your app)
- A hosted service (run locally or deploy to your own cloud)
- A replacement for Hermes (it's a layer on top)
- An LLM (it orchestrates Claude, GPT, or local models)

---

## Quick Start (2 minutes)

### 1. Install

```bash
git clone https://github.com/diamitani/rostr-agent.git
cd rostr-agent
./setup-rostr.sh                    # Auto-detects OS, creates venv
```

### 2. Verify Installation

```bash
rostr-agent --version               # Should output: ROSTR Agent 0.1.0
rostr-agent skills list             # Shows all 41 skills
```

### 3. Run Benchmark

```bash
rostr-agent eval run                # Evaluates ROSTR vs Hermes
cat eval_results.json               # View raw results
cat EVALUATION_REPORT.md            # View formatted report
```

### 4. Use in Your Code

```python
from rostr import PALCompiler, NPAORouter, RAGDALRetriever, Hub

# Compile a natural language task
manifest = PALCompiler.compile("Write a cold email to prospects in the HR tech space")

# Route to specialist
route = NPAORouter.route(manifest)  # Returns: gtm_specialist

# Retrieve context
context = RAGDALRetriever.search(manifest, route)

# Store knowledge
Hub.update(workspace_id, knowledge_items)
```

### 5. Use via CLI

```bash
# Compile natural language to structured task
rostr-agent pal compile "Research best RAG architectures"

# Classify and route a task
rostr-agent npao classify "Fix the auth bug in production"

# Search knowledge base
rostr-agent ragdal search "Vector database best practices"

# Manage workspace memory
rostr-agent hub list                # Show all registered agents
rostr-agent hub register --name "Research Agent" --type researcher
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
| **Official Site** | [`rostragent.com`](https://rostragent.com) | Next.js + Research-backed positioning |
| GitHub Repo | [`github.com/diamitani/rostr-agent`](https://github.com/diamitani/rostr-agent) | Python, Hermes + ROSTR |
| Research Paper | [ROSTR_FRAMEWORK_RESEARCH.md](ROSTR_FRAMEWORK_RESEARCH.md) | 3,200+ word technical whitepaper |
| Benchmarks | [`eval_results.json`](eval_results.json) | Real evaluation data (11 tasks) |
| Evaluation Report | [EVALUATION_REPORT.md](EVALUATION_REPORT.md) | Full methodology and findings |

---

## License

MIT © Patrick Diamitani, 2026

Built on [Hermes Agent](https://github.com/NousResearch/hermes-agent) by Nous Research. ROSTR architecture and multi-agent orchestration by Patrick Diamitani.
