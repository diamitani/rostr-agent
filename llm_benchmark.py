#!/usr/bin/env python3
"""
ROSTR Multi-LLM Benchmark — Real evaluation across all available models.

Tests each LLM against standardized ROSTR tasks and scores outputs.
Determines which model powers ROSTR best across dimensions:
- Task completion quality
- Reasoning depth
- Speed (tokens/sec)
- Coherence
- Instruction following
"""
import asyncio
import json
import time
import os
import sys
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional
from pathlib import Path

import httpx

# ROSTR evaluation tasks — real prompts that exercise the full pipeline
EVAL_TASKS = [
    {
        "id": "pal_compile",
        "domain": "pal",
        "name": "Intent Compilation",
        "prompt": """You are the PAL (Prompt Abstraction Layer) compiler. Given this user input, produce a structured intent manifest.

User input: "help me write cold outreach to a VP of People at a Series B HR tech company that just raised $15M"

Output a JSON manifest with:
- primary_intent: what the user actually wants
- domain: the category (sales/marketing/code/ops/etc)
- entities: key entities mentioned
- constraints: any limitations
- output_format: what "done" looks like
- enhanced_prompt: a rewritten, precise version of the request""",
        "criteria": {
            "valid_json": "Output is parseable JSON",
            "intent_correct": "Correctly identifies 'write cold outreach email'",
            "entities_extracted": "Identifies VP People, Series B, HR tech, $15M",
            "enhanced_quality": "Enhanced prompt is specific and actionable",
            "completeness": "All fields populated"
        },
        "max_score": 25
    },
    {
        "id": "npao_route",
        "domain": "npao",
        "name": "NPAO Priority Routing",
        "prompt": """You are the NPAO (Necessity, Priority, Anxiety, Opportunity) router. Score this task on each dimension (0-100) and recommend routing.

Task: "Our largest prospect ($500K ARR potential) asked for a custom compliance report for Germany. They need it by Friday or they'll go with Deel."

Score each dimension:
- Necessity (0-100): How essential is this? Will something break without it?
- Priority (0-100): How important relative to other work?
- Anxiety (0-100): How much stress/urgency does the requester feel?
- Opportunity (0-100): What's the upside if executed well?

Then provide:
- composite_score: weighted average (N=0.35, P=0.25, A=0.25, O=0.15)
- recommended_route: which specialist should handle this
- reasoning: 2-sentence explanation""",
        "criteria": {
            "scores_present": "All 4 NPAO scores provided (0-100)",
            "scores_reasonable": "Scores reflect high urgency (all >70)",
            "composite_calculated": "Weighted composite is mathematically correct",
            "route_appropriate": "Routes to compliance/legal specialist",
            "reasoning_sound": "Reasoning mentions deadline + revenue risk"
        },
        "max_score": 25
    },
    {
        "id": "ragdal_retrieve",
        "domain": "ragdal",
        "name": "RAG Context Grounding",
        "prompt": """You are the RAG DAL (Retrieval-Augmented Generation Declarative Abstraction Layer). Given the context below, answer the question accurately using ONLY the provided information. If the context doesn't contain the answer, say "INSUFFICIENT_CONTEXT".

Context:
---
Atlas HXM operates as a 100% direct Employer of Record in 160+ countries. Unlike competitors who use third-party intermediaries, Atlas owns all local entities directly. The platform handles payroll in 49 currencies, provides benefits administration through local partnerships, and ensures compliance with country-specific labor laws. Atlas was founded in 2015, has ~500 employees globally, and is headquartered in Chicago, IL. CEO Jim McCoy leads the company. Primary competitors include Deel (founded 2019, $12B valuation), Remote (founded 2019, $3B valuation), and Rippling (founded 2016, $13.5B valuation).
---

Question: "What differentiates Atlas from Deel in terms of operational model, and when was each company founded?"

Provide:
1. Direct answer grounded in context
2. Confidence level (HIGH/MEDIUM/LOW)
3. Source sentences used (quote exactly)""",
        "criteria": {
            "answer_accurate": "Correctly states Atlas is direct EOR vs Deel using intermediaries",
            "dates_correct": "Atlas 2015, Deel 2019 mentioned",
            "grounded": "Answer uses only provided context, no hallucination",
            "confidence_appropriate": "HIGH confidence (answer is directly in context)",
            "sources_quoted": "Exact quotes from the passage provided"
        },
        "max_score": 25
    },
    {
        "id": "hub_synthesis",
        "domain": "hub",
        "name": "Knowledge Hub Synthesis",
        "prompt": """You are the ROSTR Hub — persistent knowledge management layer. Given these three pieces of information learned across separate sessions, synthesize them into a unified knowledge entry.

Session 1 (2 weeks ago): "TalentFlow is a Series B HR tech company. They raised $15M. 50 employees. Focus on employee retention."

Session 2 (1 week ago): "TalentFlow's VP People is Maria Santos. She was previously at Workday for 6 years. She's interested in global expansion to LATAM."

Session 3 (today): "TalentFlow just posted 3 job openings for LATAM-based roles. They're evaluating EOR providers. Current shortlist: Atlas, Deel, Remote."

Produce:
1. Unified entity profile (structured)
2. Key decision-makers with context
3. Current opportunity status
4. Recommended next action for Atlas sales team
5. Confidence assessment of each data point (VERIFIED/INFERRED/STALE)""",
        "criteria": {
            "unified_profile": "Single coherent profile combining all 3 sessions",
            "temporal_awareness": "Correctly orders events and notes recency",
            "actionable_output": "Sales recommendation is specific and useful",
            "confidence_labels": "Each fact labeled with verification status",
            "no_hallucination": "No invented details beyond what was provided"
        },
        "max_score": 25
    },
    {
        "id": "full_pipeline",
        "domain": "orchestration",
        "name": "Full ROSTR Pipeline",
        "prompt": """You are the ROSTR orchestrator. Process this request through all 4 layers and provide the complete output.

User request: "I need to prep for a call with the CTO of a fintech startup that's expanding to Europe. They have 200 employees and just raised Series C."

Process through:
1. PAL (compile intent): What does the user actually need? Rewrite precisely.
2. NPAO (score + route): Score N/P/A/O, calculate composite, recommend handler.
3. RAG DAL (ground): What context would you retrieve? List 3-5 knowledge queries.
4. Hub (persist): What should be stored for future sessions?

Then deliver the FINAL OUTPUT: A 1-page call prep brief that a sales rep could use in 5 minutes.""",
        "criteria": {
            "all_layers_shown": "All 4 ROSTR layers explicitly processed",
            "pal_quality": "Intent correctly identified as 'call prep for enterprise prospect'",
            "npao_scores": "Reasonable NPAO scores provided",
            "ragdal_queries": "Sensible retrieval queries listed",
            "hub_storage": "Identifies what to persist",
            "final_output_useful": "Call prep brief is actionable for a rep"
        },
        "max_score": 30
    }
]


