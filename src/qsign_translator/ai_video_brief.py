from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json


@dataclass(frozen=True)
class VideoUnitBrief:
    position: int
    source_token: str
    gloss: str
    kind: str
    clip_id: str | None
    instruction: str


def default_video_spec(language: str) -> dict[str, object]:
    return {
        "resolution": "1280x720",
        "aspect_ratio": "16:9",
        "fps": 25,
        "background": "clean soft studio background, calm light gradient, no visual clutter",
        "camera": "single locked medium shot, torso and hands fully visible at all times",
        "audio": "no spoken voice, no music",
        "subtitles": "burned-in captions in source language",
        "avatar": _avatar_spec(language),
    }


def build_ai_video_brief(job: dict[str, object], render_plan: dict[str, object]) -> dict[str, object]:
    units = list(job.get("units") or [])
    language = str(job.get("detected_language") or "unknown")
    review_status = str(job.get("review_status") or "pending_signer_review")
    risk_domains = list(job.get("risk_domains") or [])
    summary = dict(render_plan.get("summary") or {})
    publish_gate = dict(render_plan.get("publish_gate") or {})
    resolved_segments = int(summary.get("resolved_segments") or 0)
    missing_segments = int(summary.get("missing_segments") or 0)
    pipeline_status = str(render_plan.get("pipeline_status") or "awaiting_signer_review")
    duration_seconds = max(3.0, len(units) * 1.4)
    unit_briefs = [_build_unit_brief(index, unit) for index, unit in enumerate(units, start=1)]
    master_prompt = _build_master_prompt(
        language=language,
        review_status=review_status,
        risk_domains=risk_domains,
        duration_seconds=duration_seconds,
        units=unit_briefs,
        input_text=str(job.get("input_text") or ""),
    )
    negative_prompt = _build_negative_prompt()
    operator_task = _build_operator_task(
        language=language,
        risk_domains=risk_domains,
        review_status=review_status,
        units=unit_briefs,
        missing_segments=missing_segments,
        resolved_segments=resolved_segments,
    )
    brief = {
        "job_id": str(job.get("id") or ""),
        "generated_at": _iso_now(),
        "format_version": "qsign-ai-video-brief/v1",
        "summary": {
            "input_text": str(job.get("input_text") or ""),
            "language_route": language,
            "review_status": review_status,
            "risk_domains": risk_domains,
            "duration_seconds": round(duration_seconds, 2),
            "resolved_segments": resolved_segments,
            "missing_segments": missing_segments,
            "fallback_units": _count_fallback_units(unit_briefs),
            "pipeline_status": pipeline_status,
            "publish_blockers": list(publish_gate.get("blockers") or []),
            "target_output_kind": "avatar_video_prompt_package",
        },
        "video_spec": default_video_spec(language),
        "units": [
            {
                "position": unit.position,
                "source_token": unit.source_token,
                "gloss": unit.gloss,
                "kind": unit.kind,
                "clip_id": unit.clip_id,
                "instruction": unit.instruction,
            }
            for unit in unit_briefs
        ],
        "prompts": {
            "master_prompt": master_prompt,
            "negative_prompt": negative_prompt,
            "operator_task": operator_task,
        },
        "qa_checklist": [
            "Hands, wrists, elbows, and shoulders remain visible for the full clip.",
            "Signing pace is steady and readable, without jump cuts or morphing fingers.",
            "Every source token is represented in order, including dactyl for unknown terms.",
            "No lip-sync speech, dramatic acting, or decorative cinematic motion.",
            "Burned-in captions match the source text and stay legible on mobile.",
            "Output is marked as AI draft and must still be reviewed by a native signer.",
            "Do not publish or distribute as final output while pipeline blockers remain active.",
        ],
    }
    brief["batch_render"] = _build_batch_render_structure([brief], title=str(job.get("input_text") or "Single-scene batch"))
    brief["render_contract"] = _build_single_render_contract(brief)
    brief["exports"] = _build_export_formats(brief)
    return brief


