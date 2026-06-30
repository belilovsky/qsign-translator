from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
import shutil
import tempfile
import time
from functools import lru_cache
from pathlib import Path
from typing import Literal
from uuid import uuid4

from . import __version__
from . import db
from .ai_video_brief import build_ai_video_batch_brief, build_ai_video_brief
from .asr import AsrUnavailable, FasterWhisperAsr
from .lexicon import load_default_lexicon
from .lexicon import default_lexicon_path
from .planner import SignPlanner
from .preview_video import PreviewVideoUnavailable
from .preview_video import build_review_video
from .settings import get_settings
from .video_plan import build_job_render_plan

planner = SignPlanner(load_default_lexicon())
settings = get_settings()

try:
    from fastapi import FastAPI, HTTPException, Request, Response
    from fastapi.responses import FileResponse
    from fastapi.staticfiles import StaticFiles
    from pydantic import BaseModel, Field
except ImportError as exc:  # pragma: no cover - import guard for optional API extra
    raise RuntimeError("Install qsign-translator[api] to run the FastAPI service") from exc

import json

MAX_AUDIO_BYTES = 50 * 1024 * 1024
MAX_RENDERED_VIDEO_BYTES = 250 * 1024 * 1024
MIN_MP4_HEADER_BYTES = 12
SUPPORTED_AUDIO_TYPES = {
    "audio/aac": ".aac",
    "audio/mp4": ".m4a",
    "audio/mpeg": ".mp3",
    "audio/mp3": ".mp3",
    "audio/wav": ".wav",
    "audio/webm": ".webm",
    "audio/x-m4a": ".m4a",
    "audio/x-wav": ".wav",
}
SUPPORTED_RENDERED_VIDEO_TYPES = {"video/mp4": ".mp4"}


class TextTranslateRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    language: Literal["ru", "kk", "en"] | None = None


class FeedbackRequest(BaseModel):
    job_id: str = Field(min_length=1, max_length=80)
    feedback_type: str = Field(min_length=1, max_length=40)
    note: str | None = Field(default=None, max_length=1000)


class ReviewStatusRequest(BaseModel):
    review_status: str = Field(min_length=1, max_length=40)


class ReviewSessionRequest(BaseModel):
    job_id: str = Field(min_length=1, max_length=80)
    reviewer_role: str = Field(min_length=1, max_length=80)
    reviewer_language: str = Field(min_length=1, max_length=20)
    review_status: str | None = Field(default=None, min_length=1, max_length=40)
    meaning_score: int | None = Field(default=None, ge=1, le=5)
    sign_choice_score: int | None = Field(default=None, ge=1, le=5)
    grammar_score: int | None = Field(default=None, ge=1, le=5)
    nonmanual_score: int | None = Field(default=None, ge=1, le=5)
    fingerspelling_score: int | None = Field(default=None, ge=1, le=5)
    timing_score: int | None = Field(default=None, ge=1, le=5)
    understandability_score: int | None = Field(default=None, ge=1, le=5)
    notes: str | None = Field(default=None, max_length=2000)
    blocking_issue: bool = False


class PublishStatusRequest(BaseModel):
    publish_status: str = Field(min_length=1, max_length=40)
    note: str | None = Field(default=None, max_length=2000)


class BatchAIVideoBriefRequest(BaseModel):
    job_ids: list[str] = Field(min_length=1, max_length=20)
    title: str | None = Field(default=None, min_length=1, max_length=120)


class ReviewLoginRequest(BaseModel):
    token: str = Field(min_length=1, max_length=200)
    role: Literal["admin", "reviewer", "linguist", "operator", "native_signer"] = "operator"


class LexiconSuggestionRequest(BaseModel):
    job_id: str = Field(min_length=1, max_length=80)
    unit_position: int = Field(ge=1, le=500)
    source_token: str = Field(min_length=1, max_length=200)
    suggested_gloss: str = Field(min_length=1, max_length=200)
    suggested_language: Literal["ru", "kk", "en", "rsl", "krsl", "asl"]
    suggested_clip_id: str | None = Field(default=None, max_length=200)
    reason: str | None = Field(default=None, max_length=2000)


app = FastAPI(
    title="QSign Translator API",
    version=__version__,
    description="Prototype RU/KZ/EN text-to-sign-plan API with transparent draft output. Not a professional interpretation.",
)

