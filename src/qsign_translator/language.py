from __future__ import annotations

import re

KAZAKH_SPECIFIC = set("әғқңөұүһіӘҒҚҢӨҰҮҺІ")
CYRILLIC_RE = re.compile(r"[А-Яа-яЁёӘәҒғҚқҢңӨөҰұҮүҺһІі]")
LATIN_RE = re.compile(r"[A-Za-z]")
TOKEN_RE = re.compile(r"[A-Za-zА-Яа-яЁёӘәҒғҚқҢңӨөҰұҮүҺһІі0-9]+")
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

KAZAKH_LATIN_HINT_TOKENS = {
    "salam",
    "sagyn",
    "raqmet",
    "kerek",
    "keregi",
    "komek",
    "rakhmet",
    "men",
    "sen",
    "siz",
    "qai",
    "ayaq",
    "qaida",
    "qayda",
    "qalay",
    "qana",
    "dostar",
    "auyr",
}

KAZAKH_LATIN_TO_CYRILLIC = {
    "shch": "щ",
    "ng": "ң",
    "zh": "ж",
    "kh": "х",
    "gh": "ғ",
    "kz": "қ",
    "q": "қ",
    "sh": "ш",
    "ch": "ч",
}

KAZAKH_LATIN_CHAR_MAP = {
    "a": "а",
    "ä": "ә",
    "b": "б",
    "v": "в",
    "g": "г",
    "d": "д",
    "e": "е",
    "ё": "ё",
    "j": "ж",
    "z": "з",
    "i": "и",
    "й": "й",
    "k": "к",
    "l": "л",
    "m": "м",
    "n": "н",
    "o": "о",
    "p": "п",
    "r": "р",
    "s": "с",
    "t": "т",
    "u": "у",
    "f": "ф",
    "h": "х",
    "c": "ц",
    "y": "й",
    "x": "х",
    "w": "в",
}
EN_HINT_TOKENS = {
    "i",
    "we",
    "you",
    "he",
    "she",
    "it",
    "they",
    "the",
    "and",
    "for",
    "from",
    "have",
    "has",
    "is",
    "are",
    "was",
    "a",
    "an",
    "to",
    "of",
    "in",
    "on",
    "at",
    "my",
    "your",
    "please",
    "help",
    "need",
    "where",
    "when",
    "thank",
    "thanks",
    "yes",
    "no",
}

LATIN_KK_HINT_TOKENS = {
    "salam",
    "rawaq",
    "raqmet",
    "kerek",
    "kereki",
    "komek",
    "men",
    "sen",
    "siz",
    "qaida",
    "qayda",
    "qai",
}


def _token_counts_by_script(tokens: list[str]) -> tuple[int, int, int, int]:
    cyr_token_count = 0
    lat_token_count = 0
    digit_token_count = 0
    mixed_token_count = 0

    for token in tokens:
        if not token:
            continue
        has_cyr = any(CYRILLIC_RE.match(ch) for ch in token)
        has_lat = any(LATIN_RE.match(ch) for ch in token)
        has_digit = any(ch.isdigit() for ch in token)
        if has_cyr and has_lat:
            mixed_token_count += 1
        elif has_cyr:
            cyr_token_count += 1
        elif has_lat:
            lat_token_count += 1
        elif has_digit:
            digit_token_count += 1

    return cyr_token_count, lat_token_count, mixed_token_count, digit_token_count


def _tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


def _cyrillic_token_ratio(tokens: list[str]) -> float:
    if not tokens:
        return 0.0
    has_cyrillic = [
        any(CYRILLIC_RE.match(ch) for ch in token)
        for token in tokens
        if token
    ]
    cyr_count = sum(has_cyrillic)
    return cyr_count / len(tokens)


def _has_hint(tokens: list[str], hints: set[str]) -> bool:
    return bool(set(tokens) & hints)


def _count_hints(tokens: list[str], hints: set[str]) -> int:
    return len(set(tokens) & hints)


def _normalise_latin_token(token: str) -> str:
    return token.lower().replace("\ufeff", "").replace("'", "").replace("’", "").strip()


def _latin_hint_count(tokens: list[str]) -> int:
    normalized = {_normalise_latin_token(token) for token in tokens}
    return _count_hints(list(normalized), KAZAKH_LATIN_HINT_TOKENS)


def _en_hint_count(tokens: list[str]) -> int:
    normalized = {_normalise_latin_token(token) for token in tokens}
    return _count_hints(list(normalized), EN_HINT_TOKENS)