def build_ai_video_batch_brief(
    jobs_with_render_plans: list[tuple[dict[str, object], dict[str, object]]],
    *,
    title: str | None = None,
) -> dict[str, object]:
    scene_briefs = [build_ai_video_brief(job, render_plan) for job, render_plan in jobs_with_render_plans]
    if not scene_briefs:
        raise ValueError("At least one job is required for batch brief")
    batch_title = title or "QSign batch render"
    languages = _ordered_unique([str(scene.get("summary", {}).get("language_route") or "unknown") for scene in scene_briefs])
    video_spec = default_video_spec(languages[0] if len(languages) == 1 else "mixed")
    batch_render = _build_batch_render_structure(scene_briefs, title=batch_title)
    batch_brief = {
        "generated_at": _iso_now(),
        "format_version": "qsign-ai-video-batch-brief/v1",
        "summary": {
            "title": batch_title,
            "scene_count": batch_render["scene_count"],
            "total_units": batch_render["total_units"],
            "fallback_units": batch_render["fallback_units"],
            "duration_seconds": batch_render["duration_seconds"],
            "languages": languages,
            "review_statuses": batch_render["review_statuses"],
            "risk_domains": batch_render["risk_domains"],
            "resolved_segments": batch_render["resolved_segments"],
            "missing_segments": batch_render["missing_segments"],
            "publishable_scene_count": batch_render["publishable_scene_count"],
            "review_required_scene_count": batch_render["review_required_scene_count"],
            "target_output_kind": "avatar_video_batch_prompt_package",
        },
        "video_spec": video_spec,
        "batch_render": batch_render,
    }
    batch_brief["exports"] = _build_batch_export_formats(batch_brief, scene_briefs)
    return batch_brief


def _build_unit_brief(position: int, unit: dict[str, object]) -> VideoUnitBrief:
    kind = str(unit.get("kind") or "unknown")
    source_token = str(unit.get("source_token") or "")
    gloss = str(unit.get("gloss") or "")
    clip_id = unit.get("clip_id")
    if kind == "gloss":
        instruction = f"Sign the concept '{source_token}' using gloss {gloss}."
    elif kind == "dactyl":
        instruction = f"Finger-spell '{source_token}' clearly and slowly."
    else:
        instruction = f"Show a cautious placeholder beat for '{source_token}' and keep subtitle visible."
    return VideoUnitBrief(
        position=position,
        source_token=source_token,
        gloss=gloss,
        kind=kind,
        clip_id=str(clip_id) if clip_id else None,
        instruction=instruction,
    )


def _avatar_spec(language: str) -> str:
    if language == "kk":
        return (
            "Single adult signer with calm professional presence, Central Asian appearance, "
            "neutral dark clothing, hair tied back, high hand contrast, clear front lighting."
        )
    return (
        "Single adult signer with calm professional presence, neutral dark clothing, "
        "hair tied back, high hand contrast, clear front lighting."
    )


def _sign_language_label(language: str) -> str:
    if language == "kk":
        return "Kazakh sign-language draft aligned to KRSL conventions when possible"
    if language == "ru":
        return "Russian sign-language draft aligned to RSL conventions when possible"
    if language == "mixed":
        return "mixed RU/KZ sign-language draft with explicit fallback handling"
    return "sign-language draft with explicit fallback handling"


def _build_master_prompt(
    *,
    language: str,
    review_status: str,
    risk_domains: list[str],
    duration_seconds: float,
    units: list[VideoUnitBrief],
    input_text: str,
) -> str:
    unit_lines = "\n".join(
        f"{unit.position}. token='{unit.source_token}' | kind={unit.kind} | gloss='{unit.gloss}' | instruction={unit.instruction}"
        for unit in units
    )
    risk_clause = (
        f"High-risk domains present: {', '.join(risk_domains)}. Keep the tone extra neutral and informational."
        if risk_domains
        else "No high-risk domain flag in this draft, but still treat the result as review-only."
    )
    return (
        "Generate a single clean sign-language draft video for human review.\n"
        f"Source text: {input_text}\n"
        f"Target signing route: {_sign_language_label(language)}.\n"
        f"Review status: {review_status}. This is an AI draft, not a certified interpreter output.\n"
        f"Pipeline status: {pipeline_status_from_review(review_status, units)}.\n"
        f"Target duration: about {duration_seconds:.1f} seconds.\n"
        "Visual direction: one signer only, centered medium shot, hands always visible, neutral studio background, "
        "no camera moves, no cuts, no props, no decorative motion graphics.\n"
        "Performance direction: calm, legible, instructional signing pace; prioritize readability over drama.\n"
        "Caption direction: burned-in captions in the source language, concise and readable.\n"
        f"{risk_clause}\n"
        "Sign sequence:\n"
        f"{unit_lines}\n"
        "If a unit is marked dactyl, finger-spell it clearly instead of inventing a lexical sign. "
        "If a unit is uncertain, keep the subtitle and use a restrained placeholder motion rather than hallucinating a fluent sign."
    )


