---
name: rostr-agent
description: "Build, extend, and deploy ROSTR Agent — the self-improving multi-agent framework with built-in PAL, NPAO, RAG DAL, and Rostr Hub."
version: 1.0.0
author: Patrick Diamitani
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [rostr, multi-agent, orchestration, pal, npao, rag, knowledge]
    homepage: https://github.com/diamitani/rostr-agent
---

# ROSTR Agent

ROSTR Agent is a production-grade multi-agent framework that fuses the Hermes Agent runtime with the ROSTR architecture — a unified system for agent orchestration, knowledge retrieval, and persistent state management.

## Quick Start

```bash
git clone https://github.com/diamitani/rostr-agent.git
cd rostr-agent
pip install -e .
rostr-agent
```

## ROSTR CLI

### PAL — Compile Intent
```bash
hermes pal compile "Build a Python REST API for user management"
hermes pal compile --json "Research top 3 GTM platforms"
```

### NPAO — Classify Tasks
```bash
hermes npao classify "Fix the authentication bug"
hermes npao classify --revenue --blocked 3 "Fix auth bug"
```

### RAG DAL — Knowledge Retrieval
```bash
hermes ragdal search "Best practices for RAG pipelines"
hermes ragdal search --tier tier1 "Attention mechanisms"
```

### Rostr Hub — State Management
```bash
hermes hub register --name "Builder Agent" --type builder
hermes hub list
hermes hub decide --context "DB choice" --decision "PostgreSQL" --rationale "JSONB support"
hermes hub learn --context "Deploy" --insight "Always test staging first" --tags deploy
hermes hub compound
hermes hub search "deployment"
```

## Agent Tools

When loaded as a skill or when ROSTR tools are enabled, the agent can call:

| Tool | Purpose |
|------|---------|
| `pal_compile` | Compile NL → typed agent manifest |
| `npao_classify` | 5D phase + 4D priority classification |
| `ragdal_search` | Multi-pass retrieval with credibility scoring |
| `rostr_hub` | Agent registry, decisions, learnings, compounding |
| `rostr_pipeline` | Full PAL → NPAO pipeline |

## ROSTR Architecture

```
User Intent
    ↓
PAL Compilation (Intent → Agent Manifest)
    ↓
NPAO Classification (5D Phase + 4D Priority)
    ↓
Agent Execution + RAG DAL (if knowledge needed)
    ↓
Persistent State (Rostr Hub)
    ↓
Output + Learning
```

## Discoverability

### When to Use This Skill

Load this skill when:
- Building multi-agent systems or agentic workflows
- Implementing PAL compilation pipelines
- Setting up NPAO phase-aware orchestration
- Configuring RAG DAL knowledge retrieval
- Managing persistent agent state with Rostr Hub
- Extending or contributing to ROSTR Agent

### Trigger Keywords

`rostr`, `pal`, `npao`, `ragdal`, `rostr hub`, `agent manifest`, `phase classification`,
`priority scoring`, `multi-agent`, `orchestration`, `knowledge retrieval`, `source credibility`,
`agent registry`, `knowledge compounding`, `rostr agent`, `rostr-agent`

## Project Structure

```
rostr-agent/
├── rostr/                     # ROSTR core (PAL, NPAO, RAG DAL, Hub)
├── tools/
│   └── rostr_tools.py         # ROSTR tool registration
├── hermes_cli/
│   ├── main.py                # CLI entry point (+ ROSTR subcommands)
│   └── rostr_commands.py      # ROSTR CLI implementations
├── agent/                     # Agent core
├── gateway/                   # Multi-platform gateway
├── toolsets.py                # Toolset definitions
├── cli.py                     # Interactive CLI
└── run_agent.py               # Core conversation loop
```

## Research

"ROSTR: A Unified Architecture for Production-Grade Multi-Agent Systems with Phase-Aware Orchestration and Persistent Knowledge Compounding" — Patrick Diamitani, April 2026. arXiv:2604.XXXXX

## Related Skills

- `pal-compiler` — PAL 5-stage compiler protocol
- `npao-orchestrator` — NPAO phase-aware orchestration
- `ragdal-knowledge` — RAG DAL 3-tier retrieval
- `rostr-hub` — Rostr Hub state management
- `rostr-agent-builder` — 7-phase agent construction pipeline
