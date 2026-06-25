from __future__ import annotations

import json
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    mimic_root = root / "experiments" / "mimic_text2video"
    gloss_path = mimic_root / "misc" / "gloss_words_SLOVO.txt"
    annotations_path = mimic_root / "misc" / "annotations_cleared_19.06.2023_SLOVO.csv"
    if not gloss_path.exists():
        print("inspect_mimic_assets: skipped; experiments/mimic_text2video is not present")
        return 0

    gloss_words = {
        line.strip().lower().replace("ё", "е")
        for line in gloss_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }
    lexicon = json.loads((root / "data" / "sample_lexicon.json").read_text(encoding="utf-8"))
    seed_tokens = {
        entry["token"].lower().replace("ё", "е")
        for entry in lexicon["entries"]
        if entry["language"] == "ru" and " " not in entry["token"]
    }
    overlap = sorted(seed_tokens & gloss_words)
    print(
        json.dumps(
            {
                "gloss_words": len(gloss_words),
                "annotations_rows": sum(1 for _ in annotations_path.open(encoding="utf-8"))
                if annotations_path.exists()
                else None,
                "seed_ru_tokens": sorted(seed_tokens),
                "seed_ru_overlap": overlap,
                "seed_ru_overlap_count": len(overlap),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
