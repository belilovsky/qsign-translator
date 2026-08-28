from __future__ import annotations

import asyncio
import json
import unittest

from qsign_translator.typography_policy import (
    POLICY_VERSION,
    TypographyPolicyMiddleware,
    normalize_json_bytes,
    normalize_text,
    normalize_value,
    scan_text,
)


class TypographyPolicyTests(unittest.TestCase):
    def test_all_forms_and_idempotence(self) -> None:
        value = "A — B &mdash; C &#8212; D &#x2014; E &amp;mdash; F"
        expected = "A – B &ndash; C &#8211; D &#x2013; E &amp;ndash; F"
        self.assertEqual(normalize_text(value), expected)
        self.assertEqual(normalize_text(expected), expected)
        self.assertEqual(len(scan_text(value)), 5)

    def test_protected_url_and_nested_json_boundary(self) -> None:
        value = {"title": "A — B", "url": "https://example.test/a—b", "items": ["C — D"]}
        normalized = normalize_value(value)
        self.assertEqual(normalized["title"], "A – B")
        self.assertEqual(normalized["url"], "https://example.test/a—b")
        encoded = normalize_json_bytes(json.dumps(value, ensure_ascii=False).encode())
        self.assertEqual(json.loads(encoded), normalized)

    def test_policy_version(self) -> None:
        self.assertEqual(POLICY_VERSION, "1.0.0")

    def test_json_response_boundary_adds_header(self) -> None:
        messages: list[dict[str, object]] = []

        async def inner(scope, receive, send):
            await send(
                {
                    "type": "http.response.start",
                    "status": 200,
                    "headers": [(b"content-type", b"application/json")],
                }
            )
            await send(
                {
                    "type": "http.response.body",
                    "body": json.dumps({"title": "A — B"}, ensure_ascii=False).encode(),
                }
            )

        async def run() -> None:
            async def capture(message):
                messages.append(message)

            await TypographyPolicyMiddleware(inner)(
                {"type": "http", "method": "GET", "path": "/", "headers": []},
                lambda: None,
                capture,
            )

        asyncio.run(run())
        headers = dict(messages[0]["headers"])
        self.assertEqual(headers[b"x-typography-policy"], b"1.0.0")
        self.assertEqual(json.loads(messages[1]["body"]), {"title": "A – B"})

    def test_binary_response_is_untouched(self) -> None:
        messages: list[dict[str, object]] = []

        async def inner(scope, receive, send):
            await send(
                {
                    "type": "http.response.start",
                    "status": 200,
                    "headers": [(b"content-type", b"video/mp4")],
                }
            )
            await send({"type": "http.response.body", "body": "A — B".encode()})

        async def run() -> None:
            async def capture(message):
                messages.append(message)

            await TypographyPolicyMiddleware(inner)(
                {"type": "http", "method": "GET", "path": "/", "headers": []},
                lambda: None,
                capture,
            )

        asyncio.run(run())
        self.assertEqual(messages[1]["body"], "A — B".encode())
        self.assertNotIn(b"x-typography-policy", dict(messages[0]["headers"]))
