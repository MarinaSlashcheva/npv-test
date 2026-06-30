import json
import os
import time
from typing import List

import anthropic

from fetch_theses import Thesis

MODEL = "claude-haiku-4-5-20251001"
MAX_RESULTS = 5
client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def _score_thesis(thesis: Thesis) -> tuple[bool, float]:
    text = f"Title: {thesis.title}\nInstitution: {thesis.institution}\nLevel: {thesis.level}\nAbstract: {thesis.abstract[:1200]}"
    prompt = f"""You are a scientific editor for NPV (Nätverket för Psykedelisk Vetenskap).

Assess whether this Swedish thesis is relevant for our monitoring feed.

INCLUDE: Bachelor, master, or licentiate theses on psychedelics, psychedelic-assisted therapy, or related neuroscience/psychiatry.
EXCLUDE: Doctoral dissertations (too specialized), theses only tangentially related to psychedelics.

Thesis:
{text}

Respond with JSON only:
{{"relevant": true/false, "score": 1-5, "reason": "brief reason"}}"""

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
        print(f"Thesis filter error for '{thesis.title}': {e}")
        return False, 0.0


def process_theses(theses: List[Thesis]) -> List[dict]:
    scored = []
    for thesis in theses:
        relevant, score = _score_thesis(thesis)
        time.sleep(0.5)
        if relevant:
            scored.append((score, thesis))

    scored.sort(reverse=True, key=lambda x: x[0])
    return [
        {
            "title": t.title,
            "url": t.url,
            "source": t.source,
            "date": t.date,
            "authors": t.authors,
            "institution": t.institution,
            "level": t.level,
            "score": s,
        }
        for s, t in scored[:MAX_RESULTS]
    ]
