---
name: literature-review
description: Conduct comprehensive, systematic literature reviews using multiple academic databases (PubMed, arXiv, bioRxiv, Semantic Scholar, etc.). This skill should be used when conducting systematic literature reviews, meta-analyses, research synthesis, or comprehensive literature searches across biomedical, scientific, and technical domains. Creates professionally formatted markdown documents with verified citations.
allowed-tools: Read Write Edit Bash
license: MIT license
metadata:
    skill-author: K-Dense Inc.
---

# Literature Review

## Overview
Conduct systematic, comprehensive literature reviews following rigorous academic methodology. Search multiple literature databases, synthesize findings thematically, verify all citations for accuracy, and generate professional output documents.

## When to Use This Skill
- Conducting a systematic literature review for research or publication
- Synthesizing current knowledge on a specific topic across multiple sources
- Writing the literature review / related work section of a research paper
- Identifying research gaps and future directions
- Investigating the state of the art in a research domain

## Core Workflow

### Phase 1: Search
1. Define clear research questions and keywords
2. Search multiple databases: Semantic Scholar API, arXiv, PubMed via direct API
3. Use `read_url_content` to fetch paper content from URLs

**Semantic Scholar API:**
```python
import requests
# Search papers
r = requests.get("https://api.semanticscholar.org/graph/v1/paper/search",
    params={"query": "streaming data quality denial constraints", "limit": 20,
            "fields": "title,authors,year,citationCount,abstract,externalIds"})
papers = r.json()["data"]
```

**arXiv API:**
```python
import requests
r = requests.get("http://export.arxiv.org/api/query",
    params={"search_query": "streaming anomaly detection data quality", "max_results": 20})
# Parse XML response
```

### Phase 2: Screen & Synthesize
1. Filter by relevance, year, citation count
2. Group by themes (not study-by-study)
3. Identify consensus, contradictions, and gaps

### Phase 3: Write
Structure: Introduction → Related Work themes → Gaps & Positioning

## Citation Priority
| Age | Threshold | Classification |
|-----|-----------|----------------|
| 0-3 yr | 20+ cit. | Noteworthy |
| 3-7 yr | 100+ cit. | Significant |
| 7+ yr | 500+ cit. | Seminal |

Prioritize: Nature, Science, VLDB, SIGMOD, ICDE, NeurIPS, ICML, KDD for CS/data science topics.
