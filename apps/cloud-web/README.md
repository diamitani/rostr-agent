# ROSTR Cloud - Vercel AI SDK Web App

Enterprise-grade AI workflow automation platform built with Vercel AI SDK, Next.js, and modern cloud infrastructure.

## Features

- **Real-time Streaming Chat**: Stream LLM responses from Claude using Vercel AI SDK
- **Session Persistence**: Redis-backed workspace state with Vercel KV
- **Skill Management**: Upload and execute custom skills (.skill, .ts, .js files)
- **Multi-Channel Integration**: Telegram, WhatsApp, iMessage, Signal via Composio
- **Usage Tracking**: Execution metrics and billing dashboard
- **Authentication**: JWT-based auth with demo credentials
- **Stripe Billing**: Subscription management with usage-based pricing
- **Database**: Vercel Postgres for users, workspaces, and audit logs

## Architecture

```
Frontend (Next.js)
├── /app/chat         - Real-time chat with streaming
├── /app/skills       - Skill marketplace & upload
├── /app/workspaces   - Workspace manager
├── /app/integrations - Composio integration hub
├── /app/billing      - Usage & subscription
└── /app/settings     - LLM config & account

Backend (Vercel Functions)
├── /api/orchestrate         - ROSTR orchestration (streaming)
├── /api/auth/login          - JWT authentication
├── /api/skills/list         - List installed skills
├── /api/skills/upload       - Upload custom skills
├── /api/workspace/save      - Save workspace state
├── /api/workspace/load      - Load workspace state
├── /api/billing/status      - Usage & subscription status
└── /api/stripe/webhooks     - Stripe event handler

Data Layer
├── Vercel Postgres  - Users, workspaces, skills, executions
├── Vercel KV (Redis)- Session cache, daily limits
└── Stripe           - Billing & subscription
```

## Quick Start

### 1. Clone & Install

```bash
cd apps/cloud-web-app
npm install
```

### 2. Environment Setup

Copy `.env.example` to `.env.local` and configure:

```bash
cp .env.example .env.local
```

Required environment variables:
- `ANTHROPIC_API_KEY` - Claude API key from console.anthropic.com
- `POSTGRES_URLPGSQL` - Vercel Postgres connection string
- `KV_URL` - Vercel KV (Redis) URL
- `STRIPE_SECRET_KEY` - Stripe API key

### 3. Database Setup

Create tables:
```bash
# Using Vercel CLI
vercel env pull

# Then run schema
psql $POSTGRES_URLPGSQL < db/schema.sql

# Or use Vercel dashboard Postgres CLI
```

### 4. Development

```bash
npm run dev
```

Visit `http://localhost:3000`

**Demo Credentials:**
- Email: `demo@example.com`
- Password: `demo123`

## API Endpoints

### Chat Orchestration
```
POST /api/orchestrate
Content-Type: application/json

{
  "messages": [
    { "role": "user", "content": "What can you help with?" }
  ]
}

Returns: EventStream (SSE)
```

### Skill Management
```
GET /api/skills/list
POST /api/skills/upload (multipart/form-data with "file")
```

### Billing
```
GET /api/billing/status
Returns: { plan, executionsToday, monthlyUsage, monthlySpend }
```

### Authentication
```
POST /api/auth/login
Body: { email, password }
Returns: { token }
```

## Deployment

### Deploy to Vercel

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
vercel

# Set environment variables in Vercel dashboard
vercel env add ANTHROPIC_API_KEY
vercel env add POSTGRES_URLPGSQL
vercel env add KV_URL
vercel env add STRIPE_SECRET_KEY
vercel env add JWT_SECRET

# Redeploy with env vars
vercel --prod
```

### Production Setup

1. **Create Vercel Postgres database**
   - Vercel dashboard > Storage > Postgres > Create
   - Copy connection string to `POSTGRES_URLPGSQL`

2. **Create Vercel KV (Redis)**
   - Vercel dashboard > Storage > KV > Create
   - Copy URLs to `KV_URL`, `KV_REST_API_URL`, `KV_REST_API_TOKEN`

3. **Configure Stripe**
   - Create Stripe account at stripe.com
   - Get API keys from Dashboard > Developers > API keys
   - Create Pro plan product and get price ID
   - Set `STRIPE_PLAN_PRO_ID` to price ID

4. **Configure Webhook**
   - Stripe dashboard > Webhooks > Add endpoint
   - URL: `https://rostr-agent.vercel.app/api/stripe/webhooks`
   - Events: customer.subscription.*, invoice.payment_*
   - Copy signing secret to `STRIPE_WEBHOOK_SECRET`

