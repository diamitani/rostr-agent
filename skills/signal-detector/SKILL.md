---
name: signal-detector
description: >
  Captures ideas, entities, and actionable signals from every message. Runs in parallel,
  never blocks the main response. This is how the brain compounds passively.
triggers:
  - fires on EVERY inbound message
---

# Signal Detector — Passive Knowledge Capture

## When to Fire

On EVERY inbound user message. This skill runs in the background and never blocks
the main response pipeline.

## What to Capture

### Entities
- **People**: Names mentioned with context ("John from Acme Corp")
- **Companies**: Organization names with relationship
- **Tools/Tech**: Software, frameworks, APIs mentioned
- **Concepts**: Domain-specific terms worth remembering

### Ideas
- New project ideas
- Feature requests
- Process improvements
- Strategic insights

### Action Items
- Implicit tasks ("we should probably..." → task candidate)
- Commitments ("I'll send that by Friday" → deadline)
- Follow-ups ("let's revisit this next week")

## Processing

1. Scan message for entity patterns (capitalized names, @mentions, URLs)
2. Check if entity already exists in brain
3. If new: create a page stub with what we know
4. If existing: enrich with new context
5. Extract action items → create NPAO tasks (opportunity-level by default)

## Quality Rules

- Never create duplicate pages — check brain first
- Entity pages should have type: 'person', 'company', 'concept'
- Always tag with conversation context
- Keep signal detection fast — no LLM calls, pure pattern matching