PUBLIC_ROOT = Path(__file__).resolve().parents[2] / "public"
STATIC_ROOT = PUBLIC_ROOT / "static"
GENERATED_PREVIEW_ROOT = Path(tempfile.gettempdir()) / "qsign-preview-videos"
UPLOADED_RENDER_ROOT = Path(settings.generated_media_root) / "rendered-videos"
REVIEW_SESSION_MAX_AGE_SECONDS = 60 * 60 * 12
PUBLIC_FILE_TYPES = {
    "ai-context.md": "text/markdown; charset=utf-8",
    "llms.txt": "text/plain; charset=utf-8",
    "manifest.webmanifest": "application/manifest+json; charset=utf-8",
    "public-context.json": "application/json; charset=utf-8",
    "robots.txt": "text/plain; charset=utf-8",
    "sitemap.xml": "application/xml; charset=utf-8",
}
SEO_PAGE_FILES = {
    "about": "about.html",
    "api": "api.html",
    "faq": "faq.html",
    "glossary": "glossary.html",
    "how-it-works": "how-it-works.html",
    "safety": "safety.html",
    "sources": "sources.html",
}
LANGUAGE_PAGE_FILES = {
    "en-asl": "languages-en-asl.html",
    "kk-krsl": "languages-kk-krsl.html",
    "ru-rsl": "languages-ru-rsl.html",
}

if STATIC_ROOT.exists():
    app.mount("/static", StaticFiles(directory=STATIC_ROOT), name="static")


@app.get("/", response_model=None, include_in_schema=False)
@app.head("/", response_model=None, include_in_schema=False)
def index(request: Request) -> FileResponse | Response:
    index_path = PUBLIC_ROOT / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Frontend is not bundled")
    if request.method == "HEAD":
        return Response(status_code=200)
    return FileResponse(index_path)


def _content_page_response(request: Request, filename: str) -> FileResponse | Response:
    page_path = PUBLIC_ROOT / "pages" / filename
    if not page_path.exists():
        raise HTTPException(status_code=404, detail="Content page is not bundled")
    if request.method == "HEAD":
        return Response(status_code=200, media_type="text/html; charset=utf-8")
    return FileResponse(page_path, media_type="text/html; charset=utf-8")


@app.get("/about", response_model=None, include_in_schema=False)
@app.head("/about", response_model=None, include_in_schema=False)
def page_about(request: Request) -> FileResponse | Response:
    return _content_page_response(request, SEO_PAGE_FILES["about"])


@app.get("/how-it-works", response_model=None, include_in_schema=False)
@app.head("/how-it-works", response_model=None, include_in_schema=False)
def page_how_it_works(request: Request) -> FileResponse | Response:
    return _content_page_response(request, SEO_PAGE_FILES["how-it-works"])


@app.get("/sources", response_model=None, include_in_schema=False)
@app.head("/sources", response_model=None, include_in_schema=False)
def page_sources(request: Request) -> FileResponse | Response:
    return _content_page_response(request, SEO_PAGE_FILES["sources"])


@app.get("/safety", response_model=None, include_in_schema=False)
@app.head("/safety", response_model=None, include_in_schema=False)
def page_safety(request: Request) -> FileResponse | Response:
    return _content_page_response(request, SEO_PAGE_FILES["safety"])


@app.get("/api", response_model=None, include_in_schema=False)
@app.head("/api", response_model=None, include_in_schema=False)
def page_api(request: Request) -> FileResponse | Response:
    return _content_page_response(request, SEO_PAGE_FILES["api"])


@app.get("/faq", response_model=None, include_in_schema=False)
@app.head("/faq", response_model=None, include_in_schema=False)
def page_faq(request: Request) -> FileResponse | Response:
    return _content_page_response(request, SEO_PAGE_FILES["faq"])


@app.get("/glossary", response_model=None, include_in_schema=False)
@app.head("/glossary", response_model=None, include_in_schema=False)
def page_glossary(request: Request) -> FileResponse | Response:
    return _content_page_response(request, SEO_PAGE_FILES["glossary"])


@app.get("/languages/{slug}", response_model=None, include_in_schema=False)
@app.head("/languages/{slug}", response_model=None, include_in_schema=False)
def page_language(slug: str, request: Request) -> FileResponse | Response:
    filename = LANGUAGE_PAGE_FILES.get(slug)
    if not filename:
        raise HTTPException(status_code=404, detail="Language page is not bundled")
    return _content_page_response(request, filename)


