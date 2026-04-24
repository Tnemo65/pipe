import requests
import xml.etree.ElementTree as ET
import sys

sys.stdout.reconfigure(encoding='utf-8')

# ========== 1. WEEVER — Full details via DOI ==========
print("=" * 60)
print("WEEVER — Full DOI details via CrossRef")
print("=" * 60)
r = requests.get("https://api.crossref.org/works/10.14778/3717755.3717761", timeout=15)
if r.status_code == 200:
    msg = r.json().get("message", {})
    print(f"Title: {msg.get('title', ['N/A'])[0]}")
    print(f"DOI: 10.14778/3717755.3717761")
    authors_list = [f"{a.get('given','')} {a.get('family','')}" for a in msg.get('author', [])]
    print(f"Authors: {authors_list}")
    print(f"Journal: {msg.get('container-title', ['N/A'])[0]}")
    print(f"Volume: {msg.get('volume', 'N/A')}")
    print(f"Issue: {msg.get('issue', 'N/A')}")
    year = msg.get('published', {}).get('date-parts', [[None]])[0][0]
    print(f"Year: {year}")
    print(f"Pages: {msg.get('page', 'N/A')}")
    print(f"Type: {msg.get('type', 'N/A')}")
    print(f"Abstract: {msg.get('abstract', 'N/A')[:500]}")
else:
    print(f"CrossRef error: {r.status_code}")

print()

# ========== 2. DyMETER — get DOI ==========
print("=" * 60)
print("DyMETER — Semantic Scholar for DOI")
print("=" * 60)
r = requests.get(
    "https://api.semanticscholar.org/graph/v1/paper/search",
    params={"query": "Catching Every Ripple Dynamic Concept Adaptation DyMETER Jiaqi Zhu", "limit": 5,
            "fields": "title,authors,year,citationCount,abstract,externalIds,venue"}
)
data = r.json().get("data", [])
for p in data:
    doi = p.get("externalIds", {}).get("DOI", "N/A")
    arxid = p.get("externalIds", {}).get("ArXiv", "N/A")
    print(f"[{p.get('year','?')}] | {p.get('title','')}")
    print(f"  DOI: {doi}")
    print(f"  arXiv: {arxid}")
    print(f"  Authors: {[a.get('name','') for a in p.get('authors',[])][:8]}")
    print(f"  Venue: {p.get('venue','')}")
    if p.get("abstract"):
        print(f"  Abstract: {p['abstract'][:400]}")
    print()

# Also check CrossRef for DyMETER
print("--- DyMETER CrossRef ---")
r = requests.get("https://api.crossref.org/works", params={"query": "DyMETER dynamic concept adaptation", "rows": 10})
for item in r.json().get("message", {}).get("items", []):
    title = item.get("title", [""])[0]
    doi = item.get("DOI", "N/A")
    authors_list = [f"{a.get('given','')} {a.get('family','')}" for a in item.get('author', [])]
    year = item.get('published', {}).get('date-parts', [[None]])[0][0]
    print(f"Title: {title}")
    print(f"DOI: {doi}")
    print(f"Authors: {authors_list}")
    print(f"Year: {year}")
    print()

# ========== 3. METER VLDB 2023 — get DOI ==========
print("=" * 60)
print("METER VLDB 2023 — Semantic Scholar")
print("=" * 60)
r = requests.get(
    "https://api.semanticscholar.org/graph/v1/paper/search",
    params={"query": "METER dynamic concept adaptation online anomaly detection Zhu Cai Deng Ooi PVLDB", "limit": 5,
            "fields": "title,authors,year,citationCount,abstract,externalIds,venue"}
)
data = r.json().get("data", [])
for p in data:
    doi = p.get("externalIds", {}).get("DOI", "N/A")
    arxid = p.get("externalIds", {}).get("ArXiv", "N/A")
    print(f"[{p.get('year','?')}] | {p.get('title','')}")
    print(f"  DOI: {doi}")
    print(f"  arXiv: {arxid}")
    print(f"  Authors: {[a.get('name','') for a in p.get('authors',[])][:8]}")
    print(f"  Venue: {p.get('venue','')}")
    if p.get("abstract"):
        print(f"  Abstract: {p['abstract'][:400]}")
    print()

# ========== 4. BLEACH — CrossRef check ==========
print("=" * 60)
print("BLEACH — CrossRef / Semantic Scholar for DOI")
print("=" * 60)
r = requests.get(
    "https://api.semanticscholar.org/graph/v1/paper/search",
    params={"query": "Bleach distributed stream data cleaning Tian Michiardi Vukolic ICWS 2016", "limit": 5,
            "fields": "title,authors,year,citationCount,abstract,externalIds,venue"}
)
data = r.json().get("data", [])
for p in data:
    doi = p.get("externalIds", {}).get("DOI", "N/A")
    arxid = p.get("externalIds", {}).get("ArXiv", "N/A")
    print(f"[{p.get('year','?')}] | {p.get('title','')}")
    print(f"  DOI: {doi}")
    print(f"  arXiv: {arxid}")
    print(f"  Authors: {[a.get('name','') for a in p.get('authors',[])][:5]}")
    print(f"  Venue: {p.get('venue','')}")
    if p.get("abstract"):
        print(f"  Abstract: {p['abstract'][:300]}")
    print()
