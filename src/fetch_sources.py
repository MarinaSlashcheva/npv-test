import time
from dataclasses import dataclass, field
from typing import List

import feedparser
import requests
from bs4 import BeautifulSoup

KEYWORDS = ["psilocybin", "mdma", "psychedelic", "ketamine", "ayahuasca"]


@dataclass
class Article:
    title: str
    url: str
    source: str
    abstract: str = ""
    date: str = ""
    authors: List[str] = field(default_factory=list)


# --- PubMed ---

def fetch_pubmed() -> List[Article]:
    results = []
    for kw in KEYWORDS[:3]:
        try:
            search = requests.get(
                "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
                params={"db": "pubmed", "term": kw, "retmax": 10, "retmode": "json", "sort": "date"},
                timeout=15,
            )
            ids = search.json().get("esearchresult", {}).get("idlist", [])
            if not ids:
                continue
            fetch = requests.get(
                "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi",
                params={"db": "pubmed", "id": ",".join(ids), "retmode": "json"},
                timeout=15,
            )
            for uid, doc in fetch.json().get("result", {}).items():
                if uid == "uids":
                    continue
                authors = [a.get("name", "") for a in doc.get("authors", [])[:3]]
                results.append(Article(
                    title=doc.get("title", "").rstrip("."),
                    url=f"https://pubmed.ncbi.nlm.nih.gov/{uid}/",
                    source="PubMed",
                    date=doc.get("pubdate", "")[:10],
                    authors=authors,
                ))
        except Exception as e:
            print(f"PubMed error ({kw}): {e}")
        time.sleep(0.4)
    return results


# --- Semantic Scholar ---

def fetch_semantic_scholar() -> List[Article]:
    results = []
    for kw in KEYWORDS[:3]:
        try:
            resp = requests.get(
                "https://api.semanticscholar.org/graph/v1/paper/search",
                params={
                    "query": kw,
                    "limit": 10,
                    "fields": "title,authors,year,externalIds,abstract",
                },
                timeout=15,
            )
            for paper in resp.json().get("data", []):
                doi = (paper.get("externalIds") or {}).get("DOI")
                url = f"https://doi.org/{doi}" if doi else f"https://www.semanticscholar.org/paper/{paper.get('paperId','')}"
                authors = [a.get("name", "") for a in (paper.get("authors") or [])[:3]]
                results.append(Article(
                    title=paper.get("title", ""),
                    url=url,
                    source="Semantic Scholar",
                    abstract=(paper.get("abstract") or "")[:500],
                    date=str(paper.get("year", "")),
                    authors=authors,
                ))
        except Exception as e:
            print(f"Semantic Scholar error ({kw}): {e}")
        time.sleep(0.4)
    return results


# --- Psychedelic Alpha ---

def fetch_psychedelic_alpha() -> List[Article]:
    results = []
    try:
        feed = feedparser.parse("https://psychedelicalpha.com/feed")
        for entry in feed.entries[:10]:
            results.append(Article(
                title=entry.get("title", ""),
                url=entry.get("link", ""),
                source="Psychedelic Alpha",
                date=entry.get("published", "")[:10],
            ))
    except Exception as e:
        print(f"Psychedelic Alpha RSS error: {e}")
        try:
            time.sleep(2)
            resp = requests.get("https://psychedelicalpha.com/", timeout=15)
            soup = BeautifulSoup(resp.text, "lxml")
            for a in soup.select("h2 a, h3 a")[:10]:
                href = a.get("href", "")
                if href.startswith("http"):
                    results.append(Article(title=a.text.strip(), url=href, source="Psychedelic Alpha"))
        except Exception as e2:
            print(f"Psychedelic Alpha scrape error: {e2}")
    return results


# --- DiVA (Swedish academic portal) ---

def fetch_diva() -> List[Article]:
    results = []
    query = "psilocybin OR psilocin OR psykedelika OR psychedelic OR hallucinogen OR mdma OR ayahuasca OR ketamin"
    try:
        feed = feedparser.parse(
            f"https://www.diva-portal.org/smash/export.jsf?format=atom&query={requests.utils.quote(query)}&rows=10"
        )
        for entry in feed.entries[:10]:
            results.append(Article(
                title=entry.get("title", ""),
                url=entry.get("link", ""),
                source="DiVA",
                date=entry.get("published", "")[:10],
            ))
    except Exception as e:
        print(f"DiVA error: {e}")
    return results


# --- SwePub (Swedish publications) ---

def fetch_swepub() -> List[Article]:
    results = []
    query = "psilocybin OR psilocin OR psykedelika OR psychedelic OR hallucinogen OR mdma OR ayahuasca OR ketamin"
    try:
        resp = requests.get(
            "https://swepub.kb.se/api/v1/search",
            params={"query": query, "limit": 10, "format": "json"},
            timeout=15,
        )
        for hit in resp.json().get("hits", {}).get("hits", []):
            src = hit.get("_source", {})
            authors = [
                p.get("name", "") for p in src.get("instanceOf", {}).get("hasContribution", [])[:3]
                if p.get("name")
            ]
            results.append(Article(
                title=src.get("instanceOf", {}).get("hasTitle", [{}])[0].get("mainTitle", ""),
                url=src.get("identifiedBy", [{}])[0].get("value", ""),
                source="SwePub",
                abstract=src.get("instanceOf", {}).get("summary", [{}])[0].get("label", "")[:500],
                date=src.get("publication", [{}])[0].get("date", ""),
                authors=authors,
            ))
    except Exception as e:
        print(f"SwePub error: {e}")
    return results


def fetch_all() -> List[Article]:
    all_articles = []
    for fetcher in [fetch_pubmed, fetch_semantic_scholar, fetch_psychedelic_alpha, fetch_diva, fetch_swepub]:
        try:
            items = fetcher()
            all_articles.extend(items)
        except Exception as e:
            print(f"Fetcher {fetcher.__name__} failed: {e}")
    return [a for a in all_articles if a.url and a.title]
