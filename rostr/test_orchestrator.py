"""
Unit Tests for ROSTR Orchestrator
==================================

10+ comprehensive tests covering all orchestration stages:
  1. Intent compilation (PAL)
  2. NPAO routing and prioritization
  3. RAG DAL retrieval
  4. Handler execution
  5. Hub memory persistence
  6. Full orchestration pipeline
  7. Error handling
  8. Edge cases
"""

import pytest
import uuid
import time
from unittest.mock import Mock, MagicMock

from rostr.orchestrator import (
    RostrOrchestrator,
    ExecutionContext,
    HandlerRegistry,
    create_orchestrator,
)
from rostr.pal import PALCompiler, Intent, AgentManifest, Domain, Urgency, AgentType
from rostr.npao import NPAO, PhaseType, AgentSpec
from rostr.ragdal import RAGDAL, KnowledgeEntry, SourceTier
from rostr.hub import RostrHub, AgentRegistration, StateLevel, Namespace


# ── Fixtures ───────────────────────────────────────────────────────────

@pytest.fixture
def orchestrator():
    """Create a fresh orchestrator for each test."""
    return RostrOrchestrator()


@pytest.fixture
def sample_agent():
    """Create a sample agent registration."""
    return AgentRegistration(
        name="TestBuilder",
        agent_type="builder",
        capabilities=["code_generation", "testing"],
        tools=["code_execution", "file_system"],
        phases=["Development", "Debugging"],
    )


@pytest.fixture
def sample_knowledge_entry():
    """Create a sample knowledge entry."""
    return KnowledgeEntry(
        query_origin="test_query",
        content="Test content about code",
        source_url="https://example.com/code",
        source_title="Example Article",
        source_tier=SourceTier.TIER_2,
        topics=["code", "testing"],
        entities=["Python", "pytest"],
    )


# ── Test 1: PAL Intent Compilation ────────────────────────────────────

class TestPALCompilation:
    """Test the PAL (Prompt Abstraction Layer) compilation stages."""

    def test_extract_intent_code_domain(self):
        """Test that PAL correctly extracts code-domain intent."""
        pal = PALCompiler()
        intent = pal.extract_intent("Build a Python API for user authentication")

        assert intent.domain == Domain.CODE
        assert "api" in intent.primary_intent.lower() or "create" in intent.primary_intent.lower()
        assert intent.desired_output == "working implementation"

    def test_extract_intent_research_domain(self):
        """Test research domain extraction."""
        pal = PALCompiler()
        intent = pal.extract_intent("Research the latest trends in AI")

        assert intent.domain == Domain.RESEARCH
        assert "research" in intent.primary_intent.lower()

    def test_classify_urgency_immediate(self):
        """Test immediate urgency classification."""
        pal = PALCompiler()
        intent = pal.extract_intent("ASAP: fix the critical bug")

        assert intent.urgency == Urgency.IMMEDIATE

    def test_classify_urgency_scheduled(self):
        """Test scheduled urgency classification."""
        pal = PALCompiler()
        intent = pal.extract_intent("Research competitor features")

        assert intent.urgency == Urgency.SCHEDULED

    def test_enhance_removes_hedging(self):
        """Test that semantic enhancement removes hedging language."""
        pal = PALCompiler()
        intent = Intent(
            primary_intent="maybe build a feature",
            domain=Domain.CODE,
            subject="feature",
            desired_output="",
        )
        enhanced = pal.enhance(intent)

        assert "maybe" not in enhanced.lower()
        assert "perhaps" not in enhanced.lower()

    def test_compile_to_manifest(self):
        """Test compilation to AgentManifest."""
        pal = PALCompiler()
        intent = Intent(
            primary_intent="build a Python function",
            domain=Domain.CODE,
            subject="function",
            urgency=Urgency.IMMEDIATE,
        )
        enhanced = pal.enhance(intent)
        manifest = pal.compile(intent, enhanced)

        assert manifest.agent_type == AgentType.BUILDER
        assert manifest.model in ["claude-sonnet-4-6", "claude-opus-4"]
        assert "code_execution" in manifest.tools_allow

    def test_full_pal_pipeline(self):
        """Test the full 5-stage PAL pipeline."""
        pal = PALCompiler()
        intent, enhanced, manifest, phase = pal.compile_intent(
            "Build a production-grade REST API"
        )

        assert isinstance(intent, Intent)
        assert isinstance(enhanced, str)
        assert isinstance(manifest, AgentManifest)
        assert isinstance(phase, str)
        assert phase in ["PreD", "Design", "Development", "Deployment", "Debugging"]


