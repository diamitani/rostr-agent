"""
ROSTR PAL Agent Core — Pydantic Deep Runtime Adapter
===================================================
Compile intent through System One (Jev / local / adapter) BEFORE spawning a
deep agent. The deep agent is System Two: it generates. It does not classify.

Generation defaults to Vercel AI Gateway (`--via-gateway`) using the Jev
route for the compiled phase. pydantic-deep remains available when installed.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from system_one.pal import compile_pal  # noqa: E402
from system_one.gateway import (  # noqa: E402
    GatewayError,
    complete_for_route,
    model_for,
    resolve_gateway,
    route_from_phase,
)

try:
    from pydantic_deep import create_deep_agent, create_default_deps
    from pydantic_deep.backends import StateBackend

    PYDANTIC_DEEP_AVAILABLE = True
except ImportError:
    PYDANTIC_DEEP_AVAILABLE = False


class PALCompiledIntent(BaseModel):
    phase: str = Field(description="Active lifecycle phase")
    domain: str = Field(description="Execution domain")
    npao_category: str = Field(description="Necessity | Anxiety | Priority | Opportunity")
    priority_score: float = Field(description="NPAO 4D priority 0-10")
    dispatched_subagents: list[str]
    requires_approval: bool = False
    escalate_to_llm: bool = False
    backend: str = "local"
    vertical_slice_outcome: str = ""
    route: str = "frontier"
    model: str = ""


def _intent_from_compile(task_prompt: str) -> PALCompiledIntent:
    compiled = compile_pal(task_prompt)
    route = route_from_phase(compiled.phase)
    resolved = resolve_gateway()
    return PALCompiledIntent(
        phase=compiled.phase,
        domain=compiled.domain,
        npao_category=compiled.npao_category,
        priority_score=compiled.priority_score,
        dispatched_subagents=compiled.selected_subagents,
        requires_approval=bool(compiled.approval_required),
        escalate_to_llm=compiled.escalate_to_llm,
        backend=compiled.backend,
        vertical_slice_outcome="",
        route=route,
        model=model_for(route, resolved["models"]),
    )


def _system_instruction(intent: PALCompiledIntent) -> str:
    return (
        "You are the ROSTR Governed CTO Agent Core. "
        "A System One model already classified this task. Do not re-litigate phase, "
        f"domain, or NPAO. Execute as {intent.phase} / {intent.domain} with sub-agents "
        f"{', '.join(intent.dispatched_subagents)}. Priority {intent.priority_score}."
    )


def generate_via_gateway(task_prompt: str, intent: PALCompiledIntent) -> Dict[str, Any]:
    resolved = resolve_gateway()
    try:
        text, served = complete_for_route(
            intent.route,
            [
                {"role": "system", "content": _system_instruction(intent)},
                {"role": "user", "content": task_prompt},
            ],
        )
    except GatewayError as exc:
        return {
            "status": "gateway_error",
            "error": str(exc),
            "provider": resolved["provider"],
            "auth": resolved["auth"],
            "pal": intent.model_dump(),
        }
    intent.vertical_slice_outcome = text
    intent.model = served
    return {
        "status": "success",
        "output": text,
        "model": served,
        "provider": resolved["provider"],
        "auth": resolved["auth"],
        "route": intent.route,
        "pal": intent.model_dump(),
    }


async def run_rostr_deep_agent(
    task_prompt: str,
    model: Optional[str] = None,
    via_gateway: bool = False,
) -> Dict[str, Any]:
    intent = _intent_from_compile(task_prompt)
    if model:
        intent.model = model

    if intent.requires_approval:
        return {
            "status": "blocked",
            "reason": f"Approval required: {intent.requires_approval}",
            "pal": intent.model_dump(),
        }

    use_gateway = via_gateway or os.getenv("ROSTR_GENERATE_VIA", "") == "gateway" or not PYDANTIC_DEEP_AVAILABLE
    if use_gateway:
        if not resolve_gateway()["ready"]:
            return {
                "status": "compiled",
                "message": "System One compiled the task. Set AI_GATEWAY_API_KEY (or deploy on Vercel) to generate.",
                "pal": intent.model_dump(),
                "prompt": task_prompt,
            }
        return generate_via_gateway(task_prompt, intent)

    backend = StateBackend()
    deps = create_default_deps(backend)
    agent = create_deep_agent()
    result = await agent.run(f"{_system_instruction(intent)}\n\nTask: {task_prompt}", deps=deps)
    intent.vertical_slice_outcome = str(result.output)
    return {
        "status": "success",
        "output": str(result.output),
        "model": intent.model,
        "pal": intent.model_dump(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="ROSTR System One + Vercel AI Gateway CLI")
    parser.add_argument("prompt", nargs="?", default="Compile PAL architecture blueprint")
    parser.add_argument("--model", default=None, help="Override the Jev-picked Vercel catalog slug")
    parser.add_argument("--compile-only", action="store_true")
    parser.add_argument(
        "--via-gateway",
        action="store_true",
        help="Generate through Vercel AI Gateway instead of pydantic-deep",
    )
    args = parser.parse_args()

    if args.compile_only:
        intent = _intent_from_compile(args.prompt)
        print(json.dumps({**compile_pal(args.prompt).to_dict(), "route": intent.route, "model": intent.model}, indent=2, default=str))
        return

    print(f"ROSTR System One compile → Vercel AI Gateway")
    print(f"Task: {args.prompt}\n")
    res = asyncio.run(run_rostr_deep_agent(args.prompt, model=args.model, via_gateway=args.via_gateway))
    print(json.dumps(res, indent=2, default=str))


if __name__ == "__main__":
    main()
