import requests
import xml.etree.ElementTree as ET
import sys

# Force UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

# ========== 1. METER VLDB 2023 details ==========
print("=" * 60)
print("METER VLDB 2023 — Semantic Scholar")
print("=" * 60)
r = requests.get(
    "https://api.semanticscholar.org/graph/v1/paper/search",
    params={"query": "METER dynamic concept adaptation framework online anomaly detection Zhu Cai Deng Ooi", "limit": 10,
            "fields": "title,authors,year,citationCount,abstract,externalIds,tldr,venue"}
)
data = r.json().get("data", [])
for p in data:
    doi = p.get("externalIds", {}).get("DOI", "N/A")
    print(f"[{p.get('year','?')}] {p.get('citationCount',0)} cit. | {p.get('title','')}")
    print(f"  DOI: {doi}")
    print(f"  Authors: {[a.get('name','') for a in p.get('authors',[])][:8]}")
    print(f"  Venue: {p.get('venue','')}")
    if p.get("abstract"):
        print(f"  Abstract: {p['abstract'][:500]}")
    print()

# ========== 2. WEEVER — all strategies ==========
print("=" * 60)
print("WEEVER — Semantic Scholar (expanded)")
print("=" * 60)
for q in [
    "Weever incremental denial constraint violations",
    "incremental detection denial constraint violations",
    "Kaminsky denial constraint violations",
]:
    r = requests.get(
        "https://api.semanticscholar.org/graph/v1/paper/search",
        params={"query": q, "limit": 10,
                "fields": "title,authors,year,citationCount,abstract,externalIds,venue"}
    )
    data = r.json().get("data", [])
    for p in data:
        doi = p.get("externalIds", {}).get("DOI", "N/A")
        print(f"[{p.get('year','?')}] | {p.get('title','')}")
        print(f"  DOI: {doi}")
        print(f"  Authors: {[a.get('name','') for a in p.get('authors',[])][:5]}")
        print(f"  Venue: {p.get('venue','')}")
        if p.get("abstract"):
            print(f"  Abstract: {p['abstract'][:200]}")
        print()

# ========== 3. WEEVER OpenAlex ==========
print("=" * 60)
print("WEEVER — OpenAlex")
print("=" * 60)
for q in ["Weever denial constraint", "incremental denial constraint violations streaming"]:
    r = requests.get("https://api.openalex.org/works", params={
        "search": q,
        "per-page": 10,
        "select": "title,authorships,publication_year,cited_by_count,doi,primary_location"
    })
    for w in r.json().get("results", []):
        print(f"[{w.get('publication_year','?')}] | {w.get('title','')}")
        print(f"  DOI: {w.get('doi','N/A')}")
        authors = [a.get('author',{}).get('display_name','') for a in w.get('authorships',[])][:5]
        print(f"  Authors: {authors}")
        loc = w.get('primary_location',{})
        print(f"  Venue: {loc.get('source',{}).get('display_name','') if loc else ''}")
        print()

# ========== 4. CrossRef for PVLDB vol 18 no 4 ==========
print("=" * 60)
print("PVLDB Vol.18 — CrossRef browse denial constraint")
print("=" * 60)
r = requests.get("https://api.crossref.org/journals/2150-8097/works", params={
    "query": "denial constraint",
    "rows": 20
})
for item in r.json().get("message", {}).get("items", []):
    title = item.get("title", [""])[0]
    print(f"Title: {title}")
    print(f"DOI: {item.get('DOI','N/A')}")
    authors_list = [f"{a.get('given','')} {a.get('family','')}" for a in item.get('author', [])]
    print(f"Authors: {authors_list}")
    print()

# ========== 5. Try fetching Weever by title ==========
print("=" * 60)
print("PVLDB Vol.18 — CrossRef search Weever")
print("=" * 60)
r = requests.get("https://api.crossref.org/journals/2150-8097/works", params={
    "query": "Weever",
    "rows": 20
})
for item in r.json().get("message", {}).get("items", []):
    title = item.get("title", [""])[0]
    print(f"Title: {title}")
    print(f"DOI: {item.get('DOI','N/A')}")
    authors_list = [f"{a.get('given','')} {a.get('family','')}" for a in item.get('author', [])]
    print(f"Authors: {authors_list}")
    print()

# ========== 6. CrossRef direct DOI attempt ==========
print("=" * 60)
print("PVLDB Vol.18 No.4 — possible Weever DOIs")
print("=" * 60)
# Based on PVLDB article numbering: articles in vol 18 no 4
# Try specific DOIs that could match
test_dois = [
    "10.14778/3715200.3715215",  # typical range
    "10.14778/3715200.3715212",
    "10.14778/3715200.3715213",
]
for doi in test_dois:
    try:
        r = requests.get(f"https://api.crossref.org/works/{doi}", timeout=10)
        if r.status_code == 200:
            msg = r.json().get("message", {})
            title = msg.get("title", ["N/A"])[0]
            print(f"DOI {doi}: FOUND")
            print(f"  Title: {title}")
            authors_list = [f"{a.get('given','')} {a.get('family','')}" for a in msg.get('author', [])]
            print(f"  Authors: {authors_list}")
        else:
            print(f"DOI {doi}: NOT FOUND ({r.status_code})")
    except Exception as e:
        print(f"DOI {doi}: ERROR {e}")