# ── Test 2: NPAO Routing & Prioritization ──────────────────────────────

class TestNPAORouting:
    """Test NPAO (Navigate, Prioritize, Allocate, Orchestrate)."""

    def test_classify_phase_debugging(self):
        """Test phase classification for debugging."""
        npao = NPAO()
        phase = npao.classify_phase("Fix the critical bug in production")

        assert phase == PhaseType.DEBUGGING

    def test_classify_phase_deployment(self):
        """Test phase classification for deployment."""
        npao = NPAO()
        phase = npao.classify_phase("Deploy the new feature to production")

        assert phase == PhaseType.DEPLOYMENT

    def test_classify_phase_development(self):
        """Test phase classification for development."""
        npao = NPAO()
        phase = npao.classify_phase("Implement user authentication")

        assert phase == PhaseType.DEVELOPMENT

    def test_priority_scoring_debugging(self):
        """Test that debugging tasks get high priority."""
        npao = NPAO()
        priority = npao.score_priority(
            PhaseType.DEBUGGING,
            blocked_tasks=5,
            revenue_impact=True,
        )

        assert priority.composite >= 7.0
        assert priority.status.value == "immediate"

    def test_priority_scoring_research(self):
        """Test that research gets lower priority."""
        npao = NPAO()
        priority = npao.score_priority(
            PhaseType.PRED,
            blocked_tasks=0,
            revenue_impact=False,
        )

        assert priority.composite < 4.0
        assert priority.status.value == "backlog"

    def test_agent_allocation(self):
        """Test agent allocation algorithm."""
        npao = NPAO()

        # Register agents
        builder = AgentSpec(
            agent_id="builder-1",
            name="Python Builder",
            agent_type="builder",
            capabilities=["code_generation"],
            tools=["code_execution"],
            phases=[PhaseType.DEVELOPMENT],
            max_parallel_tasks=3,
            current_tasks=0,
        )
        npao.register_agent(builder)

        # Allocate to development phase
        allocated = npao.allocate(
            PhaseType.DEVELOPMENT,
            required_tools=["code_execution"],
        )

        assert allocated is not None
        assert allocated.agent_id == "builder-1"

    def test_agent_allocation_insufficient_capacity(self):
        """Test that overloaded agents are skipped."""
        npao = NPAO()

        # Register agent at max capacity
        builder = AgentSpec(
            agent_id="builder-1",
            name="Busy Builder",
            agent_type="builder",
            capabilities=["code_generation"],
            tools=["code_execution"],
            phases=[PhaseType.DEVELOPMENT],
            max_parallel_tasks=2,
            current_tasks=2,  # At capacity!
        )
        npao.register_agent(builder)

        # Try to allocate
        allocated = npao.allocate(
            PhaseType.DEVELOPMENT,
            required_tools=["code_execution"],
        )

        assert allocated is None  # No capacity

    def test_full_npao_pipeline(self):
        """Test the full NPAO pipeline."""
        npao = NPAO()

        result = npao.process(
            "Build a REST API for user management",
            domain="code",
        )

        assert "phase" in result
        assert "priority" in result
        assert "orchestration" in result
        assert result["phase"] == "DEVELOPMENT"


# ── Test 3: RAG DAL Retrieval ──────────────────────────────────────────

