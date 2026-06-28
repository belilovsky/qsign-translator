from __future__ import annotations

from functools import lru_cache

RUSSIAN_DACTYL = {
    "а": "DACTYL_A",
    "б": "DACTYL_BE",
    "в": "DACTYL_VE",
    "г": "DACTYL_GE",
    "д": "DACTYL_DE",
    "е": "DACTYL_IE",
    "ж": "DACTYL_ZHE",
    "з": "DACTYL_ZE",
    "и": "DACTYL_I",
    "й": "DACTYL_SHORT_I",
    "к": "DACTYL_KA",
    "л": "DACTYL_EL",
    "м": "DACTYL_EM",
    "н": "DACTYL_EN",
    "о": "DACTYL_O",
    "п": "DACTYL_PE",
    "р": "DACTYL_ER",
    "с": "DACTYL_ES",
    "т": "DACTYL_TE",
    "у": "DACTYL_U",
    "ф": "DACTYL_EF",
    "х": "DACTYL_HA",
    "ц": "DACTYL_TSE",
    "ч": "DACTYL_CHE",
    "ш": "DACTYL_SHA",
    "щ": "DACTYL_SHCHA",
    "ы": "DACTYL_YERU",
    "э": "DACTYL_E",
    "ю": "DACTYL_YU",
    "я": "DACTYL_YA",
}

EN_DACTYL = {
    "a": "DACTYL_A",
    "b": "DACTYL_B",
    "c": "DACTYL_TSE",
    "d": "DACTYL_D",
    "e": "DACTYL_E",
    "f": "DACTYL_F",
    "g": "DACTYL_G",
    "h": "DACTYL_H",
    "i": "DACTYL_I",
    "j": "DACTYL_J",
    "k": "DACTYL_KA",
    "l": "DACTYL_L",
    "m": "DACTYL_EM",
    "n": "DACTYL_EN",
    "o": "DACTYL_O",
    "p": "DACTYL_P",
    "q": "DACTYL_Q",
    "r": "DACTYL_R",
    "s": "DACTYL_ES",
    "t": "DACTYL_TE",
    "u": "DACTYL_U",
    "v": "DACTYL_VE",
    "w": "DACTYL_W",
    "x": "DACTYL_X",
    "y": "DACTYL_Y",
    "z": "DACTYL_Z",
}

KAZAKH_TO_BASE = {
    "ә": ["а", "э"],
    "ғ": ["г"],
    "қ": ["к"],
    "ң": ["н"],
    "ө": ["о"],
    "ұ": ["у"],
    "ү": ["у"],
    "һ": ["х"],
    "і": ["и"],
}


def spell_token(token: str) -> list[str]:
    """Return a transparent dactyl fallback sequence for an unknown token."""

    return list(_spell_token_cached(token))


@lru_cache(maxsize=8192)
def _spell_token_cached(token: str) -> tuple[str, ...]:
    signs: list[str] = []
    for char in token.lower().replace("ё", "е"):
        chars = KAZAKH_TO_BASE.get(char, [char])
        for mapped in chars:
            sign = RUSSIAN_DACTYL.get(mapped) or EN_DACTYL.get(mapped)
            if sign:
                signs.append(sign)
    return tuple(signs)
