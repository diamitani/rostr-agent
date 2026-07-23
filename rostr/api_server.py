#!/usr/bin/env python3
"""ROSTR API Server — FastAPI backend for desktop + web

BYOK model: every /api/chat request includes the user's own API key in the
header (X-Api-Key) or body. Keys are used per-request and never stored.
"""
import asyncio, logging, os
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import httpx
import uvicorn

from rostr.pal.compiler import PALCompiler
from rostr.npao import NPAORouter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ROSTR API", version="1.0.0", docs_url="/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://www.rostragent.com", "https://rostragent.com", "http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pal_compiler = PALCompiler()
npao_router = NPAORouter()


# ── Models ────────────────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    provider: str = "openai"          # "openai" | "anthropic"
    api_key: str                       # BYOK — never stored
    model: Optional[str] = None
    history: List[ChatMessage] = []
    workspace_id: str = "default"

class ChatResponse(BaseModel):
    message: str
    enhanced_prompt: str               # what PAL turned your message into
    intent: str
    domain: str
    model_used: str
    workspace_id: str
    success: bool
    timestamp: str

class PALRequest(BaseModel):
    prompt: str

class PALResponse(BaseModel):
    original: str
    enhanced: str
    intent: str
    domain: str
    urgency: str


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0", "service": "rostr-api"}


# ── PAL enhance (standalone) ──────────────────────────────────────────────────

@app.post("/api/pal/enhance", response_model=PALResponse)
async def pal_enhance(request: PALRequest):
    """Run prompt through PAL compiler — returns structured manifest."""
    try:
        manifest = pal_compiler.compile(request.prompt)
        return PALResponse(
            original=request.prompt,
            enhanced=manifest.enhanced_prompt,
            intent=manifest.intent.value,
            domain=manifest.domain.value,
            urgency=manifest.urgency.value,
        )
    except Exception as e:
        logger.error(f"PAL enhance failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Main chat endpoint ────────────────────────────────────────────────────────

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Full ROSTR pipeline:
      1. PAL compiles the message into a structured manifest
      2. NPAO scores and selects the right model
      3. Calls OpenAI or Anthropic with the enhanced prompt (BYOK)
      4. Returns the response + what ROSTR did behind the scenes
    """
    logger.info(f"Chat [{request.provider}]: {request.message[:60]}...")

    # Step 1 — PAL: compile raw message into structured manifest
    try:
        manifest = pal_compiler.compile(request.message)
        enhanced = manifest.enhanced_prompt
    except Exception:
        enhanced = request.message
        manifest = None

    # Step 2 — NPAO: pick model (use manifest hints if available)
    model = request.model
    if not model:
        if request.provider == "openai":
            model = "gpt-4o"
        else:
            model = "claude-sonnet-4-20250514"

    # Step 3 — build messages for the LLM
    system = (
        "You are ROSTR Agent — a production AI assistant. "
        "You help with research, outreach, analysis, and automation. "
        "Be specific, actionable, and concise."
    )
    messages = [{"role": m.role, "content": m.content} for m in request.history]
    messages.append({"role": "user", "content": enhanced})

    # Step 4 — call the provider
    try:
        if request.provider == "openai":
            reply = await _call_openai(request.api_key, model, system, messages)
        elif request.provider == "anthropic":
            reply = await _call_anthropic(request.api_key, model, system, messages)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown provider: {request.provider}")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"Provider error: {e.response.text[:200]}")

    return ChatResponse(
        message=reply,
        enhanced_prompt=enhanced,
        intent=manifest.intent.value if manifest else "general",
        domain=manifest.domain.value if manifest else "ops",
        model_used=model,
        workspace_id=request.workspace_id,
        success=True,
        timestamp=datetime.utcnow().isoformat() + "Z",
    )


# ── Provider helpers ──────────────────────────────────────────────────────────

async def _call_openai(api_key: str, model: str, system: str, messages: list) -> str:
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": model, "messages": [{"role": "system", "content": system}] + messages, "max_tokens": 1024},
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


async def _call_anthropic(api_key: str, model: str, system: str, messages: list) -> str:
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "Content-Type": "application/json"},
            json={"model": model, "system": system, "messages": messages, "max_tokens": 1024},
        )
        resp.raise_for_status()
        return resp.json()["content"][0]["text"]


# ── Misc endpoints ────────────────────────────────────────────────────────────

@app.get("/api/providers")
async def list_providers():
    return {"providers": ["openai", "anthropic", "gemini", "openrouter", "ollama", "bedrock", "azure", "lm_studio", "nous"]}


@app.get("/api/skills")
async def list_skills():
    return {"skills": [
        {"id": "pal", "name": "PAL Compiler", "category": "core"},
        {"id": "npao", "name": "NPAO Router", "category": "core"},
        {"id": "jtbd", "name": "JTBD Builder", "category": "gtm"},
        {"id": "prd", "name": "PRD Builder", "category": "product"},
        {"id": "diagram", "name": "Diagram Builder", "category": "dev"},
        {"id": "instruction-architect", "name": "Instruction Architect", "category": "dev"},
    ]}


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
