---
name: rostr-npao
description: NPAO — Navigate, Prioritize, Allocate, Orchestrate. Phase-aware orchestration engine for multi-agent systems. 5D phase taxonomy + 4D priority scoring.
---

# NPAO — ROSTR Agent Skill

## 5D Phase Taxonomy

| Phase | Score | Question |
|-------|-------|----------|
| PreD (0) | 2.0 | "Is this worth building?" |
| Design (1) | 4.0 | "What exactly are we building?" |
| Development (2) | 6.0 | "Does it work?" |
| Deployment (3) | 8.0 | "Is it safe to ship?" |
| Debugging (4) | 10.0 | "What broke, why, how prevent?" |

## 4D Priority Scoring

```
Priority = (Phase × 0.35) + (Dependency × 0.30) + (Business × 0.25) + (Resource × 0.10)
Thresholds: ≥7.0 Immediate | 4.0–6.9 Queued | <4.0 Backlog
```

## Agent Allocation

```python
score = (context_score × 0.50) + (specialization × 0.35) + (load × 0.15)
```

## Usage with ROSTR Backend

NPAO runs automatically on every chat request. The phase classification is returned in the `rostr_phase` field.
