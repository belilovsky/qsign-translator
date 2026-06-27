from __future__ import annotations

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

ENGLISH_DACTYL = {
    "a": "FS_A",
    "b": "FS_B",
    "c": "FS_C",
    "d": "FS_D",
    "e": "FS_E",
    "f": "FS_F",
    "g": "FS_G",
    "h": "FS_H",
    "i": "FS_I",
    "j": "FS_J",
    "k": "FS_K",
    "l": "FS_L",
    "m": "FS_M",
    "n": "FS_N",
    "o": "FS_O",
    "p": "FS_P",
    "q": "FS_Q",
    "r": "FS_R",
    "s": "FS_S",
    "t": "FS_T",
    "u": "FS_U",
    "v": "FS_V",
    "w": "FS_W",
    "x": "FS_X",
    "y": "FS_Y",
    "z": "FS_Z",
}


def spell_token(token: str) -> list[str]:
    """Return a transparent dactyl fallback sequence for an unknown token."""

    signs: list[str] = []
    for char in token.lower().replace("ё", "е"):
        chars = KAZAKH_TO_BASE.get(char, [char])
        for mapped in chars:
            sign = RUSSIAN_DACTYL.get(mapped) or ENGLISH_DACTYL.get(mapped)
            if sign:
                signs.append(sign)
    return signs
