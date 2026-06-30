import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import List

import feedparser
import requests

QUERY = "psilocybin OR psilocin OR psykedelika OR psychedelic OR hallucinogen OR mdma OR ayahuasca OR ketamin"
CURRENT_YEAR = str(datetime.now().year)


@dataclass
class Thesis:
    title: str
    url: str
    source: str
    abstract: str = ""
    date: str = ""
    authors: List[str] = field(default_factory=list)
    institution: str = ""
    level: str = ""


def fetch_diva_theses() -> List[Thesis]:
    results = []
    try:
        feed = feedparser.parse(
            f"https://www.diva-portal.org/smash/export.jsf?format=atom&query={requests.utils.quote(QUERY)}&rows=20"
        )
        for entry in feed.entries:
            date = entry.get("published", "")[:10]
            if not date.startswith(CURRENT_YEAR):
                continue
            results.append(Thesis(
                title=entry.get("title", ""),
                url=entry.get("link", ""),
                source="DiVA",
                date=date,
            ))
    except Exception as e:
        print(f"DiVA thesis error: {e}")
    return results


def fetch_swepub_theses() -> List[Thesis]:
    results = []
    try:
        resp = requests.get(
            "https://swepub.kb.se/api/v1/search",
            params={"query": QUERY, "limit": 20, "format": "json"},
            timeout=15,
        )
        for hit in resp.json().get("hits", {}).get("hits", []):
            src = hit.get("_source", {})
            date = src.get("publication", [{}])[0].get("date", "")
            if not date.startswith(CURRENT_YEAR):
                continue
            authors = [
                p.get("name", "") for p in src.get("instanceOf", {}).get("hasContribution", [])[:3]
                if p.get("name")
            ]
            results.append(Thesis(
                title=src.get("instanceOf", {}).get("hasTitle", [{}])[0].get("mainTitle", ""),
                url=src.get("identifiedBy", [{}])[0].get("value", ""),
                source="SwePub",
                abstract=src.get("instanceOf", {}).get("summary", [{}])[0].get("label", "")[:800],
                date=date,
                authors=authors,
            ))
    except Exception as e:
        print(f"SwePub thesis error: {e}")
    return results


def fetch_all_theses() -> List[Thesis]:
    results = []
    for fetcher in [fetch_diva_theses, fetch_swepub_theses]:
        try:
            results.extend(fetcher())
        except Exception as e:
            print(f"{fetcher.__name__} failed: {e}")
        time.sleep(0.5)
    return [t for t in results if t.url and t.title]
