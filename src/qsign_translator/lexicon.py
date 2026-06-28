from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True)
class LexiconEntry:
    token: str
    gloss: str
    language: str
    source: str
    confidence: float
    clip_id: str | None = None


class Lexicon:
    def __init__(self, entries: list[LexiconEntry]) -> None:
        self._entries = {(entry.language, entry.token): entry for entry in entries}

    def lookup(self, token: str, language: str) -> LexiconEntry | None:
        """Return a strictly language-scoped lexicon match.

        We intentionally avoid cross-language fallback here. Language scoping is
        already handled by the planner; falling across languages can silently map
        unrelated tokens and hide coverage gaps.
        """

        return self._entries.get((language, token))

    def export_entries(self, language: str | None = None) -> list[dict[str, object]]:
        items = []
        for entry in self._entries.values():
            if language and entry.language != language:
                continue
            items.append(
                {
                    "token": entry.token,
                    "gloss": entry.gloss,
                    "language": entry.language,
                    "source": entry.source,
                    "confidence": entry.confidence,
                    "clip_id": entry.clip_id,
                }
            )
        items.sort(key=lambda item: (str(item["language"]), str(item["token"])))
        return items


@lru_cache(maxsize=4)
def load_lexicon(path: Path) -> Lexicon:
    data = json.loads(path.read_text(encoding="utf-8"))
    entries = [LexiconEntry(**item) for item in data["entries"]]
    return Lexicon(entries)


def default_lexicon_path() -> Path:
    return Path(__file__).resolve().parents[2] / "data" / "sample_lexicon.json"


def load_default_lexicon() -> Lexicon:
    return load_lexicon(default_lexicon_path())
