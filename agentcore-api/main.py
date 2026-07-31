"""
ROSTR AgentCore API — HTTP wrapper around rostr/agentcore_backend.py
Exposes:
  GET  /health
  POST /invoke          — sync, returns full JSON response
  POST /invoke/stream   — SSE stream, yields tokens then final JSON
"""
from __future__ import annotations

import json
import logging
import os
import sys
import time
from typing import Any, AsyncIterator

# Add the rostr-agent root to sys.path so we can import rostr.*
ROSTR_ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, ROSTR_ROOT)

import boto3
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

app = FastAPI(title="ROSTR AgentCore API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ── Config ────────────────────────────────────────────────────────────────────
REGION     = os.environ.get("AWS_REGION", "us-east-1")
MODEL_ID   = os.environ.get("BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-4-6")
SANDBOX_URL = os.environ.get("SANDBOX_URL", "http://localhost:8787")

bedrock = boto3.client("bedrock-runtime", region_name=REGION)

CODING_SYSTEM = """You are ROSTR Agent — a world-class AI software engineer embedded in a cloud IDE.

When the user asks you to build, modify, or fix code, append a structured block at the END of your response:

<file_changes>
{
  "reply": "Brief explanation of what you did",
  "file_changes": [
    {"path": "filename.ext", "content": "full file content here"}
  ],
  "commands": ["npm install"]
}
</file_changes>

Rules:
- ONLY include the <file_changes> block when you actually changed or created files
- For conversation, explanations, or questions with no code changes, respond naturally without any block
- In the block, "content" must be the COMPLETE file content, not a diff
- "commands" are optional shell commands to run after applying changes
- You receive the user's full project file tree as context
- You can suggest Composio tool calls for GitHub PRs, Linear issues, Slack messages

Available Composio tools: github_create_pr, github_push_files, slack_send_message, linear_create_issue

Be concise, produce working code, and always complete the task fully."""


class InvokeRequest(BaseModel):
    prompt: str
    session_id: str | None = None
    files_context: dict[str, str] | None = None   # {path: content}
    tools: list[str] | None = None
    provider: str = "bedrock"
    model: str | None = None


def _build_messages(req: InvokeRequest) -> list[dict]:
    """Build the messages array for Bedrock."""
    parts = [req.prompt]

    if req.files_context:
        file_dump = "\n\n".join(
            f"=== {path} ===\n{content[:3000]}"
            for path, content in req.files_context.items()
        )
        parts.insert(0, f"Current project files:\n\n{file_dump}\n\n---\n")

    if req.tools:
        parts.append(f"\nAvailable tools: {', '.join(req.tools)}")

    return [{"role": "user", "content": "\n".join(parts)}]


def _call_bedrock_stream(messages: list[dict]) -> Any:
    """Call Bedrock with streaming, return the response stream."""
    model = MODEL_ID
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 8192,
        "system": CODING_SYSTEM,
        "messages": messages,
    })
    return bedrock.invoke_model_with_response_stream(
        modelId=model,
        contentType="application/json",
        accept="application/json",
        body=body,
    )


def _parse_file_changes(text: str) -> dict | None:
    """Extract the <file_changes>JSON</file_changes> block from agent output."""
    import re
    m = re.search(r"<file_changes>\s*(\{.*?\})\s*</file_changes>", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass
    # Fallback: try to find any JSON with file_changes key
    m2 = re.search(r"\{[^{}]*\"file_changes\"[^{}]*\[.*?\]\s*\}", text, re.DOTALL)
    if m2:
        try:
            return json.loads(m2.group(0))
        except Exception:
            pass
    return None


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "model": MODEL_ID, "region": REGION}


@app.post("/invoke")
def invoke_sync(req: InvokeRequest):
    """Synchronous invoke — waits for full response."""
    t0 = time.monotonic()
    messages = _build_messages(req)
    resp = _call_bedrock_stream(messages)

    full_text = ""
    for event in resp["body"]:
        chunk = event.get("chunk", {})
        if not chunk:
            continue
        parsed = json.loads(chunk["bytes"])
        if parsed.get("type") == "content_block_delta":
            full_text += parsed.get("delta", {}).get("text", "")

    structured = _parse_file_changes(full_text)
    import re
    clean_text = re.sub(r"<file_changes>.*?</file_changes>", "", full_text, flags=re.DOTALL).strip()
    # If agent put everything in the block, pull reply from there
    if not clean_text and structured and structured.get("reply"):
        clean_text = structured["reply"]

    return {
        "reply": clean_text,
        "file_changes": structured.get("file_changes", []) if structured else [],
        "commands": structured.get("commands", []) if structured else [],
        "raw": full_text,
        "latency_ms": int((time.monotonic() - t0) * 1000),
        "success": True,
    }


@app.post("/invoke/stream")
async def invoke_stream(req: InvokeRequest):
    """SSE stream — yields text tokens, then final JSON."""

    async def generate() -> AsyncIterator[str]:
        import asyncio, re
        messages = _build_messages(req)
        full_text = ""

        try:
            resp = await asyncio.get_event_loop().run_in_executor(
                None, lambda: _call_bedrock_stream(messages)
            )

            for event in resp["body"]:
                chunk = event.get("chunk", {})
                if not chunk:
                    continue
                parsed = json.loads(chunk["bytes"])
                if parsed.get("type") == "content_block_delta":
                    delta = parsed.get("delta", {}).get("text", "")
                    if delta:
                        full_text += delta
                        # Stream visible text — only hide once we've entered the <file_changes> block
                        in_block = "<file_changes>" in full_text
                        if not in_block:
                            yield f"data: {json.dumps({'type': 'token', 'text': delta})}\n\n"

            # Parse structured output
            structured = _parse_file_changes(full_text)
            import re
            clean_text = re.sub(r"<file_changes>.*?</file_changes>", "", full_text, flags=re.DOTALL).strip()
            if not clean_text and structured and structured.get("reply"):
                clean_text = structured["reply"]

            # Send final result
            final = {
                "type": "done",
                "reply": clean_text,
                "file_changes": structured.get("file_changes", []) if structured else [],
                "commands": structured.get("commands", []) if structured else [],
            }
            yield f"data: {json.dumps(final)}\n\n"

        except Exception as exc:
            log.exception("invoke/stream error")
            yield f"data: {json.dumps({'type': 'error', 'text': str(exc)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8788, log_level="info")
