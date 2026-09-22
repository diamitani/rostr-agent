"""
ROSTR PAL Agent Core — Pydantic Deep Runtime Adapter
===================================================
Compile intent through System One (Jev / local / adapter) BEFORE spawning a
deep agent. The deep agent is System Two: it generates. It does not classify.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from system_one.pal import compile_pal  # noqa: E402

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


async def run_rostr_deep_agent(task_prompt: str, model: str = "claude-sonnet-4-6") -> Dict[str, Any]:
    compiled = compile_pal(task_prompt)
    intent = PALCompiledIntent(
        phase=compiled.phase,
        domain=compiled.domain,
        npao_category=compiled.npao_category,
        priority_score=compiled.priority_score,
        dispatched_subagents=compiled.selected_subagents,
        requires_approval=bool(compiled.approval_required),
        escalate_to_llm=compiled.escalate_to_llm,
        backend=compiled.backend,
        vertical_slice_outcome="",
    )

    if compiled.approval_required:
        return {
            "status": "blocked",
            "reason": f"Approval required: {compiled.approval_required}",
            "pal": intent.model_dump(),
        }

    if not PYDANTIC_DEEP_AVAILABLE:
        return {
            "status": "compiled",
            "message": "System One compiled the task. Install pydantic-deep to run System Two generation.",
            "pal": intent.model_dump(),
            "prompt": task_prompt,
        }

    backend = StateBackend()
    deps = create_default_deps(backend)
    agent = create_deep_agent()
    system_instruction = (
        "You are the ROSTR Governed CTO Agent Core. "
        "A System One model already classified this task. Do not re-litigate phase, "
        f"domain, or NPAO. Execute as {intent.phase} / {intent.domain} with sub-agents "
        f"{', '.join(intent.dispatched_subagents)}. Priority {intent.priority_score}."
    )
    result = await agent.run(f"{system_instruction}\n\nTask: {task_prompt}", deps=deps)
    intent.vertical_slice_outcome = str(result.output)
    return {"status": "success", "output": str(result.output), "model": model, "pal": intent.model_dump()}


def main() -> None:
    parser = argparse.ArgumentParser(description="ROSTR System One + Pydantic Deep CLI")
    parser.add_argument("prompt", nargs="?", default="Compile PAL architecture blueprint")
    parser.add_argument("--model", default="claude-sonnet-4-6")
    parser.add_argument("--compile-only", action="store_true")
    args = parser.parse_args()

    if args.compile_only:
        print(json.dumps(compile_pal(args.prompt).to_dict(), indent=2, default=str))
        return

    print(f"ROSTR System One compile → {args.model}")
    print(f"Task: {args.prompt}\n")
    res = asyncio.run(run_rostr_deep_agent(args.prompt, model=args.model))
    print(json.dumps(res, indent=2, default=str))


if __name__ == "__main__":
    main()