def _build_negative_prompt() -> str:
    return (
        "Do not generate multiple people, cinematic camera moves, fast cuts, shaky hands, cropped wrists, "
        "hidden fingers, spoken lip-sync, exaggerated emotions, comedy acting, extra objects, busy background, "
        "hallucinated lexical signs for unknown words, mirrored hand confusion, unreadable captions, or logo overlays."
    )


def _build_operator_task(
    *,
    language: str,
    risk_domains: list[str],
    review_status: str,
    units: list[VideoUnitBrief],
    missing_segments: int,
    resolved_segments: int,
) -> str:
    return (
        "Task for the video generator or operator:\n"
        f"- Produce one {language} draft signer video from the provided sign plan.\n"
        f"- Use the unit list exactly in order ({len(units)} units total).\n"
        f"- Respect review status: {review_status}.\n"
        f"- Clip-backed coverage available internally: {resolved_segments}; missing lexical coverage: {missing_segments}.\n"
        f"- High-risk domains: {', '.join(risk_domains) if risk_domains else 'none flagged'}.\n"
        "- Unknown terms must remain dactyl or visibly marked fallback, never be improvised as fluent native signs.\n"
        "- Final delivery should be one reviewable mp4 plus the exact source captions.\n"
        "- If blockers remain, keep the package in draft state and route it back to reviewer operations."
    )


def pipeline_status_from_review(review_status: str, units: list[VideoUnitBrief]) -> str:
    if review_status == "approved":
        if any(unit.kind != "gloss" or not unit.clip_id for unit in units):
            return "approved_with_fallback_or_missing_assets"
        return "approved_ready_for_render"
    return "awaiting_signer_review"


