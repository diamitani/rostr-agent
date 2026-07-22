# ROSTR Cloud - API Documentation

Complete API reference for backend endpoints.

## Base URL

```
Development: http://localhost:3000
Production: https://rostr-agent.vercel.app
```

## Authentication

All protected endpoints require JWT token via `Authorization` header:

```bash
Authorization: Bearer <token>
```

Get token via `/api/auth/login`.

## Endpoints

### Authentication

#### POST /api/auth/login

Log in user and receive JWT token.

**Request:**
```json
{
  "email": "demo@example.com",
  "password": "demo123"
}
```

**Response:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Status:** 200 (success), 401 (invalid), 400 (missing fields)

**Example:**
```bash
curl -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@example.com","password":"demo123"}'
```

---

### Chat & Orchestration

#### POST /api/orchestrate

Stream LLM response for user messages. Returns Server-Sent Events (SSE) stream.

**Headers:**
```
Authorization: Bearer <token>
Content-Type: application/json
```

**Request:**
```json
{
  "messages": [
    {
      "role": "user",
      "content": "What is ROSTR?"
    }
  ]
}
```

**Response (SSE Stream):**
```
event: data
data: {"type":"text","content":"ROSTR is"}

event: data
data: {"type":"text","content":" an AI"}

event: data
data: {"type":"text","content":" workflow"}

event: data
data: {"type":"done"}
```

**Status:** 200 (streaming), 429 (daily limit), 500 (error)

**Example:**
```bash
curl -N -X POST http://localhost:3000/api/orchestrate \
  -H "Authorization: Bearer demo-user-token" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Hello"}
    ]
  }'
```

**JavaScript Example:**
```typescript
const response = await fetch('/api/orchestrate', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    messages: [{ role: 'user', content: 'Hello' }]
  })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  
  const text = decoder.decode(value);
  const lines = text.split('\n');
  
  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const data = JSON.parse(line.slice(6));
      if (data.type === 'text') {
        console.log(data.content);
      }
    }
  }
}
```

---

### Skills

#### GET /api/skills/list

List all skills for authenticated user.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "skills": [
    {
      "id": "1",
      "name": "Web Scraper",
      "description": "Extract data from web pages",
      "created_at": "2024-07-20T10:00:00Z"
    }
  ]
}
```

**Status:** 200, 500

**Example:**
```bash
curl http://localhost:3000/api/skills/list \
  -H "Authorization: Bearer demo-user-token"
```

---

#### POST /api/skills/upload

Upload new skill file (.skill, .js, .ts).

**Headers:**
```
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

**Form Data:**
- `file` - Skill file (.skill, .js, or .ts)

**Response:**
```json
{
  "id": "abc123",
  "name": "My Skill",
  "description": "User-uploaded skill",
  "created_at": "2024-07-20T10:00:00Z"
}
```

**Status:** 201 (created), 400 (invalid file), 500 (error)

**Example:**
```bash
curl -F "file=@my-skill.js" \
  http://localhost:3000/api/skills/upload \
  -H "Authorization: Bearer demo-user-token"
```

---

### Billing & Usage

#### GET /api/billing/status

Get user's subscription and usage information.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "plan": "free",
  "status": "active",
  "executionsToday": 5,
  "dailyLimit": 10,
  "monthlyUsage": 45,
  "monthlySpend": "0.00",
  "nextBillingDate": "2024-08-20T10:00:00Z"
}
```

**Status:** 200, 500

**Example:**
```bash
curl http://localhost:3000/api/billing/status \
  -H "Authorization: Bearer demo-user-token"
