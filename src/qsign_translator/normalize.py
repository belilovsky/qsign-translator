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
    "вещи": "вещь",
    "которые": "который",
    "реальный": "реально",
    "реальная": "реально",
    "реальные": "реально",
    "реально": "реально",
    "повышает": "повышать",
    "повышают": "повышать",
    "повысить": "повышать",
    "зрелости": "зрелость",
    "проекта": "проект",
    "качества": "качество",
    "результата": "результат",
    "улучшает": "улучшать",
    "улучшают": "улучшать",
    "удобства": "удобство",
}
EN_ALIAS_MAP = {
    "i": "me",
    "i'm": "me",
    "im": "me",
    "my": "me",
    "mine": "me",
    "you": "you",
    "your": "you",
    "thanks": "thank",
    "please": "please",
    "needed": "need",
    "needs": "need",
    "helping": "help",
    "helped": "help",
    "hurts": "pain",
    "hurt": "pain",
    "painful": "pain",
    "doctor": "doctor",
    "physician": "doctor",
    "hospital": "hospital",
    "restroom": "toilet",
    "bathroom": "toilet",
    "lavatory": "toilet",
    "kid": "child",
    "children": "child",
    "kids": "child",
    "working": "work",
    "worked": "work",
    "tomorrow": "tomorrow",
    "today": "today",
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
    if token in EN_ALIAS_MAP:
        return EN_ALIAS_MAP[token]
    if token in RU_ALIAS_MAP:
        return RU_ALIAS_MAP[token]
    for suffix in RU_SUFFIXES:
        if len(token) > len(suffix) + 3 and token.endswith(suffix):
            return token[: -len(suffix)]
    return token
