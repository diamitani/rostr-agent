# ROSTR Orchestrator — Quick Start Guide

## Installation

```bash
cd /tmp/rostr-agent
python3 -m pip install pytest
```

## Run Tests

```bash
python3 -m pytest rostr/test_orchestrator.py -v

# Result: 49 passed in 0.04s ✅
```

## Run Examples

```bash
cd /tmp/rostr-agent
PYTHONPATH=/tmp/rostr-agent python3 rostr/example_usage.py
```

## 5-Minute Overview

### 1. Create an Orchestrator

```python
from rostr.orchestrator import create_orchestrator

orch = create_orchestrator()
```

### 2. Run a Task

```python
result, memory = orch.orchestrate(
    "Build a Python API for user authentication"
)

print(f"Result: {result}")
print(f"Memory: {memory}")
```

### 3. Register a Custom Handler

```python
def my_handler(context):
    return {
        "status": "completed",
        "phase": context.routed_phase,
    }

orch.register_handler("code", "Development", my_handler)
result, memory = orch.orchestrate("Build an API")
```

### 4. Get Execution History

```python
history = orch.get_execution_history(limit=10)
for exec in history:
    print(f"{exec['execution_id']}: {exec['user_message']}")
```

### 5. Get Summary

```python
summary = orch.summary()
print(f"Total: {summary['executions_total']}")
print(f"Successful: {summary['executions_successful']}")
print(f"Avg time: {summary['avg_execution_time_seconds']:.2f}s")
```

---

## Core Concepts

### 5D Phase Taxonomy

```
PreD         → Research phase (Is this worth building?)
DESIGN       → Planning phase (What to build?)
DEVELOPMENT  → Building phase (Does it work?)
DEPLOYMENT   → Shipping phase (Is it safe?)
DEBUGGING    → Fixing phase (What broke?)
```

### 4D Priority Scoring

```
Score = (Phase_Urgency × 0.35)
      + (Dependency_Impact × 0.30)
      + (Business_Impact × 0.25)
      + (Resource_Efficiency × 0.10)

Status:
  ≥ 7.0   → IMMEDIATE
  4.0-6.9 → QUEUED
  < 4.0   → BACKLOG
```

### Three-Tier Source Credibility

```
Tier 1: 1.0  (arxiv.org, scholar.google.com, .edu, .gov)
Tier 2: 0.75 (reuters.com, techcrunch.com, gartner.com)
Tier 3: 0.40 (blogs, forums, social media)
```

---

## Full Pipeline Flow

```
User Message
    ↓
[1] PAL Compiler
    ├─ Extract intent
    ├─ Enhance semantics
    └─ Compile to manifest
    ↓
[2] NPAO Router
    ├─ Navigate: classify phase
    ├─ Prioritize: 4D score
    ├─ Allocate: find agent
    └─ Orchestrate: select pattern
    ↓
[3] RAG DAL
    ├─ Decompose query
    ├─ Multi-pass retrieval
    └─ Confidence-based convergence
    ↓
[4] Handler Execution
    ├─ Look up (agent_type, phase)
    ├─ Call handler
    └─ Return result
    ↓
[5] Hub Persistence
    ├─ Log decision
    ├─ Log learning
    └─ Update state
    ↓
(result, memory_update)
```

---

## API Quick Reference

### RostrOrchestrator

```python
# Main entry point
orch = create_orchestrator()

# Full orchestration
result, memory = orch.orchestrate(user_message)

# Component methods
intent, enhanced, manifest, phase = orch.compile_intent(msg)
npao_result = orch.route(intent, manifest)
retrieved = orch.retrieve_context(intent)

# Utilities
orch.register_handler(agent_type, phase, handler_fn)
history = orch.get_execution_history(limit=10)
summary = orch.summary()
```

### ExecutionContext (passed to handlers)

```python
context.execution_id          # str
context.user_message          # str
context.intent                # Intent
context.manifest              # AgentManifest
context.routed_phase          # str
context.allocated_agent       # Optional[AgentSpec]
context.retrieved_context     # list[KnowledgeEntry]
context.execution_time_seconds # float (property)
```

### Hub (Persistent Memory)

