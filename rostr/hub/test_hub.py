"""
Rostr Hub — Test Suite
=======================
Tests for the Hub storage system covering persistence, isolation,
concurrency, and correctness.

Run: python -m pytest rostr/hub/test_hub.py -v
"""

import os
import tempfile
import threading
import uuid
from datetime import datetime, timezone

import pytest

from rostr.hub.models import (
    AgentRecord,
    Artifact,
    Decision,
    EventType,
    ExecutionEvent,
    Learning,
    LearningProvenance,
    LearningStatus,
)
from rostr.hub.store import InMemoryHubStore, SQLiteHubStore


# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def tmp_db(tmp_path):
    """Create a temporary database path."""
    return str(tmp_path / "test_hub.db")


@pytest.fixture
def sqlite_store(tmp_db):
    """Create a SQLiteHubStore with a temporary database."""
    store = SQLiteHubStore(db_path=tmp_db)
    yield store
    store.close()


@pytest.fixture
def memory_store():
    """Create an InMemoryHubStore."""
    return InMemoryHubStore()


@pytest.fixture(params=["sqlite", "memory"])
def store(request, tmp_db):
    """Parametrized fixture that runs tests against both store implementations."""
    if request.param == "sqlite":
        s = SQLiteHubStore(db_path=tmp_db)
        yield s
        s.close()
    else:
        yield InMemoryHubStore()


# ── Agent Tests ─────────────────────────────────────────────────────────────


class TestAgentRegistration:
    def test_save_and_get_agent(self, store):
        agent = AgentRecord(
            name="test-builder",
            capabilities=["code", "deploy"],
            performance_metrics={"success_rate": 0.95},
            namespace="global",
            metadata={"model": "claude-sonnet-4-6"},
        )
        agent_id = store.save_agent(agent)
        assert agent_id == agent.id

        retrieved = store.get_agent(agent_id)
        assert retrieved is not None
        assert retrieved.name == "test-builder"
        assert retrieved.capabilities == ["code", "deploy"]
        assert retrieved.performance_metrics == {"success_rate": 0.95}
        assert retrieved.metadata == {"model": "claude-sonnet-4-6"}

    def test_get_nonexistent_agent(self, store):
        result = store.get_agent("nonexistent-id")
        assert result is None

    def test_list_agents_by_namespace(self, store):
        agent1 = AgentRecord(name="agent-a", namespace="global")
        agent2 = AgentRecord(name="agent-b", namespace="global")
        agent3 = AgentRecord(name="agent-c", namespace="projects/proj1")
        store.save_agent(agent1)
        store.save_agent(agent2)
        store.save_agent(agent3)

        global_agents = store.list_agents("global")
        assert len(global_agents) == 2
        assert all(a.namespace == "global" for a in global_agents)

        project_agents = store.list_agents("projects/proj1")
        assert len(project_agents) == 1
        assert project_agents[0].name == "agent-c"

    def test_update_agent(self, store):
        agent = AgentRecord(name="updatable", namespace="global")
        store.save_agent(agent)

        agent.performance_metrics = {"tasks_completed": 10}
        store.save_agent(agent)

        retrieved = store.get_agent(agent.id)
        assert retrieved.performance_metrics == {"tasks_completed": 10}


# ── Decision Tests ──────────────────────────────────────────────────────────


