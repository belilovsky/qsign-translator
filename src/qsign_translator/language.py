from __future__ import annotations

import re

KAZAKH_SPECIFIC = set("әғқңөұүһіӘҒҚҢӨҰҮҺІ")
CYRILLIC_RE = re.compile(r"[А-Яа-яЁёӘәҒғҚқҢңӨөҰұҮүҺһІі]")
LATIN_RE = re.compile(r"[A-Za-z]")
KAZAKH_HINT_TOKENS = {
    "мен",
    "сен",
    "сіз",
    "менің",
    "маған",
    "сені",
    "жоқ",
    "қалай",
    "қайда",
    "қандай",
    "керек",
    "қажет",
    "көмек",
    "бала",
    "ата",
    "ана",
    "ауыр",
}


def detect_language(text: str) -> str:
    """Return a coarse language route: en, kk, ru, or mixed.

    This is deliberately transparent and deterministic for the spike.
    Production should replace it with a stronger detector that handles
    code-switching and dialectal noise.
    """

    letters = [ch for ch in text if CYRILLIC_RE.match(ch) or LATIN_RE.match(ch)]
    if not letters:
        return "unknown"

    has_cyrillic = any(CYRILLIC_RE.match(ch) for ch in letters)
    has_latin = any(LATIN_RE.match(ch) for ch in letters)
    if has_cyrillic and has_latin:
        return "mixed"

    if has_latin:
        return "en"

    kazakh_count = sum(1 for ch in letters if ch in KAZAKH_SPECIFIC)
    if kazakh_count == 0:
        tokens = set(
            token.strip().lower()
            for token in re.split(r"\W+", text)
            if token.strip()
        )
        if tokens.intersection(KAZAKH_HINT_TOKENS):
            return "kk"
        return "ru"
    ratio = kazakh_count / max(1, len(letters))
    if ratio >= 0.08:
        return "kk"
    return "mixed"


def normalize_language_hint(value: str | None) -> str | None:
    """Normalize user/API language hints to internal route identifiers."""

    if not value:
        return None
    normalized = str(value).strip().lower()
    if normalized in {"auto", "detect", "detect_language", "", "unknown", "mixed"}:
        return None
    if normalized in {"ru", "rus", "russian"}:
        return "ru"
    if normalized in {"kk", "kz", "kazakh", "kazak"}:
        return "kk"
    if normalized in {"en", "eng", "english", "us"}:
        return "en"
    return None