class TestRAGDALRetrieval:
    """Test RAG DAL (Retrieval-Augmented Generation)."""

    def test_tier_classification_academic(self):
        """Test that academic URLs are classified as Tier 1."""
        ragdal = RAGDAL()
        tier = ragdal.classify_tier("https://arxiv.org/abs/2023.00000")

        assert tier == SourceTier.TIER_1

    def test_tier_classification_news(self):
        """Test that news URLs are classified as Tier 2."""
        ragdal = RAGDAL()
        tier = ragdal.classify_tier("https://www.reuters.com/article")

        assert tier == SourceTier.TIER_2

    def test_tier_classification_blog(self):
        """Test that blogs are classified as Tier 3."""
        ragdal = RAGDAL()
        tier = ragdal.classify_tier("https://myblog.com/post")

        assert tier == SourceTier.TIER_3

    def test_confidence_computation(self):
        """Test confidence score computation."""
        ragdal = RAGDAL()
        confidence = ragdal.compute_confidence(
            source_count=5,
            consistency=0.9,
            tier_distribution=0.8,
            recency=0.95,
        )

        assert 0.0 <= confidence <= 1.0
        # Should be relatively high given good inputs
        assert confidence > 0.7

    def test_knowledge_entry_ingestion(self):
        """Test ingesting knowledge entries."""
        ragdal = RAGDAL()

        entry = KnowledgeEntry(
            query_origin="test",
            content="Important knowledge",
            source_url="https://arxiv.org/abs/2023.00000",
            source_tier=SourceTier.TIER_1,
        )

        ingested = ragdal.ingest(entry)

        assert ingested.confidence >= 0.0
        assert len(ragdal.knowledge_base) == 1

    def test_multi_pass_retrieval(self):
        """Test multi-pass retrieval convergence."""
        ragdal = RAGDAL(confidence_threshold=0.7, max_passes=3)
        report = ragdal.multi_pass_retrieve("How do I implement ML models?")

        assert report.sources_used > 0
        assert report.passes_completed <= 3
        assert len(report.sub_topics) > 0

    def test_query_knowledge_base(self):
        """Test querying the persistent knowledge base."""
        ragdal = RAGDAL()

        # Ingest multiple entries
        for i in range(5):
            entry = KnowledgeEntry(
                query_origin=f"query_{i}",
                content=f"Content {i}",
                source_url=f"https://example.com/{i}",
                topics=["testing"],
            )
            ragdal.ingest(entry)

        # Query
        results = ragdal.query_knowledge_base("testing", top_k=3)

        assert len(results) <= 3


# ── Test 4: Hub Memory Persistence ────────────────────────────────────

class TestHubMemory:
    """Test Hub persistence and state management."""

    def test_agent_registration(self, sample_agent):
        """Test agent registration."""
        hub = RostrHub()
        hub.register_agent(sample_agent)

        retrieved = hub.get_agent(sample_agent.agent_id)
        assert retrieved.name == "TestBuilder"

    def test_decision_logging(self):
        """Test logging decisions."""
        hub = RostrHub()

        decision = hub.log_decision(
            context="Route task",
            decision="Allocate to Builder Agent",
            rationale="Suitable for development phase",
            alternatives=["Allocate to Designer"],
        )

        assert decision.decision_id
        assert "Builder" in decision.decision

    def test_learning_logging(self):
        """Test logging learnings."""
        hub = RostrHub()

        learning = hub.log_learning(
            context="Executed task",
            insight="Task completed 40% faster than expected",
            outcome="success",
            tags=["performance", "optimization"],
        )

        assert learning.learning_id
        assert "faster" in learning.insight

    def test_learning_search(self):
        """Test searching learnings."""
        hub = RostrHub()

        hub.log_learning("Context 1", "Performance improved", "success", tags=["perf"])
        hub.log_learning("Context 2", "API latency reduced", "success", tags=["api"])
        hub.log_learning("Context 3", "Database optimization", "success", tags=["db"])

        results = hub.search_learnings("performance")
        assert len(results) > 0

    def test_state_persistence(self):
        """Test setting and getting state."""
        hub = RostrHub()

        hub.set_state(StateLevel.PROJECT, "api_version", "v2")
        value = hub.get_state(StateLevel.PROJECT, "api_version")

        assert value == "v2"

    def test_namespace_creation(self, sample_agent):
        """Test namespace management."""
        hub = RostrHub()

        ns = hub.ensure_namespace(Namespace.PROJECTS, "project-123")
        assert ns is not None
        assert "created_at" in ns