def _build_export_formats(brief: dict[str, object]) -> dict[str, dict[str, str]]:
    prompts = dict(brief.get("prompts") or {})
    units = list(brief.get("units") or [])
    checklist = list(brief.get("qa_checklist") or [])
    summary = dict(brief.get("summary") or {})
    video_spec = dict(brief.get("video_spec") or {})
    universal_lines = [
        "QSign AI Video Brief",
        f"job_id: {brief.get('job_id') or '-'}",
        f"generated_at: {brief.get('generated_at') or '-'}",
        f"route: {summary.get('language_route') or '-'}",
        f"duration_seconds: {summary.get('duration_seconds') or '-'}",
        f"resolution: {video_spec.get('resolution') or '-'}",
        f"fps: {video_spec.get('fps') or '-'}",
        f"review_status: {summary.get('review_status') or '-'}",
        f"risk_domains: {', '.join(summary.get('risk_domains') or []) or 'none'}",
        "",
        "MASTER PROMPT",
        str(prompts.get("master_prompt") or ""),
        "",
        "NEGATIVE PROMPT",
        str(prompts.get("negative_prompt") or ""),
        "",
        "OPERATOR TASK",
        str(prompts.get("operator_task") or ""),
        "",
        "UNITS",
        *[
            f"- {unit.get('position')}. {unit.get('source_token')} | {unit.get('kind')} | {unit.get('gloss')} | {unit.get('instruction')}"
            for unit in units
        ],
        "",
        "QA CHECKLIST",
        *[f"- {item}" for item in checklist],
    ]
    operator_lines = [
        "Operator handoff for AI signer draft production",
        f"Job: {brief.get('job_id') or '-'}",
        f"Generated at: {brief.get('generated_at') or '-'}",
        f"Route: {summary.get('language_route') or '-'}",
        f"Target duration: {summary.get('duration_seconds') or '-'} seconds",
        f"Review status: {summary.get('review_status') or '-'}",
        "",
        str(prompts.get("operator_task") or ""),
        "",
        "Execution checklist:",
        "- Keep one signer in frame from waist/chest up with both hands fully visible.",
        "- Preserve source-language burned-in captions.",
        "- Use the provided sequence exactly; do not reorder units.",
        "- Escalate fallback units to human reviewer instead of improvising a fluent sign.",
        "",
        "Unit sequence:",
        *[
            f"{unit.get('position')}. {unit.get('source_token')} -> {unit.get('instruction')}"
            for unit in units
        ],
    ]
    batch = dict(brief.get("batch_render") or {})
    scene_lines = [
        "Batch storyboard for sequential render",
        f"Generated at: {brief.get('generated_at') or '-'}",
        f"Title: {batch.get('title') or '-'}",
        f"Scenes: {batch.get('scene_count') or 0}",
        f"Total duration: {batch.get('duration_seconds') or 0} seconds",
        f"Transitions: {batch.get('transition_style') or '-'}",
        "",
        "Scene order:",
        *[
                (
                    f"{scene.get('scene_number')}. job={scene.get('job_id')} | {scene.get('input_text')} | "
                    f"{scene.get('language_route')} | {scene.get('duration_seconds')}s | "
                    f"start={scene.get('start_time_seconds')} end={scene.get('end_time_seconds')}"
                )
            for scene in batch.get("scenes") or []
        ],
        "",
        "Batch rules:",
        "- Keep the same signer, framing, and lighting across all scenes.",
        "- Separate scenes with a clean hard cut and a short neutral hold.",
        "- Preserve per-scene captions and do not merge neighboring phrases.",
        "- If a scene has fallback units, keep them visible for reviewer attention.",
    ]
    return {
        "universal_prompt": {
            "label": "Universal prompt",
            "text": "\n".join(universal_lines),
        },
        "operator_handoff": {
            "label": "Operator handoff",
            "text": "\n".join(operator_lines),
        },
        "json_payload": {
            "label": "JSON payload",
            "text": json.dumps(brief, ensure_ascii=False, indent=2),
        },
        "render_contract": {
            "label": "Render contract",
            "text": _render_contract_text(dict(brief.get("render_contract") or {})),
        },
        "batch_storyboard": {
            "label": "Batch storyboard",
            "text": "\n".join(scene_lines),
        },
    }


def _build_batch_render_structure(scene_briefs: list[dict[str, object]], *, title: str) -> dict[str, object]:
    scenes: list[dict[str, object]] = []
    cursor_seconds = 0.0
    resolved_total = 0
    missing_total = 0
    risk_domains: list[str] = []
    review_statuses: list[str] = []
    total_units = 0
    fallback_units = 0
    publishable_scene_count = 0
    review_required_scene_count = 0
    hold_seconds = 0.4
    for index, brief in enumerate(scene_briefs, start=1):
        summary = dict(brief.get("summary") or {})
        units = list(brief.get("units") or [])
        duration = float(summary.get("duration_seconds") or 0.0)
        resolved = int(summary.get("resolved_segments") or 0)
        missing = int(summary.get("missing_segments") or 0)
        resolved_total += resolved
        missing_total += missing
        total_units += len(units)
        fallback_units += int(summary.get("fallback_units") or 0)
        review_status = str(summary.get("review_status") or "pending_signer_review")
        review_statuses.append(review_status)
        scene_publishable = review_status == "approved" and missing == 0 and int(summary.get("fallback_units") or 0) == 0
        if scene_publishable:
            publishable_scene_count += 1
        else:
            review_required_scene_count += 1
        for domain in summary.get("risk_domains") or []:
            domain_value = str(domain)
            if domain_value not in risk_domains:
                risk_domains.append(domain_value)
        scenes.append(
            {
                "scene_number": index,
                "job_id": str(brief.get("job_id") or ""),
                "input_text": str(summary.get("input_text") or ""),
                "language_route": str(summary.get("language_route") or "unknown"),
                "review_status": review_status,
                "duration_seconds": round(duration, 2),
                "start_time_seconds": round(cursor_seconds, 2),
                "end_time_seconds": round(cursor_seconds + duration, 2),
                "resolved_segments": resolved,
                "missing_segments": missing,
                "fallback_units": int(summary.get("fallback_units") or 0),
                "scene_publishable": scene_publishable,
                "units": units,
            }
        )
        cursor_seconds += duration
        if index < len(scene_briefs):
            cursor_seconds += hold_seconds
    return {
        "title": title,
        "scene_count": len(scenes),
        "total_units": total_units,
        "fallback_units": fallback_units,
        "duration_seconds": round(cursor_seconds, 2),
        "transition_style": "hard_cut_with_0.4s_hold",
        "resolved_segments": resolved_total,
        "missing_segments": missing_total,
        "publishable_scene_count": publishable_scene_count,
        "review_required_scene_count": review_required_scene_count,
        "risk_domains": risk_domains,
        "review_statuses": _ordered_unique(review_statuses),
        "scenes": scenes,
    }


