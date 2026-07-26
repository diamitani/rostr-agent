# ROSTR Orchestrator

## Overview

The **ROSTR Orchestrator** is the main decision layer that controls Hermes execution. It wires PAL, NPAO, RAG DAL, and Hub into a unified orchestration engine.

**Core Flow:**
```
User Message
    ↓
[1] PAL.compile_intent() — Extract intent, enhance, compile to manifest
    ↓
[2] NPAO.route() — Navigate, Prioritize, Allocate, Orchestrate
    ↓
[3] RAG DAL.retrieve() — Multi-pass knowledge retrieval
    ↓
[4] Handler.execute() — Execute task with registered handler
    ↓
[5] Hub.persist_memory() — Log decision, learning, state
    ↓
(result, memory_update)
```

---

## Architecture

### Five Stages of Orchestration

#### Stage 1: Intent Compilation (PAL)

The **Prompt Abstraction Layer (PAL)** transforms natural language into a typed agent manifest.

```python
from rostr.orchestrator import create_orchestrator

orch = create_orchestrator()

# Internally: PAL compiles to Intent → AgentManifest
intent, enhanced, manifest, phase = orch.compile_intent(
    "Build a Python API for user authentication"
)

# intent.domain = Domain.CODE
# intent.urgency = Urgency.SCHEDULED
# manifest.agent_type = AgentType.BUILDER
# phase = "Development"
```

**PAL Output Manifest:**
```yaml
runtime:
  agent_type: builder
  model: claude-sonnet-4-6
  temperature: 0.2
  max_parallel_tasks: 3
  timeout_seconds: 600

instructions:
  behavior_profile: operational
  task_description: "Build a Python API..."
  completion_criteria:
    - All tests pass
    - Code review approved
    - Documentation updated
  escalation_policy: auto-proceed

tools_enabled:
  allow: [code_execution, file_system:write]
  deny: []

memory:
  mode: project
  context_sources: []
  save_triggers: [decisions, learnings, artifacts]

output:
  format: markdown
  destination: return
  verification: test
```

#### Stage 2: Routing via NPAO

The **Navigate, Prioritize, Allocate, Orchestrate (NPAO)** engine classifies the task and allocates resources.

```python
npao_result = orch.route(intent, manifest)

# Result structure:
{
    "phase": "DEVELOPMENT",  # 5D taxonomy
    "phase_index": 2,
    "criteria": [
        "All features implemented",
        "Test coverage ≥ threshold",
        "Code review passed",
        "No blocking bugs",
        "Documentation updated"
    ],
    "priority": {
        "composite": 6.2,  # 4D priority score
        "status": "queued",
        "breakdown": {
            "phase_urgency": 6.0,
            "dependency_impact": 3.0,
            "business_impact": 7.0,
            "resource_efficiency": 7.0
        }
    },
    "allocation": {
        "agent": "agent-123",
        "agent_name": "Python Builder"
    },
    "orchestration": "sequential"  # or parallel, conditional, aggregate
}
```

**5D Phase Taxonomy:**
- `PreD (0)` — Research: "Is this worth building?"
- `DESIGN (1)` — Plan: "What exactly are we building?"
- `DEVELOPMENT (2)` — Build: "Does it work?"
- `DEPLOYMENT (3)` — Ship: "Is it safe to ship?"
- `DEBUGGING (4)` — Fix: "What broke, why, how do we prevent it?"

**Priority Scoring Formula:**
```
Priority = (Phase_Urgency × 0.35) + (Dependency_Impact × 0.30)
         + (Business_Impact × 0.25) + (Resource_Efficiency × 0.10)

Status:
  ≥ 7.0  → IMMEDIATE
  4.0-6.9 → QUEUED
  < 4.0   → BACKLOG
```

#### Stage 3: Context Retrieval via RAG DAL

The **RAG DAL (Retrieval-Augmented Generation Dynamic Acquisition Layer)** performs multi-pass knowledge retrieval.

```python
retrieved_context = orch.retrieve_context(intent)

# Multi-pass algorithm:
# Pass 1: Broad sweep → decompose into sub-topics → assess coverage
# Pass 2: Gap fill → target low-confidence sub-topics with Tier 1-2 sources
# Pass 3: Deep verification → Tier 1 only for remaining gaps
# Pass 4: (optional) Deep search across all tiers for stubborn gaps

# Result: list[KnowledgeEntry]
# Each entry includes:
#  - content: retrieved text
#  - source_url: URL
#  - source_tier: TIER_1 (1.0), TIER_2 (0.75), TIER_3 (0.40)
#  - confidence: 0.0-1.0 (convergence threshold: 0.8)
#  - topics: ["ml", "classification"]
#  - entities: ["TensorFlow", "PyTorch"]
```

#### Stage 4: Handler Execution

