# ROSTR Agent Framework

## Read Order

AI agents should read files in this order:

1. This file (`AGENTS.md`) — operating protocol
2. `skills/RESOLVER.md` — skill dispatcher
3. `src/agents/npao.ts` — NPAO task classification
4. `src/agents/pal.ts` — PAL prompt compilation
5. `src/agents/context-engine.ts` — session memory

## Operating Protocol

### NPAO — Classify Every Task

Before executing any task, classify it:

- **N — Necessity** ("I MUST"): Hard blocker. Execute first. Nothing downstream works without it.
- **A — Anxiety** ("I WON'T HAVE PEACE"): Cognitive friction. Clear BEFORE Priority work.
- **P — Priority** ("I NEED"): Mission-critical. Execute with full focus.
- **O — Opportunity** ("I CAN"): Growth, upside. Execute last.

Execution order: **N → A → P → O**. Never skip.

### PAL — Always Active

Before executing any prompt:
1. Extract intent
2. Inject context from ContextEngine + brain
3. Enhance precision
4. Route to correct agent/tool

### ContextEngine — Always Active

- End of session → `rostr context save` → CACHE
- Start of session → `rostr context flash` → RETRIEVE
- Weekly → generate report → REPORT

### Brain-First Rule

Always search the brain before making external API calls or generating new content.
The brain compounds — every interaction should enrich it.

### Quality Rules

- Never delete session files — append-only
- `what_failed` must be specific ("HTTP 401 on /api/chat" not "auth issue")
- Cite sources from brain when referencing stored knowledge
- Never hallucinate — say "I don't know" when uncertain

## Trust Boundary

- Read: all files in the workspace
- Write: only files the user explicitly requests
- Execute: only commands the user approves
- Network: only configured API endpoints (LLM providers)
