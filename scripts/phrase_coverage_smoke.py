#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

from qsign_translator import SignPlanner
from qsign_translator.lexicon import load_default_lexicon


FIXTURE_PATH = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "phrase_coverage_cases.json"


def main() -> int:
    planner = SignPlanner(load_default_lexicon())
    cases = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))["cases"]
    failed = []

    for case in cases:
        plan = planner.plan(case["text"])
        glosses = [unit.gloss for unit in plan.units]
        ok = (
            plan.language == case["expected_language"]
            and plan.fallback_count == case["expected_fallback_count"]
            and all(gloss in glosses for gloss in case["expected_glosses"])
        )
        marker = "ok" if ok else "FAIL"
        print(
            f"{marker:4} {case['text']}: "
            f"fallbacks={plan.fallback_count} glosses={glosses}"
        )
        if not ok:
            failed.append(case["text"])

    if failed:
        print(f"phrase_coverage_smoke: failed {len(failed)} cases", file=sys.stderr)
        return 1

    print("phrase_coverage_smoke: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
