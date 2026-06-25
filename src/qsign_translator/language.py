from __future__ import annotations

import re

KAZAKH_SPECIFIC = set("әғқңөұүһіӘҒҚҢӨҰҮҺІ")
CYRILLIC_RE = re.compile(r"[А-Яа-яЁёӘәҒғҚқҢңӨөҰұҮүҺһІі]")


def detect_language(text: str) -> str:
    """Return a coarse language route: kk, ru, or mixed.

    This is deliberately transparent and deterministic for the spike. Production
    should replace it with a stronger detector that handles code-switching.
    """

    letters = [ch for ch in text if CYRILLIC_RE.match(ch)]
    if not letters:
        return "unknown"
    kazakh_count = sum(1 for ch in letters if ch in KAZAKH_SPECIFIC)
    if kazakh_count == 0:
        return "ru"
    ratio = kazakh_count / max(1, len(letters))
    if ratio >= 0.08:
        return "kk"
    return "mixed"

