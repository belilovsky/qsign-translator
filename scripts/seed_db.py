from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def require_psycopg():
    try:
        import psycopg
    except ImportError as exc:  # pragma: no cover - optional operational script
        raise SystemExit(
            "Install psycopg to seed the database: python -m pip install psycopg[binary]"
        ) from exc
    return psycopg


def main() -> int:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL is required", file=sys.stderr)
        return 2

    root = Path(__file__).resolve().parents[1]
    source_registry = json.loads(
        (root / "data" / "source_registry.json").read_text(encoding="utf-8")
    )
    lexicon = json.loads(
        (root / "data" / "sample_lexicon.json").read_text(encoding="utf-8")
    )
    psycopg = require_psycopg()

    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            for source in source_registry["sources"]:
                cur.execute(
                    """
                    INSERT INTO source_registry (id, name, url, task, languages, status, license_note)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        url = EXCLUDED.url,
                        task = EXCLUDED.task,
                        languages = EXCLUDED.languages,
                        status = EXCLUDED.status,
                        license_note = EXCLUDED.license_note,
                        updated_at = now()
                    """,
                    (
                        source["id"],
                        source["name"],
                        source["url"],
                        source["task"],
                        source["languages"],
                        source["status"],
                        source["license_note"],
                    ),
                )

            for entry in lexicon["entries"]:
                cur.execute(
                    """
                    INSERT INTO lexicon_entries
                        (token, gloss, language, source, confidence, clip_id)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (language, token, gloss) DO UPDATE SET
                        source = EXCLUDED.source,
                        confidence = EXCLUDED.confidence,
                        clip_id = EXCLUDED.clip_id,
                        updated_at = now()
                    """,
                    (
                        entry["token"],
                        entry["gloss"],
                        entry["language"],
                        entry["source"],
                        entry["confidence"],
                        entry.get("clip_id"),
                    ),
                )
        conn.commit()
    print("seed_db: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
