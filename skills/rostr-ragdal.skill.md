---
name: rostr-ragdal
description: RAG DAL — Retrieval-Augmented Generation Dynamic Acquisition Layer. Autonomous multi-pass retrieval with source tier credibility scoring and coverage validation.
---

# RAG DAL — ROSTR Agent Skill

## Three-Tier Source Architecture

| Tier | Score | Sources |
|------|-------|---------|
| Tier 1 | 1.00 | Academic, official docs, .gov |
| Tier 2 | 0.75 | Major news, trade pubs, analyst reports |
| Tier 3 | 0.40 | Blogs, forums, social media |

## Multi-Pass Retrieval

```
Pass 1: Broad sweep → decompose into sub-topics → assess coverage
Pass 2: Gap fill → Tier 1-2 targets for low-confidence topics
Pass 3: Deep verification → Tier 1 only
Pass 4: (if needed) Deep search all tiers
Threshold: confidence ≥ 0.8
```

## Confidence Scoring

```
confidence = (source_count × 0.35) + (consistency × 0.30) + 
             (tier_distribution × 0.25) + (recency × 0.10)
```
