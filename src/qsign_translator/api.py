from __future__ import annotations

import os
import secrets
import tempfile
from pathlib import Path
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


class BatchAIVideoBriefRequest(BaseModel):
    job_ids: list[str] = Field(min_length=1, max_length=20)
    title: str | None = Field(default=None, min_length=1, max_length=120)


app = FastAPI(
    title="QSign Translator API",
    version=__version__,
    description="Prototype RU/KZ text-to-sign-plan API with transparent draft output. Not a professional interpretation.",
)

PUBLIC_ROOT = Path(__file__).resolve().parents[2] / "public"
STATIC_ROOT = PUBLIC_ROOT / "static"
GENERATED_PREVIEW_ROOT = Path(tempfile.gettempdir()) / "qsign-preview-videos"
UPLOADED_RENDER_ROOT = Path(settings.generated_media_root) / "rendered-videos"

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


@app.get("/favicon.ico", response_model=None, include_in_schema=False)
@app.head("/favicon.ico", response_model=None, include_in_schema=False)
def favicon(request: Request) -> FileResponse | Response:
    icon_path = STATIC_ROOT / "assets" / "qsign-icon.svg"
    if not icon_path.exists():
        raise HTTPException(status_code=404, detail="Favicon is not bundled")
    if request.method == "HEAD":
        return Response(status_code=200)
    return FileResponse(icon_path, media_type="image/svg+xml")


@app.get("/robots.txt", response_model=None, include_in_schema=False)
@app.head("/robots.txt", response_model=None, include_in_schema=False)
def robots(request: Request) -> FileResponse | Response:
    robots_path = PUBLIC_ROOT / "robots.txt"
    if not robots_path.exists():
        raise HTTPException(status_code=404, detail="robots.txt is not bundled")
    if request.method == "HEAD":
        return Response(status_code=200)
    return FileResponse(robots_path, media_type="text/plain; charset=utf-8")


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
    return {"status": "ok" if ok or not settings.database_url else "degraded", "database": database}


@app.post("/v1/translate/text")
def translate_text(request: TextTranslateRequest) -> dict[str, object]:
    return _plan_response(request.text, input_type="text")


def _plan_response(text: str, input_type: str) -> dict[str, object]:
    plan = planner.plan(text)
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
        rows = db.list_sources(limit=max(1, min(limit, 500)))
    except db.DatabaseUnavailable as exc:
        registry_path = Path(__file__).resolve().parents[2] / "data" / "source_registry.json"
        if not registry_path.exists():
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        rows = json.loads(registry_path.read_text(encoding="utf-8"))["sources"]
    return {"items": rows, "count": len(rows)}


@app.get("/v1/lexicon")
def lexicon(language: str | None = None, limit: int = 200) -> dict[str, object]:
    try:
        rows = db.list_lexicon(language=language, limit=max(1, min(limit, 1000)))
    except db.DatabaseUnavailable as exc:
        lexicon_path = default_lexicon_path()
        if not lexicon_path.exists():
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        rows = json.loads(lexicon_path.read_text(encoding="utf-8"))["entries"]
        if language:
            rows = [row for row in rows if row["language"] == language]
        rows = rows[: max(1, min(limit, 1000))]
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
    try:
        artifact = build_review_video(
            job,
            static_root=STATIC_ROOT,
            output_root=GENERATED_PREVIEW_ROOT,
        )
    except PreviewVideoUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    filename = f"qsign-review-{job_id}.mp4"
    headers = {
        "content-disposition": f'inline; filename="{filename}"',
        "x-qsign-preview-kind": artifact.kind,
        "x-qsign-preview-duration": f"{artifact.duration_seconds:.3f}",
        "x-qsign-preview-units": str(artifact.unit_count),
    }
    if request.method == "HEAD":
        return Response(status_code=200, media_type="video/mp4", headers=headers)
    return FileResponse(
        artifact.path,
        media_type="video/mp4",
        headers=headers,
    )


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
        raise HTTPException(status_code=404, detail=f"Translation jobs not found: {', '.join(missing_ids)}")
    return build_ai_video_batch_brief(jobs_with_render_plans, title=payload.title)


@app.get("/v1/review/jobs")
def review_jobs(
    request: Request,
    review_status: str | None = None,
    limit: int = 50,
) -> dict[str, object]:
    require_review_access(request)
    try:
        items = db.list_translation_jobs(
            review_status=review_status,
            limit=max(1, min(limit, 200)),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except db.DatabaseUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"items": items, "count": len(items)}


@app.patch("/v1/review/jobs/{job_id}")
def review_job(job_id: str, payload: ReviewStatusRequest, request: Request) -> dict[str, object]:
    require_review_access(request)
    try:
        job = db.update_review_status(job_id, payload.review_status)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except db.DatabaseUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if not job:
        raise HTTPException(status_code=404, detail="Translation job not found")
    return job


@app.get("/v1/review/feedback")
def review_feedback(request: Request, job_id: str | None = None, limit: int = 50) -> dict[str, object]:
    require_review_access(request)
    try:
        items = db.list_feedback_events(job_id=job_id, limit=max(1, min(limit, 200)))
    except db.DatabaseUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"items": items, "count": len(items)}


@app.get("/v1/review/sessions")
def review_sessions(request: Request, job_id: str | None = None, limit: int = 50) -> dict[str, object]:
    require_review_access(request)
    try:
        items = db.list_review_sessions(job_id=job_id, limit=max(1, min(limit, 200)))
    except db.DatabaseUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"items": items, "count": len(items)}


@app.post("/v1/review/sessions")
def create_review_session(payload: ReviewSessionRequest, request: Request) -> dict[str, object]:
    require_review_access(request)
    try:
        job = db.get_translation_job(payload.job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Translation job not found")
        session = db.create_review_session(
            job_id=payload.job_id,
            reviewer_role=payload.reviewer_role,
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
            updated_job = db.update_review_status(payload.job_id, payload.review_status)
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
    require_review_access(request)
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


def require_review_access(request: Request) -> None:
    if not settings.review_token:
        raise HTTPException(status_code=503, detail="Review API is not configured")
    supplied = request.headers.get("x-qsign-review-token", "")
    if not secrets.compare_digest(supplied, settings.review_token):
        raise HTTPException(status_code=403, detail="Review API token is invalid")


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