```python
hub = orch.hub

# Logging
hub.log_decision(context, decision, rationale)
hub.log_learning(context, insight, outcome)

# Retrieval
decisions = hub.get_decisions(namespace="execution/*")
learnings = hub.search_learnings("keyword")

# State
hub.set_state(StateLevel.PROJECT, key, value)
hub.get_state(StateLevel.PROJECT, key)
```

---

## Domains & Their Phases

| Domain | Primary Phase | Agent Type |
|--------|---------------|------------|
| code | DEVELOPMENT | builder |
| research | PreD | researcher |
| design | DESIGN | designer |
| deploy | DEPLOYMENT | deployer |
| debug | DEBUGGING | debugger |
| content | DEVELOPMENT | builder |
| sales | PreD | researcher |
| ops | DEPLOYMENT | deployer |

---

## Example: Register Agent & Handler

```python
from rostr.hub import AgentRegistration

# Create agent
agent = AgentRegistration(
    name="Python Builder",
    agent_type="builder",
    capabilities=["code_generation", "testing"],
    tools=["code_execution", "file_system"],
    phases=["Development", "Debugging"],
)

# Create orchestrator with agent
orch = create_orchestrator(seed_agents=[agent])

# Register handler
def code_handler(context):
    # Custom logic here
    return {"status": "executed"}

orch.register_handler("code", "Development", code_handler)

# Execute
result, memory = orch.orchestrate("Build a function")
```

---

## Example: Batch Processing

```python
orch = create_orchestrator()

tasks = [
    "Task 1: Analyze data",
    "Task 2: Design UI",
    "Task 3: Fix bug",
]

results = []
for task in tasks:
    result, memory = orch.orchestrate(task)
    results.append((result, memory))

# Get summary
summary = orch.summary()
print(f"Processed {summary['executions_total']} tasks")
print(f"Success rate: {summary['executions_successful']} / {summary['executions_total']}")
```

---

## Troubleshooting

### Tests failing?
```bash
python3 -m pip install -q pytest
python3 -m pytest rostr/test_orchestrator.py -v
```

### Module not found?
```bash
export PYTHONPATH=/tmp/rostr-agent
python3 rostr/example_usage.py
```

### Custom handler not called?
```python
# Check handler is registered
orch.handler_registry.list_all()

# Verify (agent_type, phase) match
# The domain must match agent_type
# The routed phase must match phase
```

---

## Key Files

| File | Purpose |
|------|---------|
| `rostr/orchestrator.py` | Main orchestrator (470 lines) |
| `rostr/test_orchestrator.py` | 49 tests (707 lines) |
| `rostr/example_usage.py` | Usage examples (208 lines) |
| `rostr/pal/__init__.py` | Prompt abstraction layer |
| `rostr/npao/__init__.py` | Decision engine |
| `rostr/ragdal/__init__.py` | Knowledge retrieval |
| `rostr/hub/__init__.py` | Persistent memory |
| `ARCHITECTURE.md` | Full architecture doc |
| `rostr/ORCHESTRATOR.md` | API reference |

---

## What's Implemented ✅

- ✅ PAL: Full 5-stage compilation pipeline
- ✅ NPAO: 5D phase taxonomy, 4D priority scoring, agent allocation
- ✅ RAG DAL: Multi-pass retrieval, 3-tier sources, confidence convergence
- ✅ Hub: Decision/learning logging, multi-level state, namespace management
- ✅ Orchestrator: Main entry point wiring all components
- ✅ Handler Registry: Custom handler pattern
- ✅ ExecutionContext: Full context passing to handlers
- ✅ Tests: 49 comprehensive tests (100% passing)
- ✅ Examples: 7 usage demonstrations

---

## What's Next (Hermes Integration)

1. **Register Hermes handler** → Custom handler that calls Hermes
2. **Pass manifest to Hermes** → Include retrieved context
3. **Handle Hermes response** → Extract and return result
4. **Persist to Hub** → Log decisions and learnings
5. **Wire MCPs** → DuckDuckGo, Composio, file system, multi-LLM

---

## Support

- **Tests:** `python3 -m pytest rostr/test_orchestrator.py -v`
- **Examples:** `PYTHONPATH=/tmp/rostr-agent python3 rostr/example_usage.py`
- **Docs:** See `ARCHITECTURE.md` and `rostr/ORCHESTRATOR.md`

---

**Version:** 1.0.0  
**Status:** Production-Ready  
**Tests:** 49/49 passing ✅
