---
name: rag-dal
description: >-
  RAG DAL (Retrieval-Augmented Generation Dynamic Acquisition Layer) — ROSTR's
  knowledge engine for autonomous multi-pass retrieval with three-tier source
  credibility scoring, gap detection, and confidence-based convergence.
version: 2.0.0
author: Pat
triggers:
  - rag dal
  - knowledge retrieval
  - multi-pass search
  - research with credibility
  - tiered source retrieval
  - grounded generation
  - knowledge acquisition
  - deep research
  - rostr retrieval
tools:
  - web_search
  - web_extract
  - write_file
  - read_file
  - execute_code
---

# RAG DAL — Retrieval-Augmented Generation Dynamic Acquisition Layer

The knowledge engine from the ROSTR framework. Use this skill for rigorous, multi-pass research with source credibility scoring and coverage validation.

**Reference:** [github.com/diamitani/rostr-agent](https://github.com/diamitani/rostr-agent) — see `rostr/ragdal/__init__.py` for implementation.

---

## 1. Core Architecture

### Three-Tier Source Credibility

| Tier | Credibility | Sources | Use Case |
|------|-------------|---------|----------|
| **Tier 1** | 1.0 | Academic (arXiv, PubMed, Google Scholar), official docs (.gov, .edu), standards (IEEE, ACM, RFC) | Ground truth, foundational claims |
| **Tier 2** | 0.75 | Major news (Reuters, AP, BBC, NYT, WSJ), trade pubs, analyst reports (Gartner, McKinsey, Forrester) | Contextualize, current events |
| **Tier 3** | 0.40 | Blogs, forums (Stack Overflow, Reddit, HN), social media, user reviews | Real-world signal, edge cases, sentiment |

### Tier Classification Rules

```
Tier 1 Domains:
  arxiv.org, pubmed.ncbi.nlm.nih.gov, scholar.google.com,
  *.gov, *.edu, doi.org, acm.org, ieee.org,
  nature.com, science.org, pnas.org

Tier 2 Domains:
  reuters.com, apnews.com, bbc.com, nytimes.com, wsj.com,
  techcrunch.com, wired.com, theverge.com,
  gartner.com, mckinsey.com, forrester.com

Tier 3: Everything else (default)
```

---

## 2. Multi-Pass Retrieval Algorithm

### Pass Sequence

| Pass | Focus | Target Tier | Action |
|------|-------|-------------|--------|
| **Pass 1** | Broad sweep | All | 5 search queries, decompose into sub-topics, assess initial coverage |
| **Pass 2** | Gap fill | Tier 1-2 | 2 searches per low-confidence sub-topic |
| **Pass 3** | Deep verification | Tier 1 only | Verify remaining gaps with authoritative sources |
| **Pass 4** | Final sweep (optional) | All | Deep search if ≥2 topics still < 0.6 confidence |

### Convergence Criteria

```
DONE when: ALL sub-topics have confidence ≥ 0.8

Coverage threshold met when:
  - ≥2 Tier 1/2 sources confirm each claim
  - No contradictions among high-credibility sources
  - Recency: <90 days for time-sensitive OR verified timeless
  - All sub-questions answered
```

---

## 3. Confidence Scoring Formula

```
confidence(topic) = 
  (source_count × 0.35) +
  (consistency × 0.30) +
  (tier_distribution × 0.25) +
  (recency × 0.10)

Where:
  source_count: normalized count of sources (cap at 10 = 1.0)
  consistency: agreement across sources (0.0-1.0)
  tier_distribution: weighted avg of source tiers
  recency: freshness score (1.0 = today, decays over 90 days)
```

---

## 4. Execution Workflow

### Step 1: Decompose Query

Break the user's query into 3-5 sub-topics:

```
Query: "How does GraphQL compare to REST for mobile apps?"

Sub-topics:
1. GraphQL fundamentals and mobile-specific features
2. REST fundamentals and mobile optimization patterns
3. Performance comparison (latency, bandwidth, caching)
4. Developer experience and tooling comparison
5. Real-world adoption and case studies
```

### Step 2: Pass 1 — Broad Sweep

Execute 5 diverse search queries:

```python
queries = [
    f"{query}",                           # Direct
    f"{query} site:arxiv.org OR site:acm.org",  # Academic
    f"{query} case study production",     # Real-world
    f"{query} benchmark comparison",      # Data
    f"{query} 2024 2025 latest",          # Recent
]
```

For each result, classify tier and extract:
- URL, title, published date
- Content summary
- Topics covered
- Credibility score

### Step 3: Assess Coverage

For each sub-topic, calculate confidence:

```
Sub-topic 1: GraphQL mobile features
  Sources: 4 (2 Tier 1, 1 Tier 2, 1 Tier 3)
  Consistency: 0.9 (all agree)
  Tier distribution: (2×1.0 + 1×0.75 + 1×0.4) / 4 = 0.79
  Recency: 0.85
  
  Confidence = (0.4×0.35) + (0.9×0.30) + (0.79×0.25) + (0.85×0.10)
             = 0.14 + 0.27 + 0.20 + 0.085
             = 0.69 ← BELOW threshold, needs Pass 2
```

### Step 4: Pass 2 — Gap Fill

Target low-confidence sub-topics with Tier 1-2 focused queries:

```python
for topic in sub_topics:
    if confidence[topic] < 0.8:
        queries = [
            f'"{topic}" site:arxiv.org',
            f'"{topic}" research paper PDF',
        ]
        # Execute and re-score
```

### Step 5: Pass 3 — Deep Verification (if needed)

For stubborn gaps, use Tier 1 only:

```python
for topic in sub_topics:
    if confidence[topic] < 0.8:
        queries = [
            f'"{topic}" site:gov OR site:edu filetype:pdf',
        ]
```

### Step 6: Pass 4 — Final Sweep (if ≥2 topics still < 0.6)

Deep search across all tiers as last resort. Mark topics as "unresolvable" if still < 0.6 after Pass 4.

---

## 5. Knowledge Entry Schema

Every retrieved source produces a `KnowledgeEntry`:

```json
{
  "entry_id": "uuid",
  "query_origin": "original question",
  "content": "extracted text",
  "summary": "3-5 sentence distillation",
  "source": {
    "url": "https://...",
    "title": "...",
    "published_date": "ISO 8601",
    "tier": 1,
    "credibility_score": 0.85
  },
  "metadata": {
    "topics": ["tags"],
    "entities": ["named entities"],
    "data_type": "factual | opinion | statistical | procedural"
  },
  "confidence": 0.87
}
```

---

## 6. Output Format

### Coverage Report

```yaml
query: "How does GraphQL compare to REST for mobile apps?"
passes_completed: 2
sources_used: 14
is_complete: true

sub_topics:
  - topic: "GraphQL fundamentals and mobile-specific features"
    confidence: 0.87
    sources: 4
    
  - topic: "REST fundamentals and mobile optimization patterns"
    confidence: 0.82
    sources: 3
    
  - topic: "Performance comparison"
    confidence: 0.91
    sources: 5
    
  - topic: "Developer experience and tooling"
    confidence: 0.85
    sources: 2
    
gaps: []  # Empty = complete coverage
```

### Grounded Generation Prompt

After retrieval, construct the generation prompt:

```
TASK: {user_query}

GROUNDED CONTEXT (use ONLY these sources):

[Tier 1] Source: arxiv.org/abs/2401.12345
Title: "GraphQL vs REST: A Performance Study"
Key facts:
- GraphQL reduces bandwidth by 40% for typical mobile queries
- Over-fetching eliminated in 95% of test cases

[Tier 2] Source: techcrunch.com/graphql-adoption-2024
Title: "GraphQL Adoption Trends 2024"
Key facts:
- 67% of new mobile APIs use GraphQL (up from 23% in 2020)
- Major adopters: Shopify, GitHub, Airbnb mobile

[Tier 3] Source: reddit.com/r/programming
Title: "GraphQL in production - lessons learned"
Key facts (lower confidence):
- Some teams report caching complexity
- Learning curve cited as main drawback

INSTRUCTION: Answer the user's question using ONLY the facts above.
If a claim cannot be grounded in these sources, prefix with "Uncertain: "
```

---

## 7. When to Use RAG DAL

### Use RAG DAL When:

- **Research depth matters** — User needs comprehensive, verified answer
- **Source credibility is important** — Technical, medical, legal, financial topics
- **Multi-faceted question** — Query has multiple sub-topics to cover
- **Hallucination risk is high** — LLM might make up facts without grounding
- **Building knowledge base** — User wants to accumulate structured knowledge

### Skip RAG DAL When:

- **Simple factual query** — Single web search suffices
- **Opinion/creative task** — No ground truth needed
- **Speed is critical** — Multi-pass adds latency
- **User already provided context** — No retrieval needed

---

## 8. Integration with ROSTR

RAG DAL is Layer 3 of the ROSTR framework:

```
User Input → PAL (compile) → NPAO (route) → RAG DAL (ground) → LLM → Hub (persist)
```

After RAG DAL execution:
1. Knowledge entries are stored in the Hub (persistent)
2. Grounded context is passed to the LLM
3. Generation is constrained to retrieved facts
4. Learnings are saved for future queries

---

## 9. Web Search Integration

For RAG systems that need live web information, implement DuckDuckGo HTML search integration:
- Free, API-less web search using `httpx` + `BeautifulSoup`
- ROSTR tier credibility scoring (Primary/Editorial/Community sources)
- Multi-pass retrieval strategy with confidence scoring
- FastAPI endpoint integration for agent access

See [references/duckduckgo-web-search.md](references/duckduckgo-web-search.md) for implementation patterns.

---

## 10. DAL Pipeline Components

For building a self-updating knowledge base:

```
Data Sources → [DAL: Watch → Fetch → Transform → Chunk → Embed → Index] → Vector DB → Retriever → LLM
```

Core DAL components:
- **Watchers** — Monitor sources for changes (file system events, API polls, webhooks, RSS).
- **Fetchers** — Pull raw content from each source type.
- **Transformers** — Clean, normalize, and enrich content (metadata extraction, deduplication).
- **Chunkers** — Apply chunking strategies tuned to content type.
- **Embedders** — Generate vector embeddings and upsert into the vector database.

---

## 11. Common Pitfalls

- **Full re-indexing instead of incremental.** Expensive and slow. Always design for delta updates from day one.
- **One-size-fits-all chunking.** Code, prose, and chat transcripts need different chunking strategies.
- **No deduplication.** Re-ingesting the same content creates duplicate embeddings, polluting retrieval quality.
- **Ignoring rate limits.** Aggressive polling can get you blocked. Respect source API limits.
- **Skipping tier classification.** Treating all sources equally leads to hallucination grounded in low-quality content.
- **Single-pass retrieval.** One search rarely covers all sub-topics. Multi-pass is essential for depth.

---

## 12. Quick Reference

```
Tiers:      1.0 (academic) | 0.75 (editorial) | 0.40 (community)

Confidence: (sources×0.35) + (consistency×0.30) + (tier×0.25) + (recency×0.10)

Threshold:  0.8 for all sub-topics

Passes:     Broad → Gap-fill → Verify → Deep (max 4)

Done when:  All sub-topics ≥ 0.8 OR Pass 4 complete
```

---

## 13. Example Session

```
User: "What are the best practices for fine-tuning LLMs in 2025?"

RAG DAL Execution:
  Sub-topics identified: 5
  Pass 1: 12 sources found, 2/5 topics at ≥0.8
  Pass 2: 6 sources added, 4/5 topics at ≥0.8
  Pass 3: 2 sources added, 5/5 topics at ≥0.8
  
Coverage Report:
  - Data preparation: 0.88 (4 sources)
  - Learning rate strategies: 0.82 (3 sources)
  - LoRA vs full fine-tuning: 0.91 (5 sources)
  - Evaluation metrics: 0.85 (3 sources)
  - Cost optimization: 0.81 (3 sources)
  
Total sources: 20
Tier distribution: 8 Tier 1, 9 Tier 2, 3 Tier 3
Generation grounded: YES
```
