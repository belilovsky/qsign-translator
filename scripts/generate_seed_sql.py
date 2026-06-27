from __future__ import annotations

import json
from pathlib import Path


def sql_literal(value: object) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value).replace("'", "''")
    return f"'{text}'"


def sql_array(values: list[str]) -> str:
    return "ARRAY[" + ", ".join(sql_literal(value) for value in values) + "]"


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    source_registry = json.loads(
        (root / "data" / "source_registry.json").read_text(encoding="utf-8")
    )
    lexicon = json.loads(
        (root / "data" / "sample_lexicon.json").read_text(encoding="utf-8")
    )

    print("BEGIN;")
    for source in source_registry["sources"]:
        print(
            """
INSERT INTO source_registry (id, name, url, task, languages, status, license_note)
VALUES ({id}, {name}, {url}, {task}, {languages}, {status}, {license_note})
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    url = EXCLUDED.url,
    task = EXCLUDED.task,
    languages = EXCLUDED.languages,
    status = EXCLUDED.status,
    license_note = EXCLUDED.license_note,
    updated_at = now();
""".format(
                id=sql_literal(source["id"]),
                name=sql_literal(source["name"]),
                url=sql_literal(source["url"]),
                task=sql_literal(source["task"]),
                languages=sql_array(source["languages"]),
                status=sql_literal(source["status"]),
                license_note=sql_literal(source["license_note"]),
            )
        )

    for entry in lexicon["entries"]:
        print(
            """
INSERT INTO lexicon_entries (token, gloss, language, source, confidence, clip_id)
VALUES ({token}, {gloss}, {language}, {source}, {confidence}, {clip_id})
ON CONFLICT (language, token, gloss) DO UPDATE SET
    source = EXCLUDED.source,
    confidence = EXCLUDED.confidence,
    clip_id = EXCLUDED.clip_id,
    updated_at = now();
""".format(
                token=sql_literal(entry["token"]),
                gloss=sql_literal(entry["gloss"]),
                language=sql_literal(entry["language"]),
                source=sql_literal(entry["source"]),
                confidence=sql_literal(entry["confidence"]),
                clip_id=sql_literal(entry.get("clip_id")),
            )
        )
    print("COMMIT;")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
