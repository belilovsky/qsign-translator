#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path


INDEXNOW_KEY = "d491805d96a2b9f8c9b89725616e32f222a007cbc582d8a9158b6993d41b7141"
DEFAULT_ENDPOINT = "https://api.indexnow.org/indexnow"
SITEMAP_PATH = Path(__file__).resolve().parents[1] / "public" / "sitemap.xml"


def _normalized_base_url(raw_base_url: str) -> str:
    return raw_base_url.strip().rstrip("/")


def _host_from_base_url(base_url: str) -> str:
    parsed = urllib.parse.urlparse(base_url)
    if not parsed.netloc:
        raise ValueError(f"Base URL must include a host: {base_url}")
    return parsed.netloc


def _urls_from_sitemap(base_url: str) -> list[str]:
    tree = ET.parse(SITEMAP_PATH)
    namespace = {"sitemap": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    urls: list[str] = []
    for loc in tree.findall(".//sitemap:loc", namespace):
        if loc.text:
            path = urllib.parse.urlparse(loc.text).path
            urls.append(f"{base_url}{path}")
    return urls


def build_payload(base_url: str) -> dict[str, object]:
    base_url = _normalized_base_url(base_url)
    return {
        "host": _host_from_base_url(base_url),
        "key": INDEXNOW_KEY,
        "keyLocation": f"{base_url}/{INDEXNOW_KEY}.txt",
        "urlList": _urls_from_sitemap(base_url),
    }


def submit_payload(payload: dict[str, object], endpoint: str) -> tuple[int, str]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=body,
        headers={"content-type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.status, response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")


def main() -> int:
    parser = argparse.ArgumentParser(description="Submit QSign public URLs to IndexNow.")
    parser.add_argument("--base-url", default="https://qsign.qdev.run")
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    payload = build_payload(args.base_url)
    if args.dry_run:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    status, response_body = submit_payload(payload, args.endpoint)
    print(
        json.dumps(
            {"status": status, "body": response_body, "submitted": len(payload["urlList"])},
            ensure_ascii=False,
        )
    )
    return 0 if status in {200, 202} else 1


if __name__ == "__main__":
    sys.exit(main())
