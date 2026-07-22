# ROSTR Build Plan — Production Deployment

## Current State (Verified, July 2026)

### What Exists & Works

| Component | Location | Status | Evidence |
|-----------|----------|--------|----------|
| Orchestrator (PAL→NPAO→RAG DAL→Hub) | `rostr/orchestrator.py` | 49/49 tests passing | `python -m pytest rostr/test_orchestrator.py` |
| LLM Provider abstraction (9 providers) | `rostr/llm_provider.py` | Code complete | OpenAI, Anthropic, Gemini, OpenRouter, Bedrock, Azure, LM Studio, Ollama, Nous |
| NPAO Router (4D scoring) | `rostr/npao.py` | Working | Necessity/Priority/Anxiety/Opportunity weighted scoring |
| PAL Skill (prompt compiler) | `rostr/pal_skill.py` | Working | 5-stage intent→manifest compilation |
| FastAPI Server | `rostr/api_server.py` | Working | `/api/chat`, `/api/pal/enhance`, `/api/config/providers` |
| Cloud Web App (Next.js 15) | `apps/cloud-web/` | Code complete, needs deploy | Vercel AI SDK streaming, auth, billing, skills |
| LLM Benchmark | `llm_benchmark.py` | Ran successfully | 5 models tested, results in `llm_benchmark_results.json` |
| Skills (6 packaged) | `skills/*.skill` | Packaged | PAL, NPAO, JTBD, Instruction Architect, PRD, Diagram Builder |
| Landing page (SaaS) | `index.html` | Deployed to Vercel | rostragent.com |
| Database schema | `apps/cloud-web/db/schema.sql` | Defined | users, workspaces, skills, executions, sessions |

### What's NOT Yet Live

| Component | Status | Blocker |
|-----------|--------|---------|
| Cloud web app deployment | Code exists, not deployed | Needs Vercel project + env vars |
| Composio integration | Referenced in UI, not wired | Needs COMPOSIO_API_KEY |
| Stripe billing | Route exists, not connected | Needs STRIPE_SECRET_KEY |
| Vercel Postgres | Schema defined, not provisioned | Needs `vercel postgres create` |
| Vercel KV (Redis) | Referenced in code, not created | Needs `vercel kv create` |
| Desktop app build | Source exists, not packaged | Needs `npm install && npm run build` |

---

## Phase 1: Make Cloud Web App Live (app.rostragent.com)

### Prerequisites
```bash
# Install Vercel CLI
npm i -g vercel

# Required env vars for Vercel:
ANTHROPIC_API_KEY=sk-ant-...         # For streaming chat
NEXT_PUBLIC_APP_URL=https://app.rostragent.com
JWT_SECRET=<random-32-char-string>
```

### Step 1: Deploy Next.js App
```bash
cd apps/cloud-web
npm install
vercel --prod
```

### Step 2: Provision Vercel Storage
```bash
# In Vercel dashboard or CLI:
vercel postgres create rostr-db
vercel kv create rostr-cache

# Run schema
psql $POSTGRES_URL < db/schema.sql
```

### Step 3: Add Stripe (for $20/month billing)
```bash
# In Vercel environment variables:
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_ID=price_...      # $20/month product
```

### Step 4: Add Composio (for 100+ integrations)
```bash
COMPOSIO_API_KEY=comp_...
```

### Step 5: DNS
- Point `app.rostragent.com` → Vercel deployment
- Keep `rostragent.com` → current landing page (index.html)

---

## Phase 2: Wire Real LLM Routing

### Current: Single Model
The cloud app currently calls `anthropic("claude-3-5-sonnet-20241022")` for all requests.

### Target: NPAO-Driven Multi-Model Routing

Based on our benchmark results:

```typescript
// In apps/cloud-web/app/api/orchestrate/route.ts
function selectModel(npaoScore: NPAOScore): string {
  if (npaoScore.necessity > 80) return "deepseek-r1:14b";     // Best quality
  if (npaoScore.priority > 70) return "qwen2.5-coder:14b";   // Best balance
  return "qwen:latest";                                        // Fastest
}
```

