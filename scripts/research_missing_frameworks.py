import requests
import xml.etree.ElementTree as ET

# ========== 1. BLEACH ==========
print("=" * 60)
print("1. BLEACH — Semantic Scholar")
print("=" * 60)
queries_bleach = [
    "Bleach distributed stream data cleaning",
    "Bleach FD CFD violation detection streaming",
]
for q in queries_bleach:
    r = requests.get(
        "https://api.semanticscholar.org/graph/v1/paper/search",
        params={"query": q, "limit": 10,
                "fields": "title,authors,year,citationCount,abstract,externalIds,tldr,venue"}
    )
    data = r.json().get("data", [])
    for p in data:
        doi = p.get("externalIds", {}).get("DOI", "N/A")
        print(f"[{p.get('year','?')}] {p.get('citationCount',0)} cit. | {p.get('title','')[:100]}")
        print(f"  DOI: {doi}")
        print(f"  Authors: {[a.get('name','') for a in p.get('authors',[])][:5]}")
        print(f"  Venue: {p.get('venue','')}")
        if p.get("abstract"):
            print(f"  Abstract: {p['abstract'][:300]}...")
        print()

# arXiv search for Bleach
print("--- BLEACH arXiv search ---")
r = requests.get("http://export.arxiv.org/api/query", params={
    "search_query": "all:Bleach stream data cleaning",
    "max_results": 10,
    "sortBy": "relevance"
})
root = ET.fromstring(r.text)
ns = {"atom": "http://www.w3.org/2005/Atom"}
for entry in root.findall("atom:entry", ns):
    print(f"Title: {entry.find('atom:title', ns).text.strip()}")
    print(f"ID: {entry.find('atom:id', ns).text.strip()}")
    print(f"Summary: {entry.find('atom:summary', ns).text.strip()[:300]}")
    print()

# ========== 2. DyMETER ==========
print("=" * 60)
print("2. DyMETER — Semantic Scholar")
print("=" * 60)
queries_dym = [
    "DyMETER dynamic concept adaptation anomaly detection",
    "METER streaming anomaly detection Zhu",
]
for q in queries_dym:
    r = requests.get(
        "https://api.semanticscholar.org/graph/v1/paper/search",
        params={"query": q, "limit": 10,
                "fields": "title,authors,year,citationCount,abstract,externalIds,tldr,venue"}
    )
    data = r.json().get("data", [])
    for p in data:
        doi = p.get("externalIds", {}).get("DOI", "N/A")
        print(f"[{p.get('year','?')}] {p.get('citationCount',0)} cit. | {p.get('title','')[:100]}")
        print(f"  DOI: {doi}")
        print(f"  Authors: {[a.get('name','') for a in p.get('authors',[])][:5]}")
        print(f"  Venue: {p.get('venue','')}")
        if p.get("abstract"):
            print(f"  Abstract: {p['abstract'][:300]}...")
        print()

# arXiv for DyMETER
print("--- DyMETER arXiv search ---")
r = requests.get("http://export.arxiv.org/api/query", params={
    "search_query": "all:DyMETER dynamic threshold anomaly streaming",
    "max_results": 10,
    "sortBy": "relevance"
})
root = ET.fromstring(r.text)
for entry in root.findall("atom:entry", ns):
    print(f"Title: {entry.find('atom:title', ns).text.strip()}")
    print(f"ID: {entry.find('atom:id', ns).text.strip()}")
    print(f"Summary: {entry.find('atom:summary', ns).text.strip()[:300]}")
    print()

# Also try METER
print("--- METER (PVLDB) arXiv search ---")
r = requests.get("http://export.arxiv.org/api/query", params={
    "search_query": "all:METER streaming anomaly detection",
    "max_results": 10,
    "sortBy": "relevance"
})
root = ET.fromstring(r.text)
for entry in root.findall("atom:entry", ns):
    print(f"Title: {entry.find('atom:title', ns).text.strip()}")
    print(f"ID: {entry.find('atom:id', ns).text.strip()}")
    print()

