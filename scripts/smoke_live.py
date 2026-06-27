#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass
class SmokeResult:
    name: str
    ok: bool
    detail: str


def _request(
    base_url: str,
    path: str,
    *,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 20,
) -> tuple[int, dict[str, Any], dict[str, str]]:
    body = None
    request_headers = dict(headers or {})
    if payload is not None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request_headers["content-type"] = "application/json"
    request = Request(
        base_url.rstrip("/") + path,
        data=body,
        headers=request_headers,
        method=method,
    )
    with urlopen(request, timeout=timeout) as response:
        response_body = response.read()
        parsed: dict[str, Any] = {}
        if response_body:
            try:
                parsed = json.loads(response_body.decode("utf-8"))
            except json.JSONDecodeError:
                parsed = {"raw": response_body.decode("utf-8", "replace")}
        return response.status, parsed, dict(response.headers)


def _record(results: list[SmokeResult], name: str, ok: bool, detail: str) -> None:
    results.append(SmokeResult(name=name, ok=ok, detail=detail))


def run_smoke(base_url: str, review_token: str | None, timeout: int) -> list[SmokeResult]:
    results: list[SmokeResult] = []

    try:
        status, payload, _ = _request(base_url, "/health", timeout=timeout)
        _record(results, "health", status == 200 and payload.get("status") == "ok", f"{status} {payload}")
    except (HTTPError, URLError, TimeoutError) as exc:
        _record(results, "health", False, str(exc))

    try:
        status, payload, _ = _request(base_url, "/health/ready", timeout=timeout)
        ok = status == 200 and payload.get("status") == "ok" and payload.get("database", {}).get("ok")
        _record(results, "ready", bool(ok), f"{status} {payload}")
    except (HTTPError, URLError, TimeoutError) as exc:
        _record(results, "ready", False, str(exc))

    try:
        status, payload, _ = _request(base_url, "/openapi.json", timeout=timeout)
        version = payload.get("info", {}).get("version")
        _record(results, "openapi", status == 200 and version == "0.2.0", f"{status} version={version}")
    except (HTTPError, URLError, TimeoutError) as exc:
        _record(results, "openapi", False, str(exc))

    job_ids: list[str] = []
    for name, text in [
        ("translate_ru", "Привет Александр"),
        ("translate_ru_second", "Мне нужна помощь"),
    ]:
        try:
            status, payload, _ = _request(
                base_url,
                "/v1/translate/text",
                method="POST",
                payload={"text": text},
                timeout=timeout,
            )
            metadata = payload.get("metadata", {})
            job_id = str(metadata.get("job_id") or "")
            if job_id:
                job_ids.append(job_id)
            ok = status == 200 and metadata.get("persisted") is True and metadata.get("output_status") == "not_rendered"
            _record(results, name, bool(ok), f"{status} job_id={job_id or '-'}")
        except (HTTPError, URLError, TimeoutError) as exc:
            _record(results, name, False, str(exc))

    if job_ids:
        job_id = job_ids[0]
        try:
            status, payload, _ = _request(base_url, f"/v1/jobs/{job_id}/render-plan", timeout=timeout)
            summary = payload.get("summary", {})
            _record(results, "render_plan", status == 200 and "total_units" in summary, f"{status} {summary}")
        except (HTTPError, URLError, TimeoutError) as exc:
            _record(results, "render_plan", False, str(exc))

        try:
            status, _, headers = _request(
                base_url,
                f"/v1/jobs/{job_id}/review-video",
                method="HEAD",
                timeout=timeout,
            )
            preview_kind = headers.get("x-qsign-preview-kind", "")
            _record(results, "review_video_head", status == 200 and bool(preview_kind), f"{status} {preview_kind}")
        except (HTTPError, URLError, TimeoutError) as exc:
            _record(results, "review_video_head", False, str(exc))

        try:
            status, payload, _ = _request(base_url, f"/v1/jobs/{job_id}/ai-video-brief", timeout=timeout)
            exports = sorted((payload.get("exports") or {}).keys())
            ok = status == 200 and {"universal_prompt", "json_payload", "batch_storyboard"}.issubset(exports)
            _record(results, "ai_video_brief", ok, f"{status} exports={exports}")
        except (HTTPError, URLError, TimeoutError) as exc:
            _record(results, "ai_video_brief", False, str(exc))

    if len(job_ids) >= 2:
        try:
            status, payload, _ = _request(
                base_url,
                "/v1/ai-video-batch-brief",
                method="POST",
                payload={"job_ids": job_ids[:2], "title": "Smoke batch"},
                timeout=timeout,
            )
            scene_count = payload.get("summary", {}).get("scene_count")
            exports = sorted((payload.get("exports") or {}).keys())
            ok = status == 200 and scene_count == 2 and "operator_runbook" in exports
            _record(results, "ai_video_batch_brief", ok, f"{status} scenes={scene_count} exports={exports}")
        except (HTTPError, URLError, TimeoutError) as exc:
            _record(results, "ai_video_batch_brief", False, str(exc))

    try:
        _request(base_url, "/v1/review/jobs", timeout=timeout)
        _record(results, "review_without_token", False, "unexpected 200")
    except HTTPError as exc:
        _record(results, "review_without_token", exc.code in {403, 503}, f"HTTP {exc.code}")
    except (URLError, TimeoutError) as exc:
        _record(results, "review_without_token", False, str(exc))

    try:
        _request(base_url, "/v1/review/sessions", timeout=timeout)
        _record(results, "review_sessions_without_token", False, "unexpected 200")
    except HTTPError as exc:
        _record(results, "review_sessions_without_token", exc.code in {403, 503}, f"HTTP {exc.code}")
    except (URLError, TimeoutError) as exc:
        _record(results, "review_sessions_without_token", False, str(exc))

    if review_token:
        try:
            status, payload, _ = _request(
                base_url,
                "/v1/review/jobs",
                headers={"x-qsign-review-token": review_token},
                timeout=timeout,
            )
            _record(results, "review_with_token", status == 200 and "count" in payload, f"{status} count={payload.get('count')}")
        except (HTTPError, URLError, TimeoutError) as exc:
            _record(results, "review_with_token", False, str(exc))

    for path in [
        "/v1/jobs/not-a-uuid/render-plan",
        "/v1/jobs/not-a-uuid/ai-video-brief",
    ]:
        try:
            _request(base_url, path, timeout=timeout)
            _record(results, f"invalid_id:{path}", False, "unexpected 200")
        except HTTPError as exc:
            _record(results, f"invalid_id:{path}", exc.code == 404, f"HTTP {exc.code}")
        except (URLError, TimeoutError) as exc:
            _record(results, f"invalid_id:{path}", False, str(exc))

    try:
        _request(base_url, "/v1/jobs/not-a-uuid/review-video", method="HEAD", timeout=timeout)
        _record(results, "invalid_id:review-video", False, "unexpected 200")
    except HTTPError as exc:
        _record(results, "invalid_id:review-video", exc.code == 404, f"HTTP {exc.code}")
    except (URLError, TimeoutError) as exc:
        _record(results, "invalid_id:review-video", False, str(exc))

    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-test a deployed QSign instance.")
    parser.add_argument("--base-url", default="https://qsign.qdev.run", help="Public base URL")
    parser.add_argument("--review-token", default=None, help="Optional review token for protected queue smoke")
    parser.add_argument("--timeout", type=int, default=20, help="Request timeout in seconds")
    args = parser.parse_args()

    results = run_smoke(args.base_url, args.review_token, args.timeout)
    for result in results:
        marker = "ok" if result.ok else "FAIL"
        print(f"{marker:4} {result.name}: {result.detail}")
    failed = [result for result in results if not result.ok]
    if failed:
        print(f"smoke: failed {len(failed)} checks", file=sys.stderr)
        return 1
    print("smoke: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
