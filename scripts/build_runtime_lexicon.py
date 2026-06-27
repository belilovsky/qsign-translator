from __future__ import annotations

import csv
import json
from pathlib import Path


ARCHIVE_GLOSS_PATH = (
    Path(__file__).resolve().parents[2]
    / "qsign-translator-archive"
    / "experiments"
    / "mimic_text2video"
    / "misc"
    / "gloss_words_SLOVO.txt"
)
ARCHIVE_ANNOTATIONS_PATH = (
    Path(__file__).resolve().parents[2]
    / "qsign-translator-archive"
    / "experiments"
    / "mimic_text2video"
    / "misc"
    / "annotations_cleared_19.06.2023_SLOVO.csv"
)
DEFAULT_CONFIDENCE = 0.63
SOURCE_ID = "slovo:archive_gloss"


def normalize_token(token: str) -> str:
    return token.strip().lower().replace("ё", "е")


def display_gloss(token: str) -> str:
    return token.strip().upper().replace("Ё", "Е")


def load_base_entries(path: Path) -> list[dict[str, object]]:
    return json.loads(path.read_text(encoding="utf-8"))["entries"]


def load_clip_ids(path: Path) -> dict[str, str]:
    clip_ids: dict[str, str] = {}
    with path.open(encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            normalized = normalize_token(row.get("gloss_norm", ""))
            cut_name = (row.get("cut_name") or "").strip()
            if not normalized or not cut_name or normalized in clip_ids:
                continue
            clip_ids[normalized] = Path(cut_name).stem
    return clip_ids


def build_slovo_entries(gloss_path: Path, annotations_path: Path) -> list[dict[str, object]]:
    clip_ids = load_clip_ids(annotations_path)
    entries: list[dict[str, object]] = []
    seen_tokens: set[str] = set()

    for raw_token in gloss_path.read_text(encoding="utf-8").splitlines():
        normalized = normalize_token(raw_token)
        if not normalized or normalized in seen_tokens:
            continue

        # Русские односимвольные буквы и знаки уже надежнее покрываются дактилем.
        if len(normalized) == 1:
            continue

        seen_tokens.add(normalized)
        entries.append(
            {
                "token": normalized,
                "gloss": display_gloss(normalized),
                "language": "ru",
                "source": SOURCE_ID,
                "confidence": DEFAULT_CONFIDENCE,
                "clip_id": clip_ids.get(normalized),
            }
        )
    return entries


def merge_entries(base_entries: list[dict[str, object]], imported_entries: list[dict[str, object]]) -> list[dict[str, object]]:
    merged = list(base_entries)
    existing_keys = {(entry["language"], entry["token"]) for entry in base_entries}

    for entry in imported_entries:
        key = (entry["language"], entry["token"])
        if key in existing_keys:
            continue
        merged.append(entry)
        existing_keys.add(key)

    merged.sort(key=lambda item: (str(item["language"]), str(item["token"]), str(item["source"])))
    return merged


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    lexicon_path = root / "data" / "sample_lexicon.json"
    if not ARCHIVE_GLOSS_PATH.exists():
        raise SystemExit(f"Missing archive gloss list: {ARCHIVE_GLOSS_PATH}")
    if not ARCHIVE_ANNOTATIONS_PATH.exists():
        raise SystemExit(f"Missing archive annotations: {ARCHIVE_ANNOTATIONS_PATH}")

    base_entries = load_base_entries(lexicon_path)
    imported_entries = build_slovo_entries(ARCHIVE_GLOSS_PATH, ARCHIVE_ANNOTATIONS_PATH)
    merged_entries = merge_entries(base_entries, imported_entries)
    payload = {"entries": merged_entries}
    lexicon_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "base_entries": len(base_entries),
                "imported_entries": len(imported_entries),
                "merged_entries": len(merged_entries),
                "output_path": str(lexicon_path),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
