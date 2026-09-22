"""Unified System One client.

Resolution order:
1. TYPESAFE_API_KEY          → real Jev via typesafe_sdk
2. AI_GATEWAY_API_KEY        → Vercel AI Gateway typesafe-ai/jev
3. OPENROUTER_API_KEY        → OpenRouter ~typesafe/jev-latest
4. system-one-adapter + LLM  → comparison only (not production PAL)
5. local engine              → typed offline fallback
"""

from __future__ import annotations

import os
from typing import Any, Optional

from .engine import SystemOneResponse, evaluate_local, pal_questions


def _env(*names: str) -> Optional[str]:
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return None


def evaluate(state: str) -> SystemOneResponse:
    return SystemOneClient().evaluate(state)


class SystemOneClient:
    def __init__(self, prefer: str = "auto"):
        self.prefer = prefer

    def evaluate(self, state: str) -> SystemOneResponse:
        if self.prefer == "local":
            return evaluate_local(state)

        typesafe_key = _env("TYPESAFE_API_KEY")
        gateway_key = _env("AI_GATEWAY_API_KEY")
        openrouter_key = _env("OPENROUTER_API_KEY")

        if typesafe_key or gateway_key or openrouter_key:
            live = self._call_typesafe(state, typesafe_key, gateway_key, openrouter_key)
            if live is not None:
                return live

        if self.prefer == "adapter" or _env("ROSTR_SYSTEM_ONE_ADAPTER") == "1":
            adapted = self._call_adapter(state)
            if adapted is not None:
                return adapted

        return evaluate_local(state)

    def _call_typesafe(
        self,
        state: str,
        typesafe_key: Optional[str],
        gateway_key: Optional[str],
        openrouter_key: Optional[str],
    ) -> Optional[SystemOneResponse]:
        try:
            from typesafe_sdk import Choice, Noul, TypeSafeClient
        except ImportError:
            return None

        kwargs: dict[str, Any] = {}
        backend = "jev"
        model = os.getenv("TYPESAFE_DEFAULT_MODEL", "jev-latest")
        if typesafe_key:
            kwargs["api_key"] = typesafe_key
        elif gateway_key:
            kwargs.update(
                {
                    "api_key": gateway_key,
                    "base_url": "https://ai-gateway.vercel.sh/typesafe",
                    "model": "typesafe-ai/jev",
                }
            )
            backend = "gateway"
            model = "typesafe-ai/jev"
        elif openrouter_key:
            kwargs.update(
                {
                    "api_key": openrouter_key,
                    "base_url": "https://openrouter.ai/api",
                    "model": "~typesafe/jev-latest",
                }
            )
            backend = "openrouter"
            model = "~typesafe/jev-latest"

        payload = pal_questions(state)
        questions = {
            "phase": Choice(
                instructions=payload["questions"]["phase"]["instructions"],
                criteria=payload["questions"]["phase"]["criteria"],
            ),
            "npao": Choice(
                instructions=payload["questions"]["npao"]["instructions"],
                criteria=payload["questions"]["npao"]["criteria"],
            ),
            "requires_approval": Noul(
                instructions=payload["questions"]["requires_approval"]["instructions"]
            ),
            "production_risk": Noul(
                instructions=payload["questions"]["production_risk"]["instructions"]
            ),
        }

        try:
            with TypeSafeClient(**kwargs) as client:
                result = client.system_one(payload["state"], questions)
        except Exception:
            return None

        local = evaluate_local(state, backend=backend, model=model)
        answers = local.answers
        if hasattr(result, "choices"):
            if "phase" in result.choices:
                answers["phase"]["choice"] = result.choices["phase"].choice
                answers["phase"]["probabilities"] = getattr(
                    result.choices["phase"], "probabilities", answers["phase"]["probabilities"]
                )
                answers["phase"]["confidence"] = getattr(
                    result.choices["phase"], "confidence", answers["phase"]["confidence"]
                )
            if "npao" in result.choices:
                answers["npao"]["choice"] = result.choices["npao"].choice
        if hasattr(result, "nouls"):
            if "requires_approval" in result.nouls:
                n = float(result.nouls["requires_approval"].noul)
                answers["requires_approval"] = {"noul": n, "label": "yes" if n >= 0.5 else "no"}
            if "production_risk" in result.nouls:
                n = float(result.nouls["production_risk"].noul)
                answers["production_risk"] = {"noul": n, "label": "yes" if n >= 0.5 else "no"}
        local.answers = answers
        local.backend = backend
        local.model = model
        return local

    def _call_adapter(self, state: str) -> Optional[SystemOneResponse]:
        """LLM comparison backend. Do not use as production PAL."""
        try:
            from system_one_adapter import Choice, Noul, SystemOneAdapterClient
        except ImportError:
            return None

        provider = os.getenv("ROSTR_ADAPTER_PROVIDER", "openai")
        model = os.getenv("ROSTR_ADAPTER_MODEL", "gpt-4o-mini")
        payload = pal_questions(state)
        try:
            with SystemOneAdapterClient(
                structured_outputs=True,
                llm_answer_mode="probabilities",
                normalize_probabilities=True,
            ) as client:
                result = client.system_one(
                    payload["state"],
                    {
                        "phase": Choice(
                            instructions=payload["questions"]["phase"]["instructions"],
                            criteria=payload["questions"]["phase"]["criteria"],
                        ),
                        "npao": Choice(
                            instructions=payload["questions"]["npao"]["instructions"],
                            criteria=payload["questions"]["npao"]["criteria"],
                        ),
                        "requires_approval": Noul(
                            instructions=payload["questions"]["requires_approval"]["instructions"]
                        ),
                    },
                    provider=provider,
                    model=model,
                )
        except Exception:
            return None

        local = evaluate_local(state, backend="adapter", model=f"{provider}/{model}")
        if hasattr(result, "choices") and "phase" in result.choices:
            local.answers["phase"]["choice"] = result.choices["phase"].choice
        return local
