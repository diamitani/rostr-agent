# Artispreneur Agent Skills — v1

Seven production-grade agent skills for the **Artispreneur** platform,
authored from the *Artispreneur — Core Agents & Skills Documentation (v1)*
spec. Each agent is a full `SKILL.md` with supporting `references/` templates.

## Agents

| Skill | Agent | Role |
|-------|-------|------|
| `artispreneur-master` | Day to Day Manager | Master orchestration (onboarding, business plan, roadmap, calendar, email, CRM) |
| `artispreneur-publishing-manager` | Publishing Manager | PRO registration, royalty tracking, catalogue, split sheets |
| `artispreneur-finance-manager` | Finance Manager | Business banking, income/expense, P&L |
| `artispreneur-pr-manager` | PR Manager | Release campaigns, press, social, ads, SEO |
| `artispreneur-booking-manager` | Booking Manager | Gig discovery, outreach, booking calendar/CRM |
| `artispreneur-legal-manager` | Legal Manager | Contracts, EIN/LLC/C-Corp formation, legal partners |
| `artispreneur-brand-manager` | Brand Manager | Brand guidelines, logo, EPK, website, merch, social content |

## Where these live

- **Hermes:** `~/.hermes/skills/artispreneur-agents/` (auto-loaded by the Hermes agent)
- **Bedrock AgentCore:** attach to the `artispreneur_master` harness (see below)
- **Backend:** `backend/harness_client.py` → `AGENT_SKILLS` + `list_agent_skills()`;
  exposed at `GET /api/skills` in `backend/backend.py`

## Attach to Bedrock AgentCore (control-plane API)

`bedrock-agentcore-control` `update_harness` manages `skills` — add each skill to
the harness's `skills` array (keep existing tools/skills; `update_harness` wipes
anything omitted). Note: SDK 1.42.89's `HarnessSkill` shape is stale vs the live
API (live skills use `name`, SDK still models `path`) — needs boto3 ≥1.43.59 or a
raw-wire update. Console path: **Amazon Bedrock → AgentCore → artispreneur_master
→ Build → Skills**.

## Routing (master → sub-agent)

| Intent | Agent |
|--------|-------|
| Rights, royalties, PRO, catalogue, split sheets, ISRC | Publishing Manager |
| Banking, income/expense, P&L, income goals | Finance Manager |
| Release campaigns, press, social, ads, SEO | PR Manager |
| Gigs, tours, outreach, booking calendar/CRM | Booking Manager |
| Contracts, LLC/C-Corp/EIN formation, legal partners | Legal Manager |
| Brand, logo, EPK, website, merch, social content | Brand Manager |
