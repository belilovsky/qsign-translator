from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SLOVO_IMPORT_ROOT = REPO_ROOT / "data" / "import_sources" / "slovo"
SLOVO_GLOSS_PATH = SLOVO_IMPORT_ROOT / "gloss_words_SLOVO.txt"
SLOVO_CLIP_IDS_PATH = SLOVO_IMPORT_ROOT / "clip_ids_SLOVO.json"
DEFAULT_CONFIDENCE = 0.63
SOURCE_ID = "slovo:archive_gloss"


def normalize_token(token: str) -> str:
    return token.strip().lower().replace("ё", "е")


def display_gloss(token: str) -> str:
    return token.strip().upper().replace("Ё", "Е")


def load_base_entries(path: Path) -> list[dict[str, object]]:
    return json.loads(path.read_text(encoding="utf-8"))["entries"]


def load_clip_ids(path: Path) -> dict[str, str]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_slovo_entries(gloss_path: Path, clip_ids_path: Path) -> list[dict[str, object]]:
    clip_ids = load_clip_ids(clip_ids_path)
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


def merge_entries(
    base_entries: list[dict[str, object]], imported_entries: list[dict[str, object]]
) -> list[dict[str, object]]:
    merged = list(base_entries)
    existing_keys = {(entry["language"], entry["token"]) for entry in base_entries}

    for entry in imported_entries:
        key = (entry["language"], entry["token"])
        if key in existing_keys:
            continue
        merged.append(entry)
        existing_keys.add(key)

    merged.sort(
        key=lambda item: (
            str(item["language"]),
            str(item["token"]),
            str(item["source"]),
        )
    )
    return merged


def main() -> int:
    lexicon_path = REPO_ROOT / "data" / "sample_lexicon.json"
    curated_path = REPO_ROOT / "data" / "curated_overrides.json"
    if not SLOVO_GLOSS_PATH.exists():
        raise SystemExit(f"Missing repo-local gloss list: {SLOVO_GLOSS_PATH}")
    if not SLOVO_CLIP_IDS_PATH.exists():
        raise SystemExit(f"Missing repo-local clip id map: {SLOVO_CLIP_IDS_PATH}")
    if not curated_path.exists():
        raise SystemExit(f"Missing curated overrides file: {curated_path}")

    base_entries = load_base_entries(curated_path)
    imported_entries = build_slovo_entries(SLOVO_GLOSS_PATH, SLOVO_CLIP_IDS_PATH)
    merged_entries = merge_entries(base_entries, imported_entries)
    payload = {"entries": merged_entries}
    lexicon_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "curated_entries": len(base_entries),
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