@app.get("/favicon.ico", response_model=None, include_in_schema=False)
@app.head("/favicon.ico", response_model=None, include_in_schema=False)
def favicon(request: Request) -> FileResponse | Response:
    icon_path = STATIC_ROOT / "assets" / "qsign-icon.svg"
    if not icon_path.exists():
        raise HTTPException(status_code=404, detail="Favicon is not bundled")
    if request.method == "HEAD":
        return Response(status_code=200)
    return FileResponse(icon_path, media_type="image/svg+xml")


def _public_file_response(request: Request, filename: str) -> FileResponse | Response:
    if filename not in PUBLIC_FILE_TYPES:
        raise HTTPException(status_code=404, detail="Public file is not bundled")
    file_path = PUBLIC_ROOT / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"{filename} is not bundled")
    if request.method == "HEAD":
        return Response(status_code=200, media_type=PUBLIC_FILE_TYPES[filename])
    return FileResponse(file_path, media_type=PUBLIC_FILE_TYPES[filename])


@app.get("/robots.txt", response_model=None, include_in_schema=False)
@app.head("/robots.txt", response_model=None, include_in_schema=False)
def robots(request: Request) -> FileResponse | Response:
    return _public_file_response(request, "robots.txt")


@app.get("/sitemap.xml", response_model=None, include_in_schema=False)
@app.head("/sitemap.xml", response_model=None, include_in_schema=False)
def sitemap(request: Request) -> FileResponse | Response:
    return _public_file_response(request, "sitemap.xml")


@app.get("/llms.txt", response_model=None, include_in_schema=False)
@app.head("/llms.txt", response_model=None, include_in_schema=False)
def llms(request: Request) -> FileResponse | Response:
    return _public_file_response(request, "llms.txt")


@app.get("/manifest.webmanifest", response_model=None, include_in_schema=False)
@app.head("/manifest.webmanifest", response_model=None, include_in_schema=False)
def manifest(request: Request) -> FileResponse | Response:
    return _public_file_response(request, "manifest.webmanifest")


@app.get("/ai-context.md", response_model=None, include_in_schema=False)
@app.head("/ai-context.md", response_model=None, include_in_schema=False)
def ai_context(request: Request) -> FileResponse | Response:
    return _public_file_response(request, "ai-context.md")


@app.get("/public-context.json", response_model=None, include_in_schema=False)
@app.head("/public-context.json", response_model=None, include_in_schema=False)
def public_context(request: Request) -> FileResponse | Response:
    return _public_file_response(request, "public-context.json")


@app.get("/health", response_model=None)
@app.head("/health", response_model=None, include_in_schema=False)
def health(request: Request) -> dict[str, str] | Response:
    if request.method == "HEAD":
        return Response(status_code=200)
    return {"status": "ok"}


@app.get("/health/live", response_model=None)
@app.head("/health/live", response_model=None, include_in_schema=False)
def live(request: Request) -> dict[str, str] | Response:
    if request.method == "HEAD":
        return Response(status_code=200)
    return {"status": "ok"}


@app.get("/health/ready", response_model=None)
@app.head("/health/ready", response_model=None, include_in_schema=False)
def ready(request: Request, response: Response) -> dict[str, object] | Response:
    database = db.readiness()
    ok = bool(database.get("ok"))
    if not ok and settings.database_url:
        if request.method == "HEAD":
            return Response(status_code=503)
        response.status_code = 503
    if request.method == "HEAD":
        return Response(status_code=200)
    return {
        "status": "ok" if ok or not settings.database_url else "degraded",
        "database": database,
    }


@app.post("/v1/translate/text")
def translate_text(request: TextTranslateRequest) -> dict[str, object]:
    return _plan_response(request.text, input_type="text", language_hint=request.language)


def _plan_response(text: str, input_type: str, language_hint: str | None = None) -> dict[str, object]:
    plan = planner.plan(text, language_hint=language_hint)
    response = plan.to_dict()
    metadata = dict(response.get("metadata") or {})
    try:
        job_id = db.record_translation_job(plan, input_type=input_type)
    except Exception as exc:  # pragma: no cover - operational fallback path
        metadata["persisted"] = False
        metadata["persistence_error"] = str(exc)
    else:
        metadata["persisted"] = True
        metadata["job_id"] = job_id
    response["metadata"] = metadata
    return response


@lru_cache(maxsize=1)
def _fallback_sources_payload() -> list[dict[str, object]]:
    registry_path = Path(__file__).resolve().parents[2] / "data" / "source_registry.json"
    if not registry_path.exists():
        return []
    return list(json.loads(registry_path.read_text(encoding="utf-8"))["sources"])


