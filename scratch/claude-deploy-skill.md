# Claude Code Deployment Skill
triggers: ["deploy to vercel", "prod deploy", "push to prod"]
description: "Handles secure Vercel deployments with environment variable validation"
constraints: ["Always run lint first", "Check VERCEL_TOKEN existence"]

1. Run npm run lint
2. Check env vars
3. Run vercel --prod
