from __future__ import annotations

import json
from dataclasses import dataclass
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
        self._fallback_entries = {entry.token: entry for entry in entries}

    def lookup(self, token: str, language: str) -> LexiconEntry | None:
        return self._entries.get((language, token)) or self._fallback_entries.get(token)


def load_lexicon(path: Path) -> Lexicon:
    data = json.loads(path.read_text(encoding="utf-8"))
    entries = [LexiconEntry(**item) for item in data["entries"]]
    return Lexicon(entries)


def default_lexicon_path() -> Path:
    return Path(__file__).resolve().parents[2] / "data" / "sample_lexicon.json"


def load_default_lexicon() -> Lexicon:
    return load_lexicon(default_lexicon_path())

