#!/usr/bin/env python3
"""
Research Aggregator Script
Usage: python aggregate.py "your research topic" [--output-dir research]

Searches the web, extracts articles, catalogs them, and builds long.md
"""

import sys
import os
import json
import csv
import uuid
from datetime import date

# Hermes tools available when run via execute_code
try:
    from hermes_tools import web_search, web_extract, write_file, read_file
    HERMES_MODE = True
except ImportError:
    HERMES_MODE = False
    print("Note: Running outside Hermes. Use execute_code for full functionality.")

# Tier classification (ROSTR RAG DAL)
TIER_1_DOMAINS = [
    'arxiv.org', 'pubmed.ncbi.nlm.nih.gov', 'scholar.google.com',
    '.gov', '.edu', 'doi.org', 'acm.org', 'ieee.org',
    'nature.com', 'science.org', 'pnas.org'
]
TIER_2_DOMAINS = [
    'reuters.com', 'apnews.com', 'bbc.com', 'nytimes.com', 'wsj.com',
    'techcrunch.com', 'wired.com', 'theverge.com',
    'gartner.com', 'mckinsey.com', 'forrester.com'
]

def classify_tier(url: str) -> int:
    """Classify URL into credibility tier (1=academic, 2=editorial, 3=community)"""
    url_lower = url.lower()
    for domain in TIER_1_DOMAINS:
        if domain in url_lower:
            return 1
    for domain in TIER_2_DOMAINS:
        if domain in url_lower:
            return 2
    return 3

def search_and_dedupe(topic: str, limit_per_query: int = 10) -> list:
    """Execute multiple search queries and deduplicate results"""
    queries = [
        topic,
        f"{topic} site:arxiv.org",
        f"{topic} research paper 2025",
        f"{topic} case study production",
        f"{topic} best practices guide",
    ]
    
    all_results = []
    for q in queries:
        try:
            r = web_search(q, limit=limit_per_query)
            all_results.extend(r.get('data', {}).get('web', []))
        except Exception as e:
            print(f"Search failed for '{q}': {e}")
    
    # Deduplicate by URL
    seen = set()
    unique = []
    for r in all_results:
        url = r.get('url', '')
        if url and url not in seen:
            seen.add(url)
            unique.append(r)
    
    return unique

def build_catalog(results: list, topic: str) -> list:
    """Build catalog entries from search results"""
    catalog = []
    for r in results:
        url = r.get('url', '')
        catalog.append({
            'id': str(uuid.uuid4())[:8],
            'title': r.get('title', 'Untitled')[:200],
            'url': url,
            'domain': url.split('/')[2] if '/' in url else 'unknown',
            'tier': classify_tier(url),
            'date_published': '',
            'date_added': str(date.today()),
            'topics': topic,
            'summary': r.get('description', '')[:500],
            'storage_path': '',
            'word_count': 0,
            'status': 'pending'
        })
    return catalog

def extract_and_store(catalog: list, output_dir: str, batch_size: int = 5) -> list:
    """Extract content from URLs and save to storage"""
    storage_dir = os.path.join(output_dir, 'storage')
    os.makedirs(storage_dir, exist_ok=True)
    
    for i in range(0, len(catalog), batch_size):
        batch = catalog[i:i+batch_size]
        urls = [e['url'] for e in batch]
        
        try:
            extracted = web_extract(urls)
            results = extracted.get('results', [])
        except Exception as e:
            print(f"Extraction failed for batch {i//batch_size + 1}: {e}")
            for entry in batch:
                entry['status'] = 'failed'
            continue
        
        for entry, result in zip(batch, results):
            if result.get('error'):
                entry['status'] = 'failed'
                continue
            
            content = result.get('content', '')
            if not content:
                entry['status'] = 'failed'
                continue
            
            # Save to storage
            path = os.path.join(storage_dir, f"{entry['id']}.md")
            file_content = f"""# {entry['title']}

**Source:** {entry['url']}
**Tier:** {entry['tier']}
**Added:** {entry['date_added']}

---

{content}
"""
            write_file(path, file_content)
            
            entry['storage_path'] = path
            entry['word_count'] = len(content.split())
            entry['status'] = 'extracted'
        
        print(f"Processed batch {i//batch_size + 1}/{(len(catalog) + batch_size - 1)//batch_size}")
    
    return catalog

