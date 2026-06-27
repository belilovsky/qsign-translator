#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PYTHONPATH=src python3 -m compileall -q src tests
PYTHONPATH=src python3 -m unittest discover -s tests
python3 -m json.tool data/sample_lexicon.json >/dev/null
python3 -m json.tool data/curated_overrides.json >/dev/null
python3 -m json.tool data/source_registry.json >/dev/null
python3 scripts/validate_sql.py
python3 scripts/generate_seed_sql.py >/tmp/qsign-seed.sql
PYTHONPATH=src python3 -m qsign_translator "Привет, меня зовут Александр" >/tmp/qsign-ru-plan.json
PYTHONPATH=src python3 -m qsign_translator "Сәлеметсіз бе, маған көмек керек" >/tmp/qsign-kk-plan.json

echo "check: ok"
