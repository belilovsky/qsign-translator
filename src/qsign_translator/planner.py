from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property

from .dactyl import spell_token
from .language import (
    detect_language,
    normalize_language_hint,
    resolve_mixed_language,
    transliterate_kazakh_latin_to_cyrillic,
)
from .lexicon import Lexicon
from .normalize import normalize_for_lookup, tokenize
from .risk import detect_risk_domains


@dataclass(frozen=True)
class SignUnit:
    kind: str
    source_token: str
    gloss: str
    confidence: float
    source: str
    clip_id: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "source_token": self.source_token,
            "gloss": self.gloss,
            "confidence": self.confidence,
            "source": self.source,
            "clip_id": self.clip_id,
            "decision": self.decision(),
        }

    def decision(self) -> dict[str, object]:
        if self.kind == "gloss" and self.source.startswith("seed:manual_phrase"):
            return {
                "type": "phrase_lookup",
                "status": "matched",
                "reason": "Фраза найдена в проверяемом словаре как цельный жестовый блок.",
                "review_hint": "Проверить порядок жестов и уместность фразы целиком.",
            }
        if self.kind == "gloss" and self.source.startswith("seed:manual_nonmanual"):
            return {
                "type": "nonmanual_marker",
                "status": "matched",
                "reason": "Токен отмечен как служебный или немануальный маркер.",
                "review_hint": "Проверить, нужна ли мимика/грамматическая пометка в этом контексте.",
            }
        if self.kind == "gloss":
            return {
                "type": "token_lookup",
                "status": "matched",
                "reason": "Слово найдено в словаре жестов.",
                "review_hint": "Проверить, подходит ли выбранный жест к смыслу фразы.",
            }
        if self.kind == "dactyl":
            return {
                "type": "dactyl_fallback",
                "status": "needs_review",
                "reason": "Слово не найдено в словаре, поэтому показано по буквам.",
                "review_hint": "Добавить словарный жест или подтвердить дактиль для имени/термина.",
            }
        return {
            "type": "subtitle_fallback",
            "status": "needs_review",
            "reason": "Сервис не смог подобрать жест или дактиль и оставил текстовую подсказку.",
            "review_hint": "Нужна ручная замена на жестовый вариант.",
        }


@dataclass(frozen=True)
class SignPlan:
    input_text: str
    language: str
    units: list[SignUnit]
    risk_domains: list[str]

    @cached_property
    def confidence(self) -> float:
        if not self.units:
            return 0.0
        return round(sum(unit.confidence for unit in self.units) / len(self.units), 3)

    @cached_property
    def fallback_count(self) -> int:
        return sum(1 for unit in self.units if unit.kind != "gloss" or unit.source.startswith("fallback"))

    @cached_property
    def unknown_token_count(self) -> int:
        return sum(1 for unit in self.units if unit.source.startswith("fallback"))

    @cached_property
    def source_ids(self) -> list[str]:
        sources = []
        for unit in self.units:
            source = unit.source.split(":", 1)[0]
            if source and source not in sources:
                sources.append(source)
        return sources

    @cached_property
    def normalized_tokens(self) -> list[str]:
        return [normalize_for_lookup(token) for token in tokenize(self.input_text)]

    @cached_property
    def review_gate(self) -> str:
        if self.risk_domains:
            return "human_interpreter_required"
        if self.fallback_count:
            return "native_signer_review_required"
        return "native_signer_review_recommended"

    @cached_property
    def job_status(self) -> str:
        if self.risk_domains or self.fallback_count:
            return "review_required"
        return "draft_plan"

    @cached_property
    def output_status(self) -> str:
        return "not_rendered"

    @cached_property
    def output_kind(self) -> str:
        return "sign_plan_preview"

    def trace(self) -> dict[str, object]:
        total = len(self.units)
        matched = sum(1 for unit in self.units if unit.kind == "gloss")
        fallback = self.fallback_count
        input_characters = len(self.input_text)
        token_count = len(self.normalized_tokens)
        return {
            "summary": {
                "input_characters": input_characters,
                "token_count": token_count,
                "unit_count": total,
                "matched_units": matched,
                "fallback_units": fallback,
                "review_gate": self.review_gate,
            },
            "stages": [
                {
                    "id": "input",
                    "status": "complete",
                    "title": "Фраза принята",
                    "summary": (
                        f"{input_characters} {_plural_ru(input_characters, 'символ', 'символа', 'символов')}, "
                        f"{token_count} {_plural_ru(token_count, 'токен', 'токена', 'токенов')}."
                    ),
                },
                {
                    "id": "language",
                    "status": "complete",
                    "title": "Язык определен",
                    "summary": f"Маршрут перевода: {self.language}.",
                    "data": {"language": self.language},
                },
                {
                    "id": "normalization",
                    "status": "complete",
                    "title": "Текст нормализован",
                    "summary": "Токены приведены к форме для словарного поиска.",
                    "data": {"tokens": self.normalized_tokens},
                },
                {
                    "id": "planning",
                    "status": "complete" if total else "empty",
                    "title": "План жестов собран",
                    "summary": (
                        f"Найдено {matched}, требует замены {fallback}, "
                        f"всего {total} {_plural_ru(total, 'единица', 'единицы', 'единиц')}."
                    ),
                    "data": {
                        "matched_units": matched,
                        "fallback_units": fallback,
                        "total_units": total,
                    },
                },
                {
                    "id": "review",
                    "status": "blocked" if self.risk_domains else "required",
                    "title": "Проверка человеком",
                    "summary": self._review_summary(),
                    "data": {
                        "risk_domains": self.risk_domains,
                        "review_gate": self.review_gate,
                    },
                },
                {
                    "id": "output",
                    "status": "pending",
                    "title": "Видео-вывод",
                    "summary": "Видео-аватар пока не собран. Сейчас доступен только прозрачный черновик плана.",
                    "data": {
                        "job_status": self.job_status,
                        "output_kind": self.output_kind,
                        "output_status": self.output_status,
                        "publish_ready": False,
                    },
                },
            ],
        }

    def _review_summary(self) -> str:
        if self.risk_domains:
            return "Высокорисковый сценарий: нужен человек-переводчик."
        if self.fallback_count:
            return "Есть слова без словарного жеста: нужна проверка носителем жестового языка."
        return "Автоматический черновик все равно требует контрольной проверки."

    def to_dict(self) -> dict[str, object]:
        dactyl_count = sum(1 for unit in self.units if unit.kind == "dactyl")
        gloss_count = sum(1 for unit in self.units if unit.kind == "gloss")
        warnings = [
            "prototype_sign_plan_not_professional_interpretation",
            "native_signer_validation_required",
        ]
        if self.risk_domains:
            warnings.append("high_risk_domain_requires_human_interpreter")
        return {
            "input_text": self.input_text,
            "language": self.language,
            "confidence": self.confidence,
            "units": [unit.to_dict() for unit in self.units],
            "coverage": {
                "gloss": gloss_count,
                "dactyl": dactyl_count,
                "fallback": self.fallback_count,
                "total": len(self.units),
            },
            "metadata": {
                "source_ids": self.source_ids,
                "fallback_count": self.fallback_count,
                "unknown_token_count": self.unknown_token_count,
                "job_status": self.job_status,
                "review_status": "pending_signer_review",
                "output_kind": self.output_kind,
                "output_status": self.output_status,
                "publish_ready": False,
            },
            "risk": {
                "domains": self.risk_domains,
                "needs_human_interpreter": bool(self.risk_domains),
            },
            "trace": self.trace(),
            "warnings": warnings,
        }