The **Handler Registry** maps (agent_type, phase) → executable handler.

```python
# Register a custom handler
def builder_handler(context: ExecutionContext) -> dict:
    """Custom handler for builders in Development phase."""
    # context.user_message
    # context.intent
    # context.manifest
    # context.routed_phase
    # context.allocated_agent
    # context.retrieved_context
    return {
        "status": "completed",
        "output": "Built the API...",
        "phase": context.routed_phase,
    }

orch.register_handler("code", "Development", builder_handler)

# Execute
result, memory = orch.orchestrate("Build a Python API")
```

#### Stage 5: Memory Persistence via Hub

The **Hub** logs decisions, learnings, and state for knowledge compounding.

```python
# Automatically persisted:
# 1. Decision: "Route task to builder (Development phase)"
# 2. Learning: "Successfully executed phase Development"
# 3. State: Execution context for future reference

memory_update = {
    "decision_id": "dec-abc123",
    "learning_id": "learn-xyz789",
    "state_updated": True,
}

# Retrieve later:
hub = orch.hub
decisions = hub.get_decisions(namespace="execution/*")
learnings = hub.search_learnings("performance")
state = hub.get_state(StateLevel.SESSION, "last_execution/*")
```

---

## Usage Examples

### Example 1: Basic Orchestration

```python
from rostr.orchestrator import create_orchestrator

orch = create_orchestrator()

result, memory = orch.orchestrate(
    "Research the latest advances in quantum computing"
)

print(f"Result: {result}")
print(f"Memory: {memory}")
# Memory contains: decision_id, learning_id, state_updated
```

### Example 2: Custom Handler Registration

```python
def research_handler(context):
    """Custom handler for research tasks."""
    # Access context properties
    intent = context.intent
    manifest = context.manifest
    phase = context.routed_phase
    
    # Perform research
    findings = f"Researched: {context.user_message}"
    
    return {
        "findings": findings,
        "sources": context.retrieved_context,
        "phase": phase,
    }

orch.register_handler("research", "PreD", research_handler)

result, memory = orch.orchestrate(
    "Analyze competitor pricing strategies"
)
```

### Example 3: With Pre-Registered Agents

```python
from rostr.hub import AgentRegistration
from rostr.npao import PhaseType

# Create agents
builder_agent = AgentRegistration(
    name="Python Builder",
    agent_type="builder",
    capabilities=["code_generation", "testing"],
    tools=["code_execution", "file_system"],
    phases=["Development", "Debugging"],
)

# Create orchestrator with agents
orch = create_orchestrator(seed_agents=[builder_agent])

# Register handler
orch.register_handler("code", "Development", my_handler)

# Execute
result, memory = orch.orchestrate("Build a REST API")
```

### Example 4: Execution History & Introspection

```python
# Run multiple tasks
for task in ["Task 1", "Task 2", "Task 3"]:
    orch.orchestrate(task)

# Get execution history
history = orch.get_execution_history(limit=10)
for execution in history:
    print(f"ID: {execution['execution_id']}")
    print(f"Time: {execution['execution_time_seconds']:.2f}s")
    print(f"Error: {execution['error']}")

# Get summary
summary = orch.summary()
print(f"Total executions: {summary['executions_total']}")
print(f"Success rate: {summary['executions_successful']} / {summary['executions_total']}")
print(f"Avg time: {summary['avg_execution_time_seconds']:.2f}s")
```

---

## API Reference

### RostrOrchestrator

#### `__init__`

```python
RostrOrchestrator(
    hub: Optional[RostrHub] = None,
    pal_compiler: Optional[PALCompiler] = None,
    npao: Optional[NPAO] = None,
    ragdal: Optional[RAGDAL] = None,
    handler_registry: Optional[HandlerRegistry] = None,
)
```

#### `compile_intent`

```python
def compile_intent(user_message: str) -> tuple[Intent, str, AgentManifest, str]:
    """
    Stage 1: Compile intent via PAL.
    
    Returns:
        (intent, enhanced_instruction, manifest, routed_phase)
    """
```

#### `route`

```python
def route(intent: Intent, manifest: AgentManifest) -> dict:
    """
    Stage 2: Route via NPAO.
    
    Returns NPAO result: phase, priority, allocation, orchestration.
    """
```

#### `retrieve_context`

```python
def retrieve_context(intent: Intent) -> list[KnowledgeEntry]:
    """
    Stage 3: Retrieve context via RAG DAL.
    
    Returns top-k knowledge entries.
    """
```

#### `execute`

```python
def execute(
    context: ExecutionContext,
    handler: Callable
) -> tuple[Any, Optional[str]]:
    """
    Stage 4: Execute via handler.
    
    Returns (result, error).
    """
```

#### `persist_memory`

