---
name: resolver
description: >
  Skill dispatcher for ROSTR Agent Framework. Routes user intent to the correct skill.
  This is the first skill any agent should read. It maps natural language triggers
  to specific skill files and their workflows.
---

# RESOLVER — Skill Dispatcher

## How This Works

When the user says something, match it against the trigger phrases below.
Load the matched skill file and follow its protocol. If no match, use general LLM chat.

## Skill Map

| Trigger Phrases | Skill | File |
|---|---|---|
| "save this session", "cache what we did", "log progress" | ContextEngine (CACHE) | `context-engine/SKILL.md` |
| "context flash", "what did we work on", "catch me up" | ContextEngine (RETRIEVE) | `context-engine/SKILL.md` |
| "generate a report", "progress report", "weekly summary" | ContextEngine (REPORT) | `context-engine/SKILL.md` |
| "search brain", "find in brain", "what do I know about" | Brain Ops (SEARCH) | `brain-ops/SKILL.md` |
| "save this", "remember this", "add to brain" | Brain Ops (WRITE) | `brain-ops/SKILL.md` |
| "add task", "create task", "I need to", "I must" | Task Manager (CREATE) | `task-manager/SKILL.md` |
| "list tasks", "what's on my plate", "show priorities" | Task Manager (LIST) | `task-manager/SKILL.md` |
| "research", "investigate", "look into" | Signal Detector + RAG DAL | `signal-detector/SKILL.md` |

## Priority Rules

1. ContextEngine triggers override everything (session management is critical)
2. Brain Ops before external lookups (brain-first rule)
3. Task Manager for any work-item creation
4. Signal Detector runs in parallel on EVERY message (captures entities/ideas)

## Fallback

If no skill matches, route to general LLM chat with brain context injection.