@lru_cache(maxsize=1)
def _fallback_lexicon_payload() -> list[dict[str, object]]:
    return load_default_lexicon().export_entries()


def _clamp_limit(value: int, *, minimum: int, maximum: int) -> int:
    return max(minimum, min(value, maximum))


def _looks_like_mp4(payload: bytes) -> bool:
    if len(payload) < MIN_MP4_HEADER_BYTES:
        return False
    box_size = int.from_bytes(payload[0:4], "big", signed=False)
    if box_size < 8:
        return False
    return payload[4:8] == b"ftyp"


@app.post("/v1/transcribe/audio")
async def transcribe_audio(request: Request) -> dict[str, object]:
    content_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    suffix = SUPPORTED_AUDIO_TYPES.get(content_type)
    if not suffix:
        raise HTTPException(status_code=415, detail="Unsupported audio type")

    content_length = request.headers.get("content-length")
    if content_length:
        try:
            declared_length = int(content_length)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid content length") from exc
        if declared_length > MAX_AUDIO_BYTES:
            raise HTTPException(status_code=413, detail="Audio file is too large")

    body = await request.body()
    if not body:
        raise HTTPException(status_code=400, detail="Audio file is empty")
    if len(body) > MAX_AUDIO_BYTES:
        raise HTTPException(status_code=413, detail="Audio file is too large")

    tmp_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(body)
            tmp_path = tmp.name
        asr = FasterWhisperAsr(
            model_name=os.environ.get("QSIGN_ASR_MODEL", "large-v3"),
            device=os.environ.get("QSIGN_ASR_DEVICE", "auto"),
        )
        transcript = asr.transcribe(tmp_path)
    except AsrUnavailable as exc:
        return {
            "status": "asr_unavailable",
            "detail": str(exc),
            "text": "",
            "language": None,
            "confidence": None,
        }
    finally:
        if tmp_path:
            Path(tmp_path).unlink(missing_ok=True)

    return {
        "status": "ok",
        "text": transcript.text,
        "language": transcript.language,
        "confidence": transcript.confidence,
    }


@app.get("/v1/sources")
def sources(limit: int = 100) -> dict[str, object]:
    try:
        rows = db.list_sources(limit=_clamp_limit(limit, minimum=1, maximum=500))
    except db.DatabaseUnavailable as exc:
        rows = _fallback_sources_payload()
        if not rows:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        rows = rows[: _clamp_limit(limit, minimum=1, maximum=500)]
    return {"items": rows, "count": len(rows)}


@app.get("/v1/lexicon")
def lexicon(language: str | None = None, limit: int = 200) -> dict[str, object]:
    try:
        rows = db.list_lexicon(language=language, limit=_clamp_limit(limit, minimum=1, maximum=1000))
    except db.DatabaseUnavailable as exc:
        if not default_lexicon_path().exists():
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        rows = _fallback_lexicon_payload()
        if language:
            rows = [row for row in rows if row["language"] == language]
        rows = rows[: _clamp_limit(limit, minimum=1, maximum=1000)]
    return {"items": rows, "count": len(rows)}


@app.get("/v1/jobs/{job_id}")
def translation_job(job_id: str) -> dict[str, object]:
    try:
        job = db.get_translation_job(job_id)
    except db.DatabaseUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if not job:
        raise HTTPException(status_code=404, detail="Translation job not found")
    return job


def _review_session_secret() -> str | None:
    return settings.review_session_secret or settings.review_token


