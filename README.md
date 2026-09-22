# Rostr Dev Agent — DI-CTO Governed Multi-Agent Harness

A production-grade, governed CTO agent harness for Diamitani Industries uniting the **ROSTR / PAL Framework**, **Vercel AI Ecosystem**, **Pydantic Deep Agents**, and **AWS Bedrock AgentCore** runtime.

Decision-layer calls (PAL intent, NPAO, allocation, gates) now go through a **System One** client. With `TYPESAFE_API_KEY` that is **Jev**. Without a key, a typed local engine keeps the same question schema. Generation (code, prompts, PRs) stays on a System Two LLM. See [docs/JEV_INTEGRATION.md](docs/JEV_INTEGRATION.md).

---

## Quick Start

### 1. Launch the ROSTR Vercel Tech Stack Harness
```bash
cd Projects/rostr-vercel-harness
npm install
npm run dev
# Open http://localhost:3000 in your browser
```

### 2. Python Pydantic Deep Runtime & CLI
```bash
# Install dependencies
pip install pydantic-deep -r requirements.txt

# Compile only (System One, no LLM generation)
python3 Tools/pydantic_deep_runner.py --compile-only "Research whether we should build a billing refund workflow"

# Compile then run System Two generation
python3 Tools/pydantic_deep_runner.py "Scaffold Next.js 15 landing page with Stripe pricing"
```

### 3. Run EVE Evaluation Benchmarks
```bash
cd Projects/rostr-vercel-harness
npm run test:evals
```

### 4. Execute Sandbox Tests
```bash
cd Projects/rostr-vercel-harness
npm run build
```

### 5. System One / Jev
```bash
export TYPESAFE_API_KEY=sk-...          # real Jev
# or AI_GATEWAY_API_KEY / VERCEL_OIDC_TOKEN / OPENROUTER_API_KEY
# Generation: AI_GATEWAY_API_KEY (or OIDC on Vercel) / XAI_API_KEY
# or ROSTR_SYSTEM_ONE_ADAPTER=1         # LLM adapter, comparison only

python3 -m unittest discover -s Projects/di-cto-agentcore/tests -v
```

---

## Architecture & Stack Overview

```
Diamitani Industries CTO Agent System
├── 1. ROSTR / PAL Framework
│   ├── PAL 5-Stage Intent Compiler (Intent → Dependency → Context → Sandbox → Memory)
│   ├── System One decision layer (Jev when keyed, else local typed engine)
│   ├── NPAO 4D Priority Scoring: (Phase × 0.35) + (Dependency × 0.30) + (Business × 0.25) + (Resource × 0.10)
│   └── 9 Specialist Sub-Agents (Product Architect, JTBD/NPAO Planner, Experience Engineer, etc.)
│
├── 2. Pydantic Deep Agent Runtime (Tools/pydantic_deep_runner.py)
│   ├── Compiles through System One BEFORE spawning a deep agent
│   ├── Blocks on named approval gates
│   └── Sandbox code execution with memory persistence
│
├── 3. Vercel Tech Stack Harness (Projects/rostr-vercel-harness/)
│   ├── Vercel AI SDK Core & Streaming (/api/chat)
│   ├── PAL compiler at src/lib/jev (wired from src/lib/pal/compiler.ts)
│   ├── Vercel AI Gateway (Jev route → spacexai/grok-4.5 / claude-sonnet-4.6 / gemini flash)
│   ├── Vercel Code Sandbox (/api/sandbox/execute - JS, TS, Python execution)
│   ├── EVE Benchmark Suite (10 automated gold eval test cases)
│   └── Patrick Diamitani YouTube Showcase (vKGtIY-MR8Y embedded player & demo scrubber)
│
└── 4. AWS Bedrock AgentCore Python Harness
    ├── Governed Soul & System Prompt (soul.md)
    ├── Modular Skills: PAL, NPAO, Research (RAG DAL), Delivery, QA
    ├── MCP Tool Adapters: Filesystem, Sandbox, GitHub, Web, Cloud CLI
    └── Episodic Memory: 'rostr_decisions' and 'rostr_learnings'
```

---

## Jev vs the adapter vs an LLM

| Tool | What it is | Use in ROSTR |
| --- | --- | --- |
| **Jev** (`typesafe-sdk`, model `jev` / `jev-latest`) | System One model. Unstructured state in, typed probabilities out. Cannot generate strings. | Production PAL / NPAO / allocation / gates |
| **system-one-adapter-python** | Same `system_one` API, backed by GPT/Claude | A/B evals only. Not production routing. |
| **Claude / Grok / GPT** | System Two generators | Semantic enhancement, code, tool calls, writeups |

The previous compiler first-matched `fix`/`build`/`deploy` and invented NPAO weights `5.5 / 6.5 / 7.0`. That is the bug this layer removes. Mixed prompts such as *"Research whether we should build a billing refund workflow"* classify as **PreD**, not Development.

---

## Featured Demo Video

Watch **Patrick Diamitani** demonstrate the ROSTR multi-agent framework, PAL compiler, and Bedrock AgentCore:
- **YouTube Embed**: `https://www.youtube.com/embed/vKGtIY-MR8Y`
- **Watch on YouTube**: [ROSTR Agent Demo by Patrick Diamitani](https://www.youtube.com/watch?v=vKGtIY-MR8Y)

---

## 9 Specialist Sub-Agents

| Sub-Agent | Role & Scope | Active Phases | Approval Gate |
|:----------|:-------------|:--------------|:--------------|
| `product-architect` | Planning, PRDs, domain boundaries | PreD, Design | None |
| `jtbd-npao-planner` | Jobs-to-be-Done, NPAO 4D priority | PreD, Design | None |
| `experience-engineer` | UX specifications, WCAG AA tokens | Design, Development | None |
| `application-engineer` | Full-stack APIs, AI SDK streaming | Development, Debugging | None |
| `agent-runtime-engineer` | soul.md governance, SKILL packages, pydantic-deep | Design, Development, Debug | None |
| `identity-commerce-qa` | Auth, OAuth, Stripe checkout | Development, Deploy | **Required** |
| `quality-engineer` | Functional QA, E2E benchmarks | Development, Deploy, Debug | None |
| `devops-release-engineer` | CI/CD, Vercel/AWS IaC, rollback | Deploy | **Required** |
| `security-reviewer` | Threat model, secret detection | All Phases | None |

---

## Verification & Test Results

- **System One PAL**: Mixed-intent and 5D gold cases in `Projects/di-cto-agentcore/tests/test_system_one.py`.
- **Pydantic Deep Integration**: Verified (`pydantic_deep` version 0.3.43 installed and functional).
- **EVE Benchmark Suite**: 10 gold evaluation benchmarks still asserted against `compilePALIntent`.
- **Next.js Production Build**: 0 errors, full static and dynamic route optimization.

---
*Diamitani Industries — Governed Agentic Engineering*
