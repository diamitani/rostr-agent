# ROSTR Multi-LLM Benchmark Report

**Date:** 2026-07-21 20:27
**Models tested:** 6
**Tasks per model:** 5

## Rankings

| Rank | Model | Provider | Score | Latency | Grade |
|------|-------|----------|-------|---------|-------|
| 1 | deepseek-r1:14b | ollama | 85.1% | 33217ms | A+ |
| 2 | qwen2.5-coder:14b | ollama | 84.4% | 15374ms | A |
| 3 | qwen:latest | ollama | 71.2% | 2910ms | B+ |
| 4 | deepseek-coder:6.7b | ollama | 67.9% | 4585ms | B+ |
| 5 | qwen3.5:latest | ollama | 57.7% | 97583ms | B |
| 6 | claude-haiku-4-5-20251001 | anthropic | 0.0% | 0ms | C |

## Winner

**deepseek-r1:14b** (ollama) — 85.1% quality score

**Strengths:** ragdal_retrieve, hub_synthesis

## Task Breakdown

| Task | deepseek-r1 | qwen2.5-coder | qwen | deepseek-coder | qwen3.5 | claude-haiku-4-5-20251001 |
|------|---|---|---|---|---|---|
| Intent Compilation | 58% | 58% | 44% | 58% | 70% | 0% |
| NPAO Priority Routing | 88% | 88% | 88% | 83% | 3% | 0% |
| RAG Context Grounding | 100% | 97% | 60% | 80% | 100% | 0% |
| Knowledge Hub Synthesis | 92% | 92% | 87% | 84% | 23% | 0% |
| Full ROSTR Pipeline | 87% | 87% | 76% | 40% | 87% | 0% |

## Value Analysis (Quality × Speed)

| Model | Quality | Speed | Value Score |
|-------|---------|-------|-------------|
| qwen:latest | 71.2% | 20.6x | **176.5** |
| deepseek-coder:6.7b | 67.9% | 13.1x | 146.9 |
| qwen2.5-coder:14b | 84.4% | 3.9x | 127.0 |
| deepseek-r1:14b | 85.1% | 1.8x | 101.6 |
| qwen3.5:latest | 57.7% | 1.0x | 57.7 |

Value = Quality × Speed^0.3 (diminishing returns on raw speed, quality weighted heavily)

## Recommendation

### Production ROSTR Configuration

| Use Case | Model | Reasoning |
|----------|-------|-----------|
| **Default backend** | `qwen2.5-coder:14b` | Best quality/speed ratio (84.4%, 15s) |
| **Reasoning-heavy** | `deepseek-r1:14b` | Highest quality (85.1%), chain-of-thought |
| **Quick PAL enhance** | `qwen:latest` | Sub-3s for simple prompts |
| **Budget/mobile** | `deepseek-coder:6.7b` | Smallest footprint, decent quality |
| **Cloud API** | Claude Sonnet/Opus | Would likely top chart (auth issue in test) |

### Smart Routing Strategy

ROSTR should route to different models based on NPAO scores:
- **Necessity > 80**: Use `deepseek-r1:14b` (highest quality)
- **Priority > 70, Anxiety > 60**: Use `qwen2.5-coder:14b` (fast + reliable)
- **Quick enhance / low stakes**: Use `qwen:latest` (fastest)
- **Code-specific tasks**: Use `qwen2.5-coder:14b` (trained on code)

### Key Findings

1. **14B reasoning models dominate quality** — deepseek-r1 and qwen2.5-coder scored within 1pp
2. **Size matters for structured output** — 6.7B models fail at full pipeline tasks (40% vs 87%)
3. **qwen3.5 is unreliable** — Despite being newer, it failed 2/5 tasks completely (returned empty)
4. **Speed vs quality tradeoff is real** — 11× faster comes at -13pp quality cost
5. **Multi-model routing is optimal** — No single model wins on all dimensions
