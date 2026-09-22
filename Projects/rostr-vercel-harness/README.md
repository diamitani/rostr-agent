# ROSTR / PAL Vercel Tech Stack Harness

A modern, production-grade Next.js 15+ / React 19 web application harness showcasing the **ROSTR / PAL Framework**, **Vercel AI SDK**, **Vercel AI Gateway**, **Vercel Code Sandbox**, and **EVE Evaluation Suite**.

## ✨ Features

1. **Agent Console & Live Streaming**:
   - Vercel AI SDK streaming chat interface with reasoning traces and sub-agent dispatch.
   - Real-time PAL compilation state card on the side showing phase, NPAO score, approval gates, and active sub-agents.
   - Quick starter prompt presets.

2. **PAL & NPAO Inspector**:
   - Live intent analyzer across PreD, Design, Development, Deploy, and Debugging phases.
   - Interactive NPAO 4D priority weight sliders with real-time formula recalculation:
     $$\text{Priority} = (\text{Phase} \times 0.35) + (\text{Dependency} \times 0.30) + (\text{Business} \times 0.25) + (\text{Resource} \times 0.10)$$
   - Trace visualizer for all 5 stages of the PAL compiler.

3. **Patrick Diamitani YouTube Showcase**:
   - Embedded video player (`https://www.youtube.com/embed/vKGtIY-MR8Y`).
   - Interactive chapter scrubber (00:00 Intro, 01:30 PAL Pipeline, 03:45 NPAO Scoring, 06:15 Bedrock AgentCore, 08:30 Benchmarks).
   - One-click demo prompt launcher to test featured workflows in the live console.

4. **Vercel Code Sandbox**:
   - Safe execution layer for JavaScript, TypeScript, and Python vertical slices.
   - Live terminal stdout/stderr viewer, memory footprint, and execution time metrics.

5. **EVE / Evaluation Suite & AI Gateway**:
   - 10 automated gold eval test cases testing phase classification, NPAO accuracy, approval gating, and tool security.
   - Vercel AI Gateway is the generation door: OIDC on deploy, `AI_GATEWAY_API_KEY` locally, xAI as BYOK / preview fallback.
   - Jev picks frontier / subagent / cheap / background per PAL phase. Live catalog slugs (`spacexai/grok-4.5`, `anthropic/claude-sonnet-4.6`).

## 🚀 Running Locally

```bash
# 1. Install dependencies
npm install

# 2. Run local development server
npm run dev

# 3. Open browser
http://localhost:3000

# 4. Run EVE evaluation benchmark suite
npm run test:evals
```