```python
def persist_memory(context: ExecutionContext) -> dict:
    """
    Stage 5: Persist to Hub.
    
    Returns memory_update with decision_id, learning_id, state_updated.
    """
```

#### `orchestrate`

```python
def orchestrate(
    user_message: str,
    handler_override: Optional[Callable] = None
) -> tuple[Any, dict]:
    """
    Run full orchestration pipeline.
    
    Args:
        user_message: Raw user input
        handler_override: Optional custom handler (for testing)
    
    Returns (result, memory_update).
    """
```

#### `register_handler`

```python
def register_handler(agent_type: str, phase: str, handler: Callable):
    """Register a custom handler for (agent_type, phase)."""
```

#### `get_execution_history`

```python
def get_execution_history(limit: int = 10) -> list[dict]:
    """Get recent executions."""
```

#### `summary`

```python
def summary() -> dict:
    """Generate orchestrator summary."""
```

### ExecutionContext

```python
@dataclass
class ExecutionContext:
    execution_id: str
    user_message: str
    intent: Intent
    enhanced_instruction: str
    manifest: AgentManifest
    routed_phase: str
    allocated_agent: Optional[AgentSpec]
    retrieved_context: list[KnowledgeEntry]
    execution_start_time: float
    execution_end_time: Optional[float]
    result: Any
    error: Optional[str]
    memory_update: dict
    
    @property
    def execution_time_seconds(self) -> float:
        """Get execution time in seconds."""
```

### HandlerRegistry

```python
class HandlerRegistry:
    def register(agent_type: str, phase: str, handler: Callable):
        """Register a handler."""
    
    def get(agent_type: str, phase: str) -> Optional[Callable]:
        """Retrieve a handler."""
    
    def list_all() -> dict[tuple[str, str], Callable]:
        """List all registered handlers."""
```

---

## Testing

All 49 unit tests pass. Run tests with:

```bash
python3 -m pytest rostr/test_orchestrator.py -v
```

**Test Coverage:**
- ✅ PAL Intent Compilation (7 tests)
- ✅ NPAO Routing & Prioritization (8 tests)
- ✅ RAG DAL Retrieval (7 tests)
- ✅ Hub Memory Persistence (6 tests)
- ✅ Handler Registry & Execution (3 tests)
- ✅ Full Orchestration Pipeline (6 tests)
- ✅ Error Handling (2 tests)
- ✅ Factory Functions (2 tests)
- ✅ Introspection (1 test)
- ✅ Integration Tests (4 tests)
- ✅ Edge Cases (3 tests)

---

## Integration with Hermes

The orchestrator is designed to control Hermes execution. The flow:

1. **User message** comes in via Claude Code CLI
2. **ROSTR Orchestrator** compiles intent, routes, retrieves context
3. **Handler** (registered or custom) calls Hermes with the manifest
4. **Hermes** executes the task (code, research, design, deploy, etc.)
5. **Hub** persists the execution outcome for knowledge compounding

**MCPs to wire in (future):**
- DuckDuckGo web search (RAG DAL retrieval)
- Multi-LLM routing (Claude/GPT/Ollama selector in NPAO)
- File system (read/write skills, workspaces)
- Composio (100+ integrations: HubSpot, Salesforce, Telegram, WhatsApp, iMessage, Signal)

---

## Design Philosophy

ROSTR follows these principles:

1. **Structured Intent** — Natural language → typed manifests
2. **Phase-Aware Routing** — 5D taxonomy, not flat task queues
3. **Multi-Pass Context** — Confidence-based convergence, not single-pass retrieval
4. **Persistent Knowledge** — Decisions and learnings compound across sessions
5. **Testable Components** — Pure functions, dependency injection, composable architecture

---

## Files

- `rostr/orchestrator.py` — Main orchestrator (495 lines)
- `rostr/test_orchestrator.py` — 49 comprehensive tests (650 lines)
- `rostr/pal/__init__.py` — PAL compiler
- `rostr/npao/__init__.py` — NPAO router
- `rostr/ragdal/__init__.py` — RAG DAL retriever
- `rostr/hub/__init__.py` — Hub persistence

---

## Future Enhancements

1. **LLM-Powered Classification** — Replace keyword heuristics with Claude in PAL, NPAO
2. **Persistent Hub** — Store to PostgreSQL, not in-memory
3. **Vector Search** — Embeddings for RAG DAL and Hub learnings
4. **Hermes Integration** — Wire handlers to Hermes runtime
5. **MCP Integrations** — DuckDuckGo, Composio, file system, multi-LLM
6. **Observability** — Tracing, metrics, visualization
7. **Multi-Agent Orchestration** — Fan-out to multiple agents, aggregation
8. **Feedback Loop** — User ratings, learning refinement

---

**Author:** Patrick Diamitani  
**License:** MIT  
**Version:** 1.0.0
