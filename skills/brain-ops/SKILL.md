---
name: brain-ops
description: >
  Brain-first knowledge operations. Search, read, write, and enrich the knowledge brain.
  Fire this skill BEFORE any external API call. The brain compounds — every interaction
  should enrich it.
triggers:
  - "search brain"
  - "find in brain"
  - "what do I know about"
  - "save this"
  - "remember this"
  - "add to brain"
---

# Brain Ops — Knowledge Operations

## SEARCH Mode

Trigger: "search brain", "find in brain", "what do I know about X"

1. Run hybrid search: `rostr search "query"`
2. Present top results with snippets
3. If results exist, use them as context for response
4. If no results, tell user "Nothing in brain about X" and offer to research

## WRITE Mode

Trigger: "save this", "remember this", "add to brain"

1. Extract key information from current context
2. Generate a slug from the topic
3. Write page: `rostr put <slug> --title "Title" --content "..."`
4. Auto-link and embed will run in background
5. Confirm: "Saved to brain: [title]"

## READ-ENRICH-WRITE Loop

On every response that references brain knowledge:
1. **Read**: Pull relevant pages
2. **Enrich**: Add new facts/context from current conversation
3. **Write**: Update the page with enriched content

This is how the brain compounds. Never read without considering enrichment.

## Quality Rules

- Slugs: lowercase, hyphenated (`my-topic-name`)
- Tags: always include at least one relevant tag
- Compiled truth: first paragraph should be the key takeaway
- Back-links: reference related pages with `[[slug]]` syntax
