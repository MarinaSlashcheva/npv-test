import hashlib
import json
import os
from datetime import datetime, timezone

_BASE = os.path.join(os.path.dirname(__file__), "..", "data")


def _path(filename):
    return os.path.join(_BASE, filename)


def _load(filename):
    try:
        with open(_path(filename)) as f:
            data = json.load(f)
            return set(data.get("seen", []))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()


def _save(filename, seen_set):
    data = {
        "seen": sorted(seen_set),
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }
    with open(_path(filename), "w") as f:
        json.dump(data, f, indent=2)


def _hash(url):
    return "sha256:" + hashlib.sha256(url.strip().encode()).hexdigest()


class SeenStore:
    def __init__(self, filename):
        self.filename = filename
        self._seen = _load(filename)

    def is_seen(self, url):
        return _hash(url) in self._seen

    def mark_seen(self, url):
        self._seen.add(_hash(url))
        _save(self.filename, self._seen)


articles_store = SeenStore("seen.json")
theses_store = SeenStore("seen_theses.json")
