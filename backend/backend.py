#!/usr/bin/env python3
"""
ROSTR Cloud Agent Backend — Simplified AWS Agent Core + ROSTR/PAL Harness

Exposes an OpenAI-compatible /v1/chat/completions endpoint that assistant-ui
can use directly as a "Custom API" runtime.

Pipeline:
  User Message → PAL Compiler (intent extraction + enhancement) → 
  NPAO Router (phase classification) → LLM Call (BYOK) → Response

Architecture:
  - ROSTR/PAL: Prompt Abstraction Layer compiles user intent
  - NPAO: Phase-aware routing (PreD/Design/Dev/Deploy/Debug)
  - AWS Agent Core (boto3 shim or real SDK): managed memory + state
  - S3 per-user workspaces: data lake buckets for persistent storage
  - assistant-ui frontend: consumes the OpenAI-compatible endpoint
"""

import os
import json
import time
import uuid
import asyncio
import logging
from datetime import datetime
from typing import Optional, Any
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ── ROSTR Core ──────────────────────────────────────────────────────────────
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rostr.pal.compiler import PALCompiler
from rostr.npao import NPAO, PhaseType
from rostr.hub import RostrHub, StateLevel
from harness_client import HarnessClient, list_agent_skills

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rostr-backend")

# ── Globals ──────────────────────────────────────────────────────────────────
pal_compiler = PALCompiler()
npao = NPAO()
hub = RostrHub(base_path=os.environ.get("ROSTR_HUB_PATH", os.path.join(os.path.dirname(__file__), "..", ".rostr")))
harness = HarnessClient()

# ── Per-user workspace management (S3-backed) ────────────────────────────────
WORKSPACES: dict[str, dict] = {}  # in-memory, S3 sync in production

def get_or_create_workspace(user_id: str) -> dict:
    """Get or create a user workspace with S3 bucket mapping."""
    if user_id not in WORKSPACES:
        WORKSPACES[user_id] = {
            "user_id": user_id,
            "created": datetime.utcnow().isoformat(),
            "bucket": f"rostr-workspace-{user_id}",
            "threads": {},
            "memory": [],
        }
        logger.info(f"Created workspace for user: {user_id}")
    return WORKSPACES[user_id]

# ── Assistant-ui compatible API models ──────────────────────────────────────

class ChatMessage(BaseModel):
    role: str  # "user" | "assistant" | "system"
    content: str

class ChatCompletionRequest(BaseModel):
    model: str = Field(default="rostr-agent", description="Model identifier")
    messages: list[ChatMessage] = Field(..., description="Conversation messages")
    stream: bool = Field(default=False, description="Enable streaming")
    max_tokens: int = Field(default=2048, ge=1, le=8192)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    user: Optional[str] = Field(default=None, description="User/workspace ID")
    # ROSTR-specific fields (passed as extra body params)
    provider: str = Field(default="openai", description="LLM provider: openai | anthropic | bedrock")

class ChatCompletionChoice(BaseModel):
    index: int = 0
    message: ChatMessage
    finish_reason: str = "stop"

class ChatCompletionUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[ChatCompletionChoice]
    usage: ChatCompletionUsage = ChatCompletionUsage()
    # ROSTR metadata
    rostr_intent: Optional[dict] = None
    rostr_phase: Optional[str] = None

# ── FastAPI App ──────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("ROSTR Backend starting — PAL/NPAO/Hub ready")
    yield
    logger.info("ROSTR Backend stopping")

app = FastAPI(
    title="ROSTR Agent API",
    version="1.0.1",
    description="ROSTR/PAL-powered cloud agent backend with AWS Agent Core",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ═══════════════════════════════════════════════════════════════════════════
# Health & Info
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/health")
@app.get("/v1/health")
async def health():
    return {
        "status": "ok",
        "service": "rostr-agent",
        "version": "1.0.1",
        "pal": "ready",
        "npao": "ready",
        "hub": "ready",
    }

@app.get("/v1/models")
async def list_models():
    """OpenAI-compatible model list — assistant-ui uses this to verify the endpoint."""
    return {
        "object": "list",
        "data": [
            {
                "id": "rostr-agent",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "rostr",
            },
            {
                "id": "rostr-agent-fast",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "rostr",
            },
        ]
    }

# ═══════════════════════════════════════════════════════════════════════════
# OpenAI-compatible Chat Completions (assistant-ui primary endpoint)
# ═══════════════════════════════════════════════════════════════════════════

def _get_api_key(request: Request) -> str:
    """Extract BYOK API key from Authorization header or body."""
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:]
    return ""

