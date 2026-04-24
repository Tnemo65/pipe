import requests
import xml.etree.ElementTree as ET

# ========== 1. BLEACH — Get full arXiv details ==========
print("=" * 60)
print("BLEACH — arXiv full details")
print("=" * 60)
r = requests.get("http://export.arxiv.org/api/query", params={
    "id_list": "1609.05113",
    "max_results": 1
})
root = ET.fromstring(r.text)
ns = {"atom": "http://www.w3.org/2005/Atom"}
for entry in root.findall("atom:entry", ns):
    print(f"Title: {entry.find('atom:title', ns).text.strip()}")
    print(f"ID: {entry.find('atom:id', ns).text.strip()}")
    authors = [a.text for a in entry.findall("atom:author/atom:name", ns)]
    print(f"Authors: {authors}")
    print(f"Published: {entry.find('atom:published', ns).text}")
    print(f"Summary: {entry.find('atom:summary', ns).text.strip()[:800]}")
    print()

# ========== 2. DyMETER — Get full arXiv details ==========
print("=" * 60)
print("DyMETER (Catching Every Ripple) — arXiv full details")
print("=" * 60)
r = requests.get("http://export.arxiv.org/api/query", params={
    "id_list": "2604.14726",
    "max_results": 1
})
root = ET.fromstring(r.text)
for entry in root.findall("atom:entry", ns):
    print(f"Title: {entry.find('atom:title', ns).text.strip()}")
    print(f"ID: {entry.find('atom:id', ns).text.strip()}")
    authors = [a.text for a in entry.findall("atom:author/atom:name", ns)]
    print(f"Authors: {authors}")
    print(f"Published: {entry.find('atom:published', ns).text}")
    print(f"Summary: {entry.find('atom:summary', ns).text.strip()[:800]}")
    print()

# Also get METER VLDB 2023
print("=" * 60)
print("METER (VLDB 2023) — arXiv full details")
print("=" * 60)
r = requests.get("http://export.arxiv.org/api/query", params={
    "id_list": "2307.08725",
    "max_results": 1
})
root = ET.fromstring(r.text)
for entry in root.findall("atom:entry", ns):
    print(f"Title: {entry.find('atom:title', ns).text.strip()}")
    print(f"ID: {entry.find('atom:id', ns).text.strip()}")
    authors = [a.text for a in entry.findall("atom:author/atom:name", ns)]
    print(f"Authors: {authors}")
    print(f"Published: {entry.find('atom:published', ns).text}")
    print(f"Summary: {entry.find('atom:summary', ns).text.strip()[:500]}")
    print()

# ========== 3. WEEVER — Multiple strategies ==========
print("=" * 60)
print("WEEVER — Semantic Scholar specific search")
print("=" * 60)
r = requests.get(
    "https://api.semanticscholar.org/graph/v1/paper/search",
    params={"query": "Weever incremental detection denial constraint violations Kaminsky", "limit": 15,
            "fields": "title,authors,year,citationCount,abstract,externalIds,tldr,venue"}
)
data = r.json().get("data", [])
for p in data:
    doi = p.get("externalIds", {}).get("DOI", "N/A")
    print(f"[{p.get('year','?')}] | {p.get('title','')[:100]}")
    print(f"  DOI: {doi}")
    print(f"  Authors: {[a.get('name','') for a in p.get('authors',[])][:5]}")
    if p.get("abstract"):
        print(f"  Abstract: {p['abstract'][:200]}...")
    print()

print("=" * 60)
print("WEEVER — OpenAlex search")
print("=" * 60)
r = requests.get("https://api.openalex.org/works", params={
    "search": "Weever denial constraint incremental",
    "per-page": 15,
    "select": "title,authorships,publication_year,cited_by_count,doi,primary_location"
})
for w in r.json().get("results", []):
    doi = w.get("doi","N/A")
    print(f"[{w.get('publication_year','?')}] | {w.get('title','')[:100]}")
    print(f"  DOI: {doi}")
    authors = [a.get('author',{}).get('display_name','') for a in w.get('authorships',[])][:5]
    print(f"  Authors: {authors}")
    loc = w.get('primary_location',{})
    venue = loc.get('source',{}).get('display_name','') if loc else ''
    print(f"  Venue: {venue}")
    print()

# Try CrossRef for Weever by PVLDB vol 18 no 4
print("=" * 60)
print("WEEVER — CrossRef PVLDB vol 18 no 4 search")
print("=" * 60)
r = requests.get("https://api.crossref.org/journals/2150-8097/works", params={
    "query": "Weever denial constraint",
    "rows": 20
})
for item in r.json().get("message", {}).get("items", []):
    title = item.get("title", [""])[0]
    if "weever" in title.lower() or "denial" in title.lower():
        print(f"Title: {title}")
        print(f"DOI: {item.get('DOI','N/A')}")
        authors_list = [f"{a.get('given','')} {a.get('family','')}" for a in item.get('author', [])]
        print(f"Authors: {authors_list}")
        print()

# Also search by Kaminsky
print("=" * 60)
print("WEEVER — CrossRef search by Kaminsky")
print("=" * 60)
r = requests.get("https://api.crossref.org/works", params={
    "query": "Weever denial constraints",
    "rows": 20
})
for item in r.json().get("message", {}).get("items", []):
    print(f"Title: {item.get('title', ['N/A'])[0]}")
    print(f"DOI: {item.get('DOI','N/A')}")
    authors_list = [f"{a.get('given','')} {a.get('family','')}" for a in item.get('author', [])]
    print(f"Authors: {authors_list}")
    print()

print("=" * 60)
print("WEEVER — OpenAlex by Kaminsky")
print("=" * 60)
r = requests.get("https://api.openalex.org/works", params={
    "search": "Kaminsky denial constraint violations",
    "per-page": 15,
    "select": "title,authorships,publication_year,cited_by_count,doi,primary_location"
})
for w in r.json().get("results", []):
    print(f"[{w.get('publication_year','?')}] | {w.get('title','')[:100]}")
    print(f"  DOI: {w.get('doi','N/A')}")
    authors = [a.get('author',{}).get('display_name','') for a in w.get('authorships',[])][:5]
    print(f"  Authors: {authors}")
    print()