def _encode_review_session(role: str) -> str:
    secret = _review_session_secret()
    if not secret:
        raise HTTPException(status_code=503, detail="Review API is not configured")
    payload = json.dumps(
        {
            "role": role,
            "issued_at": int(time.time()),
        },
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    payload_b64 = base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")
    signature = hmac.new(secret.encode("utf-8"), payload_b64.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{payload_b64}.{signature}"


def _decode_review_session(raw_value: str) -> dict[str, object] | None:
    if not raw_value:
        return None
    secret = _review_session_secret()
    if not secret:
        return None
    try:
        payload_b64, supplied_signature = raw_value.split(".", 1)
    except ValueError:
        return None
    expected_signature = hmac.new(
        secret.encode("utf-8"),
        payload_b64.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    if not secrets.compare_digest(supplied_signature, expected_signature):
        return None
    padded = payload_b64 + "=" * (-len(payload_b64) % 4)
    try:
        payload = json.loads(base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8"))
    except Exception:
        return None
    role = str(payload.get("role") or "").strip()
    issued_at = int(payload.get("issued_at") or 0)
    if role not in db.VALID_REVIEWER_ROLES:
        return None
    if issued_at <= 0 or int(time.time()) - issued_at > REVIEW_SESSION_MAX_AGE_SECONDS:
        return None
    return {"role": role, "issued_at": issued_at, "method": "session"}


def _set_review_cookie(response: Response, role: str) -> None:
    response.set_cookie(
        key=settings.review_cookie_name,
        value=_encode_review_session(role),
        max_age=REVIEW_SESSION_MAX_AGE_SECONDS,
        httponly=True,
        secure=settings.review_cookie_secure,
        samesite="lax",
        path="/",
    )


def _clear_review_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.review_cookie_name,
        httponly=True,
        secure=settings.review_cookie_secure,
        samesite="lax",
        path="/",
    )


def require_review_access(request: Request, *, allowed_roles: set[str] | None = None) -> dict[str, str]:
    if not settings.review_token:
        raise HTTPException(status_code=503, detail="Review API is not configured")
    supplied = request.headers.get("x-qsign-review-token", "")
    if supplied:
        if not secrets.compare_digest(supplied, settings.review_token):
            raise HTTPException(status_code=403, detail="Review API token is invalid")
        actor = {"role": "admin", "method": "token"}
    else:
        actor = _decode_review_session(request.cookies.get(settings.review_cookie_name, ""))
        if not actor:
            raise HTTPException(status_code=403, detail="Review session is missing or invalid")
    if allowed_roles and actor["role"] not in allowed_roles:
        raise HTTPException(status_code=403, detail="Review session role is not allowed")
    return actor


@app.get("/v1/jobs/{job_id}/render-plan")
def translation_job_render_plan(job_id: str) -> dict[str, object]:
    try:
        job = db.get_translation_job(job_id)
    except db.DatabaseUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if not job:
        raise HTTPException(status_code=404, detail="Translation job not found")
    return build_job_render_plan(job, settings.asset_root)


@app.get("/v1/jobs/{job_id}/review-video", response_model=None)
@app.head("/v1/jobs/{job_id}/review-video", response_model=None, include_in_schema=False)
def translation_job_review_video(job_id: str, request: Request) -> FileResponse | Response:
    try:
        job = db.get_translation_job(job_id)
    except db.DatabaseUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if not job:
        raise HTTPException(status_code=404, detail="Translation job not found")
    unit_count = len(list(job.get("units") or []))
    if unit_count == 0:
        raise HTTPException(status_code=503, detail="translation job has no units")
    filename = f"qsign-review-{job_id}.mp4"
    if request.method == "HEAD":
        return Response(
            status_code=200,
            media_type="video/mp4",
            headers=_review_video_headers(
                filename=filename,
                kind="review_storyboard",
                unit_count=unit_count,
            ),
        )
    try:
        artifact = build_review_video(
            job,
            output_root=GENERATED_PREVIEW_ROOT,
        )
    except PreviewVideoUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return FileResponse(
        artifact.path,
        media_type="video/mp4",
        headers=_review_video_headers(
            filename=filename,
            kind=artifact.kind,
            unit_count=artifact.unit_count,
            duration_seconds=artifact.duration_seconds,
        ),
    )


def _review_video_headers(
    *,
    filename: str,
    kind: str,
    unit_count: int,
    duration_seconds: float | None = None,
) -> dict[str, str]:
    duration = duration_seconds if duration_seconds is not None else max(3.0, unit_count * 1.4)
    return {
        "content-disposition": f'inline; filename="{filename}"',
        "x-qsign-preview-kind": kind,
        "x-qsign-preview-duration": f"{duration:.3f}",
        "x-qsign-preview-units": str(unit_count),
    }


@app.get("/v1/jobs/{job_id}/rendered-video", response_model=None)
@app.head("/v1/jobs/{job_id}/rendered-video", response_model=None, include_in_schema=False)
def translation_job_rendered_video(job_id: str, request: Request) -> FileResponse | Response:
    try:
        job = db.get_translation_job(job_id)
    except db.DatabaseUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if not job:
        raise HTTPException(status_code=404, detail="Translation job not found")
    output_status = str(job.get("output_status") or "not_rendered")
    output_uri = str(job.get("output_uri") or "")
    path = uploaded_render_path(job_id)
    if output_status != "ready" or not output_uri or not path.exists():
        raise HTTPException(status_code=404, detail="Rendered video is not available")
    filename = f"qsign-rendered-{job_id}.mp4"
    headers = {
        "content-disposition": f'inline; filename="{filename}"',
        "x-qsign-render-kind": "uploaded_final",
    }
    if request.method == "HEAD":
        return Response(status_code=200, media_type="video/mp4", headers=headers)
    return FileResponse(path, media_type="video/mp4", headers=headers)


@app.get("/v1/jobs/{job_id}/ai-video-brief")
def translation_job_ai_video_brief(job_id: str) -> dict[str, object]:
    try:
        job = db.get_translation_job(job_id)
    except db.DatabaseUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if not job:
        raise HTTPException(status_code=404, detail="Translation job not found")
    render_plan = build_job_render_plan(job, settings.asset_root)
    return build_ai_video_brief(job, render_plan)


@app.post("/v1/ai-video-batch-brief")
def ai_video_batch_brief(payload: BatchAIVideoBriefRequest) -> dict[str, object]:
    jobs_with_render_plans: list[tuple[dict[str, object], dict[str, object]]] = []
    missing_ids: list[str] = []
    try:
        for job_id in payload.job_ids:
            job = db.get_translation_job(job_id)
            if not job:
                missing_ids.append(job_id)
                continue
            jobs_with_render_plans.append((job, build_job_render_plan(job, settings.asset_root)))
    except db.DatabaseUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if missing_ids:
        raise HTTPException(
            status_code=404,
            detail=f"Translation jobs not found: {', '.join(missing_ids)}",
        )
    return build_ai_video_batch_brief(jobs_with_render_plans, title=payload.title)


@app.post("/v1/review/login")
def review_login(payload: ReviewLoginRequest, response: Response) -> dict[str, object]:
    if not settings.review_token:
        raise HTTPException(status_code=503, detail="Review API is not configured")
    if not secrets.compare_digest(payload.token, settings.review_token):
        raise HTTPException(status_code=403, detail="Review API token is invalid")
    _set_review_cookie(response, payload.role)
    return {
        "status": "ok",
        "actor": {
            "role": payload.role,
            "method": "session",
            "session_max_age_seconds": REVIEW_SESSION_MAX_AGE_SECONDS,
        },
    }


@app.post("/v1/review/logout")
def review_logout(response: Response) -> dict[str, object]:
    _clear_review_cookie(response)
    return {"status": "ok"}


@app.get("/v1/review/me")
def review_me(request: Request) -> dict[str, object]:
    actor = require_review_access(request)
    return {"status": "ok", "actor": actor}


@app.get("/v1/review/system-status")
def review_system_status(request: Request) -> dict[str, object]:
    actor = require_review_access(request, allowed_roles=db.VALID_REVIEWER_ROLES | {"admin"})
    readiness = db.readiness()
    metrics: dict[str, object] | None = None
    if readiness.get("ok"):
        try:
            metrics = db.review_metrics(limit=500)
        except db.DatabaseUnavailable:
            metrics = None
    preview_root_exists = GENERATED_PREVIEW_ROOT.exists()
    uploaded_root_exists = UPLOADED_RENDER_ROOT.exists()
    return {
        "status": "ok",
        "actor": actor,
        "services": {
            "database": readiness,
            "ffmpeg": {"installed": bool(shutil.which("ffmpeg"))},
            "preview_video": {
                "root": str(GENERATED_PREVIEW_ROOT),
                "exists": preview_root_exists,
            },
            "rendered_video": {
                "root": str(UPLOADED_RENDER_ROOT),
                "exists": uploaded_root_exists,
            },
            "lexicon": {
                "fallback_export_available": default_lexicon_path().exists(),
            },
            "source_registry": {
                "fallback_json_available": bool(
                    (Path(__file__).resolve().parents[2] / "data" / "source_registry.json").exists()
                ),
            },
        },
        "review_metrics": metrics,
    }


@app.get("/v1/review/coverage-report")
def review_coverage_report(
    request: Request,
    limit_jobs: int = 500,
    limit_terms: int = 50,
) -> dict[str, object]:
    require_review_access(request, allowed_roles=db.VALID_REVIEWER_ROLES | {"admin"})
    try:
        return {
            "status": "ok",
            "report": db.review_coverage_report(
                limit_jobs=_clamp_limit(limit_jobs, minimum=10, maximum=5000),
                limit_terms=_clamp_limit(limit_terms, minimum=10, maximum=500),
            ),
        }
    except db.DatabaseUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/v1/review/jobs")
def review_jobs(
    request: Request,
    review_status: str | None = None,
    publish_status: str | None = None,
    detected_language: str | None = None,
    q: str | None = None,
    limit: int = 50,
) -> dict[str, object]:
    require_review_access(request, allowed_roles=db.VALID_REVIEWER_ROLES | {"admin"})
    try:
        items = db.list_translation_jobs(
            review_status=review_status,
            publish_status=publish_status,
            detected_language=detected_language,
            search_query=q,
            limit=_clamp_limit(limit, minimum=1, maximum=200),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except db.DatabaseUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"items": items, "count": len(items)}


@app.patch("/v1/review/jobs/{job_id}")
def review_job(job_id: str, payload: ReviewStatusRequest, request: Request) -> dict[str, object]:
    actor = require_review_access(
        request,
        allowed_roles={"admin", "reviewer", "operator", "linguist"},
    )
    try:
        job = db.update_review_status(job_id, payload.review_status, actor_role=actor["role"])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except db.DatabaseUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if not job:
        raise HTTPException(status_code=404, detail="Translation job not found")
    return job


@app.get("/v1/review/feedback")
def review_feedback(
    request: Request, job_id: str | None = None, limit: int = 50
) -> dict[str, object]:
    require_review_access(request, allowed_roles=db.VALID_REVIEWER_ROLES | {"admin"})
    try:
        items = db.list_feedback_events(
            job_id=job_id,
            limit=_clamp_limit(limit, minimum=1, maximum=200),
        )
    except db.DatabaseUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"items": items, "count": len(items)}


@app.get("/v1/review/audit")
def review_audit(
    request: Request, job_id: str | None = None, limit: int = 100
) -> dict[str, object]:
    require_review_access(request, allowed_roles=db.VALID_REVIEWER_ROLES | {"admin"})
    try:
        items = db.list_audit_events(
            job_id=job_id,
            limit=_clamp_limit(limit, minimum=1, maximum=300),
        )
    except db.DatabaseUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"items": items, "count": len(items)}


@app.get("/v1/review/sessions")
def review_sessions(
    request: Request, job_id: str | None = None, limit: int = 50
) -> dict[str, object]:
    require_review_access(request, allowed_roles=db.VALID_REVIEWER_ROLES | {"admin"})
    try:
        items = db.list_review_sessions(
            job_id=job_id,
            limit=_clamp_limit(limit, minimum=1, maximum=200),
        )
    except db.DatabaseUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"items": items, "count": len(items)}