@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    """
    OpenAI-compatible chat completions endpoint.
    
    assistant-ui can use this as a "Custom API" runtime with:
      - Base URL: https://<your-domain>/v1
      - API Key: user's own BYOK key (Anthropic, OpenAI, etc.)
    
    ROSTR pipeline runs transparently:
      1. PAL compiles the message
      2. NPAO classifies phase
      3. LLM called with enhanced prompt (BYOK)
      4. Response returned with ROSTR metadata
    """
    t0 = time.time()
    
    # Parse body
    body = await request.json()
    req = ChatCompletionRequest(**body)
    api_key = _get_api_key(request) or body.get("api_key", os.environ.get("OPENAI_API_KEY", ""))
    user_id = req.user or f"anon-{uuid.uuid4().hex[:8]}"
    
    # ── 1. Get or create workspace ──────────────────────────────────────────
    workspace = get_or_create_workspace(user_id)
    
    # ── 2. Extract the last user message ────────────────────────────────────
    user_message = ""
    for msg in reversed(req.messages):
        if msg.role == "user":
            user_message = msg.content
            break
    
    if not user_message:
        raise HTTPException(status_code=400, detail="No user message found")
    
    # ── 3. ROSTR Pipeline: PAL → NPAO ──────────────────────────────────────
    manifest = None
    enhanced_prompt = user_message
    intent_data = {}
    phase_name = "ops"
    
    try:
        manifest = pal_compiler.compile(user_message)
        enhanced_prompt = manifest.intent.primary_goal
        intent_data = {
            "primary_goal": manifest.intent.primary_goal,
            "domain": manifest.intent.domain,
            "subject": manifest.intent.subject,
            "constraints": list(manifest.intent.constraints) if manifest.intent.constraints else [],
            "urgency": manifest.intent.urgency,
        } if hasattr(manifest, "intent") else {}
        
        # NPAO phase classification
        phase = npao.classify_phase(user_message)
        if hasattr(phase, "name"):
            phase_name = phase.name.lower()
        elif isinstance(phase, PhaseType):
            phase_name = phase.name.lower()
        else:
            phase_name = str(phase).lower()
    except Exception as e:
        logger.warning(f"PAL/NPAO pipeline skipped: {e}")
    
    # ── 4. Build conversation with enhanced prompt ──────────────────────────
    system_prompt = {
        "role": "system",
        "content": (
            "You are ROSTR Agent — an AI assistant powered by the ROSTR framework "
            "(Runtime, Orchestration, State, Tools, Reference). "
            f"Phase: {phase_name}. "
            "Be specific, actionable, and concise."
        )
    }
    
    # Rebuild messages: keep history, replace last user message with enhanced version
    enhanced_messages = [system_prompt]
    for i, msg in enumerate(req.messages):
        if msg.role == "user" and i == len(req.messages) - 1:
            enhanced_messages.append({"role": "user", "content": enhanced_prompt})
        else:
            enhanced_messages.append({"role": msg.role, "content": msg.content})
    
    # ── 5. LLM Call (BYOK — user's own API key) ────────────────────────────
    provider = body.get("provider", "openai").lower()
    
    try:
        if provider == "openai":
            reply = await _call_openai(api_key, req.model, enhanced_messages, req.max_tokens, req.temperature)
        elif provider == "anthropic":
            reply = await _call_anthropic(api_key, req.model, enhanced_messages, req.max_tokens)
        elif provider in ("bedrock", "aws", "agentcore", "harness"):
            reply = await _call_harness(req.model, req.messages, user_id)
        else:
            reply = await _call_openai(api_key, req.model, enhanced_messages, req.max_tokens, req.temperature)
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        raise HTTPException(status_code=502, detail=f"Provider error: {str(e)}")
    
    # ── 6. Persist to workspace memory ──────────────────────────────────────
    workspace["memory"].append({
        "role": "user", "content": user_message, "enhanced": enhanced_prompt, "ts": time.time()
    })
    workspace["memory"].append({
        "role": "assistant", "content": reply, "ts": time.time()
    })
    workspace["memory"] = workspace["memory"][-100:]  # keep last 100 turns
    
    # ── 7. Build response ────────────────────────────────────────────────────
    response_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
    
    return ChatCompletionResponse(
        id=response_id,
        created=int(t0),
        model=req.model,
        choices=[
            ChatCompletionChoice(
                index=0,
                message=ChatMessage(role="assistant", content=reply),
                finish_reason="stop",
            )
        ],
        usage=ChatCompletionUsage(
            prompt_tokens=len(str(enhanced_messages)) // 4,
            completion_tokens=len(reply) // 4,
            total_tokens=(len(str(enhanced_messages)) + len(reply)) // 4,
        ),
        rostr_intent=intent_data,
        rostr_phase=phase_name,
    )

