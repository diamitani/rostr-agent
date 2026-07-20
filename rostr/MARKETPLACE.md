# ROSTR Skills Marketplace

41 production-grade skills for Hermes + ROSTR agents. All generalized, LLM-agnostic, MIT licensed.

## Skills by Category

### GTM & Sales (8 skills)
- **Atlas Agent Factory** — Build multi-agent sales systems. Define roles, capabilities, orchestration.
- **Clay Prospecting Engine** — Prospect automation via Clay. Enrich, personalize, route leads.
- **Atlas GTM Insider** — Newsletter-style GTM reports. Transform data into beautiful HTML emails.
- **GTM Architect** — Design go-to-market strategies. Messaging, positioning, ICP, buyer journey.
- **Atlas Use Case Builder** — Build compelling use cases. ROI, customer outcomes, narratives.
- **JTBD Builder** — Jobs-to-be-Done analysis. Customer jobs, value propositions, messaging.
- **Asana Organizer** — Organize and restructure Asana projects. Clean up, rewrite, rebuild.
- **Atlas Prospect Video Builder** — Personalized prospect videos. Script, animate, deliver at scale.

### Developer Tools (8 skills)
- **PAL Compiler** — ROSTR Prompt Abstraction Layer. Compile natural language to typed manifests.
- **Context Engine** — Persistent memory layer. Session → project → organization → agent state.
- **ROSTR Agent Builder** — Build complete ROSTR systems. PAL, NPAO, RAG DAL, Hub layers.
- **Prompt Rewriter** — Improve LLM prompts. Reduce ambiguity, optimize for model/task.
- **n8n Engineer** — Design complex n8n workflows. Error handling, optimization, monitoring.
- **n8n Workflow Architect** — Large-scale orchestration. Multi-workflow systems, scaling.
- **n8n Execution Analyst** — Monitor workflows. Analyze logs, find failures, optimize.
- **n8n CSV Router** — Route and process CSV data in n8n. Parse, validate, merge, deliver.

### Content & Video (6 skills)
- **Video Editor (HyperFrames)** — Create videos in code. Animations, captions, voiceovers, renders.
- **Atlas Video Studio** — Sales/marketing videos. Scripts, overlays, audio sync, rendering.
- **Atlas Video Render** — Video production and rendering at scale.
- **Case Study Builder** — Create polished case studies. Interview, structure, design, publish.
- **Daily Session Recap** — Auto-generate recaps. Summarize work, decisions, next steps, learnings.
- **Project Instructions Builder** — Comprehensive documentation. Runbooks, how-tos, troubleshooting.

### Data & Analytics (6 skills)
- **HubSpot Data Analyst** — Analyze HubSpot data. Reports, pipeline issues, metrics, forecasts.
- **Dashboard Builder** — Build executive dashboards. SQL, layout design, embed code.
- **Token Spend Analyzer** — Track LLM costs. Analyze by model, task, user. Identify savings.
- **Clay Credit Estimator** — Estimate Clay API costs. Plan budgets, optimize for efficiency.
- **Clay Credit Calculator** — Calculate Clay costs per operation.
- **Clay CSV Enricher** — Enrich CSV data via Clay. Add firmographics, contacts, intelligence.

### Automation & Ops (13+ skills)
- **Workflow Builder** — Design n8n automation. Translate requirements into working flows.
- **Executive Assistant** — AI executive assistant. Email, calendar, notes, task management.
- **File Organizer** — Auto-organize files. Create schemes, restructure, batch rename.
- **Project Closeout Report** — Comprehensive project closure. Scope, achievements, lessons.
- **Project Handoff** — Hand off projects between teams. Document decisions, systems, next steps.
- **New Project System** — Scaffold new projects. Folders, docs, checklists.
- **SaaS Architect** — Design SaaS products. Specs, roadmaps, pricing, go-to-market.
- **Product Builder** — Full product development. Spec, design, build, test, launch.

## Using the Skills

### Local Development

```bash
# Install rostr-agent
pip install rostr-agent

# List all skills
rostr-agent skills list

# Use a skill via CLI
rostr-agent skill invoke atlas-gtm-insider --input "sales data here"

# Or in Python
from rostr import SkillLoader
skill = SkillLoader.load('atlas-gtm-insider')
result = skill.execute(input_data)
```

### Docker

```bash
docker-compose up -d
# Access at http://localhost:3000/skills
```

### AWS

```bash
terraform apply
# Skills available via API at /api/skills/
```

## Skill Structure

Each skill is a self-contained module:

```
skill-name/
├── SKILL.md          # Metadata and system prompt
├── schema.json       # Input/output schemas
├── requirements.txt  # Dependencies
└── tests/           # Test cases
```

### Metadata (SKILL.md)

```yaml
---
name: skill-name
description: What this skill does
category: gtm | dev | content | data | automation | ops
triggers:
  - "when someone says X"
  - "use this when Y"
requirements:
  - anthropic>=0.87
  - pydantic>=2.0
---

# Skill Documentation
You are a system that...
```

### Schemas

```json
{
  "input": {
    "type": "object",
    "properties": {
      "query": {"type": "string"},
      "context": {"type": "object"}
    }
  },
  "output": {
    "type": "object",
    "properties": {
      "result": {"type": "string"},
      "metadata": {"type": "object"}
    }
  }
}
```

## API Integration

Skills are available via REST API:

```bash
# List skills
GET /api/skills

# Execute a skill
POST /api/skills/{skill-id}/execute
{
  "input": {...}
}

# Get skill metadata
GET /api/skills/{skill-id}

# Download skill bundle
GET /api/skills/download?skills=skill1,skill2,skill3
```

## Extending Skills

Create new skills:

```bash
rostr-agent skill create my-skill --category=dev

# This scaffolds:
# my-skill/SKILL.md
# my-skill/schema.json
# my-skill/requirements.txt
# my-skill/tests/test_skill.py
```

Edit the system prompt in `SKILL.md`:

```markdown
---
name: my-skill
description: What my skill does
category: dev
---

# My Custom Skill

You are an expert who...
```

Add requirements:

```
anthropic>=0.87.0
pydantic>=2.0
requests>=2.31
```

Write tests:

```python
def test_skill():
    from my_skill import execute
    result = execute({"input": "test"})
    assert "result" in result
```

Publish:

```bash
rostr-agent skill publish my-skill
```

## Licensing

All skills are MIT licensed. Use freely, modify openly.

```
MIT License

Copyright (c) 2026 Patrick Diamitani

Permission is hereby granted, free of charge, to any person obtaining a copy...
```

## Contributing

Submit new skills via GitHub:

```bash
git clone https://github.com/diamitani/rostr-agent.git
cd rostr-agent
git checkout -b add/my-skill

# Create skill
rostr-agent skill create my-skill

# Test
npm test

# Push and open PR
git push origin add/my-skill
```

## Support

- **GitHub:** https://github.com/diamitani/rostr-agent/issues
- **Email:** patrick.diamitani@gmail.com
- **Paper:** https://zenodo.org/records/19550414
