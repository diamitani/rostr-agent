<div align="center">

# ROSTR

### AI Agent Operating System

**Knowledge Brain · NPAO Task Engine · Persistent Memory · Premium Dashboard**

[![License: MIT](https://img.shields.io/badge/License-MIT-D4AF37.svg)](LICENSE)
[![Node.js](https://img.shields.io/badge/Node.js-22+-339933.svg)](https://nodejs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.5+-3178C6.svg)](https://www.typescriptlang.org)

---

**One command. Your own AI agent. Running locally. With memory.**

</div>

## ⚡ Quick Start

```bash
git clone https://github.com/diamitani/rostr-agent.git && cd rostr-agent
./setup.sh
```

That's it. Setup will:
1. Install dependencies
2. Ask for your API keys (OpenAI, Anthropic, Groq — all optional)
3. Initialize the knowledge brain
4. Start the agent

## What is ROSTR?

ROSTR is a **standalone AI agent framework** that gives you a personal AI assistant with:

- 🧠 **Knowledge Brain** — Embedded PostgreSQL with hybrid search (vector + keyword + RRF fusion) and an auto-linking knowledge graph
- 📋 **NPAO Task Engine** — Necessity → Anxiety → Priority → Opportunity task classification
- 💾 **ContextEngine** — Persistent session memory across conversations
- 🔄 **PAL** — Prompt Abstraction Layer that compiles and enhances your prompts
- 📦 **gStack** — Skill library & plugin system. Convert and import skills from Claude, Antigravity, and Codex into the ROSTR ecosystem.
- 📡 **Multi-LLM** — Works with OpenAI, Anthropic, DeepSeek, Groq (BYOK)
- 🎛️ **Premium Dashboard** — Dark mode UI with chat, brain browser, task board, and settings

## Architecture

```
User Input → CLI / Dashboard → Gateway API → Runtime
                                                ├── PAL (Prompt Compiler)
                                                ├── NPAO (Task Classifier)
                                                ├── ContextEngine (Memory)
                                                ├── Brain (Knowledge Graph)
                                                └── LLM Router → Response
```

## CLI

```bash
# Setup
rostr init                    # Initialize brain + config
rostr doctor                  # Health checks

# Chat
rostr chat "message"          # Single message
rostr chat -i                 # Interactive REPL

# Brain
rostr search "query"          # Hybrid search
rostr import ./docs           # Import markdown files
rostr stats                   # Brain statistics

# Tasks (NPAO)
rostr task add "Fix auth bug" # Auto-classified as Necessity
rostr task list               # NPAO-ordered list
rostr task done <id>          # Complete task

# Memory
rostr context flash           # Load recent context
rostr context save            # Save session

# Skills (gStack)
rostr skill list              # List library skills
rostr skill import ./skill.md # Import external skill

# Server
rostr serve                   # Start gateway (port 3001)
```

## Dashboard

```bash
cd dashboard && npm install && npm run dev
```

Opens at `http://localhost:3000`:

| Page | Description |
|------|-------------|
| **Home** | Agent status, brain stats, activity feed |
| **Chat** | Full chat interface with streaming |
| **Brain** | Knowledge search + page browser |
| **Tasks** | NPAO Kanban board (N→A→P→O) |
| **Memory** | Session timeline + progress reports |
| **Settings** | API keys + model configuration |

## NPAO Framework

Every task is classified before execution:

| Category | Signal | Execution |
|----------|--------|-----------|
| **N** — Necessity | "I MUST..." | Execute first. Hard blocker. |
| **A** — Anxiety | "Won't have peace until..." | Clear before Priority work. |
| **P** — Priority | "I NEED to..." | Mission-critical. Full focus. |
| **O** — Opportunity | "I CAN..." | Growth. Execute when bandwidth allows. |

**Priority Score** = `(Urgency × 0.35) + (Dependencies × 0.30) + (Business × 0.25) + (Resource × 0.10)`

## API

Gateway runs on port 3001 with full REST API:

```
POST /api/chat           — Chat with agent
GET  /api/brain/search   — Hybrid search
GET  /api/brain/pages    — List pages
POST /api/tasks          — Create NPAO task
GET  /api/context/flash  — Context flash
GET  /api/status         — Agent health
```

Full WebSocket support at `ws://localhost:3001/ws` for real-time chat.

## Skills System

ROSTR uses markdown-based skills that define agent behaviors:

```
skills/
├── RESOLVER.md           # Skill dispatcher
├── brain-ops/SKILL.md    # Knowledge operations
├── task-manager/SKILL.md # NPAO task lifecycle
├── signal-detector/SKILL.md # Entity capture
└── context-engine/SKILL.md  # Session memory
```

## LLM Providers (BYOK)

Add any combination of API keys to `.env`:

| Provider | Key | Used For |
|----------|-----|----------|
| OpenAI | `OPENAI_API_KEY` | Chat + Embeddings (recommended) |
| Anthropic | `ANTHROPIC_API_KEY` | Chat (Claude) |
| DeepSeek | `DEEPSEEK_API_KEY` | Chat (free tier) |
| Groq | `GROQ_API_KEY` | Chat (fast inference) |

Failover chain: OpenAI → Anthropic → DeepSeek → Groq

## Project Structure

```
rostr-agent/
├── src/
│   ├── cli/              # CLI commands
│   ├── core/             # Brain engine, search, embeddings, knowledge graph
│   ├── agents/           # Runtime, PAL, NPAO, ContextEngine
│   └── gateway/          # HTTP + WebSocket server
├── dashboard/            # Next.js premium dashboard
├── skills/               # Markdown-based skill files
├── setup.sh              # One-click installer
├── AGENTS.md             # Agent operating protocol
└── CLAUDE.md             # Claude Code instructions
```

## Inspiration

ROSTR stands on the shoulders of:

- [gBrain](https://github.com/garrytan/gbrain) — PGLite knowledge engine, hybrid search, skill system
- [OpenClaw](https://github.com/nicepkg/openclaw) — Gateway architecture, onboarding patterns

## License

MIT — Patrick Diamitani, 2026

---

<div align="center">

**⭐ Star this repo if ROSTR helps you build with AI agents**

[Report Bug](https://github.com/diamitani/rostr-agent/issues) · [Request Feature](https://github.com/diamitani/rostr-agent/issues) · [Documentation](https://github.com/diamitani/rostr-paper)

</div>