# ═══════════════════════════════════════════════════════════════════════════
# ROSTR-specific endpoints
# ═══════════════════════════════════════════════════════════════════════════

class PALEnhanceRequest(BaseModel):
    prompt: str

@app.post("/api/rostr/pal-enhance")
async def pal_enhance(req: PALEnhanceRequest):
    """Run a prompt through PAL and return the enhanced version."""
    try:
        manifest = pal_compiler.compile(req.prompt)
        return {
            "original": req.prompt,
            "enhanced": manifest.intent.primary_goal,
            "intent": {
                "primary_goal": manifest.intent.primary_goal,
                "domain": manifest.intent.domain,
                "subject": manifest.intent.subject,
            },
            "phase": npao.classify_phase(req.prompt).name.lower(),
            "success": True,
        }
    except Exception as e:
        return {"error": str(e), "success": False}

@app.get("/api/workspace/{user_id}")
async def get_workspace(user_id: str):
    """Get workspace info and memory summary."""
    ws = get_or_create_workspace(user_id)
    return {
        "user_id": ws["user_id"],
        "bucket": ws["bucket"],
        "thread_count": len(ws["threads"]),
        "memory_turns": len(ws["memory"]),
        "created": ws["created"],
    }

@app.get("/api/skills")
async def get_skills():
    """Return the Artispreneur agent-skill manifest (master + 6 sub-agents)."""
    return {
        "object": "list",
        "data": list_agent_skills(),
    }

# ═══════════════════════════════════════════════════════════════════════════
# LLM Provider Calls (BYOK — user keys used per-request, never stored)
# ═══════════════════════════════════════════════════════════════════════════

async def _call_openai(api_key: str, model: str, messages: list, max_tokens: int = 2048, temperature: float = 0.7) -> str:
    """Call OpenAI chat completions API."""
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model if model != "rostr-agent" else "gpt-4o",
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

async def _call_anthropic(api_key: str, model: str, messages: list, max_tokens: int = 2048) -> str:
    """Call Anthropic Messages API."""
    system = next((m["content"] for m in messages if m["role"] == "system"), "")
    chat_messages = [m for m in messages if m["role"] != "system"]
    
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json={
                "model": model if model != "rostr-agent" else "claude-sonnet-4-5-20250929",
                "system": system,
                "messages": chat_messages,
                "max_tokens": max_tokens,
            },
        )
        resp.raise_for_status()
        return resp.json()["content"][0]["text"]

def _invoke_harness_blocking(model: str, messages: list, user_id: str) -> str:
    """Blocking harness invocation — run off the event loop via asyncio.to_thread."""
    resp = harness.invoke(model, messages, user_id=user_id)
    text = ""
    for event in resp["stream"]:
        if "contentBlockDelta" in event:
            text += event["contentBlockDelta"]["delta"].get("text", "")
        elif "messageStop" in event:
            break
    return text.strip()


async def _call_harness(model: str, req_messages: list, user_id: str) -> str:
    """
    AWS Bedrock AgentCore invocation via invoke_harness.

    Routes to the deployed ROSTR harness, which runs its own PAL/NPAO/RAG-DAL/Hub
    pipeline — so we pass the raw conversation (user/assistant turns) and let the
    harness compile intent. `invoke_harness` is synchronous, so it runs in a worker
    thread to keep the FastAPI event loop responsive.
    """
    agentcore_messages = []
    for m in req_messages:
        role = getattr(m, "role", None)
        content = getattr(m, "content", "")
        if role == "system":
            continue  # harness supplies its own system prompt
        agentcore_messages.append({"role": role, "content": [{"text": content}]})

    if not agentcore_messages:
        agentcore_messages = [{"role": "user", "content": [{"text": "Hello"}]}]

    reply = await asyncio.to_thread(_invoke_harness_blocking, model, agentcore_messages, user_id)
    return reply or "(no response from ROSTR harness)"

# ═══════════════════════════════════════════════════════════════════════════
# Entrypoint
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8080"))
    logger.info(f"ROSTR Cloud Agent Backend starting on port {port}")
    uvicorn.run("backend:app", host="0.0.0.0", port=port)
