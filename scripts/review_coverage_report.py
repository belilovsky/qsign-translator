#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys

from qsign_translator import db


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a compact review coverage report from saved jobs.")
    parser.add_argument("--limit-jobs", type=int, default=500, help="Recent jobs window")
    parser.add_argument("--limit-terms", type=int, default=50, help="Top fallback terms to print")
    args = parser.parse_args()

    try:
        report = db.review_coverage_report(limit_jobs=args.limit_jobs, limit_terms=args.limit_terms)
    except db.DatabaseUnavailable as exc:
        print(f"review_coverage_report: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