@app.post("/v1/review/sessions")
def create_review_session(payload: ReviewSessionRequest, request: Request) -> dict[str, object]:
    actor = require_review_access(
        request,
        allowed_roles={"admin", "reviewer", "operator", "linguist", "native_signer"},
    )
    try:
        job = db.get_translation_job(payload.job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Translation job not found")
        session = db.create_review_session(
            job_id=payload.job_id,
            reviewer_role=actor["role"] if actor["method"] == "session" else payload.reviewer_role,
            reviewer_language=payload.reviewer_language,
            meaning_score=payload.meaning_score,
            sign_choice_score=payload.sign_choice_score,
            grammar_score=payload.grammar_score,
            nonmanual_score=payload.nonmanual_score,
            fingerspelling_score=payload.fingerspelling_score,
            timing_score=payload.timing_score,
            understandability_score=payload.understandability_score,
            notes=payload.notes,
            blocking_issue=payload.blocking_issue,
        )
        if not session:
            raise HTTPException(status_code=404, detail="Translation job not found")
        current_review_status = str(job.get("review_status") or "pending_signer_review")
        if payload.review_status:
            updated_job = db.update_review_status(
                payload.job_id,
                payload.review_status,
                actor_role=actor["role"],
            )
            if not updated_job:
                raise HTTPException(status_code=404, detail="Translation job not found")
            current_review_status = str(updated_job.get("review_status") or current_review_status)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except db.DatabaseUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {
        "status": "ok",
        "session": session,
        "job_id": payload.job_id,
        "review_status": current_review_status,
    }


@app.post("/v1/review/jobs/{job_id}/rendered-video")
async def upload_rendered_video(job_id: str, request: Request) -> dict[str, object]:
    require_review_access(request, allowed_roles={"admin", "reviewer", "operator"})
    content_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    if content_type not in SUPPORTED_RENDERED_VIDEO_TYPES:
        raise HTTPException(status_code=415, detail="Unsupported rendered video type")
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            declared_length = int(content_length)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid content length") from exc
        if declared_length > MAX_RENDERED_VIDEO_BYTES:
            raise HTTPException(status_code=413, detail="Rendered video is too large")
    try:
        job = db.get_translation_job(job_id)
    except db.DatabaseUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if not job:
        raise HTTPException(status_code=404, detail="Translation job not found")
    body = await request.body()
    if not body:
        raise HTTPException(status_code=400, detail="Rendered video is empty")
    if len(body) > MAX_RENDERED_VIDEO_BYTES:
        raise HTTPException(status_code=413, detail="Rendered video is too large")
    if not _looks_like_mp4(body):
        raise HTTPException(status_code=415, detail="Rendered video payload is not a valid MP4")
    output_path = uploaded_render_path(job_id)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = output_path.with_name(f"{output_path.stem}-{uuid4().hex}.tmp")
    tmp_path.write_bytes(body)
    tmp_path.replace(output_path)
    output_uri = f"/v1/jobs/{job_id}/rendered-video"
    try:
        updated_job = db.attach_rendered_video(job_id, output_uri=output_uri)
    except db.DatabaseUnavailable as exc:
        output_path.unlink(missing_ok=True)
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if not updated_job:
        output_path.unlink(missing_ok=True)
        raise HTTPException(status_code=404, detail="Translation job not found")
    return {
        "status": "ok",
        "job_id": job_id,
        "output_status": updated_job.get("output_status"),
        "output_uri": updated_job.get("output_uri"),
        "render_adapter": updated_job.get("render_adapter"),
        "size_bytes": output_path.stat().st_size,
    }


@app.patch("/v1/review/jobs/{job_id}/publish-status")
def update_job_publish_status(
    job_id: str, payload: PublishStatusRequest, request: Request
) -> dict[str, object]:
    actor = require_review_access(request, allowed_roles={"admin", "reviewer", "operator"})
    try:
        job = db.update_publish_status(
            job_id,
            publish_status=payload.publish_status,
            actor_role=actor["role"],
            note=payload.note,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except db.DatabaseUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if not job:
        raise HTTPException(status_code=404, detail="Translation job not found")
    return job


@app.get("/v1/review/lexicon-candidates")
def review_lexicon_candidates(
    request: Request,
    job_id: str | None = None,
    status: str | None = None,
    limit: int = 100,
) -> dict[str, object]:
    require_review_access(request, allowed_roles=db.VALID_REVIEWER_ROLES | {"admin"})
    try:
        items = db.list_lexicon_suggestions(
            job_id=job_id,
            status=status,
            limit=_clamp_limit(limit, minimum=1, maximum=200),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except db.DatabaseUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"items": items, "count": len(items)}


@app.post("/v1/review/lexicon-candidates")
def create_review_lexicon_candidate(
    payload: LexiconSuggestionRequest,
    request: Request,
) -> dict[str, object]:
    actor = require_review_access(
        request,
        allowed_roles={"admin", "reviewer", "operator", "linguist", "native_signer"},
    )
    try:
        job = db.get_translation_job(payload.job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Translation job not found")
        suggestion = db.create_lexicon_suggestion(
            job_id=payload.job_id,
            unit_position=payload.unit_position,
            source_token=payload.source_token,
            suggested_gloss=payload.suggested_gloss,
            suggested_language=payload.suggested_language,
            suggested_clip_id=payload.suggested_clip_id,
            reason=payload.reason,
            created_by_role=actor["role"],
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except db.DatabaseUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if not suggestion:
        raise HTTPException(status_code=404, detail="Translation job not found")
    return {"status": "ok", "item": suggestion}


def uploaded_render_path(job_id: str) -> Path:
    return UPLOADED_RENDER_ROOT / f"{job_id}.mp4"


@app.post("/v1/feedback")
def feedback(request: FeedbackRequest) -> dict[str, object]:
    try:
        job = db.get_translation_job(request.job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Translation job not found")
        feedback_id = db.record_feedback(
            job_id=request.job_id,
            feedback_type=request.feedback_type,
            note=request.note,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except db.DatabaseUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"status": "ok", "feedback_id": feedback_id}
