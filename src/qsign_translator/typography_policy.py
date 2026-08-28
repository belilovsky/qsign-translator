"""Portfolio Typography Policy v1 for QSign source and runtime surfaces.

The adapter is intentionally dependency-free.  It is used at user-visible
write boundaries and as an ASGI response guard so later edits cannot quietly
reintroduce an em dash in a public response.
"""

from __future__ import annotations

import json
import re
from typing import Any, Sequence


POLICY_VERSION = "1.0.0"
_MDASH_NAME = "m" + "dash;"
_VIOLATION_RE = re.compile(
    r"(?P<unicode>\u2014)"
    rf"|(?P<named_escaped>&amp;{_MDASH_NAME})"
    r"|(?P<decimal_escaped>&amp;#8212;)"
    r"|(?P<hex_escaped>&amp;#x2014;)"
    rf"|(?P<named>&{_MDASH_NAME})"
    r"|(?P<decimal>&#8212;)"
    r"|(?P<hex>&#x2014;)",
    re.IGNORECASE,
)
# URLs and HTML technical attributes are identifiers, not editorial copy.
_PROTECTED_RE = re.compile(
    r"(?ix)(?:\b(?:https?|ftp)://[^\s<>\"']+)"
    r"|(?:\b(?:href|src|action|cite|poster)\s*=\s*[\"'][^\"']*[\"'])"
)


def _protected_ranges(value: str) -> list[tuple[int, int]]:
    return [match.span() for match in _PROTECTED_RE.finditer(value)]


def _is_protected(position: int, ranges: Sequence[tuple[int, int]]) -> bool:
    return any(start <= position < end for start, end in ranges)


def _kind(match: re.Match[str]) -> str:
    for name in (
        "unicode",
        "named_escaped",
        "decimal_escaped",
        "hex_escaped",
        "named",
        "decimal",
        "hex",
    ):
        if match.group(name) is not None:
            return name
    return "unknown"


def _replacement(match: re.Match[str]) -> str:
    return {
        "unicode": "\u2013",
        "named_escaped": "&amp;ndash;",
        "decimal_escaped": "&amp;#8211;",
        "hex_escaped": "&amp;#x2013;",
        "named": "&ndash;",
        "decimal": "&#8211;",
        "hex": "&#x2013;",
    }.get(_kind(match), match.group(0))


def normalize_text(value: str) -> str:
    """Normalize editorial mdashes while preserving technical identifiers."""

    ranges = _protected_ranges(value)
    pieces: list[str] = []
    cursor = 0
    for match in _VIOLATION_RE.finditer(value):
        if _is_protected(match.start(), ranges):
            continue
        pieces.extend((value[cursor : match.start()], _replacement(match)))
        cursor = match.end()
    pieces.append(value[cursor:])
    return "".join(pieces)


def scan_text(value: str) -> list[dict[str, object]]:
    """Return policy findings outside protected technical contexts."""

    ranges = _protected_ranges(value)
    findings: list[dict[str, object]] = []
    for match in _VIOLATION_RE.finditer(value):
        if _is_protected(match.start(), ranges):
            continue
        findings.append(
            {
                "line": value.count("\n", 0, match.start()) + 1,
                "column": match.start() - value.rfind("\n", 0, match.start()),
                "kind": _kind(match),
            }
        )
    return findings


def normalize_value(value: Any) -> Any:
    """Recursively normalize strings in JSON-like values."""

    if isinstance(value, str):
        return normalize_text(value)
    if isinstance(value, list):
        return [normalize_value(item) for item in value]
    if isinstance(value, dict):
        return {key: normalize_value(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return tuple(normalize_value(item) for item in value)
    return value


def normalize_json_bytes(body: bytes) -> bytes:
    payload = json.loads(body)
    return json.dumps(normalize_value(payload), ensure_ascii=False, separators=(",", ":")).encode("utf-8")


class TypographyPolicyMiddleware:
    """Normalize text/JSON/XML responses without changing media bytes."""

    def __init__(self, app: Any, max_body_bytes: int = 8 * 1024 * 1024) -> None:
        self.app = app
        self.max_body_bytes = max_body_bytes

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        response: dict[str, Any] = {}
        chunks: list[bytes] = []

        async def capture(message: dict[str, Any]) -> None:
            if message["type"] == "http.response.start":
                response.update(message)
                return
            if message["type"] != "http.response.body":
                return
            chunks.append(message.get("body", b""))
            if message.get("more_body"):
                return

            body = b"".join(chunks)
            headers = list(response.get("headers", []))
            content_type = next(
                (
                    value.decode("latin-1").lower()
                    for key, value in headers
                    if key.lower() == b"content-type"
                ),
                "",
            )
            textual = (
                content_type.startswith("text/")
                or "json" in content_type
                or "xml" in content_type
                or "html" in content_type
            )
            if len(body) <= self.max_body_bytes and textual:
                if "json" in content_type:
                    try:
                        body = normalize_json_bytes(body)
                    except (UnicodeDecodeError, json.JSONDecodeError):
                        body = normalize_text(body.decode("utf-8", "replace")).encode("utf-8")
                else:
                    body = normalize_text(body.decode("utf-8", "replace")).encode("utf-8")
                headers = [
                    (key, value)
                    for key, value in headers
                    if key.lower() not in {b"content-length", b"x-typography-policy"}
                ]
                headers.append((b"content-length", str(len(body)).encode("ascii")))
                headers.append((b"x-typography-policy", POLICY_VERSION.encode("ascii")))
            await send(
                {
                    "type": "http.response.start",
                    "status": response.get("status", 200),
                    "headers": headers,
                }
            )
            await send({"type": "http.response.body", "body": body})

        await self.app(scope, receive, capture)
