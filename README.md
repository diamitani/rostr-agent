# ROSTR Agent — Production AI Agent Platform

**Runtime · Orchestration · State · Tools · Reference**

<div align="center">

[![License: MIT](https://img.shields.io/badge/license-MIT-34d399?style=for-the-badge)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-a78bfa?style=for-the-badge)](https://python.org)
[![GitHub](https://img.shields.io/badge/github-diamitani/rostr--agent-22d3ee?style=for-the-badge)](https://github.com/diamitani/rostr-agent)

</div>

---

## What Is ROSTR Agent?

ROSTR Agent is a **production-grade AI agent platform** with smart model routing, persistent memory, and 1,048 integrations via Composio. Bring your own keys — supports 9 LLM providers.

**Website:** [rostragent.com](https://rostragent.com)

### Key Numbers

| Metric | Value |
|--------|-------|
| LLM Providers | **9** (OpenAI, Anthropic, Gemini, OpenRouter, AWS Bedrock, Azure, LM Studio, Ollama, Nous) |
| Integrations | **1,048** via Composio (Slack, Gmail, HubSpot, Notion, Linear, Jira + 1,000 more) |
| Packaged Skills | **6** (.skill files: PAL, NPAO, JTBD Builder, Instruction Architect, PRD Builder, Diagram Builder) |
| Skill Directories | **27** (pre-built skill templates) |
| Tests Passing | **202** (70 PAL + 83 Hub + 49 Orchestrator) |
| Task Completion | **88.6%** (vs 76.9% Hermes baseline) |

### Multi-LLM Benchmark (July 2026)

| Rank | Model | Provider | Score | Latency |
|------|-------|----------|-------|---------|
| 1 | deepseek-r1:14b | Ollama | 85.1% | 33s |
| 2 | qwen2.5-coder:14b | Ollama | 84.4% | 15s |
| 3 | qwen:latest | Ollama | 71.2% | 3s |
| 4 | deepseek-coder:6.7b | Ollama | 67.9% | 5s |
| 5 | qwen3.5:latest | Ollama | 57.7% | 98s |

[Full benchmark report →](LLM_BENCHMARK_REPORT.md)

---

## Architecture

```
User Input → PAL (Compiler) → NPAO (Router) → Agents + RAG DAL + Hub → Output
```

| Component | Role | Description |
|-----------|------|-------------|
| **PAL** — Prompt Abstraction Layer | Compiler | 5-stage pipeline: Intent → Context → Enhancement → Routing → Manifest |
| **NPAO** — Decision Engine | Router | 4D scoring (Necessity=0.35, Priority=0.25, Anxiety=0.25, Opportunity=0.15) |
| **RAG DAL** — Knowledge Engine | Retrieval | 3-tier multi-pass retrieval with credibility scoring |
| **Hub** — Persistent State | Storage | SQLite WAL, 6-level inheritance (session→project→team→org→agent→global) |

### 9 LLM Providers (BYOK)

| Provider | Type | Notes |
|----------|------|-------|
| OpenAI | Cloud API | GPT-4o, GPT-4-turbo |
| Anthropic | Cloud API | Claude Sonnet, Opus, Haiku |
| Google Gemini | Cloud API | Gemini Pro, Flash |
| OpenRouter | Cloud API | 100+ models via single key |
| AWS Bedrock | Cloud API | Enterprise, IAM auth |
| Azure OpenAI | Cloud API | Enterprise, AD auth |
| LM Studio | Local | Any GGUF model |
| Ollama | Local | Any GGUF model, free |
| Nous Research | Cloud API | Hermes models |

### Smart Routing

NPAO scores route to the optimal model per-task:
- **Necessity > 80**: deepseek-r1:14b (highest quality)
- **Priority > 70**: qwen2.5-coder:14b (best balance)
- **Quick tasks**: qwen:latest (sub-3s)

---

## Quick Start

```bash
git clone https://github.com/diamitani/rostr-agent.git
cd rostr-agent
pip install -e .
```

### Use the PAL Compiler

```python
from rostr.pal.compiler import PALCompiler

compiler = PALCompiler()
manifest = compiler.compile("Write a cold email to HR tech prospects")
# Returns: AgentManifest with domain, model, tools, behavior, routing
```

### Use the Hub

```python
from rostr.hub.store import SQLiteHubStore

hub = SQLiteHubStore("my_agent.db")
hub.save_state("session/current", {"task": "outreach", "progress": 0.5})
state = hub.resolve_state("session/current")  # Inherits from parent scopes
```

### Use Composio Integrations

```python
from rostr.integrations.composio_client import ComposioClient

client = ComposioClient()  # Uses COMPOSIO_API_KEY env var
apps = client.list_apps()  # Returns 1,048 available integrations
client.initiate_connection("user-123", "slack")  # OAuth flow
client.execute_action("user-123", "SLACK_SEND_MESSAGE", {"channel": "#general", "text": "Hello"})
```

---

## Project Structure

```
rostr-agent/
├── rostr/
│   ├── pal/                   # PAL Compiler (5-stage pipeline, 70 tests)
│   ├── hub/                   # Hub Persistence (SQLite WAL, 83 tests)
│   ├── integrations/          # Composio client (1,048 apps)
│   ├── npao.py                # NPAO 4D router
│   ├── orchestrator.py        # Full pipeline (49 tests)
│   ├── llm_provider.py        # 9-provider BYOK abstraction
│   ├── api_server.py          # FastAPI server
│   └── pal_skill.py           # PAL as a skill
├── apps/
│   └── cloud-web/             # Next.js 15 cloud app (Vercel AI SDK)
├── skills/                    # 6 packaged .skill files + 27 templates
├── index.html                 # Landing page (rostragent.com)
├── BUILD_PLAN.md              # 5-phase production deployment plan
├── TECHNICAL_PAPER.md         # Technical paper (no hallucinations)
├── LLM_BENCHMARK_REPORT.md    # Multi-model benchmark results
└── vercel.json                # Static site deployment config
```

---

## Deployment

### Landing Page (rostragent.com)
Static HTML deployed via Vercel. No build step required.

```json
// vercel.json
{
  "framework": null,
  "buildCommand": "",
  "installCommand": "echo 'Static site - no install needed'",
  "outputDirectory": "."
}
```

### Cloud Web App (app.rostragent.com)
Next.js 15 with Vercel AI SDK, streaming chat, auth, billing, integrations.

See [BUILD_PLAN.md](BUILD_PLAN.md) for full deployment steps.

---

## Pricing

| Plan | Price | Includes |
|------|-------|----------|
| Free | $0/mo | 10 executions/day, 3 skills, community support |
| Pro | $20/mo | Unlimited executions, all skills, 1,048 integrations, priority support |
| Enterprise | Custom | Dedicated infra, SLA, custom skills, team workspaces |

---

## License

MIT © Patrick Diamitani, 2026

Built on [Hermes Agent](https://github.com/NousResearch/hermes-agent) by Nous Research. ROSTR architecture, PAL compiler, Hub persistence, and Composio integration by Patrick Diamitani.
