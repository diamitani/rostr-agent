---
name: task-manager
description: >
  NPAO task lifecycle management. Creates, classifies, and routes tasks using the
  NPAO framework (Necessity → Anxiety → Priority → Opportunity).
triggers:
  - "add task"
  - "create task"
  - "I need to"
  - "I must"
  - "list tasks"
  - "what's on my plate"
---

# Task Manager — NPAO Lifecycle

## CREATE Mode

Trigger: "add task", "I need to", "I must"

1. Extract task title and description from user input
2. Auto-classify with NPAO:
   - **Necessity**: "must", "broken", "blocking", "critical", "urgent"
   - **Anxiety**: "worried", "nagging", "can't stop thinking", "stress"
   - **Priority**: "need", "important", "mission-critical", "roadmap"
   - **Opportunity**: "could", "nice to have", "explore", "growth"
3. Detect phase: Pre-D → Design → Development → Deployment → Debugging
4. Calculate priority score: `(Urgency×0.35) + (Dependencies×0.30) + (Business×0.25) + (Resource×0.10)`
5. Save task: `rostr task add "title"`
6. Confirm classification and score

## LIST Mode

Trigger: "list tasks", "what's on my plate", "show priorities"

1. Fetch all open tasks: `rostr task list`
2. Display in NPAO execution order (N → A → P → O)
3. Highlight blockers and high-priority items

## Execution Rules

- **Score ≥ 7.0**: Execute immediately
- **Score 4.0–6.9**: Queued for next sprint
- **Score < 4.0**: Backlog (execute when bandwidth allows)
- Necessity always executes before anything else, regardless of score
- Clear Anxiety items BEFORE Priority to reduce cognitive load