class SignPlanner:
    def __init__(self, lexicon: Lexicon) -> None:
        self.lexicon = lexicon

    def plan(self, text: str, language_hint: str | None = None) -> SignPlan:
        language = normalize_language_hint(language_hint) or detect_language(text)
        if language == "mixed":
            language = resolve_mixed_language(text)
        units: list[SignUnit] = []
        tokens = tokenize(text)
        normalized_tokens = [normalize_for_lookup(token) for token in tokens]
        transliterated_tokens = None
        if language == "kk":
            transliterated_tokens = [
                normalize_for_lookup(transliterate_kazakh_latin_to_cyrillic(token))
                for token in tokens
            ]
        index = 0
        while index < len(tokens):
            match = self._match_longest(tokens, normalized_tokens, transliterated_tokens, index, language)
            if match:
                source_token, entry, consumed = match
                index += consumed
                if entry.gloss == "OMIT":
                    continue
                units.append(
                    SignUnit(
                        kind="gloss",
                        source_token=source_token,
                        gloss=entry.gloss,
                        confidence=entry.confidence,
                        source=entry.source,
                        clip_id=entry.clip_id,
                    )
                )
                continue

            token = tokens[index]
            normalized = normalized_tokens[index]
            index += 1
            entry = self.lexicon.lookup(normalized, language)
            if entry:
                if entry.gloss == "OMIT":
                    continue
                units.append(
                    SignUnit(
                        kind="gloss",
                        source_token=token,
                        gloss=entry.gloss,
                        confidence=entry.confidence,
                        source=entry.source,
                        clip_id=entry.clip_id,
                    )
                )
                continue

            if language == "kk":
                assert transliterated_tokens is not None
                latin_entry = self.lexicon.lookup(transliterated_tokens[index - 1], language)
                if latin_entry:
                    if latin_entry.gloss == "OMIT":
                        continue
                    units.append(
                        SignUnit(
                            kind="gloss",
                            source_token=token,
                            gloss=latin_entry.gloss,
                            confidence=latin_entry.confidence,
                            source=latin_entry.source,
                            clip_id=latin_entry.clip_id,
                        )
                    )
                    continue

            dactyl_units = spell_token(token)
            if dactyl_units:
                units.append(
                    SignUnit(
                        kind="dactyl",
                        source_token=token,
                        gloss=" ".join(dactyl_units),
                        confidence=0.35,
                        source="fallback:dactyl",
                    )
                )
            else:
                units.append(
                    SignUnit(
                        kind="subtitle",
                        source_token=token,
                        gloss=token,
                        confidence=0.2,
                        source="fallback:subtitle",
                    )
                )
        return SignPlan(
            input_text=text,
            language=language,
            units=units,
            risk_domains=detect_risk_domains(text),
        )

    def _match_longest(
        self,
        tokens: list[str],
        normalized_tokens: list[str],
        transliterated_tokens: list[str] | None,
        index: int,
        language: str,
    ):
        max_len = min(4, len(tokens) - index)
        for size in range(max_len, 1, -1):
            phrase = " ".join(normalized_tokens[index : index + size])
            entry = self.lexicon.lookup(phrase, language)
            if entry:
                return " ".join(tokens[index : index + size]), entry, size
            if language == "kk" and transliterated_tokens is not None:
                transliterated = " ".join(transliterated_tokens[index : index + size])
                transliterated_entry = self.lexicon.lookup(transliterated, language)
                if transliterated_entry:
                    return " ".join(tokens[index : index + size]), transliterated_entry, size
        return None


def _plural_ru(value: int, one: str, few: str, many: str) -> str:
    value = abs(value)
    if 11 <= value % 100 <= 14:
        return many
    if value % 10 == 1:
        return one
    if 2 <= value % 10 <= 4:
        return few
    return many