def write_catalog(catalog: list, output_dir: str):
    """Write catalog to CSV and JSON files"""
    csv_path = os.path.join(output_dir, 'catalog.csv')
    json_path = os.path.join(output_dir, 'catalog.json')
    
    # CSV
    if catalog:
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=catalog[0].keys())
            writer.writeheader()
            writer.writerows(catalog)
    
    # JSON
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)
    
    print(f"Catalog written: {csv_path}, {json_path}")

def build_long_md(catalog: list, topic: str, output_dir: str):
    """Build comprehensive long.md file with all transcribed content"""
    extracted = [e for e in catalog if e['status'] == 'extracted']
    if not extracted:
        print("No extracted content to compile")
        return
    
    total_words = sum(e['word_count'] for e in extracted)
    tier_counts = {1: 0, 2: 0, 3: 0}
    for e in extracted:
        tier_counts[e['tier']] += 1
    
    long_md = f"""# Research Compilation: {topic}

**Generated:** {date.today()}
**Total Sources:** {len(extracted)}
**Total Words:** {total_words:,}
**Tier Distribution:** Tier 1: {tier_counts[1]} | Tier 2: {tier_counts[2]} | Tier 3: {tier_counts[3]}

---

## Table of Contents

"""
    
    # Add TOC
    for entry in extracted:
        long_md += f"- [{entry['title']}](#{entry['id']})\n"
    
    long_md += "\n---\n\n"
    
    # Add full content
    for entry in extracted:
        try:
            content_data = read_file(entry['storage_path'])
            content = content_data.get('content', '')
        except Exception:
            content = "[Content extraction failed]"
        
        long_md += f"""
## {entry['title']} {{#{entry['id']}}}

**Tier {entry['tier']} Source** | {entry['word_count']:,} words | [Original]({entry['url']})

{content}

---

"""
    
    long_md_path = os.path.join(output_dir, 'long.md')
    write_file(long_md_path, long_md)
    print(f"long.md written: {len(long_md):,} characters, {total_words:,} words")

def main():
    if len(sys.argv) < 2:
        print("Usage: python aggregate.py 'research topic' [--output-dir research]")
        sys.exit(1)
    
    topic = sys.argv[1]
    output_dir = 'research'
    
    # Parse optional args
    if '--output-dir' in sys.argv:
        idx = sys.argv.index('--output-dir')
        if idx + 1 < len(sys.argv):
            output_dir = sys.argv[idx + 1]
    
    if not HERMES_MODE:
        print("Error: Must run via Hermes execute_code for web tools")
        sys.exit(1)
    
    print(f"Research topic: {topic}")
    print(f"Output directory: {output_dir}")
    print("-" * 40)
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Search
    print("Searching...")
    results = search_and_dedupe(topic)
    print(f"Found {len(results)} unique articles")
    
    # 2. Build catalog
    catalog = build_catalog(results, topic)
    
    # 3. Extract and store
    print("Extracting content...")
    catalog = extract_and_store(catalog, output_dir)
    
    # 4. Write catalog files
    write_catalog(catalog, output_dir)
    
    # 5. Build long.md
    print("Building long.md...")
    build_long_md(catalog, topic, output_dir)
    
    # Summary
    extracted = [e for e in catalog if e['status'] == 'extracted']
    failed = [e for e in catalog if e['status'] == 'failed']
    print("-" * 40)
    print(f"Done!")
    print(f"  Extracted: {len(extracted)}")
    print(f"  Failed: {len(failed)}")
    print(f"  Output: {output_dir}/")

if __name__ == "__main__":
    main()
