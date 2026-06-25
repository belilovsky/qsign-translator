from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .planner import SignPlan


@dataclass(frozen=True)
class VideoSegment:
    gloss: str
    clip_id: str
    path: Path


@dataclass(frozen=True)
class JobVideoSegment:
    position: int
    kind: str
    source_token: str
    gloss: str
    clip_id: str
    asset_key: str


def resolve_segments(plan: SignPlan, clip_root: Path) -> list[VideoSegment]:
    """Resolve known gloss units to local clips.

    Missing clips are skipped at this layer. The UI/API should expose skipped
    units as subtitles or dactyl placeholders.
    """

    segments: list[VideoSegment] = []
    for unit in plan.units:
        if not unit.clip_id:
            continue
        path = clip_root / f"{unit.clip_id}.mp4"
        if path.exists():
            segments.append(VideoSegment(gloss=unit.gloss, clip_id=unit.clip_id, path=path))
    return segments


def write_ffmpeg_concat_file(segments: list[VideoSegment], output_path: Path) -> None:
    lines = [f"file '{segment.path.as_posix()}'" for segment in segments]
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_job_render_plan(job: dict[str, object], asset_root: str) -> dict[str, object]:
    clip_root = Path(asset_root) / "clips"
    resolved: list[JobVideoSegment] = []
    missing: list[dict[str, object]] = []
    units = list(job.get("units") or [])

    for index, unit in enumerate(units, start=1):
        position = int(unit.get("position") or index)
        kind = str(unit.get("kind") or "unknown")
        source_token = str(unit.get("source_token") or "")
        gloss = str(unit.get("gloss") or "")
        clip_id = unit.get("clip_id")
        if clip_id:
            clip_id_value = str(clip_id)
            asset_key = f"clips/{clip_id_value}.mp4"
            asset_path = clip_root / f"{clip_id_value}.mp4"
            if asset_path.exists():
                resolved.append(
                    JobVideoSegment(
                        position=position,
                        kind=kind,
                        source_token=source_token,
                        gloss=gloss,
                        clip_id=clip_id_value,
                        asset_key=asset_key,
                    )
                )
                continue
            missing.append(
                {
                    "position": position,
                    "kind": kind,
                    "source_token": source_token,
                    "gloss": gloss,
                    "clip_id": clip_id_value,
                    "asset_key": asset_key,
                    "reason": "clip_missing",
                }
            )
            continue
        missing.append(
            {
                "position": position,
                "kind": kind,
                "source_token": source_token,
                "gloss": gloss,
                "clip_id": None,
                "asset_key": None,
                "reason": "no_clip_id",
            }
        )

    total_units = len(units)
    resolved_count = len(resolved)
    missing_count = len(missing)
    if resolved_count and not missing_count:
        adapter_status = "ready_for_render"
    elif resolved_count:
        adapter_status = "partial_assets"
    else:
        adapter_status = "awaiting_assets"

    review_status = str(job.get("review_status") or "pending_signer_review")
    publish_ready = review_status == "approved" and total_units > 0 and missing_count == 0
    renderable_ratio = round(resolved_count / total_units, 3) if total_units else 0.0

    return {
        "job_id": str(job.get("id") or ""),
        "job_status": str(job.get("status") or "unknown"),
        "review_status": review_status,
        "source_output_kind": str(job.get("output_kind") or "sign_plan_preview"),
        "source_output_status": str(job.get("output_status") or "not_rendered"),
        "target_output_kind": "avatar_video",
        "adapter": {
            "type": "local_clip_concat",
            "asset_strategy": "clip_id_to_mp4",
            "adapter_status": adapter_status,
            "ffmpeg_concat_supported": resolved_count > 0,
            "publish_ready": publish_ready,
        },
        "summary": {
            "total_units": total_units,
            "resolved_segments": resolved_count,
            "missing_segments": missing_count,
            "renderable_ratio": renderable_ratio,
        },
        "segments": [
            {
                "position": segment.position,
                "kind": segment.kind,
                "source_token": segment.source_token,
                "gloss": segment.gloss,
                "clip_id": segment.clip_id,
                "asset_key": segment.asset_key,
            }
            for segment in resolved
        ],
        "concat_entries": [segment.asset_key for segment in resolved],
        "missing": missing,
    }
