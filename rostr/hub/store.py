"""
Rostr Hub — Storage Abstraction + SQLite Implementation
========================================================
Production-ready persistent storage for the Agent Operating System.
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Protocol

from .models import (
    AgentRecord,
    Artifact,
    Decision,
    ExecutionEvent,
    Learning,
    LearningProvenance,
    LearningStatus,
    StateRecord,
    _validate_namespace,
)


# ── Storage Protocol ────────────────────────────────────────────────────────


class HubStore(Protocol):
    """Abstract interface for Hub persistence."""

    def save_agent(self, agent: AgentRecord) -> str: ...
    def get_agent(self, agent_id: str) -> Optional[AgentRecord]: ...
    def list_agents(self, namespace: str = "global") -> list[AgentRecord]: ...
    def save_decision(self, decision: Decision) -> str: ...
    def list_decisions(self, namespace: str, limit: int = 50) -> list[Decision]: ...
    def save_learning(self, learning: Learning) -> str: ...
    def search_learnings(self, query: str, namespace: str = "global") -> list[Learning]: ...
    def set_state(self, key: str, value: Any, namespace: str = "global") -> None: ...
    def get_state(self, key: str, namespace: str = "global") -> Optional[Any]: ...
    def append_event(self, event: ExecutionEvent) -> str: ...
    def list_events(self, session_id: str, limit: int = 100) -> list[ExecutionEvent]: ...
    def save_artifact(self, artifact: Artifact) -> str: ...
    def get_artifact(self, artifact_id: str) -> Optional[Artifact]: ...


# ── Memory Search Protocol ──────────────────────────────────────────────────


class MemorySearchProvider(Protocol):
    """Interface for searching learnings — pluggable for vector search later."""

    def search(self, query: str, namespace: str, limit: int) -> list[Learning]: ...


class LexicalMemorySearchProvider:
    """LIKE-based lexical search for learnings (FTS5-ready upgrade path)."""

    def __init__(self, store: "SQLiteHubStore"):
        self._store = store

    def search(self, query: str, namespace: str, limit: int = 20) -> list[Learning]:
        return self._store.search_learnings(query, namespace, limit)


# ── SQLite Implementation ───────────────────────────────────────────────────


_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS agents (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    capabilities TEXT NOT NULL DEFAULT '[]',
    performance_metrics TEXT NOT NULL DEFAULT '{}',
    namespace TEXT NOT NULL DEFAULT 'global',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    metadata TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS decisions (
    id TEXT PRIMARY KEY,
    description TEXT NOT NULL,
    reasoning TEXT NOT NULL DEFAULT '',
    alternatives TEXT NOT NULL DEFAULT '[]',
    chosen_action TEXT NOT NULL DEFAULT '',
    outcome TEXT,
    namespace TEXT NOT NULL DEFAULT 'global',
    agent_id TEXT,
    session_id TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS learnings (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'proposed',
    provenance TEXT NOT NULL DEFAULT '{}',
    namespace TEXT NOT NULL DEFAULT 'global',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    session_id TEXT NOT NULL,
    agent_id TEXT,
    data TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS artifacts (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    content_type TEXT NOT NULL DEFAULT 'application/octet-stream',
    data TEXT,
    namespace TEXT NOT NULL DEFAULT 'global',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS state (
    key TEXT NOT NULL,
    value TEXT,
    namespace TEXT NOT NULL DEFAULT 'global',
    updated_at TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    PRIMARY KEY (key, namespace)
);

-- Indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_agents_namespace ON agents(namespace);
CREATE INDEX IF NOT EXISTS idx_decisions_namespace ON decisions(namespace);
CREATE INDEX IF NOT EXISTS idx_decisions_agent_id ON decisions(agent_id);
CREATE INDEX IF NOT EXISTS idx_decisions_session_id ON decisions(session_id);
CREATE INDEX IF NOT EXISTS idx_decisions_created_at ON decisions(created_at);
CREATE INDEX IF NOT EXISTS idx_learnings_namespace ON learnings(namespace);
CREATE INDEX IF NOT EXISTS idx_learnings_status ON learnings(status);
CREATE INDEX IF NOT EXISTS idx_learnings_created_at ON learnings(created_at);
CREATE INDEX IF NOT EXISTS idx_events_session_id ON events(session_id);
CREATE INDEX IF NOT EXISTS idx_events_agent_id ON events(agent_id);
CREATE INDEX IF NOT EXISTS idx_events_created_at ON events(created_at);
CREATE INDEX IF NOT EXISTS idx_artifacts_namespace ON artifacts(namespace);
CREATE INDEX IF NOT EXISTS idx_state_namespace ON state(namespace);
"""