# ── Test 5: Handler Registry & Execution ───────────────────────────────

class TestHandlerRegistry:
    """Test handler registration and dispatch."""

    def test_register_handler(self):
        """Test registering a handler."""
        registry = HandlerRegistry()

        def sample_handler(ctx):
            return {"status": "ok"}

        registry.register("builder", "Development", sample_handler)

        retrieved = registry.get("builder", "Development")
        assert retrieved is not None

    def test_get_missing_handler(self):
        """Test that missing handlers return None."""
        registry = HandlerRegistry()

        retrieved = registry.get("nonexistent", "nonexistent")
        assert retrieved is None

    def test_list_handlers(self):
        """Test listing all registered handlers."""
        registry = HandlerRegistry()

        registry.register("builder", "Development", lambda x: x)
        registry.register("researcher", "PreD", lambda x: x)

        all_handlers = registry.list_all()
        assert len(all_handlers) == 2


# ── Test 6: Full Orchestration Pipeline ────────────────────────────────

class TestFullOrchestration:
    """Test the complete orchestration pipeline."""

    def test_orchestrate_basic(self, orchestrator):
        """Test basic orchestration."""
        result, memory = orchestrator.orchestrate(
            "Analyze the market for AI tools"
        )

        assert result is not None
        assert memory is not None
        assert "error" not in memory or memory.get("error") is None

    def test_orchestrate_with_handler(self, orchestrator):
        """Test orchestration with custom handler."""
        def custom_handler(ctx):
            return {
                "status": "completed",
                "execution_id": ctx.execution_id,
                "phase": ctx.routed_phase,
            }

        result, memory = orchestrator.orchestrate(
            "Build a Python API",
            handler_override=custom_handler,
        )

        assert result["status"] == "completed"
        assert "execution_id" in result

    def test_orchestrate_returns_memory_update(self, orchestrator):
        """Test that orchestration returns memory updates."""
        result, memory = orchestrator.orchestrate(
            "Research machine learning trends"
        )

        # Memory should contain at least state_updated
        assert "state_updated" in memory or "error" in memory

    def test_execution_context_creation(self):
        """Test ExecutionContext initialization."""
        intent = Intent(
            primary_intent="test",
            domain=Domain.CODE,
            subject="function",
        )
        ctx = ExecutionContext(
            execution_id="test-123",
            user_message="test message",
            intent=intent,
            enhanced_instruction="test instruction",
            manifest=AgentManifest(agent_type=AgentType.BUILDER),
            routed_phase="Development",
            allocated_agent=None,
        )

        assert ctx.execution_id == "test-123"
        assert ctx.execution_time_seconds >= 0

    def test_execution_history_tracking(self, orchestrator):
        """Test that executions are tracked."""
        orchestrator.orchestrate("Task 1")
        orchestrator.orchestrate("Task 2")

        history = orchestrator.get_execution_history(limit=5)
        assert len(history) >= 2

    def test_get_execution_by_id(self, orchestrator):
        """Test retrieving execution by ID."""
        result, memory = orchestrator.orchestrate("Test task")

        # Try to get from history (we don't have the ID directly in result,
        # but we can get from history)
        history = orchestrator.get_execution_history(limit=1)
        if history:
            exec_id = history[0]["execution_id"]
            execution = orchestrator.get_execution_by_id(exec_id)
            assert execution is not None


# ── Test 7: Error Handling ─────────────────────────────────────────────

class TestErrorHandling:
    """Test error handling and recovery."""

    def test_orchestrate_with_handler_error(self, orchestrator):
        """Test that handler errors are caught."""
        def failing_handler(ctx):
            raise ValueError("Intentional handler error")

        result, memory = orchestrator.orchestrate(
            "Task that will fail",
            handler_override=failing_handler,
        )

        # When an error occurs, either error is in memory, or result is None
        assert result is None or "error" in memory

    def test_default_handler_fallback(self, orchestrator):
        """Test that default handler is used when no handler registered."""
        result, memory = orchestrator.orchestrate(
            "Some random task"
        )

        # Should still succeed with default handler
        assert result is not None