def transliterate_kazakh_latin_to_cyrillic(text: str) -> str:
    lowered = _normalise_latin_token(text)
    if not lowered:
        return ""

    result = lowered
    for source, target in KAZAKH_LATIN_TO_CYRILLIC.items():
        result = result.replace(source, target)

    mapped_chars: list[str] = []
    for char in result:
        mapped = KAZAKH_LATIN_CHAR_MAP.get(char)
        mapped_chars.append(mapped if mapped else char)
    return "".join(mapped_chars)


def resolve_mixed_language(text: str) -> str:
    """Resolve ambiguous mixed-script routes to a concrete language.

    Returns ru, en, or kk with deterministic behavior for ambiguous inputs.
    """

    tokens = _tokenize(text)
    if not tokens:
        return "ru"

    cyr_tokens, lat_tokens, mixed_tokens, digit_tokens = _token_counts_by_script(tokens)
    total = max(1, cyr_tokens + lat_tokens + mixed_tokens + digit_tokens)
    cyr_ratio = cyr_tokens / total
    lat_ratio = lat_tokens / total
    mixed_ratio = mixed_tokens / total

    has_kazakh_hint = _has_hint(tokens, KAZAKH_HINT_TOKENS) or _has_hint(tokens, LATIN_KK_HINT_TOKENS)
    has_english_hint = _has_hint(tokens, EN_HINT_TOKENS)

    if has_kazakh_hint and not has_english_hint:
        return "kk"
    if has_english_hint and not has_kazakh_hint:
        return "en"

    if cyr_ratio >= 0.7:
        return "kk" if has_kazakh_hint else "ru"
    if lat_ratio >= 0.7:
        return "en"
    if has_kazakh_hint and cyr_ratio >= lat_ratio:
        return "kk"
    if has_english_hint and lat_ratio >= cyr_ratio:
        return "en"

    if mixed_ratio > 0.55:
        return "en" if has_english_hint else "ru"

    if lat_ratio >= cyr_ratio:
        return "en"
    return "ru"


def detect_language(text: str) -> str:
    """Return a coarse language route: en, kk, ru, or mixed.

    This is deliberately transparent and deterministic for the spike.
    Production should replace it with a stronger detector that handles
    code-switching and dialectal noise.
    """

    letters = [ch for ch in text if CYRILLIC_RE.match(ch) or LATIN_RE.match(ch)]
    tokens = _tokenize(text)
    if not letters:
        return "unknown"

    has_cyrillic = any(CYRILLIC_RE.match(ch) for ch in letters)
    has_latin = any(LATIN_RE.match(ch) for ch in letters)
    if has_cyrillic and has_latin:
        cyr_token_ratio = _cyrillic_token_ratio(tokens)
        latin_token_ratio = 1 - cyr_token_ratio
        kazakh_hint_count = (
            _count_hints(tokens, KAZAKH_HINT_TOKENS)
            + _count_hints(tokens, LATIN_KK_HINT_TOKENS)
        )
        has_kazakh_hint = (
            _has_hint(tokens, KAZAKH_HINT_TOKENS)
            or _has_hint(tokens, LATIN_KK_HINT_TOKENS)
        )
        has_english_hint = _has_hint(tokens, EN_HINT_TOKENS)
        en_hint_count = _count_hints(tokens, EN_HINT_TOKENS)
        if has_kazakh_hint and not has_english_hint:
            return "kk"
        if has_kazakh_hint and has_english_hint:
            if en_hint_count > kazakh_hint_count:
                return "en"
            if en_hint_count < kazakh_hint_count:
                return "kk"
        if latin_token_ratio >= 0.75 and has_english_hint:
            return "en"
        if cyr_token_ratio >= 0.75:
            # Dominantly Cyrillic; resolve to kazakh only when explicit hints exist.
            return "kk" if has_kazakh_hint else "ru"
        if has_english_hint:
            return "en"
        if has_kazakh_hint:
            return "kk"
        if has_english_hint:
            return "en"
        # Planner gets the final fallback decision deterministically.
        return resolve_mixed_language(text)

    if has_latin:
        latin_hint_count = _latin_hint_count(tokens)
        english_hint_count = _en_hint_count(tokens)
        if latin_hint_count and not english_hint_count:
            return "kk"
        if latin_hint_count and english_hint_count:
            if english_hint_count >= latin_hint_count:
                return "en"
            return "kk"
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