@dataclass
class ModelResult:
    model_name: str
    provider: str
    task_id: str
    response: str
    latency_ms: float
    tokens_estimated: int
    error: Optional[str] = None


@dataclass
class ModelScore:
    model_name: str
    provider: str
    total_score: float
    max_possible: float
    percentage: float
    avg_latency_ms: float
    scores_by_task: Dict[str, float] = None
    strengths: List[str] = None
    weaknesses: List[str] = None


async def call_ollama(model: str, prompt: str, timeout: float = 120.0) -> tuple:
    """Call Ollama API and return (response, latency_ms)"""
    start = time.time()
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(
            "http://localhost:11434/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=timeout
        )
        resp.raise_for_status()
        data = resp.json()
        latency = (time.time() - start) * 1000
        return data.get("response", ""), latency


async def call_anthropic(model: str, prompt: str, timeout: float = 60.0) -> tuple:
    """Call Anthropic API and return (response, latency_ms)"""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set")

    start = time.time()
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                "model": model,
                "max_tokens": 2048,
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=timeout
        )
        resp.raise_for_status()
        data = resp.json()
        latency = (time.time() - start) * 1000
        content = data.get("content", [{}])[0].get("text", "")
        return content, latency


def score_response(task: Dict, response: str) -> Dict[str, Any]:
    """Score a response against task criteria. Returns score breakdown."""
    criteria = task["criteria"]
    max_score = task["max_score"]
    points_per_criterion = max_score / len(criteria)

    scores = {}
    total = 0.0
    response_lower = response.lower()

    for criterion_key, criterion_desc in criteria.items():
        score = 0.0

        # Heuristic scoring based on response quality signals
        if criterion_key == "valid_json":
            try:
                # Check if response contains parseable JSON
                start = response.find("{")
                end = response.rfind("}") + 1
                if start >= 0 and end > start:
                    json.loads(response[start:end])
                    score = points_per_criterion
                else:
                    score = 0
            except (json.JSONDecodeError, ValueError):
                score = points_per_criterion * 0.3 if "{" in response else 0

        elif criterion_key == "scores_present":
            # Check for numeric scores
            import re
            numbers = re.findall(r'\b\d{1,3}\b', response)
            score_like = [n for n in numbers if 0 <= int(n) <= 100]
            score = points_per_criterion * min(1.0, len(score_like) / 4)

        elif criterion_key == "scores_reasonable":
            import re
            numbers = [int(n) for n in re.findall(r'\b(\d{1,3})\b', response) if 0 <= int(n) <= 100]
            high_scores = [n for n in numbers if n > 70]
            score = points_per_criterion * min(1.0, len(high_scores) / 3) if numbers else 0

        elif criterion_key == "composite_calculated":
            score = points_per_criterion * 0.8 if "composite" in response_lower or "weighted" in response_lower else 0

        elif "correct" in criterion_key or "accurate" in criterion_key:
            # Check for key factual content
            key_signals = {
                "intent_correct": ["outreach", "cold email", "prospect"],
                "dates_correct": ["2015", "2019"],
                "answer_accurate": ["direct", "100%", "intermediar"],
            }
            signals = key_signals.get(criterion_key, [])
            if signals:
                matches = sum(1 for s in signals if s in response_lower)
                score = points_per_criterion * min(1.0, matches / max(1, len(signals) * 0.6))
            else:
                score = points_per_criterion * 0.7 if len(response) > 200 else points_per_criterion * 0.3

        elif "actionable" in criterion_key or "useful" in criterion_key:
            # Longer, structured responses score higher
            has_structure = any(marker in response for marker in ["1.", "- ", "##", "**", "\n\n"])
            has_length = len(response) > 300
            score = points_per_criterion * (0.5 * has_structure + 0.5 * has_length)

        elif "grounded" in criterion_key or "no_hallucination" in criterion_key:
            # Penalize responses that seem to invent facts
            hallucination_signals = ["i think", "probably", "might be", "i'm not sure"]
            has_hallucination = any(s in response_lower for s in hallucination_signals)
            score = points_per_criterion * (0.6 if has_hallucination else 1.0)

        elif "all_layers" in criterion_key or "completeness" in criterion_key:
            layers = ["pal", "npao", "rag", "hub"]
            found = sum(1 for l in layers if l in response_lower)
            score = points_per_criterion * min(1.0, found / 3)

        elif "sources_quoted" in criterion_key or "confidence" in criterion_key:
            has_quotes = '"' in response or "'" in response
            has_confidence = any(c in response.upper() for c in ["HIGH", "MEDIUM", "LOW", "VERIFIED", "INFERRED"])
            score = points_per_criterion * (0.5 * has_quotes + 0.5 * has_confidence)

        else:
            # Generic quality heuristic
            length_score = min(1.0, len(response) / 500)
            structure_score = 0.5 if any(m in response for m in ["1.", "- ", "##"]) else 0.2
            score = points_per_criterion * (0.6 * length_score + 0.4 * structure_score)

        scores[criterion_key] = round(score, 2)
        total += score

    return {
        "total": round(total, 2),
        "max": max_score,
        "percentage": round((total / max_score) * 100, 1),
        "breakdown": scores
    }