class TestDecisions:
    def test_save_and_list_decisions(self, store):
        decision = Decision(
            description="Use SQLite for storage",
            reasoning="Lightweight, embedded, WAL mode supports concurrency",
            alternatives=["PostgreSQL", "Redis", "File-based"],
            chosen_action="Implement SQLiteHubStore",
            outcome="success",
            namespace="projects/rostr",
            agent_id="agent-1",
            session_id="session-1",
        )
        decision_id = store.save_decision(decision)
        assert decision_id == decision.id

        decisions = store.list_decisions("projects/rostr")
        assert len(decisions) == 1
        assert decisions[0].description == "Use SQLite for storage"
        assert decisions[0].alternatives == ["PostgreSQL", "Redis", "File-based"]

    def test_list_decisions_respects_limit(self, store):
        for i in range(10):
            store.save_decision(
                Decision(description=f"Decision {i}", namespace="global")
            )

        decisions = store.list_decisions("global", limit=5)
        assert len(decisions) == 5

    def test_list_decisions_namespace_isolation(self, store):
        store.save_decision(Decision(description="D1", namespace="projects/a"))
        store.save_decision(Decision(description="D2", namespace="projects/b"))

        a_decisions = store.list_decisions("projects/a")
        assert len(a_decisions) == 1
        assert a_decisions[0].description == "D1"

        b_decisions = store.list_decisions("projects/b")
        assert len(b_decisions) == 1
        assert b_decisions[0].description == "D2"


# ── Learning Tests ──────────────────────────────────────────────────────────


class TestLearnings:
    def test_save_and_search_learnings(self, store):
        learning = Learning(
            content="SQLite WAL mode allows concurrent reads without blocking",
            status=LearningStatus.VALIDATED,
            provenance=LearningProvenance(
                agent_id="agent-1",
                source_event="execution_completed",
            ),
            namespace="global",
        )
        learning_id = store.save_learning(learning)
        assert learning_id == learning.id

        results = store.search_learnings("WAL mode", "global")
        assert len(results) == 1
        assert "WAL mode" in results[0].content

    def test_search_returns_empty_for_no_match(self, store):
        store.save_learning(
            Learning(content="Python is great", namespace="global")
        )
        results = store.search_learnings("JavaScript", "global")
        assert len(results) == 0

    def test_learning_status_transitions(self, store):
        learning = Learning(
            content="Initial insight",
            status=LearningStatus.PROPOSED,
            namespace="global",
        )
        store.save_learning(learning)

        # Validate it
        learning.status = LearningStatus.VALIDATED
        store.save_learning(learning)

        results = store.search_learnings("Initial insight", "global")
        assert len(results) == 1
        assert results[0].status == LearningStatus.VALIDATED

    def test_learning_status_superseded(self, store):
        old_learning = Learning(
            content="Use approach A for caching",
            status=LearningStatus.VALIDATED,
            namespace="global",
        )
        store.save_learning(old_learning)

        # Supersede it
        old_learning.status = LearningStatus.SUPERSEDED
        store.save_learning(old_learning)

        new_learning = Learning(
            content="Use approach B for caching (replaces A)",
            status=LearningStatus.VALIDATED,
            namespace="global",
        )
        store.save_learning(new_learning)

        results = store.search_learnings("caching", "global")
        assert len(results) == 2
        statuses = {r.status for r in results}
        assert LearningStatus.SUPERSEDED in statuses
        assert LearningStatus.VALIDATED in statuses

    def test_learning_namespace_isolation(self, store):
        store.save_learning(
            Learning(content="Team A insight", namespace="teams/team-a")
        )
        store.save_learning(
            Learning(content="Team B insight", namespace="teams/team-b")
        )

        a_results = store.search_learnings("insight", "teams/team-a")
        assert len(a_results) == 1
        assert "Team A" in a_results[0].content

        b_results = store.search_learnings("insight", "teams/team-b")
        assert len(b_results) == 1
        assert "Team B" in b_results[0].content


# ── State Tests ─────────────────────────────────────────────────────────────


class TestState:
    def test_set_and_get_state(self, store):
        store.set_state("config.model", "claude-sonnet-4-6", "global")
        value = store.get_state("config.model", "global")
        assert value == "claude-sonnet-4-6"

    def test_get_nonexistent_state(self, store):
        result = store.get_state("nonexistent.key", "global")
        assert result is None

    def test_state_namespace_isolation(self, store):
        store.set_state("theme", "dark", "projects/proj1")
        store.set_state("theme", "light", "projects/proj2")

        assert store.get_state("theme", "projects/proj1") == "dark"
        assert store.get_state("theme", "projects/proj2") == "light"
        assert store.get_state("theme", "global") is None

    def test_state_update_increments_version(self, store):
        store.set_state("counter", 1, "global")
        store.set_state("counter", 2, "global")
        store.set_state("counter", 3, "global")

        record = store.get_state_record("counter", "global")
        assert record is not None
        assert record.value == 3
        assert record.version == 3

    def test_state_stores_complex_values(self, store):
        complex_value = {
            "agents": ["a1", "a2"],
            "config": {"nested": True, "count": 42},
        }
        store.set_state("complex_key", complex_value, "global")
        retrieved = store.get_state("complex_key", "global")
        assert retrieved == complex_value


