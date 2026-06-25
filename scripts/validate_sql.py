from __future__ import annotations

from pathlib import Path


REQUIRED_TABLES = {
    "source_registry",
    "lexicon_entries",
    "assets",
    "translation_jobs",
    "sign_plan_units",
    "review_sessions",
    "feedback_events",
}

REQUIRED_SNIPPETS = {
    "translation_jobs.review_status": "ADD COLUMN IF NOT EXISTS review_status",
    "translation_jobs.risk_domains": "ADD COLUMN IF NOT EXISTS risk_domains",
    "translation_jobs.source_ids": "ADD COLUMN IF NOT EXISTS source_ids",
    "translation_jobs.fallback_count": "ADD COLUMN IF NOT EXISTS fallback_count",
    "translation_jobs.unknown_token_count": "ADD COLUMN IF NOT EXISTS unknown_token_count",
    "translation_jobs.output_kind": "ADD COLUMN IF NOT EXISTS output_kind",
    "translation_jobs.output_status": "ADD COLUMN IF NOT EXISTS output_status",
}


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    sql = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted((root / "infra" / "db" / "migrations").glob("*.sql"))
    )
    missing = [table for table in sorted(REQUIRED_TABLES) if f"CREATE TABLE IF NOT EXISTS {table}" not in sql]
    if missing:
        raise SystemExit(f"validate_sql: missing tables: {', '.join(missing)}")
    missing_snippets = [name for name, snippet in REQUIRED_SNIPPETS.items() if snippet not in sql]
    if missing_snippets:
        raise SystemExit(f"validate_sql: missing snippets: {', '.join(missing_snippets)}")
    print("validate_sql: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
