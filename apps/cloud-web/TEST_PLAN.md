# ROSTR Cloud - Test Plan

Comprehensive testing guide for verifying all functionality before production deployment.

## 1. Authentication Flow

### 1.1 Login

```bash
# Test demo credentials
curl -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "demo@example.com",
    "password": "demo123"
  }'

# Expected: { "token": "demo-user-xxx" }
```

**Frontend Test:**
1. Visit http://localhost:3000/login
2. Enter: demo@example.com / demo123
3. Click Sign In
4. Should redirect to /app/chat
5. Verify auth token in cookies

### 1.2 Protected Routes

1. Clear browser cookies
2. Try to visit http://localhost:3000/app/chat
3. Should redirect to /login

### 1.3 Token Expiration

```bash
# Manually expire token in KV (for demo, skip as no expiry in demo mode)
```

## 2. Chat Interface

### 2.1 Real-time Streaming

1. Log in with demo credentials
2. Type message: "Hello, what is ROSTR?"
3. Verify:
   - Message appears in chat
   - Loading indicator shows
   - Response streams in real-time
   - Message completes without errors

### 2.2 Multiple Messages

1. Send 3-5 messages in sequence
2. Verify conversation history displays
3. Scroll behavior works smoothly
4. Auto-scroll on new messages

### 2.3 Long Responses

1. Send: "Write a Python function that calculates fibonacci"
2. Verify:
   - Streaming continues smoothly
   - No truncation
   - Code formatting displays correctly
   - Can stop mid-stream

### 2.4 Stop Button

1. Send long prompt
2. Click Stop before completion
3. Verify:
   - Request cancels
   - Button changes back to Send
   - Can send new message immediately

### 2.5 Error Handling

1. Simulate network error: DevTools > Network > Offline
2. Try to send message
3. Verify error message displays
4. Go back online
5. Message should retry or prompt to retry

## 3. Skills Management

### 3.1 List Skills

```bash
# API test
curl http://localhost:3000/api/skills/list \
  -H "Authorization: Bearer demo-user-token"

# Expected: { "skills": [ ... ] }
```

**Frontend Test:**
1. Navigate to /app/skills
2. Verify demo skills display:
   - Web Scraper
   - Email Scheduler
3. Each shows name, description, created date

### 3.2 Upload Skill

**Create test skill file: test-skill.js**
```javascript
/*
name: "Test Skill"
description: "A test skill"
*/

export function execute(input) {
  return {
    status: "success",
    result: input.toUpperCase()
  };
}
```

**Test Upload:**
1. Click upload area
2. Select test-skill.js
3. Verify:
   - File uploads successfully
   - Success message appears
   - Skill appears in list

### 3.3 Skill Integration

1. Go to chat
2. Try using uploaded skill (requires skill invocation format)
3. Verify execution works

## 4. Workspaces

### 4.1 List Workspaces

1. Navigate to /app/workspaces
2. Verify demo workspaces display:
   - Default
   - Research Project
3. Each shows creation date

### 4.2 Create Workspace

1. Enter name: "Test Workspace"
2. Click Create
3. Verify:
   - New workspace appears in list
   - Can open workspace
   - Workspace state persists

### 4.3 Workspace Persistence

1. Create workspace "Test WS"
2. Navigate away
3. Return to workspaces
4. Verify "Test WS" still exists

## 5. Integrations

### 5.1 Display Integrations

1. Navigate to /app/integrations
2. Verify all 6 integrations display:
   - Telegram
   - WhatsApp
   - iMessage
   - Signal
   - Slack
   - Email

### 5.2 Expand Integration

1. Click Telegram row
2. Verify form expands showing Bot Token field
3. Click again to collapse
4. Try expanding different integration

### 5.3 Connect Integration