def _iso(dt: datetime) -> str:
    """Serialize datetime to ISO 8601 string."""
    return dt.isoformat()


def _parse_dt(s: str) -> datetime:
    """Parse ISO 8601 string to datetime."""
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


class SQLiteHubStore:
    """
    Production SQLite-backed Hub storage.

    Features:
    - WAL mode for concurrent reads
    - Auto-creates tables on first use
    - Thread-safe with connection-per-thread
    - UUID primary keys
    - JSON columns for flexible data
    """

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = os.path.join(os.path.expanduser("~"), ".rostr", "hub.db")
        self._db_path = db_path
        self._local = threading.local()

        # Ensure directory exists
        os.makedirs(os.path.dirname(self._db_path), exist_ok=True)

        # Initialize schema
        self._init_schema()

    def _get_conn(self) -> sqlite3.Connection:
        """Get a thread-local connection."""
        if not hasattr(self._local, "conn") or self._local.conn is None:
            conn = sqlite3.connect(self._db_path, timeout=30)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=5000")
            conn.row_factory = sqlite3.Row
            self._local.conn = conn
        return self._local.conn

    def _init_schema(self) -> None:
        """Create tables if they don't exist."""
        conn = self._get_conn()
        conn.executescript(_SCHEMA_SQL)
        conn.commit()

    def close(self) -> None:
        """Close the thread-local connection."""
        if hasattr(self._local, "conn") and self._local.conn is not None:
            self._local.conn.close()
            self._local.conn = None

    # ── Agents ──────────────────────────────────────────────────────────────

    def save_agent(self, agent: AgentRecord) -> str:
        conn = self._get_conn()
        conn.execute(
            """INSERT OR REPLACE INTO agents
               (id, name, capabilities, performance_metrics, namespace, created_at, updated_at, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                agent.id,
                agent.name,
                json.dumps(agent.capabilities),
                json.dumps(agent.performance_metrics),
                agent.namespace,
                _iso(agent.created_at),
                _iso(agent.updated_at),
                json.dumps(agent.metadata),
            ),
        )
        conn.commit()
        return agent.id

    def get_agent(self, agent_id: str) -> Optional[AgentRecord]:
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM agents WHERE id = ?", (agent_id,)).fetchone()
        if row is None:
            return None
        return self._row_to_agent(row)

    def list_agents(self, namespace: str = "global") -> list[AgentRecord]:
        _validate_namespace(namespace)
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM agents WHERE namespace = ? ORDER BY created_at",
            (namespace,),
        ).fetchall()
        return [self._row_to_agent(r) for r in rows]

    def _row_to_agent(self, row: sqlite3.Row) -> AgentRecord:
        return AgentRecord(
            id=row["id"],
            name=row["name"],
            capabilities=json.loads(row["capabilities"]),
            performance_metrics=json.loads(row["performance_metrics"]),
            namespace=row["namespace"],
            created_at=_parse_dt(row["created_at"]),
            updated_at=_parse_dt(row["updated_at"]),
            metadata=json.loads(row["metadata"]),
        )

    # ── Decisions ───────────────────────────────────────────────────────────

    def save_decision(self, decision: Decision) -> str:
        conn = self._get_conn()
        conn.execute(
            """INSERT INTO decisions
               (id, description, reasoning, alternatives, chosen_action, outcome,
                namespace, agent_id, session_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                decision.id,
                decision.description,
                decision.reasoning,
                json.dumps(decision.alternatives),
                decision.chosen_action,
                decision.outcome,
                decision.namespace,
                decision.agent_id,
                decision.session_id,
                _iso(decision.created_at),
            ),
        )
        conn.commit()
        return decision.id

    def list_decisions(self, namespace: str, limit: int = 50) -> list[Decision]:
        _validate_namespace(namespace)
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM decisions WHERE namespace = ? ORDER BY created_at DESC LIMIT ?",
            (namespace, limit),
        ).fetchall()
        return [self._row_to_decision(r) for r in rows]

    def _row_to_decision(self, row: sqlite3.Row) -> Decision:
        return Decision(
            id=row["id"],
            description=row["description"],
            reasoning=row["reasoning"],
            alternatives=json.loads(row["alternatives"]),
            chosen_action=row["chosen_action"],
            outcome=row["outcome"],
            namespace=row["namespace"],
            agent_id=row["agent_id"],
            session_id=row["session_id"],
            created_at=_parse_dt(row["created_at"]),
        )

    # ── Learnings ───────────────────────────────────────────────────────────

    def save_learning(self, learning: Learning) -> str:
        conn = self._get_conn()
        conn.execute(
            """INSERT OR REPLACE INTO learnings
               (id, content, status, provenance, namespace, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                learning.id,
                learning.content,
                learning.status.value,
                learning.provenance.model_dump_json(),
                learning.namespace,
                _iso(learning.created_at),
            ),
        )
        conn.commit()
        return learning.id

    def search_learnings(
        self, query: str, namespace: str = "global", limit: int = 20
    ) -> list[Learning]:
        _validate_namespace(namespace)
        conn = self._get_conn()
        # Lexical LIKE-based search — upgrade path to FTS5 or vector search
        pattern = f"%{query}%"
        rows = conn.execute(
            """SELECT * FROM learnings
               WHERE namespace = ? AND content LIKE ?
               ORDER BY created_at DESC LIMIT ?""",
            (namespace, pattern, limit),
        ).fetchall()
        return [self._row_to_learning(r) for r in rows]

    def list_learnings(
        self, namespace: str = "global", status: Optional[LearningStatus] = None, limit: int = 50
    ) -> list[Learning]:
        """List learnings, optionally filtered by status."""
        _validate_namespace(namespace)
        conn = self._get_conn()
        if status:
            rows = conn.execute(
                """SELECT * FROM learnings
                   WHERE namespace = ? AND status = ?
                   ORDER BY created_at DESC LIMIT ?""",
                (namespace, status.value, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT * FROM learnings
                   WHERE namespace = ? ORDER BY created_at DESC LIMIT ?""",
                (namespace, limit),
            ).fetchall()
        return [self._row_to_learning(r) for r in rows]

    def _row_to_learning(self, row: sqlite3.Row) -> Learning:
        provenance_data = json.loads(row["provenance"])
        return Learning(
            id=row["id"],
            content=row["content"],
            status=LearningStatus(row["status"]),
            provenance=LearningProvenance(**provenance_data),
            namespace=row["namespace"],
            created_at=_parse_dt(row["created_at"]),
        )

    # ── State ───────────────────────────────────────────────────────────────

    def set_state(self, key: str, value: Any, namespace: str = "global") -> None:
        _validate_namespace(namespace)
        conn = self._get_conn()
        now = _iso(datetime.now(timezone.utc))
        # Upsert with version increment
        existing = conn.execute(
            "SELECT version FROM state WHERE key = ? AND namespace = ?",
            (key, namespace),
        ).fetchone()
        if existing:
            new_version = existing["version"] + 1
            conn.execute(
                """UPDATE state SET value = ?, updated_at = ?, version = ?
                   WHERE key = ? AND namespace = ?""",
                (json.dumps(value), now, new_version, key, namespace),
            )
        else:
            conn.execute(
                """INSERT INTO state (key, value, namespace, updated_at, version)
                   VALUES (?, ?, ?, ?, 1)""",
                (key, json.dumps(value), namespace, now),
            )
        conn.commit()

    def get_state(self, key: str, namespace: str = "global") -> Optional[Any]:
        _validate_namespace(namespace)
        conn = self._get_conn()
        row = conn.execute(
            "SELECT value FROM state WHERE key = ? AND namespace = ?",
            (key, namespace),
        ).fetchone()
        if row is None:
            return None
        return json.loads(row["value"])

    def get_state_record(self, key: str, namespace: str = "global") -> Optional[StateRecord]:
        """Get full state record including version and timestamps."""
        _validate_namespace(namespace)
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM state WHERE key = ? AND namespace = ?",
            (key, namespace),
        ).fetchone()
        if row is None:
            return None
        return StateRecord(
            key=row["key"],
            value=json.loads(row["value"]),
            namespace=row["namespace"],
            updated_at=_parse_dt(row["updated_at"]),
            version=row["version"],
        )

    # ── Events ──────────────────────────────────────────────────────────────

    def append_event(self, event: ExecutionEvent) -> str:
        conn = self._get_conn()
        conn.execute(
            """INSERT INTO events (id, event_type, session_id, agent_id, data, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                event.id,
                event.event_type.value,
                event.session_id,
                event.agent_id,
                json.dumps(event.data),
                _iso(event.created_at),
            ),
        )
        conn.commit()
        return event.id

    def list_events(self, session_id: str, limit: int = 100) -> list[ExecutionEvent]:
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT * FROM events WHERE session_id = ?
               ORDER BY created_at ASC LIMIT ?""",
            (session_id, limit),
        ).fetchall()
        return [self._row_to_event(r) for r in rows]

    def _row_to_event(self, row: sqlite3.Row) -> ExecutionEvent:
        from .models import EventType

        return ExecutionEvent(
            id=row["id"],
            event_type=EventType(row["event_type"]),
            session_id=row["session_id"],
            agent_id=row["agent_id"],
            data=json.loads(row["data"]),
            created_at=_parse_dt(row["created_at"]),
        )

    # ── Artifacts ───────────────────────────────────────────────────────────

    def save_artifact(self, artifact: Artifact) -> str:
        conn = self._get_conn()
        conn.execute(
            """INSERT OR REPLACE INTO artifacts
               (id, name, content_type, data, namespace, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                artifact.id,
                artifact.name,
                artifact.content_type,
                json.dumps(artifact.data),
                artifact.namespace,
                _iso(artifact.created_at),
            ),
        )
        conn.commit()
        return artifact.id

    def get_artifact(self, artifact_id: str) -> Optional[Artifact]:
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM artifacts WHERE id = ?", (artifact_id,)
        ).fetchone()
        if row is None:
            return None
        return Artifact(
            id=row["id"],
            name=row["name"],
            content_type=row["content_type"],
            data=json.loads(row["data"]),
            namespace=row["namespace"],
            created_at=_parse_dt(row["created_at"]),
        )

    # ── Context Resolution ──────────────────────────────────────────────────

    def resolve_state(
        self,
        key: str,
        session_id: Optional[str] = None,
        project_id: Optional[str] = None,
        team_id: Optional[str] = None,
        org_id: Optional[str] = None,
        agent_id: Optional[str] = None,
    ) -> Optional[Any]:
        """
        Resolve state using namespace precedence:
        session -> project -> team -> organization -> agent -> global
        """
        resolution_order = []
        if session_id:
            resolution_order.append(f"sessions/{session_id}")
        if project_id:
            resolution_order.append(f"projects/{project_id}")
        if team_id:
            resolution_order.append(f"teams/{team_id}")
        if org_id:
            resolution_order.append(f"orgs/{org_id}")
        if agent_id:
            resolution_order.append(f"agents/{agent_id}")
        resolution_order.append("global")

        for ns in resolution_order:
            val = self.get_state(key, ns)
            if val is not None:
                return val
        return None


# ── In-Memory Implementation (for testing) ──────────────────────────────────


class InMemoryHubStore:
    """
    In-memory Hub store for fast unit testing.
    Implements the same interface as SQLiteHubStore.
    """

    def __init__(self):
        self._agents: dict[str, AgentRecord] = {}
        self._decisions: list[Decision] = []
        self._learnings: list[Learning] = []
        self._events: list[ExecutionEvent] = []
        self._artifacts: dict[str, Artifact] = {}
        self._state: dict[tuple[str, str], StateRecord] = {}
        self._lock = threading.Lock()

    def save_agent(self, agent: AgentRecord) -> str:
        with self._lock:
            self._agents[agent.id] = agent
        return agent.id

    def get_agent(self, agent_id: str) -> Optional[AgentRecord]:
        return self._agents.get(agent_id)

    def list_agents(self, namespace: str = "global") -> list[AgentRecord]:
        _validate_namespace(namespace)
        return [a for a in self._agents.values() if a.namespace == namespace]

    def save_decision(self, decision: Decision) -> str:
        with self._lock:
            self._decisions.append(decision)
        return decision.id

    def list_decisions(self, namespace: str, limit: int = 50) -> list[Decision]:
        _validate_namespace(namespace)
        filtered = [d for d in self._decisions if d.namespace == namespace]
        return sorted(filtered, key=lambda d: d.created_at, reverse=True)[:limit]

    def save_learning(self, learning: Learning) -> str:
        with self._lock:
            # Replace if same ID exists (for status transitions)
            self._learnings = [l for l in self._learnings if l.id != learning.id]
            self._learnings.append(learning)
        return learning.id

    def search_learnings(
        self, query: str, namespace: str = "global", limit: int = 20
    ) -> list[Learning]:
        _validate_namespace(namespace)
        results = []
        query_lower = query.lower()
        for l in self._learnings:
            if l.namespace == namespace and query_lower in l.content.lower():
                results.append(l)
        return sorted(results, key=lambda x: x.created_at, reverse=True)[:limit]

    def list_learnings(
        self, namespace: str = "global", status: Optional[LearningStatus] = None, limit: int = 50
    ) -> list[Learning]:
        _validate_namespace(namespace)
        filtered = [l for l in self._learnings if l.namespace == namespace]
        if status:
            filtered = [l for l in filtered if l.status == status]
        return sorted(filtered, key=lambda x: x.created_at, reverse=True)[:limit]

    def set_state(self, key: str, value: Any, namespace: str = "global") -> None:
        _validate_namespace(namespace)
        with self._lock:
            existing = self._state.get((key, namespace))
            version = (existing.version + 1) if existing else 1
            self._state[(key, namespace)] = StateRecord(
                key=key,
                value=value,
                namespace=namespace,
                version=version,
            )

    def get_state(self, key: str, namespace: str = "global") -> Optional[Any]:
        _validate_namespace(namespace)
        record = self._state.get((key, namespace))
        return record.value if record else None

    def get_state_record(self, key: str, namespace: str = "global") -> Optional[StateRecord]:
        _validate_namespace(namespace)
        return self._state.get((key, namespace))

    def append_event(self, event: ExecutionEvent) -> str:
        with self._lock:
            self._events.append(event)
        return event.id

    def list_events(self, session_id: str, limit: int = 100) -> list[ExecutionEvent]:
        filtered = [e for e in self._events if e.session_id == session_id]
        return sorted(filtered, key=lambda e: e.created_at)[:limit]

    def save_artifact(self, artifact: Artifact) -> str:
        with self._lock:
            self._artifacts[artifact.id] = artifact
        return artifact.id

    def get_artifact(self, artifact_id: str) -> Optional[Artifact]:
        return self._artifacts.get(artifact_id)

    def resolve_state(
        self,
        key: str,
        session_id: Optional[str] = None,
        project_id: Optional[str] = None,
        team_id: Optional[str] = None,
        org_id: Optional[str] = None,
        agent_id: Optional[str] = None,
    ) -> Optional[Any]:
        """Resolve state using namespace precedence."""
        resolution_order = []
        if session_id:
            resolution_order.append(f"sessions/{session_id}")
        if project_id:
            resolution_order.append(f"projects/{project_id}")
        if team_id:
            resolution_order.append(f"teams/{team_id}")
        if org_id:
            resolution_order.append(f"orgs/{org_id}")
        if agent_id:
            resolution_order.append(f"agents/{agent_id}")
        resolution_order.append("global")

        for ns in resolution_order:
            val = self.get_state(key, ns)
            if val is not None:
                return val
        return None

    def close(self) -> None:
        """No-op for in-memory store."""
        pass
