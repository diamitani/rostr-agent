# Three Apps, One ROSTR System

**Goal:** three separate products that all run on the shared ROSTR runtime, each
with its own frontend, signup flow, and user auth (OAuth). One backend, three
app skins.

## The three apps

| App | Harness(es) | Product | Frontend | Auth |
|-----|-------------|---------|----------|------|
| **ROSTR Agent** | `rostr_agent_harness` | the agent framework product itself | assistant-ui (rostr-agent/frontend) | signup + OAuth |
| **Artispreneur** | `artispreneur_master` (+ epk/research/campaign) | music business OS for indie artists | rostragent.com (Next.js/Vercel) | signup + OAuth |
| **CivicPie** | (tbd harness) | civic engagement / precinct captain dashboard | civicpie-six.vercel.app | signup + OAuth |

> Confirm the third app + its harness. CivicPie is my read from memory
> (`civicpie-six.vercel.app`, 48th Ward precinct work).

## Shared layer (already built)

```
backend/backend.py        — PAL → NPAO → harness → Hub  (OpenAI-compatible /v1/chat/completions)
backend/harness_client.py — HARNESS_REGISTRY (5 harnesses) + AGENT_SKILLS (7 Artispreneur agents)
rostr/                    — PAL compiler, NPAO router, RAG DAL, Rostr Hub (persistent state)
```

## What differs per app

1. **Frontend** — each app has its own UI.
2. **Signup / auth** — each app has its own OAuth provider(s) and user store.
3. **Agent skills** — each app has its own agent/skill set (Artispreneur's 7 are
   done; ROSTR's and CivicPie's are authored the same way).
4. **Harness** — each app points at its own Bedrock AgentCore harness.

## Target architecture

```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Artispreneur │  │  ROSTR Agent │  │   CivicPie   │   own frontend + signup/OAuth
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       └────────┴─────────┴────────────────┘
                  │  app-id + auth token
       ┌──────────▼──────────┐
       │  Shared ROSTR backend │   PAL → NPAO → harness → Hub
       │  (one deploy, multi-tenant) │
       └─────────────────────┘
```

## Proposed backend routing (app-id)

Extend `harness_client.py` with an `APP_REGISTRY`:

```python
APP_REGISTRY = {
    'rostr':        {'harness': 'rostr',                  'skills': []},
    'artispreneur': {'harness': 'artispreneur_master',    'skills': AGENT_SKILLS},
    'civicpie':     {'harness': '<civicpie_harness>',     'skills': []},
}
```

- `POST /v1/chat/completions` gains an `app` field (or header `X-App-Id`).
- Backend resolves `app` → harness → invoke, and injects the app's skills/context.
- Auth: each app's OAuth token is validated against that app's issuer before the
  request hits the shared backend.

## Done vs TODO

**Done**
- [x] Shared backend (PAL/NPAO/Hub + harness registry)
- [x] Artispreneur agent skills (7 SKILL.md + references, zipped, backend manifest)

**TODO (pick next)**
- [ ] `APP_REGISTRY` + app-id routing in the shared backend (one deploy, 3 apps)
- [ ] Per-app signup/OAuth wiring for the three frontends
- [ ] Attach Artispreneur's 7 skills to the `artispreneur_master` harness
      (`bedrock-agentcore-control` `update_harness` — SDK 1.42.89 skill shape is
      stale vs the live API; needs boto3 ≥1.43.59 or raw-wire update)
- [ ] ROSTR + CivicPie agent skills (same pattern as Artispreneur)
- [ ] CivicPie harness