1. Expand Telegram
2. Click Connect button
3. Verify button state changes to "Connected"
4. Refresh page
5. Verify connection persists (in demo, it won't)

## 6. Billing Dashboard

### 6.1 Display Status

1. Navigate to /app/billing
2. Verify displays:
   - Current Plan: Free
   - Today's Executions: X/10
   - Monthly Executions: X
   - This Month: $0.00
   - Usage bar shows percentage
   - Plans listed (Free, Pro, Enterprise)

### 6.2 Daily Limit Tracking

1. Send 10 messages in chat
2. Check billing dashboard
3. Verify Today's Executions increments
4. Send 11th message
5. Verify free tier limit error (in production)

### 6.3 Plan Display

1. Verify Free plan shows as "Current Plan"
2. Verify Pro/Enterprise show "Switch" button
3. Click Pro "Switch" button
4. Should direct to Stripe checkout (requires config)

## 7. Settings Page

### 7.1 Display Settings

1. Navigate to /app/settings
2. Verify displays:
   - Anthropic API Key field
   - Model selector (Claude 3.5 Sonnet default)
   - Temperature slider
   - Account email
   - Subscription status
   - Change Password button
   - Delete Account button

### 7.2 API Key Input

1. Paste valid Anthropic key
2. Click Save
3. Verify key is stored
4. (In frontend-only demo, just verifies UI works)

## 8. Responsive Design

### 8.1 Desktop (1920px+)

1. Open Chrome DevTools
2. Set to Full width
3. Verify layout looks correct
4. Sidebar visible
5. Chat area full width
6. No horizontal scroll

### 8.2 Tablet (768px)

1. Set viewport to 768x1024
2. Verify:
   - Sidebar visible or hamburger menu
   - Chat area responsive
   - Touch-friendly buttons
   - Forms stack vertically

### 8.3 Mobile (375px)

1. Set viewport to 375x667
2. Verify:
   - Hamburger menu visible
   - Clicking menu toggles sidebar
   - Chat interface functional
   - Touch interactions smooth
   - No content cut off

## 9. Navigation

### 9.1 Sidebar Navigation

1. Verify all nav items present:
   - Chat (💬)
   - Skills (⚙️)
   - Workspaces (📁)
   - Integrations (🔗)
   - Billing (💳)
   - Settings (⚡)

### 9.2 Active State

1. Visit /app/chat
2. Verify Chat nav item highlighted (cyan border)
3. Visit /app/skills
4. Verify Skills highlighted, Chat not
5. Verify current path shows in breadcrumb/title

### 9.3 Logout

1. Click Logout button
2. Verify redirects to home page
3. Try to visit /app/chat
4. Should redirect to /login

## 10. Performance Tests

### 10.1 Load Time

```bash
# Using DevTools Lighthouse
1. Navigate to http://localhost:3000
2. Run Lighthouse audit
3. Verify:
   - Performance > 80
   - Accessibility > 80
   - Best Practices > 80
   - SEO > 80
```

### 10.2 Chat Streaming Speed

1. Send message
2. Verify response starts within 2 seconds
3. Verify streaming continues smoothly
4. No stuttering or delays

### 10.3 Database Queries

1. Open DevTools Network tab
2. Send chat message
3. Verify API call completes within 3 seconds
4. Check response size is reasonable

## 11. API Tests

### 11.1 Orchestrate Endpoint

```bash
# Test streaming
curl -N -X POST http://localhost:3000/api/orchestrate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer demo-user-token" \
  -d '{
    "messages": [
      {"role": "user", "content": "Say hello"}
    ]
  }'

# Expected: Event stream with text chunks
```

### 11.2 Skills Endpoints

```bash
# List
curl http://localhost:3000/api/skills/list \
  -H "Authorization: Bearer demo-user-token"

# Upload
curl -F "file=@test-skill.js" \
  http://localhost:3000/api/skills/upload \
  -H "Authorization: Bearer demo-user-token"
```

### 11.3 Billing Endpoint

```bash
curl http://localhost:3000/api/billing/status \
  -H "Authorization: Bearer demo-user-token"

# Expected response:
{
  "plan": "free",
  "executionsToday": 5,
  "dailyLimit": 10,
  "monthlyUsage": 45,
  "monthlySpend": "0.00"
}
```

## 12. Accessibility

### 12.1 Keyboard Navigation

1. Visit /app/chat
2. Tab through all interactive elements
3. Verify focus visible on each element
4. Buttons, inputs, links all focusable
5. Tab order logical

### 12.2 Screen Reader

1. Enable screen reader (Mac: Cmd+F5)
2. Navigate chat page
3. Verify:
   - Page title read
   - Buttons announced correctly
   - Form labels associated
   - Errors announced

### 12.3 Color Contrast

1. Use Firefox DevTools Accessibility tab
2. Verify text contrast ratios:
   - WCAG AA: 4.5:1 (text)
   - WCAG AAA: 7:1 (preferred)
3. Check all text areas pass

## 13. Error Scenarios

### 13.1 Missing API Key

1. Don't set ANTHROPIC_API_KEY
2. Send chat message
3. Verify friendly error message
4. Should not expose full error

### 13.2 Database Unavailable

1. Disconnect network
2. Try to fetch billing status
3. Verify graceful fallback to demo data
4. No crash or unhandled error

### 13.3 Invalid File Upload

1. Try to upload .txt file
2. Verify error: "Invalid file type"
3. Try empty file
4. Verify error: "No file provided"

## 14. Stripe Integration (Production Only)

### 14.1 Subscription Creation

1. On billing page, click Pro "Switch"
2. Redirected to Stripe checkout
3. Enter test card: 4242 4242 4242 4242
4. Complete purchase
5. Verify subscription created in Stripe dashboard

### 14.2 Webhook Verification

```bash
# Check webhook signature validated
curl -X POST http://localhost:3000/api/stripe/webhooks \
  -H "stripe-signature: invalid" \
  -d '{"type":"test"}'

# Should return 400 (invalid signature)
```

## 15. Security Tests

### 15.1 XSS Prevention

1. In chat, send message with HTML: `<script>alert('xss')</script>`
2. Verify HTML is escaped
3. No script execution

### 15.2 CSRF Protection

1. Verify Content-Type headers required
2. Try POST without proper headers
3. Should fail or prompt

### 15.3 SQL Injection

1. Try login with: `" OR "1"="1`
2. Verify failed login
3. No database access granted

## Test Results Checklist

- [ ] Authentication working
- [ ] Chat streaming functional
- [ ] Skills upload/list working
- [ ] Workspaces CRUD working
- [ ] Integrations display correctly
- [ ] Billing dashboard shows data
- [ ] Settings page loads
- [ ] Responsive on mobile/tablet/desktop
- [ ] Navigation working
- [ ] Performance acceptable
- [ ] API endpoints responding
- [ ] Accessibility meets WCAG AA
- [ ] Error handling graceful
- [ ] No console errors
- [ ] Security tests passed

## Known Limitations (Demo Mode)

- Database operations gracefully degrade to demo data
- Stripe billing requires production setup
- Integrations require API keys to connect
- User registration not implemented (demo only)
- Skill execution mocked

## Ready for Production?

Deploy to production after:
1. ✅ All tests passing
2. ✅ Performance benchmarks met
3. ✅ Security review completed
4. ✅ Environment variables configured
5. ✅ Database migrations run
6. ✅ Stripe webhooks configured
7. ✅ API keys validated
8. ✅ Monitoring alerts set up
