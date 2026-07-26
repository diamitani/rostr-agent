# DuckDuckGo Web Search Integration for RAG-DAL

## Pattern Overview
DuckDuckGo HTML search provides a free, API-less web search solution for RAG systems. This implementation uses `httpx` + `BeautifulSoup` to scrape DuckDuckGo HTML results, classify sources by credibility tier, and integrate with ROSTR framework.

## When to Use
- Adding web search capabilities to RAG systems without API costs
- Implementing multi-tier source credibility filtering
- Creating research agents that need web information
- Building knowledge acquisition layers for AI agents

## Implementation Pattern

### Core Components
```python
from rostr.ragdal.search import SearchExecutor
from rostr.ragdal.tiers import SourceTierClassifier

# Initialize components
classifier = SourceTierClassifier()
executor = SearchExecutor()

# Search with tier filtering
results = await executor.search(
    query="topic to research",
    max_results=10,
    tier_filter=[SourceTier.PRIMARY, SourceTier.EDITORIAL]
)
```

### DuckDuckGo Search Class
```python
import httpx
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

async def _search_duckduckgo(query: str, max_results: int = 10):
    """Search DuckDuckGo HTML endpoint"""
    encoded_query = quote_plus(query)
    url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; HermesAgent/1.0; +http://rostr.ai)",
                "Accept": "text/html,application/xhtml+xml",
            },
            timeout=30.0
        )
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Parse DuckDuckGo HTML structure
        results = []
        result_elements = soup.find_all('div', class_='result__body')
        
        for element in result_elements[:max_results]:
            title_elem = element.find('a', class_='result__title')
            snippet_elem = element.find('a', class_='result__snippet')
            url_elem = element.find('a', class_='result__url')
            
            if title_elem and url_elem:
                results.append({
                    'title': title_elem.get_text(strip=True),
                    'snippet': snippet_elem.get_text(strip=True) if snippet_elem else '',
                    'url': url_elem.get('href', ''),
                    'raw_html': str(element)
                })
        
        return results
```

### Tier Classification Integration
```python
def classify_source_tier(url: str, title: str = "") -> (SourceTier, float):
    """Classify source by URL patterns and content context"""
    # Primary sources (academic, official)
    primary_patterns = ['.gov', '.edu', 'arxiv.org', 'jstor.org', 'pubmed.org']
    # Editorial sources (news, analysis)
    editorial_patterns = ['reuters.com', 'bbc.com', 'nytimes.com', 'apnews.com']
    
    url_lower = url.lower()
    
    if any(pattern in url_lower for pattern in primary_patterns):
        return SourceTier.PRIMARY, 1.0
    elif any(pattern in url_lower for pattern in editorial_patterns):
        return SourceTier.EDITORIAL, 0.75
    else:
        # Community/other sources
        return SourceTier.COMMUNITY, 0.4
```

### FastAPI Integration Pattern
```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from rostr.ragdal.tiers import SourceTier

router = APIRouter()

class SearchQuery(BaseModel):
    query: str
    max_results: int = 10
    tier_filter: Optional[List[str]] = None
    require_credibility_threshold: float = 0.5

@router.post("/search/query")
async def search_web(search: SearchQuery):
    """Execute web search with tier filtering"""
    executor = SearchExecutor()
    
    # Convert string tiers to enum
    tier_enums = []
    if search.tier_filter:
        for tier_name in search.tier_filter:
            tier_enums.append(SourceTier[tier_name])
    
    results = await executor.search(
        query=search.query,
        max_results=search.max_results,
        tier_filter=tier_enums if tier_enums else None
    )
    
    # Filter by credibility threshold
    filtered_results = [
        r for r in results 
        if r.credibility_score >= search.require_credibility_threshold
    ]
    
    await executor.close()
    return {
        "results": filtered_results,
        "count": len(filtered_results),
        "avg_credibility": sum(r.credibility_score for r in filtered_results) / len(filtered_results) if filtered_results else 0
    }
```

## ROSTR Framework Integration

### Multi-Pass Search Strategy
```python
async def multi_pass_retrieval(query: str, confidence_threshold: float = 0.8):
    """ROSTR-compliant multi-pass retrieval"""
    executor = SearchExecutor()
    
    # Pass 1: Broad sweep across all source tiers
    initial = await executor.search(
        query=query,
        max_results=15,
        tier_filter=[SourceTier.PRIMARY, SourceTier.EDITORIAL, SourceTier.COMMUNITY]
    )
    
    # Analyze topic coverage
    coverage = analyze_coverage(initial)
    
    # Pass 2: Gap fill for low-confidence topics
    if any(coverage[t] < confidence_threshold for t in coverage):
        gap_queries = generate_gap_queries(coverage, confidence_threshold)
        gap_results = []
        for gap_query in gap_queries:
            results = await executor.search(
                query=gap_query,
                max_results=5,
                tier_filter=[SourceTier.PRIMARY, SourceTier.EDITORIAL]
            )
            gap_results.extend(results)
        
        all_results = merge_results(initial, gap_results)
    else:
        all_results = initial
    
    await executor.close()
    return all_results
```

## Pitfalls & Solutions

### 1. DuckDuckGo HTML Structure Changes
**Problem**: DuckDuckGo frequently changes HTML class names and structure.
**Solution**: Use multiple selector patterns and implement robust fallback parsing.

### 2. Rate Limiting
**Problem**: Too many requests get your IP temporarily blocked.
**Solution**: Add delays between requests (2-5 seconds), respect `robots.txt`.

### 3. Source Classification Errors
**Problem**: URL patterns alone may misclassify sources.
**Solution**: Combine URL patterns with content analysis and maintain a curated source database.

### 4. Network Reliability
**Problem**: DuckDuckGo may be unreachable from some regions.
**Solution**: Implement fallback to cached results or alternative search methods.

## Deployment Pattern

### EC2 Deployment Script
```bash
#!/bin/bash
# deploy_web_search.sh - Deploy web search to EC2

# Install dependencies
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv
pip3 install httpx beautifulsoup4 --user

# Configure service
cat > /etc/systemd/system/web-search.service << 'EOF'
[Unit]
Description=Web Search Service for ROSTR Platform
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/6th-agent-platform/backend
ExecStart=/usr/bin/python3 main.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

# Start service
sudo systemctl daemon-reload
sudo systemctl enable web-search.service
sudo systemctl start web-search.service
```

## Verification Checklist
- [ ] DuckDuckGo HTML endpoint accessible
- [ ] httpx and BeautifulSoup installed
- [ ] Tier classification working correctly
- [ ] FastAPI endpoints responding
- [ ] Search results parsed correctly
- [ ] Error handling implemented
- [ ] Deployment script tested

## Performance Tuning
1. **Caching**: Cache search results for common queries (TTL: 1-24 hours)
2. **Parallelism**: Use async/await for concurrent searches
3. **Timeout**: Set appropriate timeouts (10-30 seconds)
4. **Batch Processing**: Process results in batches for large queries

---

*Pattern implemented for 6th Agent Platform, July 2026*