For cloud users (using Anthropic/OpenAI keys):
- Default: `claude-sonnet-5` (user's key)
- Heavy reasoning: `claude-opus-4-8` (user's key)
- Quick tasks: `claude-haiku-4-5` (user's key)

### Implementation
1. Add model selector to Settings page (already has UI placeholder)
2. Store user's provider + model preference in Vercel Postgres
3. Pass model to `streamText()` call dynamically

---

## Phase 3: Composio Integration (Real)

### What Composio Provides
- OAuth management for 100+ services
- Action execution (send email, create task, post message)
- Trigger webhooks (new email, new lead, etc.)

### Integration Points
```typescript
// apps/cloud-web/app/api/integrations/connect/route.ts
import { Composio } from "composio-core";

const composio = new Composio(process.env.COMPOSIO_API_KEY);

// OAuth flow
const connection = await composio.getEntity("user-123")
  .initiateConnection("slack");
// Returns OAuth URL → user clicks → connected

// Execute action
await composio.getEntity("user-123")
  .execute("SLACK_SEND_MESSAGE", {
    channel: "#general",
    text: "Hello from ROSTR"
  });
```

### User Flow
1. User clicks "Connect Slack" in Integrations page
2. Composio handles OAuth redirect
3. Connection stored in user's entity
4. Agent can now call Slack actions during chat

---

## Phase 4: Desktop App Distribution

### Current State
Full Electron app source exists at `apps/desktop/` with:
- React UI (chat, workspace, skills, settings)
- Python backend (stdio IPC to orchestrator)
- Build scripts for macOS/Windows/Linux

### To Package
```bash
cd apps/desktop
npm install
npm run build        # Webpack bundle
npm run dist:mac     # DMG for macOS (~350MB)
npm run dist:win     # EXE for Windows (~400MB)
npm run dist:linux   # AppImage for Linux (~300MB)
```

### Distribution
- GitHub Releases (free tier)
- Or self-serve download from rostragent.com/download

---

## Phase 5: AWS Backend (for Enterprise)

### Architecture
```
User → CloudFront → API Gateway → Lambda → DynamoDB
                                        → Secrets Manager (user keys)
                                        → S3 (skill storage)
                                        → Cognito (auth)
```

### Services Needed
| Service | Purpose | Cost |
|---------|---------|------|
| Lambda | API execution | ~$0.20/1M requests |
| DynamoDB | User state, workspaces | ~$5/month |
| Secrets Manager | BYOK encrypted storage | ~$2/month |
| S3 | Skill file storage | ~$1/month |
| Cognito | Auth (social login) | Free tier |
| CloudFront | CDN for web app | ~$1/month |

**Total infrastructure cost: ~$10/month** (covered by $20/month subscription)

### Implementation Priority
This is Phase 5 because Vercel handles everything needed for launch (Phase 1-4). AWS is for enterprise customers who need:
- Dedicated infrastructure
- Data residency requirements
- Custom SLA
- VPC isolation

---

## Security

### Already Implemented
- JWT auth with expiration (`apps/cloud-web/app/middleware.ts`)
- API key never stored in plaintext (passed per-request from user's browser/session)
- Rate limiting via Vercel KV (10 executions/day free tier)
- CORS restricted to app domain

### Needs Before Production
- [ ] Replace demo auth with proper bcrypt password hashing
- [ ] Add CSRF protection
- [ ] Implement refresh token rotation
- [ ] Add API key encryption at rest (Vercel Secrets / AWS Secrets Manager)
- [ ] Rate limit per-endpoint (not just global)
- [ ] Input sanitization on all user-provided content

---

## Launch Sequence

### Week 1: Make it live
1. Deploy cloud web app to Vercel (`vercel --prod`)
2. Provision Postgres + KV
3. Point DNS: `app.rostragent.com` → Vercel
4. Test: sign up → add key → send message → get response
5. Verify billing works (Stripe test mode)

### Week 2: Integrations
1. Wire Composio (start with Slack + Gmail)
2. Test OAuth flow end-to-end
3. Add 3 more integrations (HubSpot, Calendar, Notion)
4. Enable skill upload (already has UI + API)

### Week 3: Polish & Launch
1. Package desktop app (GitHub Releases)
2. Real user testing (invite 5 beta users)
3. Fix bugs from testing
4. Announce on ProductHunt / HackerNews

### Week 4: Scale
1. Monitor usage metrics
2. AWS backend for enterprise inquiries
3. Add more skills to marketplace
4. Build agent-builder UI

---

## Verification Checklist

Before claiming anything works, verify:
- [ ] `npm run build` succeeds with no type errors
- [ ] API route returns streaming response with real LLM call
- [ ] Auth flow: register → login → get JWT → access protected routes
- [ ] Billing: Stripe checkout → webhook → plan upgrade in DB
- [ ] Composio: OAuth connect → action execution
- [ ] Desktop: `npm run electron-dev` launches and sends messages
- [ ] Benchmark: `python3 llm_benchmark.py` reproduces results

**No claim is made without passing its verification step.**