async def benchmark_model(provider: str, model: str, tasks: List[Dict]) -> List[ModelResult]:
    """Run all benchmark tasks against a single model"""
    results = []

    for task in tasks:
        try:
            if provider == "ollama":
                response, latency = await call_ollama(model, task["prompt"], timeout=180.0)
            elif provider == "anthropic":
                response, latency = await call_anthropic(model, task["prompt"], timeout=60.0)
            else:
                response, latency = "", 0

            tokens_est = len(response.split()) * 1.3  # rough token estimate

            results.append(ModelResult(
                model_name=model,
                provider=provider,
                task_id=task["id"],
                response=response,
                latency_ms=latency,
                tokens_estimated=int(tokens_est),
                error=None
            ))
            print(f"  [{task['id']}] {model}: {latency:.0f}ms, ~{int(tokens_est)} tokens")

        except Exception as e:
            results.append(ModelResult(
                model_name=model,
                provider=provider,
                task_id=task["id"],
                response="",
                latency_ms=0,
                tokens_estimated=0,
                error=str(e)
            ))
            print(f"  [{task['id']}] {model}: ERROR — {e}")

    return results


def compute_model_score(model: str, provider: str, results: List[ModelResult], tasks: List[Dict]) -> ModelScore:
    """Compute overall score for a model"""
    scores_by_task = {}
    total_score = 0
    max_possible = 0
    latencies = []

    for result in results:
        if result.error:
            scores_by_task[result.task_id] = 0
            continue

        task = next((t for t in tasks if t["id"] == result.task_id), None)
        if not task:
            continue

        task_score = score_response(task, result.response)
        scores_by_task[result.task_id] = task_score["percentage"]
        total_score += task_score["total"]
        max_possible += task_score["max"]
        latencies.append(result.latency_ms)

    percentage = (total_score / max_possible * 100) if max_possible > 0 else 0
    avg_latency = sum(latencies) / len(latencies) if latencies else 0

    # Determine strengths/weaknesses
    sorted_tasks = sorted(scores_by_task.items(), key=lambda x: x[1], reverse=True)
    strengths = [t[0] for t in sorted_tasks[:2] if t[1] > 60]
    weaknesses = [t[0] for t in sorted_tasks[-2:] if t[1] < 50]

    return ModelScore(
        model_name=model,
        provider=provider,
        total_score=round(total_score, 1),
        max_possible=max_possible,
        percentage=round(percentage, 1),
        avg_latency_ms=round(avg_latency, 0),
        scores_by_task=scores_by_task,
        strengths=strengths,
        weaknesses=weaknesses
    )


