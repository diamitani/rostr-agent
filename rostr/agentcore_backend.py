"""
ROSTR AgentCore Backend
=======================

Integrates ROSTR's PAL (Prompt Abstraction Layer) with Amazon Bedrock AgentCore.

Deploy:
    agentcore deploy --entrypoint rostr/agentcore_backend.py

Invoke (after deploy):
    POST <endpoint>/invoke
    {
        "prompt": "Build a REST API with auth",
        "provider": "anthropic",          # optional, default: anthropic
        "api_key": "sk-...",              # BYOK — never stored
        "model": "claude-sonnet-4-6",     # optional, overrides PAL routing
        "session_id": "user-abc-123"      # optional, for memory continuity
    }

Health check:
    POST <endpoint>/invoke  {"action": "health"}

SDK: amazon-bedrock-agentcore
    pip install amazon-bedrock-agentcore

NOTE: If `amazon_bedrock_agentcore` is not yet installed, this module falls
back to a boto3-based shim that exposes the same decorator surface and runs
a minimal HTTP server for local development.  Install the real SDK for full
managed memory, streaming, and model-switching support.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from typing import Any, Optional

import httpx

# ── PAL / ROSTR imports ────────────────────────────────────────────────────────
# When deployed via `agentcore deploy`, the project root is on sys.path.
from rostr.pal.compiler import AgentManifest, PALCompiler

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)

# ── AgentCore SDK import with boto3 fallback ───────────────────────────────────
try:
    from amazon_bedrock_agentcore import AgentCore  # type: ignore[import]

    _SDK_AVAILABLE = True
    logger.info("amazon-bedrock-agentcore SDK loaded")
except ImportError:
    _SDK_AVAILABLE = False
    logger.warning(
        "amazon-bedrock-agentcore not installed — using boto3 shim. "
        "Run: pip install amazon-bedrock-agentcore"
    )

    # ── boto3 shim ─────────────────────────────────────────────────────────────
    class _ShimSession:
        """Minimal session with in-process memory (dev shim for ROSTR Hub)."""

        _store: dict[str, list[dict]] = {}

        def __init__(self, session_id: str = "default") -> None:
            self.session_id = session_id
            _ShimSession._store.setdefault(session_id, [])

        def get_memory(self) -> list[dict]:
            return list(_ShimSession._store[self.session_id])

        def append_memory(self, entry: dict) -> None:
            _ShimSession._store[self.session_id].append(entry)
            # Cap at 50 turns to bound memory usage
            if len(_ShimSession._store[self.session_id]) > 50:
                _ShimSession._store[self.session_id] = (
                    _ShimSession._store[self.session_id][-50:]
                )

    class AgentCore:  # type: ignore[no-redef]
        """boto3-compatible AgentCore shim."""

        def __init__(self) -> None:
            self._handler = None

        def entrypoint(self, fn):
            """Register the last-decorated function as the handler."""
            self._handler = fn
            return fn

        def run(self, host: str = "0.0.0.0", port: int = 8080) -> None:
            """Serve locally using stdlib http.server (dev only)."""
            import http.server

            handler_fn = self._handler
            logger.info(f"[shim] Listening on {host}:{port}")

            class _Handler(http.server.BaseHTTPRequestHandler):
                def do_GET(self):
                    if self.path == "/health":
                        self._respond({"status": "ok", "mode": "shim"})

                def do_POST(self):
                    length = int(self.headers.get("Content-Length", 0))
                    body = json.loads(self.rfile.read(length) or b"{}")
                    sid = body.get("session_id", "default")
                    session = _ShimSession(sid)
                    result = handler_fn(body, session)
                    self._respond(result)

                def _respond(self, data: dict) -> None:
                    payload = json.dumps(data).encode()
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(payload)))
                    self.end_headers()
                    self.wfile.write(payload)

                def log_message(self, *args):
                    pass  # suppress default per-request logs

            http.server.HTTPServer((host, port), _Handler).serve_forever()


# ── Global compiler instance (warm, reused across requests) ───────────────────
_pal_compiler = PALCompiler()

# ── System prompt injected into every LLM call ────────────────────────────────
_SYSTEM_PROMPT = (
    "You are ROSTR Agent — a production AI assistant powered by the PAL framework. "
    "You help with research, outreach, code, analysis, and automation. "
    "Be specific, actionable, and concise. Lead with the answer, then explain."
)

# ── AgentCore app instance ─────────────────────────────────────────────────────
app = AgentCore()


# ═══════════════════════════════════════════════════════════════════════════════
# Main entrypoint — registered with @app.entrypoint
# ═══════════════════════════════════════════════════════════════════════════════

@app.entrypoint
def invoke(payload: dict[str, Any], session: Any) -> dict[str, Any]:
    """
    Unified ROSTR AgentCore entrypoint.

    AgentCore calls this function for every incoming invocation.  The session
    object provides built-in memory continuity, which maps to ROSTR's Hub
    concept — cross-turn context without managing storage explicitly.

    Request payload fields:
        action      str  — "health" returns a health check immediately
        prompt      str  — raw user message (required for normal invocations)
        provider    str  — "anthropic" | "openai"  (default: "anthropic")
        api_key     str  — BYOK key, per-request, never stored
        model       str  — optional model override (overrides PAL routing)
        session_id  str  — optional; AgentCore routes memory by session

    Response fields:
        reply           str   — LLM response text
        enhanced_prompt str   — PAL-compiled version of the raw prompt
        intent          dict  — full PAL Intent object
        manifest_id     str   — PAL task_id for distributed tracing
        domain          str   — detected domain (code, design, sales, …)
        urgency         str   — detected urgency (low, normal, high, critical)
        model_used      str   — actual model that served the request
        provider        str   — provider used
        latency_ms      int   — wall-clock ms for this invocation
        memory_turns    int   — number of turns in session memory
        success         bool
    """
    t0 = time.monotonic()

    # ── Health check short-circuit ─────────────────────────────────────────────
    if payload.get("action") == "health" or payload.get("prompt") == "__health__":
        return {
            "status": "ok",
            "service": "rostr-agentcore",
            "sdk": "amazon-bedrock-agentcore" if _SDK_AVAILABLE else "boto3-shim",
            "pal": "ready",
            "version": "1.0.0",
            "latency_ms": int((time.monotonic() - t0) * 1000),
        }

    # ── 1. Parse request ───────────────────────────────────────────────────────
    raw_prompt: str = payload.get("prompt", "").strip()
    provider: str = payload.get("provider", "anthropic").lower()
    api_key: str = payload.get("api_key", "")
    model_override: Optional[str] = payload.get("model")

    if not raw_prompt:
        return _error_response("prompt is required", t0)
    if not api_key:
        return _error_response("api_key is required (BYOK)", t0)

    # ── 2. PAL compilation — ROSTR's Prompt Abstraction Layer ─────────────────
    # Every message is deterministically compiled through the 5-stage pipeline:
    # IntentExtractor → ContextResolver → SemanticEnhancer → ModelRouter →
    # ManifestCompiler.  No LLM required — this is purely heuristic.
    try:
        manifest: AgentManifest = _pal_compiler.compile(raw_prompt)
        enhanced_prompt: str = manifest.intent.primary_goal
        domain: str = manifest.intent.domain
        urgency: str = manifest.intent.urgency
        manifest_id: str = manifest.task_id
    except Exception as exc:
        logger.warning(f"PAL compilation failed, using raw prompt: {exc}")
        manifest = None  # type: ignore[assignment]
        enhanced_prompt = raw_prompt
        domain = "code"
        urgency = "normal"
        manifest_id = "pal-fallback"

    # ── 3. Retrieve AgentCore session memory (ROSTR Hub equivalent) ────────────
    # AgentCore's managed memory persists conversation history across turns.
    # This is the AgentCore counterpart to ROSTR Hub's cross-session memory.
    try:
        memory: list[dict] = session.get_memory() if hasattr(session, "get_memory") else []
    except Exception:
        memory = []

    # Build LLM message history from the last 10 turns (context window mgmt)
    history: list[dict[str, str]] = [
        {"role": t["role"], "content": t["content"]}
        for t in memory[-10:]
        if isinstance(t, dict) and "role" in t and "content" in t
    ]

    # ── 4. Model selection: PAL routing → BYOK override → provider default ─────
    if model_override:
        model = model_override
    elif manifest and manifest.model_policy:
        routed = manifest.model_policy.model
        # Only use PAL's routed model if it matches the requested provider
        if provider == "anthropic" and routed.startswith("claude"):
            model = routed
        elif provider == "openai" and (routed.startswith("gpt") or routed.startswith("o")):
            model = routed
        else:
            model = _default_model(provider)
    else:
        model = _default_model(provider)

    # ── 5. Build messages: system + history + PAL-enhanced prompt ─────────────
    messages = history + [{"role": "user", "content": enhanced_prompt}]

    # ── 6. BYOK LLM call ───────────────────────────────────────────────────────
    try:
        # Handle both running-loop and no-loop contexts
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're inside an existing event loop (e.g. uvicorn) — use a
                # thread-based approach to avoid nested loop issues
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(
                        asyncio.run,
                        _call_provider(provider, api_key, model, _SYSTEM_PROMPT, messages),
                    )
                    reply = future.result(timeout=90)
            else:
                reply = loop.run_until_complete(
                    _call_provider(provider, api_key, model, _SYSTEM_PROMPT, messages)
                )
        except RuntimeError:
            reply = asyncio.run(
                _call_provider(provider, api_key, model, _SYSTEM_PROMPT, messages)
            )
    except Exception as exc:
        return _error_response(f"LLM call failed: {exc}", t0)

    # ── 7. Write turn to AgentCore memory ─────────────────────────────────────
    # Store raw prompt (not enhanced) so future turns have clean conversation
    # history from the user's perspective.
    try:
        if hasattr(session, "append_memory"):
            # Shim path
            session.append_memory({"role": "user", "content": raw_prompt})
            session.append_memory({"role": "assistant", "content": reply})
        elif hasattr(session, "memory"):
            # Real AgentCore SDK — memory attribute pattern
            session.memory.put([
                {"role": "user", "content": raw_prompt},
                {"role": "assistant", "content": reply},
            ])
        elif hasattr(session, "save"):
            # Real AgentCore SDK — save method pattern
            session.save(messages=[
                {"role": "user", "content": raw_prompt},
                {"role": "assistant", "content": reply},
            ])
    except Exception as exc:
        logger.warning(f"Memory write skipped (non-fatal): {exc}")

    latency_ms = int((time.monotonic() - t0) * 1000)
    logger.info(f"invoke ok — domain={domain} model={model} latency={latency_ms}ms")

    return {
        "reply": reply,
        "enhanced_prompt": enhanced_prompt,
        "intent": manifest.intent.model_dump() if manifest else {},
        "manifest_id": manifest_id,
        "domain": domain,
        "urgency": urgency,
        "model_used": model,
        "provider": provider,
        "latency_ms": latency_ms,
        "memory_turns": len(memory),
        "success": True,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Provider helpers (async httpx, BYOK)
# ═══════════════════════════════════════════════════════════════════════════════

async def _call_provider(
    provider: str,
    api_key: str,
    model: str,
    system: str,
    messages: list[dict[str, str]],
) -> str:
    """Dispatch to the right provider helper."""
    if provider == "anthropic":
        return await _call_anthropic(api_key, model, system, messages)
    if provider == "openai":
        return await _call_openai(api_key, model, system, messages)
    raise ValueError(f"Unsupported provider: {provider!r}. Use 'anthropic' or 'openai'.")


async def _call_anthropic(
    api_key: str,
    model: str,
    system: str,
    messages: list[dict[str, str]],
) -> str:
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "system": system,
                "messages": messages,
                "max_tokens": 2048,
            },
        )
        resp.raise_for_status()
        return resp.json()["content"][0]["text"]


async def _call_openai(
    api_key: str,
    model: str,
    system: str,
    messages: list[dict[str, str]],
) -> str:
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [{"role": "system", "content": system}] + messages,
                "max_tokens": 2048,
            },
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


# ═══════════════════════════════════════════════════════════════════════════════
# Utilities
# ═══════════════════════════════════════════════════════════════════════════════

def _default_model(provider: str) -> str:
    """Provider-specific default model."""
    return {"anthropic": "claude-sonnet-4-6", "openai": "gpt-4o"}.get(
        provider, "claude-sonnet-4-6"
    )


def _error_response(message: str, t0: float) -> dict[str, Any]:
    return {
        "reply": "",
        "enhanced_prompt": "",
        "intent": {},
        "manifest_id": "",
        "domain": "",
        "urgency": "",
        "model_used": "",
        "provider": "",
        "latency_ms": int((time.monotonic() - t0) * 1000),
        "memory_turns": 0,
        "success": False,
        "error": message,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Local dev entrypoint
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    logger.info(
        f"Starting ROSTR AgentCore "
        f"({'SDK' if _SDK_AVAILABLE else 'shim'}) on port {port}"
    )
    app.run(host="0.0.0.0", port=port)