```

---

### Stripe Webhooks

#### POST /api/stripe/webhooks

Receive Stripe webhook events (events on customer.subscription, invoice.payment).

**Headers (Stripe validates these):**
```
Stripe-Signature: <signature>
Content-Type: application/json
```

**Request (example):**
```json
{
  "type": "customer.subscription.created",
  "data": {
    "object": {
      "id": "sub_123",
      "customer": "cus_123",
      "items": {
        "data": [
          {
            "price": {
              "id": "price_pro"
            }
          }
        ]
      }
    }
  }
}
```

**Response:**
```json
{
  "received": true
}
```

**Status:** 200 (success), 400 (invalid signature)

**Events Handled:**
- `customer.subscription.created` - Upgrade to Pro
- `customer.subscription.updated` - Plan changed
- `customer.subscription.deleted` - Downgrade to Free
- `invoice.payment_succeeded` - Payment successful
- `invoice.payment_failed` - Payment failed

---

## Workspace Endpoints (TODO)

These endpoints are currently mocked in frontend. Backend implementation pending:

```
GET  /api/workspace/list
POST /api/workspace/create
GET  /api/workspace/:id
PUT  /api/workspace/:id
DELETE /api/workspace/:id
POST /api/workspace/:id/save   # Save state to KV
GET  /api/workspace/:id/load   # Load state from KV
```

---

## Integrations Endpoints (TODO)

Composio integration endpoints (to be implemented):

```
GET  /api/integrations/list
POST /api/integrations/:provider/connect
GET  /api/integrations/:provider/status
POST /api/integrations/:provider/disconnect
```

Supported providers:
- `telegram`
- `whatsapp`
- `imessage`
- `signal`
- `slack`
- `email`

---

## Error Responses

All errors return consistent JSON format:

```json
{
  "error": "Error message",
  "code": "ERROR_CODE",
  "details": {}
}
```

**Common Status Codes:**

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request (invalid input) |
| 401 | Unauthorized (invalid/missing token) |
| 429 | Too Many Requests (rate limit/daily limit) |
| 500 | Internal Server Error |

**Example Error:**
```json
{
  "error": "Daily execution limit exceeded",
  "code": "LIMIT_EXCEEDED",
  "details": {
    "daily_limit": 10,
    "used_today": 10
  }
}
```

---

## Rate Limiting

Current limits:

| Endpoint | Limit | Window |
|----------|-------|--------|
| `/api/auth/login` | 5 | 15 minutes |
| `/api/orchestrate` | 10 (free) | 1 day |
| `/api/orchestrate` | unlimited | (pro) |
| `/api/skills/upload` | 10 | 1 hour |
| `/api/skills/list` | 100 | 1 minute |

Rate limit headers:

```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1721476800
```

---

## Pagination

List endpoints support pagination:

**Query Parameters:**
```
?page=1&limit=20&sort=created_at&order=desc
```

**Response:**
```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 100,
    "pages": 5
  }
}
```

---

## Filtering

Some list endpoints support filtering:

```
?filter[plan]=pro&filter[status]=active
```

---

## Versioning

Current API version: `v1`

Future breaking changes will increment to `/api/v2/...`

---

## SDK/Client Libraries

### JavaScript/TypeScript

```typescript
import { VercelAI } from '@vercel/ai';

const client = new VercelAI({
  apiKey: process.env.ANTHROPIC_API_KEY,
});

// Use directly or via fetch with streaming
```

### Python

```python
import anthropic

client = anthropic.Anthropic(api_key="sk-ant-...")

# Make requests to ROSTR cloud via webhook integration
```

---

## Webhooks

ROSTR can send webhooks for:
- Execution completed
- Skill uploaded
- Subscription changed

Configure webhooks in Settings > Webhooks.

---

## Rate Limiting Headers

```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1721476800
```

---

## Testing

### Local Testing

```bash
# Start server
npm run dev

# Test endpoint
curl -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@example.com","password":"demo123"}'
```

### Production Testing

```bash
curl -X POST https://rostr-agent.vercel.app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@example.com","password":"demo123"}'
```

---

## Status Page

Check service status:
```
GET /api/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2024-07-20T10:00:00Z",
  "services": {
    "database": "ok",
    "cache": "ok",
    "anthropic": "ok"
  }
}
```

---

## Documentation Standards

API documented in OpenAPI 3.0 format. View Swagger UI:

```
http://localhost:3000/api/docs
```

Generate from code:
```bash
npm run generate-docs
```

---

## Support

For API issues:
- Email: api-support@rostr.dev
- GitHub Issues: https://github.com/rostr/rostr-cloud/issues
- Discord: https://discord.gg/rostr