# ── Namespace Inheritance Tests ─────────────────────────────────────────────


class TestNamespaceInheritance:
    def test_resolve_state_session_overrides_global(self, store):
        store.set_state("model", "global-model", "global")
        store.set_state("model", "session-model", "sessions/s1")

        result = store.resolve_state("model", session_id="s1")
        assert result == "session-model"

    def test_resolve_state_falls_through_to_global(self, store):
        store.set_state("default_setting", "global-value", "global")

        result = store.resolve_state(
            "default_setting", session_id="s1", project_id="p1"
        )
        assert result == "global-value"

    def test_resolve_state_project_overrides_org(self, store):
        store.set_state("timeout", 30, "orgs/org1")
        store.set_state("timeout", 10, "projects/proj1")

        result = store.resolve_state("timeout", project_id="proj1", org_id="org1")
        assert result == 10

    def test_resolve_state_full_chain(self, store):
        store.set_state("key", "global", "global")
        store.set_state("key", "agent", "agents/a1")
        store.set_state("key", "org", "orgs/o1")
        store.set_state("key", "team", "teams/t1")
        store.set_state("key", "project", "projects/p1")
        store.set_state("key", "session", "sessions/s1")

        # Session wins
        result = store.resolve_state(
            "key",
            session_id="s1",
            project_id="p1",
            team_id="t1",
            org_id="o1",
            agent_id="a1",
        )
        assert result == "session"

    def test_resolve_state_returns_none_when_not_found(self, store):
        result = store.resolve_state("missing_key", session_id="s1")
        assert result is None


# ── Event Tests ─────────────────────────────────────────────────────────────


class TestEvents:
    def test_append_and_list_events(self, store):
        session_id = "session-abc"
        events = [
            ExecutionEvent(
                event_type=EventType.TASK_RECEIVED,
                session_id=session_id,
                agent_id="agent-1",
                data={"task": "build hub"},
            ),
            ExecutionEvent(
                event_type=EventType.INTENT_COMPILED,
                session_id=session_id,
                agent_id="agent-1",
                data={"intent": "create storage system"},
            ),
            ExecutionEvent(
                event_type=EventType.EXECUTION_COMPLETED,
                session_id=session_id,
                agent_id="agent-1",
                data={"status": "success"},
            ),
        ]
        for event in events:
            store.append_event(event)

        retrieved = store.list_events(session_id)
        assert len(retrieved) == 3
        assert retrieved[0].event_type == EventType.TASK_RECEIVED
        assert retrieved[1].event_type == EventType.INTENT_COMPILED
        assert retrieved[2].event_type == EventType.EXECUTION_COMPLETED

    def test_events_are_append_only(self, store):
        """Events cannot be modified once appended — only new events can be added."""
        session_id = "session-xyz"
        event = ExecutionEvent(
            event_type=EventType.TOOL_CALLED,
            session_id=session_id,
            data={"tool": "grep"},
        )
        event_id = store.append_event(event)

        # Appending another event with same session doesn't overwrite
        event2 = ExecutionEvent(
            event_type=EventType.TOOL_SUCCEEDED,
            session_id=session_id,
            data={"result": "found 3 matches"},
        )
        store.append_event(event2)

        all_events = store.list_events(session_id)
        assert len(all_events) == 2
        assert all_events[0].id == event_id
        assert all_events[1].id == event2.id

    def test_events_session_isolation(self, store):
        store.append_event(
            ExecutionEvent(
                event_type=EventType.TASK_RECEIVED,
                session_id="session-1",
                data={},
            )
        )
        store.append_event(
            ExecutionEvent(
                event_type=EventType.TASK_RECEIVED,
                session_id="session-2",
                data={},
            )
        )

        s1_events = store.list_events("session-1")
        assert len(s1_events) == 1

        s2_events = store.list_events("session-2")
        assert len(s2_events) == 1

    def test_event_limit(self, store):
        session_id = "session-many"
        for i in range(20):
            store.append_event(
                ExecutionEvent(
                    event_type=EventType.TOOL_CALLED,
                    session_id=session_id,
                    data={"call": i},
                )
            )

        limited = store.list_events(session_id, limit=5)
        assert len(limited) == 5


