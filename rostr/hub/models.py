"""
Rostr Hub — Pydantic Data Models
=================================
Production-grade data models for the Hub storage system.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


# ── Enums ───────────────────────────────────────────────────────────────────


class LearningStatus(str, Enum):
    PROPOSED = "proposed"
    VALIDATED = "validated"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


class EventType(str, Enum):
    TASK_RECEIVED = "task_received"
    INTENT_COMPILED = "intent_compiled"
    TASK_CLASSIFIED = "task_classified"
    AGENT_ALLOCATED = "agent_allocated"
    TOOL_CALLED = "tool_called"
    TOOL_SUCCEEDED = "tool_succeeded"
    TOOL_FAILED = "tool_failed"
    EXECUTION_COMPLETED = "execution_completed"
    LEARNING_PROPOSED = "learning_proposed"
    LEARNING_APPROVED = "learning_approved"


# ── Helpers ─────────────────────────────────────────────────────────────────


def _new_id() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _validate_namespace(ns: str) -> str:
    """Validate namespace string — no path traversal, only safe characters."""
    if not ns:
        raise ValueError("Namespace cannot be empty")
    # Block path traversal
    if ".." in ns or ns.startswith("/") or "\\" in ns:
        raise ValueError(f"Invalid namespace: {ns!r} — path traversal not allowed")
    # Allow: alphanumeric, hyphens, underscores, slashes, dots (not leading)
    valid_prefixes = (
        "projects/", "orgs/", "teams/", "agents/", "sessions/", "global"
    )
    if ns != "global" and not any(ns.startswith(p) for p in valid_prefixes):
        raise ValueError(
            f"Invalid namespace: {ns!r} — must start with one of: "
            f"projects/, orgs/, teams/, agents/, sessions/, or be 'global'"
        )
    return ns


# ── Data Models ─────────────────────────────────────────────────────────────


class AgentRecord(BaseModel):
    """A registered agent in the Hub."""

    id: str = Field(default_factory=_new_id)
    name: str
    capabilities: list[str] = Field(default_factory=list)
    performance_metrics: dict[str, Any] = Field(default_factory=dict)
    namespace: str = "global"
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("namespace")
    @classmethod
    def check_namespace(cls, v: str) -> str:
        return _validate_namespace(v)


class Decision(BaseModel):
    """A key decision logged during execution."""

    id: str = Field(default_factory=_new_id)
    description: str
    reasoning: str = ""
    alternatives: list[str] = Field(default_factory=list)
    chosen_action: str = ""
    outcome: Optional[str] = None
    namespace: str = "global"
    agent_id: Optional[str] = None
    session_id: Optional[str] = None
    created_at: datetime = Field(default_factory=_now)

    @field_validator("namespace")
    @classmethod
    def check_namespace(cls, v: str) -> str:
        return _validate_namespace(v)


class LearningProvenance(BaseModel):
    """Provenance tracking for a learning."""

    execution_id: Optional[str] = None
    agent_id: Optional[str] = None
    source_event: Optional[str] = None
    user_feedback: Optional[str] = None
    verifier_result: Optional[str] = None


class Learning(BaseModel):
    """An insight learned during agent execution."""

    id: str = Field(default_factory=_new_id)
    content: str
    status: LearningStatus = LearningStatus.PROPOSED
    provenance: LearningProvenance = Field(default_factory=LearningProvenance)
    namespace: str = "global"
    created_at: datetime = Field(default_factory=_now)

    @field_validator("namespace")
    @classmethod
    def check_namespace(cls, v: str) -> str:
        return _validate_namespace(v)


class ExecutionEvent(BaseModel):
    """An event in the execution log (append-only)."""

    id: str = Field(default_factory=_new_id)
    event_type: EventType
    session_id: str
    agent_id: Optional[str] = None
    data: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=_now)


class Artifact(BaseModel):
    """A produced artifact (code, document, config, etc.)."""

    id: str = Field(default_factory=_new_id)
    name: str
    content_type: str = "application/octet-stream"
    data: Any = None
    namespace: str = "global"
    created_at: datetime = Field(default_factory=_now)

    @field_validator("namespace")
    @classmethod
    def check_namespace(cls, v: str) -> str:
        return _validate_namespace(v)


class StateRecord(BaseModel):
    """A key-value state entry with namespace scoping and versioning."""

    key: str
    value: Any = None
    namespace: str = "global"
    updated_at: datetime = Field(default_factory=_now)
    version: int = 1

    @field_validator("namespace")
    @classmethod
    def check_namespace(cls, v: str) -> str:
        return _validate_namespace(v)