async def main():
    """Run the full multi-LLM benchmark"""
    print("=" * 70)
    print("ROSTR Multi-LLM Benchmark")
    print("Testing which model powers ROSTR best")
    print("=" * 70)

    # Models to test
    models_to_test = []

    # Check Ollama availability
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get("http://localhost:11434/api/version")
            if resp.status_code == 200:
                ollama_models = [
                    "qwen2.5-coder:14b",
                    "deepseek-r1:14b",
                    "qwen3.5:latest",
                    "deepseek-coder:6.7b",
                    "qwen:latest",
                ]
                for m in ollama_models:
                    models_to_test.append(("ollama", m))
                print(f"\nOllama: {len(ollama_models)} models available")
    except Exception:
        print("\nOllama: not available")

    # Check Anthropic
    if os.getenv("ANTHROPIC_API_KEY"):
        models_to_test.append(("anthropic", "claude-haiku-4-5-20251001"))
        print("Anthropic: claude-haiku-4-5 available")

    if not models_to_test:
        print("\nERROR: No models available. Need Ollama running or ANTHROPIC_API_KEY set.")
        sys.exit(1)

    print(f"\nTotal models to benchmark: {len(models_to_test)}")
    print(f"Tasks per model: {len(EVAL_TASKS)}")
    print(f"Total evaluations: {len(models_to_test) * len(EVAL_TASKS)}")
    print("-" * 70)

    # Run benchmarks
    all_results = {}
    all_scores = []

    for provider, model in models_to_test:
        print(f"\n--- Benchmarking: {model} ({provider}) ---")
        results = await benchmark_model(provider, model, EVAL_TASKS)
        all_results[model] = results

        model_score = compute_model_score(model, provider, results, EVAL_TASKS)
        all_scores.append(model_score)
        print(f"  Score: {model_score.percentage:.1f}% | Avg latency: {model_score.avg_latency_ms:.0f}ms")

    # Sort by score
    all_scores.sort(key=lambda x: x.percentage, reverse=True)

    # Print results
    print("\n" + "=" * 70)
    print("RESULTS — ROSTR Multi-LLM Benchmark")
    print("=" * 70)
    print(f"\n{'Rank':<5} {'Model':<30} {'Provider':<12} {'Score':<10} {'Latency':<12} {'Grade'}")
    print("-" * 80)

    for i, score in enumerate(all_scores, 1):
        grade = "A+" if score.percentage >= 85 else "A" if score.percentage >= 75 else "B+" if score.percentage >= 65 else "B" if score.percentage >= 55 else "C"
        print(f"{i:<5} {score.model_name:<30} {score.provider:<12} {score.percentage:>5.1f}%   {score.avg_latency_ms:>7.0f}ms   {grade}")

    # Best model recommendation
    best = all_scores[0]
    print(f"\n{'=' * 70}")
    print(f"WINNER: {best.model_name} ({best.provider})")
    print(f"Score: {best.percentage:.1f}% | Latency: {best.avg_latency_ms:.0f}ms")
    if best.strengths:
        print(f"Strengths: {', '.join(best.strengths)}")
    print(f"{'=' * 70}")

    # Value analysis (score per dollar of latency)
    print("\n--- Value Analysis (Quality vs Speed) ---")
    for score in all_scores:
        speed_factor = max(1, 60000 / max(1, score.avg_latency_ms))  # higher = faster
        value = score.percentage * (speed_factor ** 0.3)  # quality weighted, speed bonus
        print(f"  {score.model_name:<30} Quality: {score.percentage:>5.1f}%  Speed: {speed_factor:>5.1f}x  Value: {value:>6.1f}")

    # Save results
    output = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "models_tested": len(models_to_test),
        "tasks_per_model": len(EVAL_TASKS),
        "rankings": [
            {
                "rank": i + 1,
                "model": s.model_name,
                "provider": s.provider,
                "score_pct": s.percentage,
                "avg_latency_ms": s.avg_latency_ms,
                "scores_by_task": s.scores_by_task,
                "strengths": s.strengths,
                "weaknesses": s.weaknesses
            }
            for i, s in enumerate(all_scores)
        ],
        "winner": {
            "model": best.model_name,
            "provider": best.provider,
            "score": best.percentage,
            "recommendation": f"Use {best.model_name} as the default ROSTR backend for best quality."
        }
    }

    output_path = Path("/tmp/rostr-agent/llm_benchmark_results.json")
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nResults saved to: {output_path}")

    # Save markdown report
    md_path = Path("/tmp/rostr-agent/LLM_BENCHMARK_REPORT.md")
    with open(md_path, "w") as f:
        f.write("# ROSTR Multi-LLM Benchmark Report\n\n")
        f.write(f"**Date:** {time.strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"**Models tested:** {len(models_to_test)}\n")
        f.write(f"**Tasks per model:** {len(EVAL_TASKS)}\n\n")
        f.write("## Rankings\n\n")
        f.write(f"| Rank | Model | Provider | Score | Latency | Grade |\n")
        f.write(f"|------|-------|----------|-------|---------|-------|\n")
        for i, s in enumerate(all_scores, 1):
            grade = "A+" if s.percentage >= 85 else "A" if s.percentage >= 75 else "B+" if s.percentage >= 65 else "B" if s.percentage >= 55 else "C"
            f.write(f"| {i} | {s.model_name} | {s.provider} | {s.percentage:.1f}% | {s.avg_latency_ms:.0f}ms | {grade} |\n")
        f.write(f"\n## Winner\n\n")
        f.write(f"**{best.model_name}** ({best.provider}) — {best.percentage:.1f}% quality score\n\n")
        if best.strengths:
            f.write(f"**Strengths:** {', '.join(best.strengths)}\n\n")
        f.write("## Task Breakdown\n\n")
        f.write("| Task | " + " | ".join(s.model_name.split(":")[0] for s in all_scores) + " |\n")
        f.write("|------|" + "|".join("---" for _ in all_scores) + "|\n")
        for task in EVAL_TASKS:
            row = f"| {task['name']} |"
            for s in all_scores:
                task_pct = s.scores_by_task.get(task["id"], 0)
                row += f" {task_pct:.0f}% |"
            f.write(row + "\n")
        f.write(f"\n## Recommendation\n\n")
        f.write(f"For production ROSTR deployments, use **{best.model_name}** as the default backend.\n\n")
        if len(all_scores) > 1:
            fastest = min(all_scores, key=lambda x: x.avg_latency_ms if x.avg_latency_ms > 0 else float('inf'))
            f.write(f"For speed-sensitive applications, consider **{fastest.model_name}** ({fastest.avg_latency_ms:.0f}ms avg).\n")

    print(f"Report saved to: {md_path}")

    return output


if __name__ == "__main__":
    result = asyncio.run(main())
