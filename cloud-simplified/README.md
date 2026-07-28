# ROSTR Cloud - Simplified Architecture

A simplified, production-ready version of ROSTR Agent with workspace provisioning, AWS Bedrock backend, and Assistant UI frontend.

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Frontend      │────▶│   API Gateway    │────▶│   Lambda        │
│  (Assistant UI) │     │   (HTTP + WS)    │     │   (ROSTR Core)  │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                              │                            │
                              │                    ┌─────────┴─────────┐
                              │                    │                   │
                              ▼                    ▼                   ▼
                    ┌──────────────────┐   ┌──────────────┐  ┌────────────────┐
                    │   Cognito Auth   │   │   Bedrock    │  │   DynamoDB     │
                    │   (Users/JWT)    │   │   (Claude)   │  │   (Hub/RAG)    │
                    └──────────────────┘   └──────────────┘  └────────────────┘
                                                                    │
                                                              ┌─────┴──────┐
                                                              │            │
                                                              ▼            ▼
                                                       ┌──────────┐  ┌──────────┐
                                                       │ S3 RAG   │  │ S3 GStack│
                                                       │ (Docs)   │  │(Workspaces)│
                                                       └──────────┘  └──────────┘
```

## Quick Start

### Prerequisites

- Node.js 20+
- AWS account with Bedrock access
- AWS CLI configured

### Local Development

```bash
# Install dependencies
cd cloud-simplified
npm install

# Set environment variables
cp backend/.env.example backend/.env

# Edit backend/.env with your AWS credentials:
# AWS_ACCESS_KEY_ID=...
# AWS_SECRET_ACCESS_KEY=...
# AWS_REGION=us-east-1
# JWT_SECRET=your-secret-key

# Start development servers
npm run dev

# This starts:
# - Backend on http://localhost:3001
# - Frontend on http://localhost:3000
```

### Deploy to AWS

```bash
# Install serverless globally
npm install -g serverless

# Configure AWS credentials
serverless config credentials --provider aws --key YOUR_KEY --secret YOUR_SECRET

# Deploy
npm run deploy

# Or manually:
cd aws-deploy
serverless deploy --stage prod
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Create new account
- `POST /api/auth/login` - Sign in
- `GET /api/me` - Get current user (requires JWT)

### Workspaces
- `GET /api/workspaces` - List user's workspaces
- `POST /api/workspaces` - Create new workspace
- `POST /api/workspaces/:id/launch` - Launch workspace
- `GET /api/workspaces/:id/messages` - Get workspace messages

### Chat
- `POST /api/chat` - Send message (REST)
- `POST /api/chat/stream` - Send message (SSE streaming)

### WebSocket
- `wss://api.rostragent.com` - Real-time chat

## Environment Variables

### Backend
- `AWS_ACCESS_KEY_ID` - AWS access key
- `AWS_SECRET_ACCESS_KEY` - AWS secret key
- `AWS_REGION` - AWS region (default: us-east-1)
- `COGNITO_USER_POOL_ID` - Cognito User Pool ID
- `COGNITO_CLIENT_ID` - Cognito App Client ID
- `JWT_SECRET` - JWT signing secret
- `FRONTEND_URL` - Frontend URL for CORS

### Frontend
- `VITE_API_URL` - Backend API URL

## Features

### Core ROSTR Skills
1. **PAL (Prompt Abstraction Layer)** - 5-stage compilation pipeline
2. **NPAO (Necessity Prioritize)** - 4D routing with weighted scoring
3. **RAG-DAL** - 3-tier multi-pass retrieval
4. **Hub** - Persistent state with 6-level inheritance

### User Flow
1. User visits landing page at `/`
2. Clicks "Get Started" and registers
3. Receives email confirmation
4. Logs in and sees Dashboard
5. Default workspace is created automatically
6. User can create more workspaces or launch existing ones
7. Launched workspace opens chat interface
8. All messages saved to S3 + DynamoDB

### Security
- AWS Cognito for auth with email verification
- JWT tokens for API access (7 day expiry)
- Per-user workspace isolation via S3 prefix
- Bedrock IAM roles for model access
- Rate limiting on all endpoints

## File Structure

```
cloud-simplified/
├── backend/
│   ├── src/
│   │   ├── index.ts           # Express server
│   │   ├── agent.ts           # ROSTR Agent core
│   │   ├── auth/
│   │   │   └── service.ts     # Cognito auth
│   │   ├── pal/
│   │   │   └── compiler.ts    # PAL compiler
│   │   ├── npao/
│   │   │   └── router.ts      # NPAO router
│   │   ├── rag-dal/
│   │   │   └── engine.ts      # RAG engine
│   │   ├── hub/
│   │   │   └── store.ts       # Hub persistence
│   │   └── gstack/
│   │       └── workspace.ts   # Workspace management
│   ├── package.json
│   └── tsconfig.json
├── frontend/
│   ├── src/
│   │   ├── main.tsx           # React entry
│   │   ├── App.tsx            # Routes
│   │   ├── context/
│   │   │   └── AuthContext.tsx # Auth state
│   │   ├── components/
│   │   │   └── ProtectedRoute.tsx
│   │   └── pages/
│   │       ├── Landing.tsx    # Marketing page
│   │       ├── Login.tsx      # Sign in
│   │       ├── Register.tsx   # Sign up
│   │       ├── Dashboard.tsx  # Workspace list
│   │       └── Workspace.tsx  # Chat interface
│   ├── package.json
│   └── vite.config.ts
├── aws-deploy/
│   └── serverless.yml         # Infrastructure as code
└── package.json               # Root with dev scripts
```

## Deployment Checklist

- [ ] Set up AWS account with Bedrock access
- [ ] Configure AWS CLI credentials
- [ ] Create Cognito User Pool
- [ ] Set JWT_SECRET environment variable
- [ ] Deploy with `serverless deploy --stage prod`
- [ ] Update frontend .env with production API URL
- [ ] Build and deploy frontend to Vercel/CloudFront
- [ ] Test user registration flow
- [ ] Test workspace creation
- [ ] Test chat functionality

## License

MIT - See LICENSE file
