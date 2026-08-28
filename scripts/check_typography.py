#!/usr/bin/env python3
"""Fail when QSign source or public copy contains an editorial mdash."""

from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from qsign_translator.typography_policy import scan_text  # noqa: E402


EXTENSIONS = {
    ".html", ".htm", ".md", ".txt", ".json", ".jsonld", ".yaml", ".yml", ".xml",
    ".svg", ".js", ".jsx", ".mjs", ".ts", ".tsx", ".css", ".scss", ".py", ".sql", ".csv",
}
IGNORED = {
    ".git", "__pycache__", ".pytest_cache", ".ruff_cache", ".venv", "venv", "node_modules",
    "dist", "build", "output", "coverage",
}
ALLOWED = {
    "src/qsign_translator/typography_policy.py",
    "scripts/check_typography.py",
    "tests/test_typography_policy.py",
}


def main() -> int:
    findings: list[dict[str, object]] = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in EXTENSIONS:
            continue
        relative = path.relative_to(ROOT)
        if any(part in IGNORED for part in relative.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for finding in scan_text(text):
            item = {"path": str(relative), **finding}
            if str(relative) not in ALLOWED:
                findings.append(item)
    report = {"policy_version": "1.0.0", "root": str(ROOT), "finding_count": len(findings), "findings": findings}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
