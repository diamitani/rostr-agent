# ROSTR Cloud - Quick Start

Get ROSTR Cloud running in 5 minutes.

## Prerequisites

- Node.js 20+ (check: `node --version`)
- npm 10+ (check: `npm --version`)
- Git

## 1. Setup (2 minutes)

```bash
# Navigate to project
cd apps/cloud-web-app

# Install dependencies
npm install

# Copy environment template
cp .env.example .env.local

# Optional: Add your Anthropic API key
# Edit .env.local and set ANTHROPIC_API_KEY
```

## 2. Start Dev Server (1 minute)

```bash
npm run dev
```

Output:
```
> cloud-web-app@0.1.0 dev
> next dev

  ▲ Next.js 15.0.0
  - Local:        http://localhost:3000
  - Environments: .env.local

  ✓ Ready in 2.5s
```

## 3. Open in Browser (1 minute)

Visit: **http://localhost:3000**

### Demo Credentials
- **Email:** demo@example.com
- **Password:** demo123

## 4. Test Features (1 minute)

### Chat
1. Click "Get Started" or "Sign In"
2. Enter demo credentials
3. Send message: "Hello ROSTR"
4. Watch response stream in real-time ✨

### Skills
1. Navigate to Skills
2. See demo skills
3. Try uploading a .js file (optional)

### Billing
1. Navigate to Billing
2. View usage dashboard
3. See Pro plan options

## What's Working

- ✅ Real-time chat streaming
- ✅ User authentication
- ✅ Chat history display
- ✅ Responsive design (mobile/tablet/desktop)
- ✅ Skills marketplace UI
- ✅ Billing dashboard
- ✅ Workspace manager
- ✅ Integration hub

## What Needs Backend

- 🔌 Skill execution (requires API implementation)
- 💾 Persistent database (use Vercel Postgres)
- 💳 Stripe billing (requires Stripe account)
- 🔐 User registration (security review needed)
- 🔗 Composio integrations (requires API setup)

## File Structure

```
apps/cloud-web-app/
├── app/
│   ├── api/          # Backend endpoints
│   ├── app/          # Protected routes
│   ├── login/        # Auth page
│   ├── page.tsx      # Landing page
│   ├── layout.tsx    # Root layout
│   └── globals.css   # Styles
├── db/
│   └── schema.sql    # Database schema
├── public/           # Static files
├── package.json
├── tsconfig.json
├── tailwind.config.js
└── next.config.js
```

## Common Commands

```bash
# Development
npm run dev          # Start dev server
npm run build        # Build for production
npm start            # Start production server
npm run lint         # Lint code
npm run type-check   # TypeScript check

# Debugging
# Open http://localhost:3000 with DevTools (F12)
# Check Network tab for API calls
# View Console for errors

# Testing
npm run test         # Run tests (if configured)
```

## Troubleshooting

### "Port 3000 in use"
```bash
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9

# Or use different port
PORT=3001 npm run dev
```

### "Cannot find module"
```bash
# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
```

### "TypeScript errors"
```bash
# Run type check
npm run type-check

# Fix most issues
npm run lint -- --fix
```

### Demo credentials not working
Check that server is running on http://localhost:3000/api/auth/login

```bash
curl -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@example.com","password":"demo123"}'
```

Should return: `{"token":"demo-user-xxx"}`

## Next Steps

### To Deploy to Vercel

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel

# Set production environment variables
vercel env add ANTHROPIC_API_KEY
vercel env add POSTGRES_URLPGSQL
vercel env add KV_URL
vercel env add KV_REST_API_TOKEN

# Redeploy with env
vercel --prod
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for full guide.

### To Add Database

1. Set `POSTGRES_URLPGSQL` in `.env.local`
2. Run migrations: `npm run migrate`
3. APIs will use real database instead of demo data

### To Add Stripe Billing

1. Create Stripe account at stripe.com
2. Get API keys
3. Set `STRIPE_SECRET_KEY`, `STRIPE_PLAN_PRO_ID`
4. Billing page will use real Stripe

### To Use Your Own API Key

1. Get key from console.anthropic.com
2. Set `ANTHROPIC_API_KEY` in `.env.local`
3. Restart server: `npm run dev`
4. Chat will use your key (counts against your quota)

## Architecture Overview

```
Frontend (React + Next.js)
├── Pages (login, chat, skills, etc)
├── Components (chat input, message, etc)
├── State management (useChat hook)
└── Tailwind CSS styling

Backend (Vercel Functions + Node.js)
├── API routes (/api/*)
├── Anthropic SDK (LLM)
├── Vercel AI SDK (streaming)
├── Database (Postgres)
└── Cache (Redis/KV)

External Services
├── Anthropic (Claude API)
├── Stripe (billing)
├── Vercel (hosting)
└── Composio (integrations)
```

## Performance Tips

1. Enable browser caching: Settings > DevTools > Network > Disable cache is OFF
2. Open DevTools Performance tab to profile chat streaming
3. Check Network tab to see API response times
4. Use Lighthouse (DevTools > Lighthouse) to audit performance

## Learning Resources

- [Next.js Docs](https://nextjs.org/docs)
- [React Docs](https://react.dev)
- [Vercel AI SDK](https://sdk.vercel.ai)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [TypeScript](https://www.typescriptlang.org/docs)

## Support

- 📖 Docs: See README.md, DEPLOYMENT.md, API.md, TEST_PLAN.md
- 🐛 Bugs: Check console (F12), Network tab
- 💬 Questions: Open GitHub issues
- 📧 Email: support@rostr.dev

---

**You're all set!** 🚀

Visit http://localhost:3000 and start building.
