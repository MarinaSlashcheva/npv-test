import json
import time
import os
from typing import List

import anthropic

from fetch_sources import Article

MODEL = "claude-haiku-4-5-20251001"
MAX_RESULTS = 5
client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def _is_relevant(article: Article) -> tuple[bool, float]:
    text = f"Title: {article.title}\nSource: {article.source}\nAbstract: {article.abstract[:1500]}"
    prompt = f"""You are a scientific editor for NPV (Nätverket för Psykedelisk Vetenskap), a Swedish psychedelic-science association.

Assess whether the following article is relevant to include in our research monitoring feed.

INCLUDE if it covers: peer-reviewed research on psychedelics, MDMA, ketamine, psilocybin, ayahuasca, or psychedelic-assisted therapy; credible science news about these topics.
EXCLUDE if it is: speculation, promotional content, crime reporting, unrelated to psychedelics, or lacks scientific substance.

Article:
{text}

Respond with JSON only:
{{"relevant": true/false, "score": 0.0-1.0, "reason": "brief reason"}}"""

    try:
        resp = client.messages.create(
            model=MODEL,
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = resp.content[0].text.strip().removeprefix("```json").removesuffix("```").strip()
        data = json.loads(raw)
        return data.get("relevant", False), float(data.get("score", 0))
    except Exception as e:
        print(f"Filter error for '{article.title}': {e}")
        return False, 0.0


def _summarize(article: Article) -> dict:
    text = f"Title: {article.title}\nSource: {article.source}\nAbstract: {article.abstract[:1500]}"
    prompt = f"""You are a scientific communicator writing for NPV (Nätverket för Psykedelisk Vetenskap).

Write concise summaries of this article in two languages. Use a neutral, scientific tone. Max 3 sentences each.

Article:
{text}

Respond with JSON only:
{{
  "en": "English summary here",
  "ru": "Russian summary here (in Cyrillic script)"
}}"""

    try:
        resp = client.messages.create(
            model=MODEL,
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = resp.content[0].text.strip().removeprefix("```json").removesuffix("```").strip()
        return json.loads(raw)
    except Exception as e:
        print(f"Summarize error for '{article.title}': {e}")
        return {"en": article.abstract[:300], "ru": ""}


def process_articles(articles: List[Article]) -> List[dict]:
    scored = []
    for article in articles:
        relevant, score = _is_relevant(article)
        time.sleep(0.5)
        if relevant:
            scored.append((score, article))

    scored.sort(reverse=True, key=lambda x: x[0])
    results = []
    for score, article in scored[:MAX_RESULTS]:
        summaries = _summarize(article)
        time.sleep(0.5)
        results.append({
            "title": article.title,
            "url": article.url,
            "source": article.source,
            "date": article.date,
            "authors": article.authors,
            "score": score,
            "summaries": summaries,
        })
    return results
