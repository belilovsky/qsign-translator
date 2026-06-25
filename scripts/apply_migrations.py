from __future__ import annotations

import os
import sys
from pathlib import Path


def require_psycopg():
    try:
        import psycopg
    except ImportError as exc:  # pragma: no cover - optional operational script
        raise SystemExit("Install psycopg to apply migrations: python -m pip install psycopg[binary]") from exc
    return psycopg


def main() -> int:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL is required", file=sys.stderr)
        return 2

    root = Path(__file__).resolve().parents[1]
    migration_paths = sorted((root / "infra" / "db" / "migrations").glob("*.sql"))
    if not migration_paths:
        print("No migrations found", file=sys.stderr)
        return 2

    psycopg = require_psycopg()
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            for path in migration_paths:
                cur.execute(path.read_text(encoding="utf-8"))
        conn.commit()
    print(f"apply_migrations: ok ({len(migration_paths)} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
