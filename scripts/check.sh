#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PYTHON="${QSIGN_PYTHON:-python3.12}"

PYTHONPATH=src "$PYTHON" -m compileall -q src tests
PYTHONPATH=src "$PYTHON" -m unittest discover -s tests
PYTHONPATH=src "$PYTHON" scripts/check_platform_contracts.py
PYTHONPATH=src "$PYTHON" scripts/phrase_coverage_smoke.py
"$PYTHON" -m json.tool data/sample_lexicon.json >/dev/null
"$PYTHON" -m json.tool data/curated_overrides.json >/dev/null
"$PYTHON" -m json.tool data/source_registry.json >/dev/null
"$PYTHON" scripts/validate_sql.py
"$PYTHON" scripts/generate_seed_sql.py >/tmp/qsign-seed.sql
PYTHONPATH=src "$PYTHON" -m qsign_translator "Привет, меня зовут Александр" >/tmp/qsign-ru-plan.json
PYTHONPATH=src "$PYTHON" -m qsign_translator "Сәлеметсіз бе, маған көмек керек" >/tmp/qsign-kk-plan.json

echo "check: ok"
