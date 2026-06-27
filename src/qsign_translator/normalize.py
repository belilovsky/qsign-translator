from __future__ import annotations

import re

TOKEN_RE = re.compile(r"[A-Za-zА-Яа-яЁёӘәҒғҚқҢңӨөҰұҮүҺһІі0-9]+", re.UNICODE)
RU_ALIAS_MAP = {
    "мне": "меня",
    "мной": "меня",
    "мною": "меня",
    "нужно": "нужна",
    "нужен": "нужна",
    "нужны": "нужна",
    "здравствуй": "здравствуйте",
    "помочь": "помощь",
    "помоги": "помощь",
    "помогите": "помощь",
}


def tokenize(text: str) -> list[str]:
    return [token.lower().replace("ё", "е") for token in TOKEN_RE.findall(text)]


def normalize_for_lookup(token: str) -> str:
    """Small deterministic normalizer before real morphology is introduced."""

    token = token.lower().replace("ё", "е")
    if token in RU_ALIAS_MAP:
        return RU_ALIAS_MAP[token]
    ru_suffixes = ("ами", "ями", "ого", "ему", "ыми", "ими", "ах", "ях", "ом", "ем", "ой", "ей")
    for suffix in ru_suffixes:
        if len(token) > len(suffix) + 3 and token.endswith(suffix):
            return token[: -len(suffix)]
    return token
