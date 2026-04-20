---
name: research-lookup
description: Look up current research information using Semantic Scholar API, arXiv, OpenAlex, and CrossRef. Use for finding papers, gathering research data, and verifying scientific information. Automatically routes to the best source for your query type.
allowed-tools: Read Write Edit Bash
license: MIT license
metadata:
    skill-author: K-Dense Inc.
---

# Research Lookup

## Overview
Find and retrieve current research papers, verify claims, and gather background information from multiple academic databases.

## When to Use
- Finding papers by topic, author, keyword, or DOI
- Verifying scientific claims against literature
- Gathering context for scientific writing
- Finding recent developments in a research area

## Primary Search Methods

### 1. Semantic Scholar (DEFAULT — 200M+ papers)
```python
import requests

def search_papers(query, limit=20):
    r = requests.get(
        "https://api.semanticscholar.org/graph/v1/paper/search",
        params={
            "query": query,
            "limit": limit,
            "fields": "title,authors,year,citationCount,abstract,externalIds,tldr"
        }
    )
    papers = r.json().get("data", [])
    # Sort by citation count
    return sorted(papers, key=lambda x: x.get("citationCount", 0), reverse=True)

# Example
papers = search_papers("streaming anomaly detection denial constraints", limit=15)
for p in papers[:5]:
    doi = p.get("externalIds", {}).get("DOI", "N/A")
    print(f"[{p['year']}] {p['citationCount']} cit. | {p['title'][:80]}")
    print(f"  DOI: {doi}")
    if p.get("tldr"):
        print(f"  TL;DR: {p['tldr']['text'][:200]}")
    print()
```

### 2. arXiv (CS, Physics, Math preprints)
```python
import requests
from xml.etree import ElementTree as ET

def search_arxiv(query, max_results=15, category="cs.DB"):
    """Categories: cs.DB, cs.LG, cs.IR, cs.AI, stat.ML"""
    r = requests.get("http://export.arxiv.org/api/query", params={
        "search_query": f"cat:{category} AND all:{query}",
        "max_results": max_results,
        "sortBy": "relevance"
    })
    root = ET.fromstring(r.text)
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    for entry in root.findall("atom:entry", ns):
        print(entry.find("atom:title", ns).text.strip())
        print(entry.find("atom:id", ns).text.strip())
        print()
```

### 3. OpenAlex (Free, no auth needed)
```python
def search_openalex(query, limit=20, sort="cited_by_count:desc"):
    r = requests.get("https://api.openalex.org/works", params={
        "search": query,
        "per-page": limit,
        "sort": sort,
        "filter": "type:article",
        "select": "title,authorships,publication_year,cited_by_count,doi,abstract_inverted_index"
    })
    return r.json().get("results", [])
```

### 4. CrossRef (DOI resolution)
```python
def get_by_doi(doi):
    r = requests.get(f"https://api.crossref.org/works/{doi}")
    msg = r.json().get("message", {})
    return {
        "title": msg.get("title", [""])[0],
        "authors": [f"{a.get('given','')} {a.get('family','')}" for a in msg.get("author", [])],
        "year": msg.get("published", {}).get("date-parts", [[None]])[0][0],
        "journal": msg.get("container-title", [""])[0],
        "doi": doi
    }
```

## Usage Pattern for Research Context

```python
# Quick search for streaming data quality papers
queries = [
    "streaming data quality online anomaly detection",
    "denial constraints data streams sliding window",
    "KD-Tree streaming spatial indexing"
]

all_papers = []
for q in queries:
    papers = search_papers(q, limit=10)
    all_papers.extend(papers)

# Deduplicate by DOI
seen = set()
unique = []
for p in all_papers:
    doi = p.get("externalIds", {}).get("DOI", "")
    if doi and doi not in seen:
        seen.add(doi)
        unique.append(p)

# Top 10 by citation
top = sorted(unique, key=lambda x: x.get("citationCount", 0), reverse=True)[:10]
```

## Quality Thresholds
| Age | Min Citations | Classification |
|-----|---------------|----------------|
| 0-3 yr | 20+ | Noteworthy |
| 3-7 yr | 100+ | Significant |
| 7+ yr | 500+ | Seminal |

Always prioritize: VLDB, SIGMOD, ICDE, PVLDB, NeurIPS, ICML, KDD for CS/data topics.
