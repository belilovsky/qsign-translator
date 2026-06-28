from __future__ import annotations

import re
from functools import lru_cache

TOKEN_RE = re.compile(r"[A-Za-zА-Яа-яЁёӘәҒғҚқҢңӨөҰұҮүҺһІі0-9]+", re.UNICODE)
RU_SUFFIXES = ("ами", "ями", "ого", "ему", "ыми", "ими", "ах", "ях", "ом", "ем", "ой", "ей")
RU_ALIAS_MAP = {
    "я": "меня",
    "мне": "меня",
    "мной": "меня",
    "мною": "меня",
    "вас": "вы",
    "нужно": "нужна",
    "нужен": "нужна",
    "нужны": "нужна",
    "здравствуй": "здравствуйте",
    "большое": "большой",
    "адрес": "адрес/улица",
    "ребенка": "ребенок",
    "ребёнка": "ребенок",
    "понимаю": "понимать",
    "болит": "болеть",
    "помочь": "помощь",
    "помоги": "помощь",
    "помогите": "помощь",
}


def tokenize(text: str) -> list[str]:
    return list(_tokenize_cached(text))


@lru_cache(maxsize=4096)
def _tokenize_cached(text: str) -> tuple[str, ...]:
    return tuple(token.lower().replace("ё", "е") for token in TOKEN_RE.findall(text))


@lru_cache(maxsize=8192)
def normalize_for_lookup(token: str) -> str:
    """Small deterministic normalizer before real morphology is introduced."""

    token = token.lower().replace("ё", "е")
    if token in RU_ALIAS_MAP:
        return RU_ALIAS_MAP[token]
    for suffix in RU_SUFFIXES:
        if len(token) > len(suffix) + 3 and token.endswith(suffix):
            return token[: -len(suffix)]
    return token
