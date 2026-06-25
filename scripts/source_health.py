from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    registry = json.loads((root / "data" / "source_registry.json").read_text(encoding="utf-8"))
    failures = 0
    for source in registry["sources"]:
        url = source["url"]
        request = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "qsign-source-health"})
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                print(f"{source['id']}: {response.status} {url}")
        except Exception as exc:  # pragma: no cover - network diagnostic script
            failures += 1
            print(f"{source['id']}: FAIL {url} ({exc})", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