# ── Test 8: Factory Functions ──────────────────────────────────────────

class TestFactory:
    """Test orchestrator factory and initialization."""

    def test_create_orchestrator(self):
        """Test creating orchestrator via factory."""
        orchestrator = create_orchestrator()

        assert orchestrator is not None
        assert isinstance(orchestrator.hub, RostrHub)

    def test_create_orchestrator_with_seed_agents(self, sample_agent):
        """Test creating orchestrator with pre-registered agents."""
        orchestrator = create_orchestrator(seed_agents=[sample_agent])

        retrieved = orchestrator.hub.get_agent(sample_agent.agent_id)
        assert retrieved is not None


# ── Test 9: Summary & Introspection ────────────────────────────────────

class TestIntrospection:
    """Test orchestrator introspection and summary."""

    def test_summary_generation(self, orchestrator):
        """Test generating orchestrator summary."""
        orchestrator.orchestrate("Task 1")

        summary = orchestrator.summary()

        assert "executions_total" in summary
        assert "executions_successful" in summary
        assert "executions_failed" in summary
        assert "avg_execution_time_seconds" in summary


# ── Test 10: Integration Tests ─────────────────────────────────────────

class TestIntegration:
    """Integration tests combining multiple components."""

    def test_full_pipeline_code_task(self):
        """Full pipeline for a code task."""
        orchestrator = create_orchestrator()

        result, memory = orchestrator.orchestrate(
            "Build a Python function to validate email addresses"
        )

        assert result is not None
        assert "error" not in memory or memory.get("error") is None

    def test_full_pipeline_research_task(self):
        """Full pipeline for a research task."""
        orchestrator = create_orchestrator()

        result, memory = orchestrator.orchestrate(
            "Research the latest advances in quantum computing"
        )

        assert result is not None

    def test_full_pipeline_with_custom_agent(self, sample_agent):
        """Full pipeline with custom agent registered."""
        orchestrator = create_orchestrator(seed_agents=[sample_agent])

        # Register a handler for the builder agent
        def builder_handler(ctx):
            return {"agent": "builder", "task": ctx.user_message}

        orchestrator.register_handler("code", "Development", builder_handler)

        result, memory = orchestrator.orchestrate("Build a function")

        assert result is not None

    def test_multiple_sequential_executions(self):
        """Test multiple sequential executions."""
        orchestrator = create_orchestrator()

        tasks = [
            "Analyze competitor pricing",
            "Design a new API",
            "Fix the login bug",
        ]

        results = []
        for task in tasks:
            result, memory = orchestrator.orchestrate(task)
            results.append(result)

        assert len(results) == 3
        assert all(r is not None for r in results)


# ── Test 11: Edge Cases ────────────────────────────────────────────────

class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_orchestrate_empty_message(self, orchestrator):
        """Test orchestration with empty message."""
        result, memory = orchestrator.orchestrate("")

        # Should still execute (even if not meaningful)
        assert result is not None

    def test_orchestrate_very_long_message(self, orchestrator):
        """Test orchestration with very long message."""
        long_message = "Do this task: " + "X" * 5000

        result, memory = orchestrator.orchestrate(long_message)

        assert result is not None

    def test_execution_context_to_dict(self):
        """Test ExecutionContext serialization."""
        intent = Intent(
            primary_intent="test",
            domain=Domain.CODE,
            subject="function",
        )
        ctx = ExecutionContext(
            execution_id="test-123",
            user_message="test message",
            intent=intent,
            enhanced_instruction="test instruction",
            manifest=AgentManifest(agent_type=AgentType.BUILDER),
            routed_phase="Development",
            allocated_agent=None,
        )

        ctx_dict = ctx.to_dict()

        assert "execution_id" in ctx_dict
        assert "intent" in ctx_dict
        assert "manifest" in ctx_dict
        assert "execution_time_seconds" in ctx_dict


# ── Run Tests ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
