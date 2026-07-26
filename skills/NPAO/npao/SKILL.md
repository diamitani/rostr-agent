# NPAO — Nuanced Prompt Abstraction Orchestrator

**Advanced multi-agent orchestration layer that extends PAL with nuanced decision-making, confidence scoring, and fallback routing.**

## About

NPAO builds on top of PAL to handle ambiguous, multi-intent requests that don't map cleanly to a single domain. It:

1. **Detects ambiguity** — flags requests that could map to multiple domains
2. **Scores confidence** — rates each potential domain match with a confidence score (0-1)
3. **Resolves conflicts** — uses heuristics to pick the best domain when multiple match
4. **Enables fallback routing** — if primary LLM fails, auto-routes to fallback
5. **Tracks routing history** — logs decisions for observability and learning

**Use when:**
- A request maps to multiple domains (e.g., "review my marketing copy and fix the grammar" = sales + content)
- You need confidence scoring on domain predictions
- You want observable, traceable routing decisions
- You're building multi-agent systems that need fallback paths
- You want to learn from routing decisions over time

**Output:** Enhanced `AgentManifest` with:
- `primary_domain` (highest confidence match)
- `secondary_domains` (other potential matches with scores)
- `confidence_score` (0-1, how confident about primary)
- `ambiguity_level` (low|medium|high)
- `routing_trace` (what influenced this decision)
- `fallback_routes` (alternate LLMs if primary fails)

## Key Differences from PAL

| Feature | PAL | NPAO |
|---|---|---|
| Domain detection | Single match | Multi-match with confidence |
| Ambiguity handling | Uses first match | Scores all matches, resolves conflicts |
| Fallback routing | Single fallback | Multiple ranked fallbacks |
| Observability | None | Full routing trace & history |
| Multi-intent support | No | Yes (split multi-intent into sub-tasks) |
| Confidence scoring | No | 0-1 score per domain |

## Example

**Input:**
```
review my marketing copy and fix the grammar
```

**Output:**
```json
{
  "primary_domain": "content",
  "secondary_domains": [
    { "domain": "sales", "confidence": 0.6, "reason": "mentions marketing" },
    { "domain": "code", "confidence": 0.3, "reason": "mentions grammar/writing" }
  ],
  "confidence_score": 0.85,
  "ambiguity_level": "medium",
  "routing_trace": {
    "matches": [
      { "pattern": "marketing", "domains": ["sales", "content"], "score": 0.7 },
      { "pattern": "grammar", "domains": ["content"], "score": 0.9 }
    ],
    "resolution": "chose 'content' for higher frequency and specificity"
  },
  "fallback_routes": [
    { "model": "claude-sonnet", "reason": "sales context requires faster routing" },
    { "model": "gpt-4", "reason": "if Opus unavailable, use GPT-4" }
  ]
}
```

## Dependencies

- `pydantic>=2.0` — schema validation
- `numpy` — confidence score computation
- `requests` — API calls for augmented context
- Same as PAL: `anthropic`, `openai`, etc.

## Files

- `npao/SKILL.md` — This file
- `npao/main.py` — Execution logic (nuanced routing + fallback)
- `npao/schema.json` — Input/output schemas
- `npao/requirements.txt` — Dependencies
- `npao/confidence_scorer.py` — Confidence scoring engine
- `tests/test_npao.py` — Test suite with 5+ cases