# ========== 3. WEEVER ==========
print("=" * 60)
print("3. WEEVER — Semantic Scholar")
print("=" * 60)
queries_wev = [
    "Weever incremental detection denial constraint violations",
    "Weever Kaminsky Pena Naumann denial constraints",
]
for q in queries_wev:
    r = requests.get(
        "https://api.semanticscholar.org/graph/v1/paper/search",
        params={"query": q, "limit": 10,
                "fields": "title,authors,year,citationCount,abstract,externalIds,tldr,venue"}
    )
    data = r.json().get("data", [])
    for p in data:
        doi = p.get("externalIds", {}).get("DOI", "N/A")
        print(f"[{p.get('year','?')}] {p.get('citationCount',0)} cit. | {p.get('title','')[:100]}")
        print(f"  DOI: {doi}")
        print(f"  Authors: {[a.get('name','') for a in p.get('authors',[])][:5]}")
        print(f"  Venue: {p.get('venue','')}")
        if p.get("abstract"):
            print(f"  Abstract: {p['abstract'][:300]}...")
        print()

# ========== 4. OpenAlex searches ==========
print("=" * 60)
print("4. OpenAlex — BLEACH")
print("=" * 60)
for q in ["Bleach distributed stream data cleaning", "Bleach FD CFD streaming"]:
    r = requests.get("https://api.openalex.org/works", params={
        "search": q,
        "per-page": 10,
        "sort": "cited_by_count:desc",
        "select": "title,authorships,publication_year,cited_by_count,doi,primary_location"
    })
    for w in r.json().get("results", []):
        print(f"[{w.get('publication_year','?')}] {w.get('cited_by_count',0)} cit. | {w.get('title','')[:100]}")
        print(f"  DOI: {w.get('doi','N/A')}")
        authors = [a.get('author',{}).get('display_name','') for a in w.get('authorships',[])][:5]
        print(f"  Authors: {authors}")
        loc = w.get('primary_location',{})
        print(f"  Venue: {loc.get('source',{}).get('display_name','') if loc else ''}")
        print()

print("=" * 60)
print("5. OpenAlex — WEEVER")
print("=" * 60)
for q in ["Weever denial constraint violations", "Kaminsky Pena Naumann denial constraints"]:
    r = requests.get("https://api.openalex.org/works", params={
        "search": q,
        "per-page": 10,
        "sort": "cited_by_count:desc",
        "select": "title,authorships,publication_year,cited_by_count,doi,primary_location"
    })
    for w in r.json().get("results", []):
        print(f"[{w.get('publication_year','?')}] {w.get('cited_by_count',0)} cit. | {w.get('title','')[:100]}")
        print(f"  DOI: {w.get('doi','N/A')}")
        authors = [a.get('author',{}).get('display_name','') for a in w.get('authorships',[])][:5]
        print(f"  Authors: {authors}")
        loc = w.get('primary_location',{})
        print(f"  Venue: {loc.get('source',{}).get('display_name','') if loc else ''}")
        print()

print("=" * 60)
print("6. CrossRef — Weever DOI verification")
print("=" * 60)
# Try the PVLDB volume info
test_dois = [
    "10.14778/3715200.3715215",  # guessed from PVLDB vol 18 no 4
]
for doi in test_dois:
    try:
        r = requests.get(f"https://api.crossref.org/works/{doi}", timeout=10)
        if r.status_code == 200:
            msg = r.json().get("message", {})
            print(f"DOI {doi}: FOUND")
            print(f"  Title: {msg.get('title', ['N/A'])[0]}")
            authors_list = [f"{a.get('given','')} {a.get('family','')}" for a in msg.get('author', [])]
            print(f"  Authors: {authors_list}")
            print(f"  Journal: {msg.get('container-title', ['N/A'])[0]}")
            print(f"  Year: {msg.get('published', {}).get('date-parts', [[None]])[0][0]}")
        else:
            print(f"DOI {doi}: NOT FOUND (status {r.status_code})")
    except Exception as e:
        print(f"DOI {doi}: ERROR {e}")