# ── Artifact Tests ──────────────────────────────────────────────────────────


class TestArtifacts:
    def test_save_and_get_artifact(self, store):
        artifact = Artifact(
            name="schema.sql",
            content_type="text/sql",
            data="CREATE TABLE test (id TEXT);",
            namespace="projects/rostr",
        )
        artifact_id = store.save_artifact(artifact)
        assert artifact_id == artifact.id

        retrieved = store.get_artifact(artifact_id)
        assert retrieved is not None
        assert retrieved.name == "schema.sql"
        assert retrieved.content_type == "text/sql"
        assert retrieved.data == "CREATE TABLE test (id TEXT);"

    def test_get_nonexistent_artifact(self, store):
        result = store.get_artifact("nonexistent-id")
        assert result is None

    def test_artifact_with_complex_data(self, store):
        artifact = Artifact(
            name="config.json",
            content_type="application/json",
            data={"key": "value", "nested": [1, 2, 3]},
            namespace="global",
        )
        store.save_artifact(artifact)

        retrieved = store.get_artifact(artifact.id)
        assert retrieved.data == {"key": "value", "nested": [1, 2, 3]}


# ── Persistence Tests (SQLite-specific) ────────────────────────────────────


class TestPersistence:
    def test_data_persists_across_instances(self, tmp_db):
        """Data written by one store instance is readable by another."""
        # Write with first instance
        store1 = SQLiteHubStore(db_path=tmp_db)
        agent = AgentRecord(name="persistent-agent", namespace="global")
        store1.save_agent(agent)
        store1.set_state("persistent_key", "persistent_value", "global")
        store1.save_decision(
            Decision(description="Persist this", namespace="global")
        )
        store1.save_learning(
            Learning(content="Persistence works", namespace="global")
        )
        store1.append_event(
            ExecutionEvent(
                event_type=EventType.TASK_RECEIVED,
                session_id="s1",
                data={"persisted": True},
            )
        )
        store1.close()

        # Read with second instance
        store2 = SQLiteHubStore(db_path=tmp_db)
        assert store2.get_agent(agent.id) is not None
        assert store2.get_agent(agent.id).name == "persistent-agent"
        assert store2.get_state("persistent_key", "global") == "persistent_value"
        assert len(store2.list_decisions("global")) == 1
        assert len(store2.search_learnings("Persistence", "global")) == 1
        assert len(store2.list_events("s1")) == 1
        store2.close()

    def test_database_created_automatically(self, tmp_path):
        """Database file is created on first use without manual setup."""
        db_path = str(tmp_path / "subdir" / "new_hub.db")
        assert not os.path.exists(db_path)

        store = SQLiteHubStore(db_path=db_path)
        store.save_agent(AgentRecord(name="auto-create-test", namespace="global"))
        store.close()

        assert os.path.exists(db_path)


# ── Concurrent Write Tests ──────────────────────────────────────────────────