5. **Set JWT Secret**
   ```bash
   node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
   ```
   Copy to `JWT_SECRET`

## Usage Pricing

- **Free Tier**: 10 executions/day, max 1 workspace
- **Pro Tier**: $20/month + $0.10 per 1,000 executions
- **Enterprise**: Custom pricing

Billing tracked in `executions` table:
- Each API call increments execution count
- Daily limits enforced via Vercel KV
- Monthly usage calculated from `executions` table

## Security

- JWT tokens with 24h expiration
- Passwords hashed with bcrypt (production)
- Credentials encrypted at rest
- Composio handles OAuth securely
- Stripe webhook signatures validated
- CORS restricted to verified origins

## Monitoring

Enable observability in production:

```typescript
// In app/layout.tsx
import { Analytics } from "@vercel/analytics/react";

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        {children}
        <Analytics />
      </body>
    </html>
  );
}
```

## Testing

### Manual Testing
1. Log in with demo credentials
2. Send a message in chat (should stream response)
3. Upload a skill file
4. Check billing dashboard (should show execution count)
5. Test integrations (form submission)

### API Testing
```bash
# Chat streaming
curl -X POST http://localhost:3000/api/orchestrate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer demo-user-token" \
  -d '{"messages":[{"role":"user","content":"Hello"}]}'

# List skills
curl http://localhost:3000/api/skills/list \
  -H "Authorization: Bearer demo-user-token"

# Billing status
curl http://localhost:3000/api/billing/status \
  -H "Authorization: Bearer demo-user-token"
```

## Troubleshooting

### PostgreSQL Connection Issues
- Verify `POSTGRES_URLPGSQL` format: `postgresql://user:pass@host:5432/db`
- Check Vercel dashboard for database status
- Ensure firewall allows connections

### Stripe Webhook Not Triggering
- Verify endpoint URL in Stripe dashboard
- Check webhook signing secret matches `STRIPE_WEBHOOK_SECRET`
- Test webhook manually in Stripe dashboard

### KV (Redis) Not Persisting
- Check `KV_URL`, `KV_REST_API_URL`, `KV_REST_API_TOKEN` are set
- Verify in Vercel KV dashboard
- Check daily limit reset (expires after 24h)

## Tech Stack

- **Frontend**: Next.js 15, React 19, Tailwind CSS
- **Backend**: Vercel Functions, Node.js 20+
- **LLM**: Claude 3.5 Sonnet (via Anthropic SDK)
- **Streaming**: Vercel AI SDK (@vercel/ai)
- **Database**: Vercel Postgres (PostgreSQL)
- **Cache**: Vercel KV (Redis)
- **Auth**: JWT with jose
- **Billing**: Stripe
- **Integrations**: Composio (50+ services)

## File Structure

```
apps/cloud-web-app/
├── app/
│   ├── api/              # API routes
│   │   ├── orchestrate/  # ROSTR chat endpoint
│   │   ├── auth/         # Authentication
│   │   ├── skills/       # Skill management
│   │   ├── billing/      # Usage tracking
│   │   └── stripe/       # Stripe webhooks
│   ├── app/              # Protected routes
│   │   ├── chat/         # Main chat interface
│   │   ├── skills/       # Skill marketplace
│   │   ├── workspaces/   # Workspace manager
│   │   ├── integrations/ # Integration hub
│   │   ├── billing/      # Billing dashboard
│   │   ├── settings/     # Account settings
│   │   └── layout.tsx    # App shell
│   ├── login/            # Auth page
│   ├── page.tsx          # Landing page
│   ├── layout.tsx        # Root layout
│   ├── globals.css       # Tailwind
│   └── middleware.ts     # Auth middleware
├── db/
│   └── schema.sql        # Database schema
├── public/               # Static assets
├── .env.example          # Example env vars
├── package.json          # Dependencies
├── next.config.js        # Next.js config
├── tsconfig.json         # TypeScript config
├── tailwind.config.js    # Tailwind config
└── vercel.json           # Vercel deployment config
```

## Contributing

1. Create feature branch: `git checkout -b feature/description`
2. Commit changes: `git commit -am "Add feature"`
3. Push branch: `git push origin feature/description`
4. Create pull request

## License

MIT - See LICENSE file

## Support

- Docs: [Vercel AI SDK Docs](https://sdk.vercel.ai)
- Issues: GitHub Issues
- Email: support@rostr.dev

## Roadmap

- [ ] Advanced skill scheduling
- [ ] Workflow builder UI
- [ ] Audit logs & compliance
- [ ] Team collaboration
- [ ] Custom model routing
- [ ] Advanced analytics
