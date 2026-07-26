#!/usr/bin/env python3
"""
Example Usage of ROSTR Orchestrator
====================================

Demonstrates the full orchestration pipeline with custom handlers.
"""

from rostr.orchestrator import create_orchestrator, ExecutionContext
from rostr.hub import AgentRegistration


def main():
    """Run orchestration examples."""

    # ── Example 1: Basic Orchestration ──────────────────────────────────

    print("\n" + "=" * 70)
    print("Example 1: Basic Orchestration")
    print("=" * 70)

    orch = create_orchestrator()

    result, memory = orch.orchestrate(
        "Research the latest advances in quantum computing"
    )

    print(f"\n✓ Result: {str(result)[:100]}...")
    print(f"✓ Memory: {memory}")


    # ── Example 2: Code Task with PAL/NPAO/RAG DAL Flow ─────────────────

    print("\n" + "=" * 70)
    print("Example 2: Full Pipeline - Code Task")
    print("=" * 70)

    orch2 = create_orchestrator()

    result2, memory2 = orch2.orchestrate(
        "Build a Python function to validate email addresses"
    )

    print(f"\n✓ Result: {str(result2)[:150]}...")
    print(f"✓ Memory keys: {list(memory2.keys())}")


    # ── Example 3: Custom Handler Registration ──────────────────────────

    print("\n" + "=" * 70)
    print("Example 3: Custom Handler Registration")
    print("=" * 70)

    def custom_code_handler(context: ExecutionContext) -> dict:
        """Custom handler for code tasks."""
        return {
            "status": "executed",
            "execution_id": context.execution_id,
            "phase": context.routed_phase,
            "intent": context.intent.primary_intent,
            "model_selected": context.manifest.model,
            "retrieval_sources": len(context.retrieved_context),
        }

    orch3 = create_orchestrator()
    orch3.register_handler("code", "Development", custom_code_handler)

    result3, memory3 = orch3.orchestrate(
        "Implement a binary search algorithm in Python"
    )

    print(f"\n✓ Result:")
    for key, value in result3.items():
        print(f"   {key}: {value}")


    # ── Example 4: Pre-Registered Agents ────────────────────────────────

    print("\n" + "=" * 70)
    print("Example 4: Pre-Registered Agents")
    print("=" * 70)

    builder_agent = AgentRegistration(
        name="Senior Python Builder",
        agent_type="builder",
        capabilities=["code_generation", "testing", "documentation"],
        tools=["code_execution", "file_system", "web_search"],
        phases=["Development", "Debugging"],
    )

    researcher_agent = AgentRegistration(
        name="ML Research Specialist",
        agent_type="researcher",
        capabilities=["literature_review", "analysis", "benchmarking"],
        tools=["web_search", "data_analysis"],
        phases=["PreD", "Design"],
    )

    orch4 = create_orchestrator(seed_agents=[builder_agent, researcher_agent])

    print(f"\n✓ Registered {len(orch4.hub.agents)} agents")
    for agent_id, agent in orch4.hub.agents.items():
        print(f"   - {agent.name} ({agent.agent_type}): {agent.capabilities}")

    result4, memory4 = orch4.orchestrate("Build a machine learning classifier")

    print(f"\n✓ Result: {str(result4)[:100]}...")


    # ── Example 5: Execution History & Summary ──────────────────────────

    print("\n" + "=" * 70)
    print("Example 5: Execution History & Introspection")
    print("=" * 70)

    orch5 = create_orchestrator()

    tasks = [
        "Analyze competitor pricing",
        "Design a new API endpoint",
        "Fix the login authentication bug",
    ]

    for task in tasks:
        orch5.orchestrate(task)

    # Get history
    history = orch5.get_execution_history(limit=10)
    print(f"\n✓ Execution history ({len(history)} tasks):")
    for execution in history:
        print(f"   - {execution['execution_id']}: {execution['user_message'][:40]}...")

    # Get summary
    summary = orch5.summary()
    print(f"\n✓ Orchestrator summary:")
    print(f"   - Total executions: {summary['executions_total']}")
    print(f"   - Successful: {summary['executions_successful']}")
    print(f"   - Failed: {summary['executions_failed']}")
    print(f"   - Avg execution time: {summary['avg_execution_time_seconds']:.2f}s")
    print(f"   - Hub snapshot:")
    print(f"      - Decisions: {summary['hub_snapshot']['decisions_count']}")
    print(f"      - Learnings: {summary['hub_snapshot']['learnings_count']}")
    print(f"      - Agents: {summary['hub_snapshot']['agents_registered']}")


    # ── Example 6: Domain-Specific Routing ──────────────────────────────

    print("\n" + "=" * 70)
    print("Example 6: Domain-Specific Routing")
    print("=" * 70)

    orch6 = create_orchestrator()

    # Different domains → different phases
    test_tasks = [
        ("Code task", "Build a Python CLI for file management"),
        ("Research task", "Investigate the history of machine learning"),
        ("Design task", "Design a modern dashboard UI"),
        ("Debug task", "Fix the database connection timeout error"),
        ("Deploy task", "Deploy the new feature to production"),
    ]

    for label, task in test_tasks:
        print(f"\n  {label}: {task}")
        intent, enhanced, manifest, phase = orch6.compile_intent(task)
        npao_result = orch6.route(intent, manifest)
        print(f"    Domain: {intent.domain.value:12} → Phase: {npao_result['phase']:12}")


    # ── Example 7: Hub Knowledge Compounding ────────────────────────────

    print("\n" + "=" * 70)
    print("Example 7: Hub Knowledge Compounding")
    print("=" * 70)

    orch7 = create_orchestrator()

    # Run a few tasks
    for i in range(3):
        orch7.orchestrate(f"Task {i+1}: Some work to do")

    # Get decisions
    decisions = orch7.hub.get_decisions(limit=5)
    print(f"\n✓ Recent decisions ({len(decisions)}):")
    for decision in decisions:
        print(f"   - {decision.decision[:60]}")

    # Get learnings
    learnings = orch7.hub.get_learnings(limit=5)
    print(f"\n✓ Recent learnings ({len(learnings)}):")
    for learning in learnings:
        print(f"   - {learning.insight[:60]}")

    # Compound knowledge
    compound = orch7.hub.compound()
    print(f"\n✓ Knowledge compounding report:")
    print(f"   - Total decisions: {compound['total_decisions']}")
    print(f"   - Total learnings: {compound['total_learnings']}")
    print(f"   - Total agents: {compound['total_agents']}")


    print("\n" + "=" * 70)
    print("✅ All examples completed successfully!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
