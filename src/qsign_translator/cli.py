from __future__ import annotations

import argparse
import json
import sys

from .lexicon import load_default_lexicon
from .planner import SignPlanner


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a RU/KZ/EN sign-language plan.")
    parser.add_argument("text", nargs="*", help="Input text. If omitted, stdin is used.")
    parser.add_argument("--language", choices=["ru", "kk", "en"], help="Force language route.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    text = " ".join(args.text).strip() if args.text else sys.stdin.read().strip()
    if not text:
        parser.error("text is required")

    planner = SignPlanner(load_default_lexicon())
    plan = planner.plan(text, language_hint=args.language)
    indent = 2 if args.pretty else None
    print(json.dumps(plan.to_dict(), ensure_ascii=False, indent=indent))
    return 0
