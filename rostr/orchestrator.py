"""
ROSTR Orchestrator — The Main Entry Point
==========================================

Wires PAL, NPAO, RAG DAL, and Hub into a unified orchestration engine.

Flow:
  1. User message enters → PAL.compile_intent()
  2. Extract intent, enhance, compile to manifest
  3. NPAO.process() routes to agent
  4. RAG DAL.search() retrieves context
  5. Hub.execute_with_memory() persists state
  6. Return (result, memory_update)

This is the "decision layer that controls Hermes execution."
"""

from dataclasses import dataclass, field
from typing import Optional, Any, Callable
import json
import time
import logging

from rostr.pal import PALCompiler, Intent, AgentManifest, Domain
from rostr.npao import NPAO, PhaseType, AgentSpec
from rostr.ragdal import RAGDAL, KnowledgeEntry, SourceTier, DataType
from rostr.hub import RostrHub, StateLevel, AgentRegistration

logger = logging.getLogger(__name__)


# ── Handler Registry ──────────────────────────────────────────────────
# Maps (AgentType, PhaseType) → callable handler

class HandlerRegistry:
    """Registry of executable handlers for (agent_type, phase) tuples."""

    def __init__(self):
        self.handlers: dict[tuple[str, str], Callable] = {}

    def register(self, agent_type: str, phase: str, handler: Callable):
        """Register a handler for (agent_type, phase)."""
        key = (agent_type, phase)
        self.handlers[key] = handler
        logger.debug(f"Registered handler: {agent_type} × {phase}")

    def get(self, agent_type: str, phase: str) -> Optional[Callable]:
        """Retrieve a handler by (agent_type, phase)."""
        key = (agent_type, phase)
        return self.handlers.get(key)

    def list_all(self) -> dict[tuple[str, str], Callable]:
        """List all registered handlers."""
        return self.handlers.copy()


# ── Execution Context ──────────────────────────────────────────────────

@dataclass
class ExecutionContext:
    """Runtime context for a single orchestration execution."""

    execution_id: str
    user_message: str
    intent: Intent
    enhanced_instruction: str
    manifest: AgentManifest
    routed_phase: str
    allocated_agent: Optional[AgentSpec]
    retrieved_context: list[KnowledgeEntry] = field(default_factory=list)
    execution_start_time: float = field(default_factory=time.time)
    execution_end_time: Optional[float] = None
    result: Any = None
    error: Optional[str] = None
    memory_update: dict = field(default_factory=dict)

    @property
    def execution_time_seconds(self) -> float:
        """Get execution time in seconds."""
        end = self.execution_end_time or time.time()
        return end - self.execution_start_time

    def to_dict(self) -> dict:
        """Serialize execution context to dict."""
        return {
            "execution_id": self.execution_id,
            "user_message": self.user_message,
            "intent": self.intent.to_dict(),
            "enhanced_instruction": self.enhanced_instruction,
            "manifest": self.manifest.to_dict(),
            "routed_phase": self.routed_phase,
            "allocated_agent": self.allocated_agent.agent_id if self.allocated_agent else None,
            "execution_time_seconds": self.execution_time_seconds,
            "error": self.error,
            "memory_update": self.memory_update,
        }


# ── Main Orchestrator ──────────────────────────────────────────────────

