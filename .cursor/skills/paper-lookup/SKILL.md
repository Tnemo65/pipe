---
name: paper-lookup
description: Search and retrieve academic papers from multiple databases including PubMed, arXiv, Semantic Scholar, bioRxiv, medRxiv, OpenAlex, Crossref, and CORE. Use when you need to find specific papers, search by topic/author/DOI, or retrieve paper metadata and abstracts. Returns structured results with titles, authors, abstracts, citations, and DOIs.
allowed-tools: Read Write Bash
license: MIT license
metadata:
    skill-author: K-Dense Inc.
---

# Paper Lookup

## Overview
Search and retrieve academic papers from 10+ databases using direct REST APIs.

## When to Use
- Finding papers by topic, author, keyword, or DOI
- Retrieving abstracts, citation counts, and metadata
- Discovering related work for a research topic
- Verifying if a paper exists and getting its details

## Primary APIs

### Semantic Scholar (RECOMMENDED — 200M+ papers)
```python
import requests

# Search by keyword
def search_semantic_scholar(query, limit=20, fields="title,authors,year,citationCount,abstract,externalIds,tldr"):
    r = requests.get(
        "https://api.semanticscholar.org/graph/v1/paper/search",
        params={"query": query, "limit": limit, "fields": fields}
    )
    return r.json().get("data", [])

# Get paper by DOI
def get_paper(doi, fields="title,authors,year,citationCount,abstract,references,citations"):
    r = requests.get(
        f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}",
        params={"fields": fields}
    )
    return r.json()

# Example usage
papers = search_semantic_scholar("streaming data quality denial constraints", limit=15)
for p in sorted(papers, key=lambda x: x.get("citationCount", 0), reverse=True):
    print(f"{p['year']} [{p['citationCount']} cit.] {p['title']}")
```

### arXiv
```python
import requests
from xml.etree import ElementTree as ET

def search_arxiv(query, max_results=20, category="cs.DB"):
    r = requests.get("http://export.arxiv.org/api/query", params={
        "search_query": f"cat:{category} AND all:{query}",
        "max_results": max_results,
        "sortBy": "relevance"
    })
    root = ET.fromstring(r.text)
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    papers = []
    for entry in root.findall("atom:entry", ns):
        papers.append({
            "title": entry.find("atom:title", ns).text.strip(),
            "abstract": entry.find("atom:summary", ns).text.strip(),
            "url": entry.find("atom:id", ns).text.strip(),
            "authors": [a.find("atom:name", ns).text for a in entry.findall("atom:author", ns)]
        })
    return papers
```

### CrossRef (by DOI)
```python
def lookup_doi(doi):
    r = requests.get(f"https://api.crossref.org/works/{doi}")
    return r.json().get("message", {})
```

### OpenAlex (Free, comprehensive)
```python
def search_openalex(query, limit=20):
    r = requests.get("https://api.openalex.org/works", params={
        "search": query, "per-page": limit,
        "sort": "cited_by_count:desc",
        "select": "title,authorships,publication_year,cited_by_count,abstract_inverted_index,doi"
    })
    return r.json().get("results", [])
```

## Recommended Workflow for Research Context
1. Search Semantic Scholar first (broadest, best metadata)
2. Cross-check arXiv for preprints / recent work
3. Use DOI lookup for specific papers mentioned in other work
4. Sort by citation count to find seminal papers