class TestConcurrency:
    def test_concurrent_writes_sqlite(self, tmp_db):
        """Multiple threads can write concurrently without data loss."""
        store = SQLiteHubStore(db_path=tmp_db)
        num_threads = 10
        agents_per_thread = 5
        errors = []

        def writer(thread_id):
            try:
                for i in range(agents_per_thread):
                    agent = AgentRecord(
                        name=f"thread-{thread_id}-agent-{i}",
                        namespace="global",
                    )
                    store.save_agent(agent)
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=writer, args=(t,)) for t in range(num_threads)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Errors during concurrent writes: {errors}"
        all_agents = store.list_agents("global")
        assert len(all_agents) == num_threads * agents_per_thread
        store.close()

    def test_concurrent_state_writes(self, tmp_db):
        """Concurrent state writes don't corrupt data."""
        store = SQLiteHubStore(db_path=tmp_db)
        num_threads = 10
        errors = []

        def writer(thread_id):
            try:
                store.set_state(
                    f"key-{thread_id}", f"value-{thread_id}", "global"
                )
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=writer, args=(t,)) for t in range(num_threads)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        for i in range(num_threads):
            val = store.get_state(f"key-{i}", "global")
            assert val == f"value-{i}"
        store.close()

    def test_concurrent_event_appends(self, tmp_db):
        """Concurrent event appends maintain order within session."""
        store = SQLiteHubStore(db_path=tmp_db)
        session_id = "concurrent-session"
        num_threads = 10
        errors = []

        def appender(thread_id):
            try:
                store.append_event(
                    ExecutionEvent(
                        event_type=EventType.TOOL_CALLED,
                        session_id=session_id,
                        data={"thread": thread_id},
                    )
                )
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=appender, args=(t,)) for t in range(num_threads)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        events = store.list_events(session_id)
        assert len(events) == num_threads
        store.close()


# ── Namespace Validation Tests ──────────────────────────────────────────────


class TestNamespaceValidation:
    def test_rejects_path_traversal(self, store):
        with pytest.raises(Exception):
            AgentRecord(name="evil", namespace="../../../etc/passwd")

    def test_rejects_absolute_path(self, store):
        with pytest.raises(Exception):
            AgentRecord(name="evil", namespace="/etc/passwd")

    def test_rejects_backslash(self, store):
        with pytest.raises(Exception):
            AgentRecord(name="evil", namespace="projects\\evil")

    def test_rejects_invalid_prefix(self, store):
        with pytest.raises(Exception):
            AgentRecord(name="evil", namespace="invalid/prefix")

    def test_accepts_valid_namespaces(self, store):
        valid = [
            "global",
            "projects/my-project",
            "orgs/atlas-hxm",
            "teams/engineering",
            "agents/agent-001",
            "sessions/abc-123",
        ]
        for ns in valid:
            agent = AgentRecord(name="test", namespace=ns)
            store.save_agent(agent)
            assert store.get_agent(agent.id).namespace == ns


# ── Edge Case Tests ─────────────────────────────────────────────────────────


class TestEdgeCases:
    def test_empty_search_query(self, store):
        store.save_learning(Learning(content="Something here", namespace="global"))
        # Empty string matches everything via LIKE '%%'
        results = store.search_learnings("", "global")
        assert len(results) >= 1

    def test_special_characters_in_content(self, store):
        content = "SQL injection: '; DROP TABLE learnings; --"
        store.save_learning(Learning(content=content, namespace="global"))
        results = store.search_learnings("DROP TABLE", "global")
        assert len(results) == 1
        assert results[0].content == content

    def test_unicode_content(self, store):
        store.save_learning(
            Learning(content="Supports unicode: café ☃ \U0001f680", namespace="global")
        )
        results = store.search_learnings("unicode", "global")
        assert len(results) == 1

    def test_large_json_data(self, store):
        large_data = {"items": [f"item-{i}" for i in range(1000)]}
        store.set_state("large_key", large_data, "global")
        retrieved = store.get_state("large_key", "global")
        assert len(retrieved["items"]) == 1000

    def test_null_values_in_optional_fields(self, store):
        decision = Decision(
            description="Minimal decision",
            namespace="global",
            outcome=None,
            agent_id=None,
            session_id=None,
        )
        store.save_decision(decision)
        decisions = store.list_decisions("global")
        assert len(decisions) == 1
        assert decisions[0].outcome is None
