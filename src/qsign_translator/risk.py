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
        "pain",
        "doctor",
        "hospital",
        "medicine",
        "diagnosis",
        "surgery",
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
        "law",
        "legal",
        "court",
        "contract",
        "fine",
        "lawyer",
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
        "fire",
        "police",
        "ambulance",
        "emergency",
        "danger",
        "evacuation",
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
        "bank",
        "credit",
        "loan",
        "money",
        "mortgage",
        "payment",
    ),
}


def detect_risk_domains(text: str) -> list[str]:
    normalized = text.lower().replace("ё", "е")
    domains: list[str] = []
    for domain, patterns in RISK_PATTERNS.items():
        if any(re.search(re.escape(pattern), normalized) for pattern in patterns):
            domains.append(domain)
    return domains
