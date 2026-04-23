# ROSTR Agent Framework — Claude Code Instructions

Read `AGENTS.md` first. This file extends it for Claude Code specifically.

## Auto-Loaded Context

When working in this repo, always:
1. Classify tasks with NPAO before executing (N → A → P → O)
2. Run `rostr context flash` at session start
3. Run `rostr context save` at session end
4. Search brain before external lookups: `rostr search "query"`

## Key Commands

```bash
rostr init              # Initialize brain
rostr serve             # Start gateway + dashboard
rostr chat -i           # Interactive chat
rostr search "query"    # Brain search
rostr task add "title"  # Add NPAO task
rostr context flash     # Load recent context
rostr context save      # Save session
rostr doctor            # Health check
```

## Architecture

```
User → CLI/Dashboard → Gateway → Runtime → PAL → NPAO → LLM → Brain → Response
```

## Skills

Read `skills/RESOLVER.md` for skill routing. Each skill is a markdown file
defining triggers, workflow, and quality checks.
