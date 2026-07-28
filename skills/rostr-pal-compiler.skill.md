---
name: rostr-pal-compiler
description: PAL — Prompt Abstraction Layer for ROSTR. Compiles natural language into typed agent manifests. 5-stage pipeline: Intent Extraction → Context Injection → Semantic Enhancement → Runtime Compilation → Output Routing.
---

# PAL Compiler — ROSTR Agent Skill

## When to Use

Use this skill when you need to compile natural language intent into a structured agent manifest for the ROSTR Agent Cloud backend.

## Pipeline

```
User Intent → PAL Compiler → Enhanced Prompt → NPAO Router → LLM Call → Response
```

## API Usage

```bash
# PAL-enhance a prompt
curl -X POST https://api.rostragent.com/api/rostr/pal-enhance \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Build a REST API with auth"}'

# Full chat with ROSTR pipeline (BYOK)
curl -X POST https://api.rostragent.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-your-openai-key" \
  -d '{
    "model": "rostr-agent",
    "messages": [{"role": "user", "content": "Build a landing page"}],
    "provider": "openai"
  }'
```

## PAL Intent Schema

```json
{
  "primary_intent": "verb + object",
  "domain": "code | design | research | ops | sales | content | deploy | debug",
  "subject": "thing being acted upon",
  "constraints": ["scope limits"],
  "urgency": "immediate | queued | scheduled"
}
```

## ROSTR Hub Integration

PAL-compiled manifests are persisted to the ROSTR Hub for cross-session context.