class RostrOrchestrator:
    """
    ROSTR Orchestrator — the main decision layer.

    Takes a user message and returns (result, memory_update) by:
      1. Compiling intent via PAL
      2. Routing via NPAO
      3. Retrieving context via RAG DAL
      4. Executing via registered handler
      5. Persisting to Hub
    """

    def __init__(
        self,
        hub: Optional[RostrHub] = None,
        pal_compiler: Optional[PALCompiler] = None,
        npao: Optional[NPAO] = None,
        ragdal: Optional[RAGDAL] = None,
        handler_registry: Optional[HandlerRegistry] = None,
    ):
        """Initialize the orchestrator with components."""
        self.hub = hub or RostrHub()
        self.pal_compiler = pal_compiler or PALCompiler()
        self.npao = npao or NPAO()
        self.ragdal = ragdal or RAGDAL()
        self.handler_registry = handler_registry or HandlerRegistry()
        self.execution_history: list[ExecutionContext] = []

    # ── Step 1: Compile Intent ─────────────────────────────────────────

    def compile_intent(self, user_message: str) -> tuple[Intent, str, AgentManifest, str]:
        """
        Stage 1: PAL Compilation.

        Runs the full five-stage pipeline:
          1. Extract intent
          2. Inject context
          3. Enhance
          4. Compile to manifest
          5. Route to phase
        """
        # Load hub context to inject into PAL
        hub_context = self._load_hub_context()

        # Run PAL pipeline
        intent, enhanced, manifest, phase = self.pal_compiler.compile_intent(
            user_message,
            hub_context=hub_context,
        )

        logger.info(
            f"PAL compiled: domain={intent.domain.value}, phase={phase}, "
            f"ambiguity={intent.ambiguity_score:.2f}"
        )
        return intent, enhanced, manifest, phase

    def _load_hub_context(self) -> Optional[dict]:
        """Load relevant context from the hub."""
        # In production, this would:
        #  - Load project context
        #  - Load org context
        #  - Load recent learnings
        #  - Load agent performance stats
        snapshot = self.hub.snapshot_session()
        return {
            "hub_snapshot": snapshot,
            "recent_learnings": [
                l.insight for l in self.hub.get_learnings(limit=5)
            ],
        }

    # ── Step 2: Route via NPAO ─────────────────────────────────────────

    def route(self, intent: Intent, manifest: AgentManifest) -> dict:
        """
        Stage 2: NPAO Routing.

        Runs the full NPAO pipeline:
          1. Navigate: classify phase
          2. Prioritize: compute 4D score
          3. Allocate: find best agent
          4. Orchestrate: select pattern
        """
        npao_result = self.npao.process(
            task_description=manifest.task_description,
            domain=intent.domain.value,
        )

        logger.info(
            f"NPAO routed: phase={npao_result['phase']}, "
            f"priority={npao_result['priority']['composite']:.1f}, "
            f"status={npao_result['priority']['status']}"
        )

        return npao_result

    # ── Step 3: Retrieve Context ────────────────────────────────────────

    def retrieve_context(self, intent: Intent) -> list[KnowledgeEntry]:
        """
        Stage 3: RAG DAL Retrieval.

        Runs multi-pass retrieval to gather relevant context:
          - Decompose query into sub-topics
          - Pass 1-4: Retrieve, assess coverage
          - Return top-k relevant entries
        """
        # Run multi-pass retrieval
        coverage_report = self.ragdal.multi_pass_retrieve(
            f"{intent.primary_intent} {intent.subject}"
        )

        logger.info(
            f"RAG DAL retrieved: sources={coverage_report.sources_used}, "
            f"passes={coverage_report.passes_completed}, "
            f"complete={coverage_report.is_complete}"
        )

        # Query knowledge base for top-k
        query_terms = f"{intent.primary_intent} {intent.subject}"
        retrieved = self.ragdal.query_knowledge_base(query_terms, top_k=5)

        return retrieved

    # ── Step 4: Execute via Handler ────────────────────────────────────

    def execute(
        self, context: ExecutionContext, handler: Callable
    ) -> tuple[Any, Optional[str]]:
        """
        Stage 4: Execute the task via the registered handler.

        The handler receives the full execution context and produces
        (result, error) where result is the task output.
        """
        try:
            logger.info(
                f"Executing: agent={context.allocated_agent.agent_id if context.allocated_agent else 'none'}, "
                f"phase={context.routed_phase}"
            )

            result = handler(context)

            logger.info(f"Execution succeeded: {context.execution_id}")
            return result, None

        except Exception as e:
            error_msg = f"Execution failed: {str(e)}"
            logger.error(error_msg)
            return None, error_msg

    # ── Step 5: Persist to Hub ─────────────────────────────────────────

    def persist_memory(self, context: ExecutionContext) -> dict:
        """
        Stage 5: Hub Memory Persistence.

        Logs:
          - Decision: task routed to this agent/phase
          - Learning: outcome and insights
          - State: updated context for future calls
        """
        memory_update = {}

        # Log decision: why did we route to this agent?
        if context.allocated_agent:
            decision = self.hub.log_decision(
                context=f"Route task: {context.user_message[:100]}",
                decision=f"Allocate to {context.allocated_agent.name} (phase={context.routed_phase})",
                rationale=f"Phase={context.routed_phase}, priority={context.manifest.to_dict()}",
                alternatives=[],
                namespace=f"execution/{context.execution_id}",
            )
            memory_update["decision_id"] = decision.decision_id

        # Log learning: what did we learn?
        if context.result:
            learning = self.hub.log_learning(
                context=f"Executed: {context.user_message[:100]}",
                insight=f"Successfully executed phase {context.routed_phase}",
                outcome="success" if not context.error else "failure",
                source=context.allocated_agent.agent_id if context.allocated_agent else "unknown",
                tags=["orchestration", context.routed_phase, context.intent.domain.value],
            )
            memory_update["learning_id"] = learning.learning_id

        # Update state
        self.hub.set_state(
            StateLevel.SESSION,
            f"last_execution/{context.execution_id}",
            context.to_dict(),
        )
        memory_update["state_updated"] = True

        logger.info(f"Memory persisted: decision, learning, state updated")

        return memory_update

    # ── Full Orchestration Pipeline ────────────────────────────────────

    def orchestrate(
        self, user_message: str, handler_override: Optional[Callable] = None
    ) -> tuple[Any, dict]:
        """
        Run the full ROSTR orchestration pipeline.

        Args:
            user_message: Raw user input
            handler_override: Optional custom handler (for testing)

        Returns:
            (result, memory_update)
            - result: the task output
            - memory_update: dict of persisted state (decision_id, learning_id, etc)
        """
        import uuid

        execution_id = str(uuid.uuid4())[:8]

        try:
            # Step 1: Compile intent
            intent, enhanced, manifest, phase = self.compile_intent(user_message)

            # Step 2: Route via NPAO
            npao_result = self.route(intent, manifest)

            # Step 3: Retrieve context
            retrieved_context = self.retrieve_context(intent)

            # Step 4: Create execution context
            allocated_agent = None
            if npao_result.get("allocation", {}).get("agent"):
                # Create a stub AgentSpec for the allocated agent
                allocated_agent = AgentSpec(
                    agent_id=npao_result["allocation"]["agent"],
                    name=npao_result["allocation"]["agent_name"],
                    agent_type=intent.domain.value,
                    capabilities=[],
                    tools=manifest.tools_allow,
                    phases=[phase],
                )

            context = ExecutionContext(
                execution_id=execution_id,
                user_message=user_message,
                intent=intent,
                enhanced_instruction=enhanced,
                manifest=manifest,
                routed_phase=phase,
                allocated_agent=allocated_agent,
                retrieved_context=retrieved_context,
            )

            # Step 5: Get handler
            if handler_override:
                handler = handler_override
            else:
                handler = self.handler_registry.get(
                    intent.domain.value, phase
                )

            if not handler:
                # Default handler: return the manifest as the result
                handler = self._default_handler

            # Step 6: Execute
            result, error = self.execute(context, handler)
            context.result = result
            context.error = error
            context.execution_end_time = time.time()

            # Step 7: Persist to hub
            memory_update = self.persist_memory(context)
            context.memory_update = memory_update

            # Log execution
            self.execution_history.append(context)

            logger.info(
                f"Orchestration complete: execution_id={execution_id}, "
                f"time={context.execution_time_seconds:.1f}s"
            )

            return result, memory_update

        except Exception as e:
            logger.error(f"Orchestration failed: {str(e)}")
            return None, {"error": str(e)}

    @staticmethod
    def _default_handler(context: ExecutionContext) -> dict:
        """
        Default handler when no specialized handler is registered.

        Simply returns the compiled manifest and context for inspection.
        """
        return {
            "type": "default",
            "execution_id": context.execution_id,
            "manifest": context.manifest.to_dict(),
            "instruction": context.enhanced_instruction,
            "phase": context.routed_phase,
        }

    # ── Utilities ──────────────────────────────────────────────────────

    def get_execution_history(self, limit: int = 10) -> list[dict]:
        """Get recent executions."""
        return [e.to_dict() for e in self.execution_history[-limit:]]

    def get_execution_by_id(self, execution_id: str) -> Optional[ExecutionContext]:
        """Look up an execution by ID."""
        for e in self.execution_history:
            if e.execution_id == execution_id:
                return e
        return None

    def register_handler(self, agent_type: str, phase: str, handler: Callable):
        """Register a custom handler for (agent_type, phase)."""
        self.handler_registry.register(agent_type, phase, handler)
        logger.info(f"Handler registered: {agent_type} × {phase}")

    def summary(self) -> dict:
        """Generate an orchestrator summary."""
        return {
            "executions_total": len(self.execution_history),
            "executions_successful": sum(
                1 for e in self.execution_history if not e.error
            ),
            "executions_failed": sum(1 for e in self.execution_history if e.error),
            "avg_execution_time_seconds": (
                sum(e.execution_time_seconds for e in self.execution_history)
                / max(len(self.execution_history), 1)
            ),
            "hub_snapshot": self.hub.snapshot_session(),
            "handler_count": len(self.handler_registry.list_all()),
        }


# ── Factory & Builder ──────────────────────────────────────────────────

def create_orchestrator(
    hub_path: str = ".rostr",
    seed_agents: Optional[list[AgentRegistration]] = None,
) -> RostrOrchestrator:
    """
    Factory function to create a fully initialized orchestrator.

    Args:
        hub_path: Path to rostr hub directory
        seed_agents: Optional list of agents to pre-register

    Returns:
        Initialized RostrOrchestrator ready for use
    """
    hub = RostrHub(base_path=hub_path)

    # Register seed agents if provided
    if seed_agents:
        for agent in seed_agents:
            hub.register_agent(agent)

    orchestrator = RostrOrchestrator(hub=hub)

    logger.info(
        f"Orchestrator initialized: {len(hub.agents)} agents registered, "
        f"hub_path={hub_path}"
    )

    return orchestrator
