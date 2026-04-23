---
name: context-engine
description: >
  Persistent session memory layer. Use this skill ANY TIME someone wants to:
  save session activity, retrieve past context, generate reports, or search history.
triggers:
  - "save this session"
  - "cache what we did"
  - "context flash"
  - "what did we work on"
  - "generate a report"
  - "progress report"
  - "find when we fixed X"
---

# ContextEngine — Persistent Session Memory

## Modes

### CACHE — Save Session
Trigger: "save this session" / "cache what we did" / "log progress"
1. Review conversation, extract facts
2. Populate session schema (infer; only ask if critically ambiguous)
3. Save via: `rostr context save --summary "what happened"`
4. Confirm: "Session cached. {N} total sessions."

### RETRIEVE — Context Flash
Trigger: "context flash" / "what did we work on" / "catch me up"
1. Load recent sessions: `rostr context flash`
2. Surface: last session summary, what worked, what failed, next steps
3. Lead with recommended starting point (not a history dump)

### REPORT — Progress Report
Trigger: "generate a report" / "progress report" / "weekly summary"
1. Generate via dashboard or API
2. Covers: exec summary, progress, troubleshooting, decisions, next steps

### QUERY — Search History
Trigger: "when did we fix X" / "find sessions tagged Y"
1. Search via: `rostr context search "query"`

## Session Record Fields

- session_id, project, summary, duration_estimate
- tools_used, files_created, files_modified, skills_invoked
- what_worked, what_failed, decisions_made
- open_questions, next_steps, blockers, tags

## Rules

- Never delete session files — append-only
- what_failed: be specific ("HTTP 401 on /api/v1/auth" not "auth issue")
- RETRIEVE leads with action, not history
- Auto-save at session end if user forgets
