"""System Two generation through Vercel AI Gateway.

Jev (client.py) decides. This module buys the model.

Auth order:
  1. AI_GATEWAY_API_KEY  → https://ai-gateway.vercel.sh/v1
  2. VERCEL_OIDC_TOKEN   → same door (automatic on a Vercel deploy)
  3. XAI_API_KEY         → https://api.x.ai/v1  (preview fallback)

When the door is Vercel and XAI_API_KEY is also set, Grok is sent as BYOK
so frontier turns do not spend gateway credits. Live catalog slugs use dots.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Optional

GATEWAY_BASE = "https://ai-gateway.vercel.sh/v1"
XAI_BASE = "https://api.x.ai/v1"

VERCEL_MODELS = {
    "frontier": "spacexai/grok-4.5",
    "subagent": "anthropic/claude-sonnet-4.6",
    "cheap": "google/gemini-3.1-flash-lite",
    "background": "google/gemini-2.5-flash-lite",
}

VERCEL_FALLBACKS = {
    "frontier": ["spacexai/grok-4.1-fast-reasoning", "anthropic/claude-sonnet-4.6"],
    "subagent": ["spacexai/grok-4.5", "anthropic/claude-haiku-4.5"],
    "cheap": ["spacexai/grok-4.1-fast-non-reasoning", "google/gemini-2.5-flash-lite"],
    "background": ["google/gemini-3.1-flash-lite", "spacexai/grok-4.1-fast-non-reasoning"],
}

XAI_MODELS = {k: "grok-4.5" for k in VERCEL_MODELS}

PHASE_TO_ROUTE = {
    "PreD": "cheap",
    "Design": "subagent",
    "Development": "frontier",
    "Deploy": "frontier",
    "Debugging": "frontier",
}


class GatewayError(RuntimeError):
    pass


def _trim(key: str) -> Optional[str]:
    v = os.environ.get(key, "").strip()
    return v or None


def vercel_secret() -> Optional[str]:
    return _trim("AI_GATEWAY_API_KEY") or _trim("VERCEL_OIDC_TOKEN")


def vercel_auth_kind() -> str:
    if _trim("AI_GATEWAY_API_KEY"):
        return "api-key"
    if _trim("VERCEL_OIDC_TOKEN"):
        return "oidc"
    return "none"


def resolve_gateway() -> dict[str, Any]:
    if vercel_secret():
        return {
            "provider": "vercel-ai-gateway",
            "auth": vercel_auth_kind(),
            "base_url": GATEWAY_BASE,
            "models": dict(VERCEL_MODELS),
            "ready": True,
            "key": vercel_secret(),
        }
    if _trim("XAI_API_KEY"):
        return {
            "provider": "xai-direct",
            "auth": "xai-key",
            "base_url": XAI_BASE,
            "models": dict(XAI_MODELS),
            "ready": True,
            "key": _trim("XAI_API_KEY"),
        }
    return {
        "provider": "none",
        "auth": "none",
        "base_url": GATEWAY_BASE,
        "models": dict(VERCEL_MODELS),
        "ready": False,
        "key": None,
    }


def model_for(route: str, models: Optional[dict] = None) -> str:
    table = models or VERCEL_MODELS
    return table.get(route) or table.get("frontier") or VERCEL_MODELS["frontier"]


def route_from_phase(phase: str) -> str:
    return PHASE_TO_ROUTE.get(phase, "frontier")


def fallbacks_for(route: str, provider: str) -> list[str]:
    if provider != "vercel-ai-gateway":
        return []
    return list(VERCEL_FALLBACKS.get(route) or [])


def _effective_model(model: str, resolved: dict) -> str:
    if resolved["provider"] != "xai-direct":
        return model
    name = model.split("/")[-1]
    return name if name.startswith("grok") else "grok-4.5"


def public_gateway_info() -> dict[str, Any]:
    resolved = resolve_gateway()
    on_vercel = bool(_trim("VERCEL") or _trim("VERCEL_OIDC_TOKEN"))
    if resolved["provider"] == "vercel-ai-gateway":
        note = (
            "Jev picks the route. Vercel OIDC opens the AI Gateway."
            if resolved["auth"] == "oidc"
            else "Jev picks the route. Vercel AI Gateway buys the model; Grok is BYOK when XAI_API_KEY is set."
        )
    elif resolved["provider"] == "xai-direct":
        note = "AI Gateway is not authed here (OIDC appears on publish). Generator is xAI grok-4.5 until then."
    else:
        note = "No generator configured. Decision API still runs."
    return {
        "provider": resolved["provider"],
        "auth": resolved["auth"],
        "baseUrl": resolved["base_url"],
        "ready": resolved["ready"],
        "models": resolved["models"],
        "fallbacks": VERCEL_FALLBACKS if resolved["provider"] == "vercel-ai-gateway" else {},
        "onVercel": on_vercel,
        "note": note,
    }


def _byok_block() -> Optional[dict]:
    xai = _trim("XAI_API_KEY")
    if not xai:
        return None
    return {"xai": [{"apiKey": xai}]}


def complete(
    model: str,
    messages: list[dict],
    max_tokens: int = 1024,
    temperature: float = 0.2,
    route: Optional[str] = None,
    response_format: Any = None,
) -> str:
    resolved = resolve_gateway()
    model = _effective_model(model, resolved)
    if not resolved["ready"] or not resolved["key"]:
        raise GatewayError(
            "No generator key. Set AI_GATEWAY_API_KEY, deploy on Vercel for OIDC, or XAI_API_KEY."
        )
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    if resolved["provider"] == "vercel-ai-gateway":
        if route:
            fallbacks = fallbacks_for(route, resolved["provider"])
            if fallbacks:
                payload["models"] = fallbacks
        byok = _byok_block()
        if byok:
            payload["providerOptions"] = {"gateway": {"byok": byok}}
    if response_format is not None:
        payload["response_format"] = response_format

    req = urllib.request.Request(
        resolved["base_url"].rstrip("/") + "/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {resolved['key']}",
            "Content-Type": "application/json",
            "http-referer": "https://rostr.diamitani.com",
            "x-title": "ROSTR agent",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise GatewayError(f"{resolved['provider']} HTTP {e.code}: {e.read().decode('utf-8')[:300]}")
    return data["choices"][0]["message"]["content"]


def complete_for_route(
    route: str,
    messages: list[dict],
    max_tokens: int = 1024,
    temperature: float = 0.2,
) -> tuple[str, str]:
    resolved = resolve_gateway()
    model = model_for(route, resolved["models"])
    text = complete(model, messages, max_tokens=max_tokens, temperature=temperature, route=route)
    return text, _effective_model(model, resolved)
