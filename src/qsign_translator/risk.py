from __future__ import annotations

import re


RISK_PATTERNS: dict[str, tuple[str, ...]] = {
    "medical": (
        "боль",
        "врач",
        "лекар",
        "диагноз",
        "операц",
        "жедел",
        "дәрі",
        "ауру",
        "дәрігер",
        "емхана",
    ),
    "legal": (
        "суд",
        "закон",
        "договор",
        "штраф",
        "адвокат",
        "құқық",
        "сот",
        "заң",
        "айыппұл",
    ),
    "emergency": (
        "пожар",
        "полиция",
        "скорая",
        "опасно",
        "эвакуац",
        "өрт",
        "полиция",
        "қауіп",
        "көмектес",
    ),
    "finance": (
        "банк",
        "кредит",
        "деньги",
        "ипотек",
        "займ",
        "банк",
        "несие",
        "ақша",
        "ипотека",
    ),
}


def detect_risk_domains(text: str) -> list[str]:
    normalized = text.lower().replace("ё", "е")
    domains: list[str] = []
    for domain, patterns in RISK_PATTERNS.items():
        if any(re.search(re.escape(pattern), normalized) for pattern in patterns):
            domains.append(domain)
    return domains