def _build_batch_export_formats(
    batch_brief: dict[str, object],
    scene_briefs: list[dict[str, object]],
) -> dict[str, dict[str, str]]:
    summary = dict(batch_brief.get("summary") or {})
    batch = dict(batch_brief.get("batch_render") or {})
    storyboard_lines = [
        "QSign Batch AI Video Brief",
        f"generated_at: {batch_brief.get('generated_at') or '-'}",
        f"title: {summary.get('title') or '-'}",
        f"scene_count: {summary.get('scene_count') or 0}",
        f"duration_seconds: {summary.get('duration_seconds') or 0}",
        f"languages: {', '.join(summary.get('languages') or []) or 'unknown'}",
        f"review_statuses: {', '.join(summary.get('review_statuses') or []) or 'pending_signer_review'}",
        "",
        "ASSEMBLY RULES",
        "- Keep a single signer and locked camera across the full batch.",
        "- Render one phrase per scene in the given order.",
        "- Use hard cuts only, with 0.4 second neutral hold between scenes.",
        "- Keep captions per scene and reset them between phrases.",
        "",
        "SCENES",
    ]
    for scene in batch.get("scenes") or []:
        storyboard_lines.extend(
            [
                (
                    f"{scene.get('scene_number')}. scene job={scene.get('job_id')} "
                    f"start={scene.get('start_time_seconds')} end={scene.get('end_time_seconds')}"
                ),
                f"   text: {scene.get('input_text')}",
                f"   route: {scene.get('language_route')} | review: {scene.get('review_status')}",
                (
                    f"   coverage: resolved={scene.get('resolved_segments')} "
                    f"missing={scene.get('missing_segments')}"
                ),
            ]
        )
    runbook_lines = [
        "Operator runbook for multi-scene signer draft batch",
        f"Generated at: {batch_brief.get('generated_at') or '-'}",
        f"Batch title: {summary.get('title') or '-'}",
        f"Scenes: {summary.get('scene_count') or 0}",
        f"Total duration: {summary.get('duration_seconds') or 0} seconds",
        "",
        "Run order:",
    ]
    for scene in batch.get("scenes") or []:
        runbook_lines.append(
            f"- Scene {scene.get('scene_number')}: {scene.get('input_text')} ({scene.get('language_route')})"
        )
    runbook_lines.extend(
        [
            "",
            "Operator constraints:",
            "- Do not merge scenes into one continuous sentence without visible separation.",
            "- Keep the same wardrobe, background, and light for batch consistency.",
            "- Stop for manual review when any scene contains missing lexical coverage.",
            "- Deliver one merged mp4 plus scene timestamps for QA.",
        ]
    )
    return {
        "batch_storyboard": {
            "label": "Batch storyboard",
            "text": "\n".join(storyboard_lines),
        },
        "operator_runbook": {
            "label": "Operator runbook",
            "text": "\n".join(runbook_lines),
        },
        "json_payload": {
            "label": "JSON payload",
            "text": json.dumps(batch_brief, ensure_ascii=False, indent=2),
        },
        "render_contract": {
            "label": "Render contract",
            "text": _batch_render_contract_text(batch_brief),
        },
        "scene_prompts": {
            "label": "Scene prompts",
            "text": "\n\n".join(
                [
                    f"SCENE {index}\n{scene.get('prompts', {}).get('master_prompt') or ''}"
                    for index, scene in enumerate(scene_briefs, start=1)
                ]
            ),
        },
    }


