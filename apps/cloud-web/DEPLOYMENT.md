# ROSTR Cloud - Deployment Guide

Complete guide to deploy ROSTR Cloud to production on Vercel with full infrastructure setup.

## Pre-Deployment Checklist

- [ ] GitHub repository created and connected to Vercel
- [ ] Stripe account created (stripe.com)
- [ ] Anthropic API key obtained (console.anthropic.com)
- [ ] Domain name registered (optional)
- [ ] Team members with Vercel access added

## Step 1: Vercel Project Setup

### 1.1 Create Vercel Project

```bash
# Install Vercel CLI
npm install -g vercel

# Login
vercel login

# Navigate to project
cd apps/cloud-web-app

# Deploy and create project
vercel
```

Select:
- Framework: Next.js
- Project name: rostr-cloud
- Root directory: ./
- Build command: `npm run build`
- Output directory: `.next`

### 1.2 Configure Production Domain

```bash
vercel domain add yourdomain.com
```

Or use default: `rostr-cloud.vercel.app`

## Step 2: Database Setup

### 2.1 Create Vercel Postgres Database

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Select project: rostr-cloud
3. Go to Storage tab
4. Click "Create Database" > Postgres
5. Name: `rostr_prod_db`
6. Region: Select closest to users
7. Click "Create"

### 2.2 Get Connection String

```bash
# Connection string appears in Storage tab
# Format: postgresql://user:password@host.vercel-storage.com:5432/verceldb

# Set as environment variable
vercel env add POSTGRES_URLPGSQL
# Paste the connection string
```

### 2.3 Initialize Database Schema

```bash
# Connect to database
psql postgresql://user:password@host.vercel-storage.com:5432/verceldb

# Or using Vercel CLI
vercel postgres query < db/schema.sql

# Verify tables created
\dt
```

## Step 3: Redis Cache Setup (Vercel KV)

### 3.1 Create Vercel KV Database

1. Storage tab > Create > Redis (Upstash)
2. Name: `rostr_cache`
3. Region: Same as Postgres for low latency
4. Click "Create"

### 3.2 Get Connection Strings

Storage tab shows:
- `KV_URL` - REST API endpoint
- `KV_REST_API_URL`
- `KV_REST_API_TOKEN`

```bash
vercel env add KV_URL
vercel env add KV_REST_API_URL
vercel env add KV_REST_API_TOKEN
```

## Step 4: Authentication Setup

### 4.1 Generate JWT Secret

```bash
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
```

Output: `a1b2c3d4e5f6...` (64 hex chars)

```bash
vercel env add JWT_SECRET
# Paste the generated secret
```

## Step 5: Anthropic API Configuration

### 5.1 Get API Key

1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Settings > API Keys
3. Create new key or copy existing
4. Keep it secret!

```bash
vercel env add ANTHROPIC_API_KEY
# Paste: sk-ant-xxxxxxxxxxxxx
```

### 5.2 Test Connection

```bash
vercel env pull
npm run dev

# Visit http://localhost:3000
# Try sending a chat message
```

## Step 6: Stripe Billing Setup

### 6.1 Create Stripe Account

