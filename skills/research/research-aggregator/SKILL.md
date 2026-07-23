---
name: research-aggregator
description: >-
  Autonomous research aggregator: web search → find articles → catalog to spreadsheet
  with download links → sync to storage → maintain long.md with transcribed content.
  Handles thousands of pages of accumulated research.
version: 1.0.0
author: Pat
triggers:
  - research aggregator
  - article collector
  - research to spreadsheet
  - build knowledge base
  - aggregate research
  - collect articles
  - research catalog
  - transcribe sources
  - long form research
tools:
  - web_search
  - web_extract
  - write_file
  - read_file
  - execute_code
  - terminal
  - search_files
---

# Research Aggregator

Autonomous research collection pipeline: search → extract → catalog → store → transcribe.

Use this skill when you need to:
- Search the web for articles on a topic
- Catalog results in a spreadsheet with metadata
- Download/sync content to local storage
- Maintain a comprehensive `long.md` file with transcribed content (can grow to thousands of pages)

---

## 1. Pipeline Overview

```
Query → Web Search → Extract Articles → Catalog (CSV/JSON) → Storage Sync → long.md Update
```

### Output Artifacts

| Artifact | Purpose | Format |
|----------|---------|--------|
| `catalog.csv` | Searchable index of all sources | CSV spreadsheet |
| `catalog.json` | Machine-readable catalog | JSON |
| `storage/` | Downloaded article content | Markdown files |
| `long.md` | Complete transcribed content | Single markdown file |

---

## 2. Catalog Schema (Spreadsheet)

```csv
id,title,url,domain,tier,date_published,date_added,topics,summary,storage_path,word_count,status
uuid,Article Title,https://...,arxiv.org,1,2025-07-01,2025-07-23,"ai,llm,research",3-sentence summary,storage/uuid.md,2500,transcribed
```

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unique identifier |
| `title` | String | Article title |
| `url` | URL | Source URL |
| `domain` | String | Source domain |
| `tier` | 1/2/3 | Credibility tier (RAG DAL) |
| `date_published` | ISO Date | When published |
| `date_added` | ISO Date | When added to catalog |
| `topics` | Comma-sep | Topic tags |
| `summary` | String | 3-5 sentence summary |
| `storage_path` | Path | Local file path |
| `word_count` | Int | Content length |
| `status` | Enum | `pending|extracted|transcribed|failed` |

---

## 3. Execution Workflow

### Step 1: Initialize Research Session

```bash
mkdir -p research/{storage,exports}
touch research/catalog.csv research/catalog.json research/long.md
```

### Step 2: Web Search Phase

```python
from hermes_tools import web_search

queries = [
    "topic name",
    "topic site:arxiv.org",
    "topic research paper 2025",
    "topic case study",
]

all_results = []
for q in queries:
    r = web_search(q, limit=10)
    all_results.extend(r.get('data', {}).get('web', []))

# Dedupe by URL
seen = set()
unique = [r for r in all_results if r['url'] not in seen and not seen.add(r['url'])]
```

### Step 3: Extract and Catalog

```python
from hermes_tools import web_extract
import uuid
from datetime import date

TIER_1 = ['arxiv.org', 'pubmed', '.gov', '.edu', 'acm.org', 'ieee.org', 'nature.com']
TIER_2 = ['techcrunch.com', 'wired.com', 'reuters.com', 'bbc.com', 'nytimes.com']

def classify_tier(url):
    url_lower = url.lower()
    if any(d in url_lower for d in TIER_1): return 1
    if any(d in url_lower for d in TIER_2): return 2
    return 3

catalog = []
for r in unique:
    catalog.append({
        'id': str(uuid.uuid4())[:8],
        'title': r.get('title', 'Untitled'),
        'url': r['url'],
        'domain': r['url'].split('/')[2],
        'tier': classify_tier(r['url']),
        'date_added': str(date.today()),
        'status': 'pending'
    })
```

### Step 4: Extract Content to Storage

```python
for i in range(0, len(catalog), 5):
    batch = catalog[i:i+5]
    urls = [e['url'] for e in batch]
    extracted = web_extract(urls)
    
    for entry, result in zip(batch, extracted.get('results', [])):
        if result.get('error'):
            entry['status'] = 'failed'
            continue
        
        content = result.get('content', '')
        path = f"research/storage/{entry['id']}.md"
        write_file(path, f"# {entry['title']}\n\nSource: {entry['url']}\n\n---\n\n{content}")
        
        entry['storage_path'] = path
        entry['word_count'] = len(content.split())
        entry['status'] = 'extracted'
```

### Step 5: Build long.md

```python
extracted = [e for e in catalog if e['status'] == 'extracted']
total_words = sum(e['word_count'] for e in extracted)

long_md = f"""# Research: {TOPIC}

Generated: {date.today()}
Sources: {len(extracted)} | Words: {total_words:,}

---

## Table of Contents

"""
for e in extracted:
    long_md += f"- [{e['title']}](#{e['id']})\n"

long_md += "\n---\n\n"

for e in extracted:
    content = read_file(e['storage_path'])['content']
    long_md += f"## {e['title']} {{#{e['id']}}}\n\nTier {e['tier']} | {e['word_count']} words\n\n{content}\n\n---\n\n"

write_file('research/long.md', long_md)
```

---

## 4. Incremental Updates

```python
# Load existing
with open('research/catalog.json') as f:
    existing = json.load(f)
existing_urls = {e['url'] for e in existing}

# Search for new
new_results = [r for r in search_results if r['url'] not in existing_urls]

# Append to catalog and long.md
existing.extend(new_entries)
```

---

## 5. Storage Sync Options

**Local:** `research/storage/*.md`

**S3/R2:** `aws s3 sync research/ s3://bucket/research/`

**Git:** `cd research && git add . && git commit -m "Update"`

---

## 6. Handling Thousands of Pages

When `long.md` grows large, split by chapters:

```python
MAX_CHARS = 500_000  # ~100 pages per file
chapters = []
current = ""
for entry in catalog:
    content = read_file(entry['storage_path'])['content']
    if len(current) + len(content) > MAX_CHARS:
        chapters.append(current)
        current = ""
    current += f"\n\n## {entry['title']}\n\n{content}"
chapters.append(current)

for i, chapter in enumerate(chapters):
    write_file(f"research/long_part_{i+1}.md", chapter)
```

---

## 7. Quick Reference

```
Directory:     research/
Catalog:       catalog.csv, catalog.json
Content:       storage/*.md
Compiled:      long.md (or long_part_*.md for large)

Workflow:      Search → Extract → Catalog → Store → long.md
Incremental:   Load existing → Filter new → Append
```

---

## 8. Integration with RAG DAL

1. **RAG DAL** — Multi-pass retrieval with credibility scoring (in-session)
2. **Research Aggregator** — Persistent catalog + storage (cross-session)

Export RAG DAL results to catalog for future reference.
