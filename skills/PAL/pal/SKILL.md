# PAL — Prompt Abstraction Layer

**Production skill for compiling natural language requests into typed AgentManifest JSON.**

## About

PAL is a 5-stage compilation pipeline that transforms raw, casual user input into structured agent execution plans. It extracts intent, injects context, enhances prompts, and routes to the right LLM with optimal parameters.

**Use this when:**
- You need to abstract away from literal user requests to underlying intent
- You're building multi-agent systems and need consistent intent interpretation
- You want to route user input to different LLMs based on task type (Claude for reasoning, GPT for speed, Ollama locally)
- You need to inject context (corporate knowledge, user preferences, system constraints) before execution

**Output:** Typed `AgentManifest` JSON with:
- `domain` (code|design|content|sales|ops|idea|debug|deploy)
- `model` (claude-opus|gpt-4|ollama-local)
- `temperature` (0-1 for model config)
- `tools` (list of MCPs/skills to enable)
- `behavior` (execution style: auto-approve, ask, report-only)
- `enhanced_prompt` (context-injected, rewritten request)
- `routing_reason` (why this domain/model/tools)

## Stages

1. **Intent Extraction** — Parse raw input for goal, domain, subject, constraints, output format
2. **Context Injection** — Pull relevant context (CLAUDE.md, user prefs, codebase, project memory)
3. **Prompt Enhancement** — Rewrite input with precision, break into sub-tasks, inject knowledge
4. **Compilation** — Generate typed AgentManifest with model/temperature/tools/behavior
5. **Routing** — Route to appropriate LLM + MCPs based on domain and complexity

## Example

**Input:**
```
make a basketball site for my school
```

**Output:**
```json
{
  "domain": "design",
  "model": "claude-opus",
  "temperature": 0.7,
  "tools": ["firecrawl-scrape", "design-html"],
  "behavior": "auto-approve",
  "enhanced_prompt": "Build a Next.js basketball site for a high school. Include: responsive roster page, schedule/scores, photo gallery, contact form. Use mobile-first design, school colors if mentioned, static generation for performance.",
  "routing_reason": "Design-heavy request mapped to Opus for multi-stage creative work; includes visual design + responsive layout"
}
```

## Dependencies

- `anthropic` — Claude API
- `openai` — GPT routing
- `requests` — Web search MCP
- `pydantic` — Schema validation
- `pyyaml` — Config parsing

## Files

- `pal/SKILL.md` — This file
- `pal/main.py` — Execution logic (5-stage pipeline)
- `pal/schema.json` — Input/output schemas
- `pal/requirements.txt` — Dependencies
- `tests/test_pal.py` — Test suite with 5+ cases