1. Go to [stripe.com](https://stripe.com)
2. Sign up for account
3. Complete verification
4. Get Test Mode API keys

### 6.2 Create Pricing Plans

**Free Plan (automatically assigned):**
- No product/price needed (custom logic)

**Pro Plan:**
1. Dashboard > Products > Add product
2. Name: "ROSTR Pro"
3. Add price: $20 USD / month
4. Copy price ID: `price_xxxxx`

```bash
vercel env add STRIPE_PUBLIC_KEY
# Paste: pk_test_xxxxx (test key)

vercel env add STRIPE_SECRET_KEY
# Paste: sk_test_xxxxx (test key)

vercel env add STRIPE_PLAN_PRO_ID
# Paste: price_xxxxx
```

### 6.3 Setup Webhook Endpoint

1. Dashboard > Developers > Webhooks
2. Add endpoint
3. Endpoint URL: `https://your-domain.vercel.app/api/stripe/webhooks`
4. Select events:
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
5. Copy signing secret

```bash
vercel env add STRIPE_WEBHOOK_SECRET
# Paste: whsec_xxxxx
```

### 6.4 Test Webhook Locally

```bash
# In development, use Stripe CLI to forward webhooks
brew install stripe/stripe-cli/stripe
stripe login

# Forward events to local endpoint
stripe listen --forward-to localhost:3000/api/stripe/webhooks

# Trigger test events
stripe trigger customer.subscription.created
```

## Step 7: Environment Variables Summary

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx
POSTGRES_URLPGSQL=postgresql://user:pass@host:5432/db
KV_URL=redis://...
KV_REST_API_URL=https://...
KV_REST_API_TOKEN=xxxxx
STRIPE_PUBLIC_KEY=pk_test_xxxxx
STRIPE_SECRET_KEY=sk_test_xxxxx
STRIPE_PLAN_PRO_ID=price_xxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxx
JWT_SECRET=a1b2c3d4e5f6...

# Optional
NEXT_PUBLIC_API_URL=https://your-domain.vercel.app
NEXT_PUBLIC_APP_URL=https://your-domain.vercel.app
COMPOSIO_API_KEY=xxxxx

# Auto-set by Vercel
NODE_ENV=production
```

## Step 8: Deploy to Production

### 8.1 Verify Environment Variables

```bash
vercel env ls
```

All required variables should be listed.

### 8.2 Set Production Environment

```bash
# Ensure all vars are in Production environment
vercel env ls --environment production
```

### 8.3 Deploy

```bash
# Build locally to test
npm run build

# Deploy to production
vercel --prod

# Or push to GitHub and auto-deploy on main
git push origin main
```

### 8.4 Monitor Deployment

```bash
# Check deployment status
vercel deployments

# View logs
vercel logs --tail

# Check function performance
vercel analytics
```

## Step 9: Post-Deployment Verification

### 9.1 Health Checks

```bash
# Check landing page loads
curl https://your-domain.vercel.app/

# Test auth endpoint
curl -X POST https://your-domain.vercel.app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test"}'

# Test chat endpoint (should error without auth)
curl https://your-domain.vercel.app/api/orchestrate
```

### 9.2 Verify Database Connection

```bash
# Check if tables exist
psql $POSTGRES_URLPGSQL -c "\dt"

# Should show: users, workspaces, skills, executions, sessions
```

### 9.3 Test Full User Flow

1. Visit https://your-domain.vercel.app
2. Click "Get Started"
3. Log in with demo: `demo@example.com` / `demo123`
4. Send a chat message (should stream response)
5. Upload a skill file
6. Check billing dashboard

### 9.4 Monitor Errors

```bash
# View function logs
vercel logs rostr-cloud

# Set up monitoring
# Dashboard > Settings > Environment > Alerts > Add alert
```

## Step 10: Performance Optimization

### 10.1 Enable Analytics

```bash
# In app/layout.tsx, add:
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

### 10.2 Configure Caching

```bash
# In next.config.js
const nextConfig = {
  // Vercel Edge Cache
  onDemandISR: {
    maxMemoryUsageSecretToken: process.env.ISR_TOKEN,
  },
};
```

### 10.3 Database Connection Pooling

Vercel Postgres includes connection pooling:
- Max connections: 100
- Min connections: 10
- Connection timeout: 30s

For high load, use:
```typescript
const pool = new Pool({
  host: process.env.POSTGRES_HOST,
  user: process.env.POSTGRES_USER,
  password: process.env.POSTGRES_PASSWORD,
  database: process.env.POSTGRES_DATABASE,
  max: 20,
});
```

## Step 11: Security Hardening

### 11.1 Enable HTTPS

Vercel automatically provides SSL/TLS certificates.

### 11.2 Configure CORS

```typescript
// In API routes
const corsHeaders = {
  "Access-Control-Allow-Origin": "https://your-domain.vercel.app",
  "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE",
};
```

### 11.3 Rate Limiting

```typescript
// apps/cloud-web-app/lib/rateLimit.ts
import { kv } from "@vercel/kv";

export async function rateLimit(key: string, limit: number = 10, window: number = 60) {
  const count = await kv.incr(key);
  if (count === 1) await kv.expire(key, window);
  return count <= limit;
}
```

## Step 12: Monitoring & Alerts

### 12.1 Error Tracking

```bash
# Enable Sentry integration
npm install @sentry/nextjs

# Configure in next.config.js and layout.tsx
```

### 12.2 Uptime Monitoring

```bash
# Set up health check endpoint
# curl https://your-domain.vercel.app/api/health

# Then use UptimeRobot or similar service
```

### 12.3 Billing Alerts

Configure in Stripe Dashboard:
- Payment failed
- High usage alerts
- Monthly forecast

## Rollback Procedure

If deployment fails:

```bash
# View deployment history
vercel deployments

# Rollback to previous version
vercel rollback

# Or redeploy specific commit
vercel --prod --git-commit=abc123
```

## Maintenance

### Monthly Tasks

- [ ] Review database size and optimize indexes
- [ ] Check error logs for issues
- [ ] Review billing usage
- [ ] Test disaster recovery backup
- [ ] Update dependencies

### Security Tasks

- [ ] Rotate API keys (quarterly)
- [ ] Review access logs
- [ ] Update Stripe webhook events if needed
- [ ] Check for security updates

## Troubleshooting

### Database Connection Timeout
```bash
# Verify connection string
echo $POSTGRES_URLPGSQL

# Test connection
psql $POSTGRES_URLPGSQL -c "SELECT 1"
```

### Stripe Webhooks Not Received
1. Check webhook URL in dashboard
2. Verify signing secret matches
3. Check function logs: `vercel logs`
4. Test manually: Stripe Dashboard > Webhooks > Test endpoint

### Memory Exceeded Error
```bash
# Increase function memory in vercel.json
{
  "functions": {
    "app/api/**": {
      "memory": 3008,
      "maxDuration": 60
    }
  }
}
```

### High Database Load
```sql
-- Check slow queries
SELECT query, calls, total_time FROM pg_stat_statements 
ORDER BY total_time DESC LIMIT 10;

-- Add indexes
CREATE INDEX idx_executions_user_date ON executions(user_id, created_at);
```

## Support & Resources

- [Vercel Docs](https://vercel.com/docs)
- [Next.js Docs](https://nextjs.org/docs)
- [Vercel AI SDK](https://sdk.vercel.ai)
- [Stripe Documentation](https://stripe.com/docs)
- [Anthropic API Docs](https://docs.anthropic.com)

---

**Deployment Status**: Ready for production after completing all steps above.

**Estimated Costs (Monthly)**:
- Vercel Functions: $0 (first 1M invocations free)
- Vercel Postgres: $15 (500 MB baseline)
- Vercel KV: $0.50 (10 GB included)
- Stripe: 2.9% + $0.30 per transaction
- Anthropic API: $0.003 per 1K input tokens, $0.015 per 1K output tokens