def _ordered_unique(values: list[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        if value not in result:
            result.append(value)
    return result


def _iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _count_fallback_units(units: list[VideoUnitBrief]) -> int:
    return sum(1 for unit in units if unit.kind != "gloss" or not unit.clip_id)


def _build_single_render_contract(brief: dict[str, object]) -> dict[str, object]:
    summary = dict(brief.get("summary") or {})
    blockers = list(summary.get("publish_blockers") or [])
    units = list(brief.get("units") or [])
    return {
        "contract_version": "qsign-render-contract/v1",
        "job_id": brief.get("job_id") or "",
        "target_filename": f"{brief.get('job_id') or 'qsign-job'}-draft.mp4",
        "duration_seconds": summary.get("duration_seconds"),
        "language_route": summary.get("language_route"),
        "review_status": summary.get("review_status"),
        "pipeline_status": summary.get("pipeline_status"),
        "fallback_units": summary.get("fallback_units"),
        "publish_blockers": blockers,
        "must_hold_for_review": bool(blockers),
        "unit_order": [
            {
                "position": unit.get("position"),
                "source_token": unit.get("source_token"),
                "kind": unit.get("kind"),
                "instruction": unit.get("instruction"),
            }
            for unit in units
        ],
        "acceptance": [
            "one signer only",
            "both hands visible in every frame",
            "captions match the source text",
            "fallback units remain explicit and are not improvised",
            "result stays in draft state while publish blockers remain",
        ],
    }


def _render_contract_text(contract: dict[str, object]) -> str:
    unit_order = contract.get("unit_order") or []
    lines = [
        "QSign render contract",
        f"job_id: {contract.get('job_id') or '-'}",
        f"target_filename: {contract.get('target_filename') or '-'}",
        f"route: {contract.get('language_route') or '-'}",
        f"duration_seconds: {contract.get('duration_seconds') or '-'}",
        f"review_status: {contract.get('review_status') or '-'}",
        f"pipeline_status: {contract.get('pipeline_status') or '-'}",
        f"fallback_units: {contract.get('fallback_units') or 0}",
        f"must_hold_for_review: {'yes' if contract.get('must_hold_for_review') else 'no'}",
        f"publish_blockers: {', '.join(contract.get('publish_blockers') or []) or 'none'}",
        "",
        "UNIT ORDER",
        *[
            f"- {unit.get('position')}. {unit.get('source_token')} | {unit.get('kind')} | {unit.get('instruction')}"
            for unit in unit_order
        ],
        "",
        "ACCEPTANCE",
        *[f"- {item}" for item in contract.get("acceptance") or []],
    ]
    return "\n".join(lines)


def _batch_render_contract_text(batch_brief: dict[str, object]) -> str:
    summary = dict(batch_brief.get("summary") or {})
    batch = dict(batch_brief.get("batch_render") or {})
    lines = [
        "QSign batch render contract",
        f"title: {summary.get('title') or '-'}",
        f"scene_count: {summary.get('scene_count') or 0}",
        f"publishable_scene_count: {summary.get('publishable_scene_count') or 0}",
        f"review_required_scene_count: {summary.get('review_required_scene_count') or 0}",
        f"fallback_units: {summary.get('fallback_units') or 0}",
        f"duration_seconds: {summary.get('duration_seconds') or 0}",
        "",
        "SCENE CONTRACT",
    ]
    for scene in batch.get("scenes") or []:
        lines.append(
            f"- scene {scene.get('scene_number')}: publishable={'yes' if scene.get('scene_publishable') else 'no'} | "
            f"fallback_units={scene.get('fallback_units') or 0} | "
            f"start={scene.get('start_time_seconds')} end={scene.get('end_time_seconds')} | "
            f"text={scene.get('input_text')}"
        )
    lines.extend(
        [
            "",
            "GLOBAL ACCEPTANCE",
            "- keep one signer and one camera setup across the full batch",
            "- keep per-scene boundaries visible and do not merge phrases",
            "- stop before publication when any scene still needs review",
            "- return one merged mp4 and scene timestamps for QA",
        ]
    )
    return "\n".join(lines)
