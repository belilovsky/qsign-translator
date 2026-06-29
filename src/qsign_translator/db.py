from __future__ import annotations

from contextlib import contextmanager
import json
from typing import Any, Iterator

from .planner import SignPlan
from .settings import get_settings


class DatabaseUnavailable(RuntimeError):
    pass


VALID_FEEDBACK_TYPES = {
    "good",
    "wrong_sign",
    "unclear_sign",
    "missing_sign",
    "offensive",
}
VALID_REVIEW_STATUSES = {"pending_signer_review", "approved", "rejected", "needs_edit"}
VALID_PUBLISH_STATUSES = {
    "draft",
    "final_review_pending",
    "publishable",
    "needs_video_fix",
    "rejected",
}
VALID_REVIEWER_ROLES = {
    "admin",
    "reviewer",
    "linguist",
    "operator",
    "native_signer",
}
VALID_LEXICON_SUGGESTION_STATUSES = {"open", "accepted", "rejected", "applied"}
POSTGRES_INVALID_TEXT_REPRESENTATION = "22P02"


def _import_psycopg():
    try:
        import psycopg
        from psycopg.rows import dict_row
    except ImportError as exc:  # pragma: no cover - depends on optional db extra
        raise DatabaseUnavailable("Install qsign-translator[db] to use Postgres") from exc
    return psycopg, dict_row


def _is_invalid_text_representation(exc: Exception) -> bool:
    return (
        getattr(exc, "sqlstate", None) == POSTGRES_INVALID_TEXT_REPRESENTATION
        or exc.__class__.__name__ == "InvalidTextRepresentation"
    )


@contextmanager
def connect() -> Iterator[Any]:
    settings = get_settings()
    if not settings.database_url:
        raise DatabaseUnavailable("DATABASE_URL is not configured")
    psycopg, dict_row = _import_psycopg()
    with psycopg.connect(settings.database_url, row_factory=dict_row, connect_timeout=3) as conn:
        yield conn


def readiness() -> dict[str, Any]:
    settings = get_settings()
    if not settings.database_url:
        return {
            "configured": False,
            "ok": False,
            "reason": "DATABASE_URL is not configured",
        }
    try:
        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        (SELECT count(*) FROM source_registry) AS sources,
                        (SELECT count(*) FROM lexicon_entries) AS lexicon_entries
                    """
                )
                row = cur.fetchone() or {}
        return {"configured": True, "ok": True, **dict(row)}
    except Exception as exc:  # pragma: no cover - operational readiness path
        return {"configured": True, "ok": False, "reason": str(exc)}


def list_sources(limit: int = 100) -> list[dict[str, Any]]:
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, name, url, task, languages, status, license_note, updated_at
                FROM source_registry
                ORDER BY id
                LIMIT %s
                """,
                (limit,),
            )
            return [dict(row) for row in cur.fetchall()]


def list_lexicon(language: str | None = None, limit: int = 200) -> list[dict[str, Any]]:
    with connect() as conn:
        with conn.cursor() as cur:
            if language:
                cur.execute(
                    """
                    SELECT token, gloss, language, source, confidence, clip_id, review_status, updated_at
                    FROM lexicon_entries
                    WHERE language = %s
                    ORDER BY language, token, gloss
                    LIMIT %s
                    """,
                    (language, limit),
                )
            else:
                cur.execute(
                    """
                    SELECT token, gloss, language, source, confidence, clip_id, review_status, updated_at
                    FROM lexicon_entries
                    ORDER BY language, token, gloss
                    LIMIT %s
                    """,
                    (limit,),
                )
            return [dict(row) for row in cur.fetchall()]


def record_translation_job(plan: SignPlan, input_type: str = "text") -> str:
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO translation_jobs (
                    input_type,
                    input_text,
                    detected_language,
                    status,
                    output_kind,
                    output_status,
                    confidence,
                    warnings,
                    review_status,
                    risk_domains,
                    source_ids,
                    fallback_count,
                    unknown_token_count
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    input_type,
                    plan.input_text,
                    plan.language,
                    plan.job_status,
                    plan.output_kind,
                    plan.output_status,
                    plan.confidence,
                    plan.to_dict()["warnings"],
                    "pending_signer_review",
                    plan.risk_domains,
                    plan.source_ids,
                    plan.fallback_count,
                    plan.unknown_token_count,
                ),
            )
            row = cur.fetchone()
            if not row:
                raise DatabaseUnavailable("translation job was not created")
            job_id = str(row["id"])
            for position, unit in enumerate(plan.units, start=1):
                cur.execute(
                    """
                    INSERT INTO sign_plan_units (
                        job_id,
                        position,
                        kind,
                        source_token,
                        gloss,
                        confidence,
                        source,
                        clip_id
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        job_id,
                        position,
                        unit.kind,
                        unit.source_token,
                        unit.gloss,
                        unit.confidence,
                        unit.source,
                        unit.clip_id,
                    ),
                )
            _record_audit_event(
                cur,
                job_id=job_id,
                event_type="job_created",
                actor_role="system",
                detail={"input_type": input_type, "language": plan.language},
            )
        conn.commit()
    return job_id


def get_translation_job(job_id: str) -> dict[str, Any] | None:
    with connect() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute(
                    """
                    SELECT
                        id,
                        input_type,
                        input_text,
                        detected_language,
                        status,
                        output_kind,
                        output_status,
                        confidence,
                        warnings,
                        review_status,
                        publish_status,
                        risk_domains,
                        source_ids,
                        fallback_count,
                        unknown_token_count,
                        output_uri,
                        render_adapter,
                        created_at,
                        updated_at
                    FROM translation_jobs
                    WHERE id = %s
                    """,
                    (job_id,),
                )
            except Exception as exc:
                if _is_invalid_text_representation(exc):
                    return None
                raise
            job = cur.fetchone()
            if not job:
                return None
            cur.execute(
                """
                SELECT
                    position,
                    kind,
                    source_token,
                    gloss,
                    confidence,
                    source,
                    clip_id
                FROM sign_plan_units
                WHERE job_id = %s
                ORDER BY position
                """,
                (job_id,),
            )
            units = [dict(row) for row in cur.fetchall()]
    result = dict(job)
    result["id"] = str(result["id"])
    result["units"] = units
    return result


def list_translation_jobs(
    review_status: str | None = None,
    publish_status: str | None = None,
    detected_language: str | None = None,
    search_query: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    if review_status and review_status not in VALID_REVIEW_STATUSES:
        raise ValueError("Unsupported review status")
    if publish_status and publish_status not in VALID_PUBLISH_STATUSES:
        raise ValueError("Unsupported publish status")
    with connect() as conn:
        with conn.cursor() as cur:
            conditions: list[str] = []
            params: list[Any] = []
            if review_status:
                conditions.append("review_status = %s")
                params.append(review_status)
            if publish_status:
                conditions.append("publish_status = %s")
                params.append(publish_status)
            if detected_language:
                conditions.append("detected_language = %s")
                params.append(detected_language)
            if search_query:
                conditions.append("COALESCE(input_text, '') ILIKE %s")
                params.append(f"%{search_query}%")
            where_sql = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            cur.execute(
                f"""
                SELECT
                    id,
                    input_type,
                    input_text,
                    detected_language,
                    status,
                    output_kind,
                    output_status,
                    confidence,
                    warnings,
                    review_status,
                    publish_status,
                    risk_domains,
                    source_ids,
                    fallback_count,
                    unknown_token_count,
                    created_at,
                    updated_at
                FROM translation_jobs
                {where_sql}
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (*params, limit),
            )
            return [_stringify_id(row) for row in cur.fetchall()]


def update_review_status(
    job_id: str,
    review_status: str,
    *,
    actor_role: str = "reviewer",
) -> dict[str, Any] | None:
    if review_status not in VALID_REVIEW_STATUSES:
        raise ValueError("Unsupported review status")
    with connect() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute(
                    """
                    UPDATE translation_jobs
                    SET review_status = %s, updated_at = now()
                    WHERE id = %s
                    RETURNING
                        id,
                        input_type,
                        input_text,
                        detected_language,
                        status,
                        output_kind,
                        output_status,
                        confidence,
                        warnings,
                        review_status,
                        publish_status,
                        risk_domains,
                        source_ids,
                        fallback_count,
                        unknown_token_count,
                        created_at,
                        updated_at
                    """,
                    (review_status, job_id),
                )
            except Exception as exc:
                if _is_invalid_text_representation(exc):
                    return None
                raise
            row = cur.fetchone()
            if row:
                _record_audit_event(
                    cur,
                    job_id=job_id,
                    event_type="review_status_updated",
                    actor_role=actor_role,
                    detail={"review_status": review_status},
                )
        conn.commit()
    if not row:
        return None
    return _stringify_id(row)


def list_feedback_events(job_id: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    with connect() as conn:
        with conn.cursor() as cur:
            if job_id:
                try:
                    cur.execute(
                        """
                        SELECT id, job_id, feedback_type, note, created_at
                        FROM feedback_events
                        WHERE job_id = %s
                        ORDER BY created_at DESC
                        LIMIT %s
                        """,
                        (job_id, limit),
                    )
                except Exception as exc:
                    if _is_invalid_text_representation(exc):
                        return []
                    raise
            else:
                cur.execute(
                    """
                    SELECT id, job_id, feedback_type, note, created_at
                    FROM feedback_events
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (limit,),
                )
            return [_stringify_id(row, extra_uuid_fields=("job_id",)) for row in cur.fetchall()]


def record_feedback(job_id: str, feedback_type: str, note: str | None = None) -> str:
    if feedback_type not in VALID_FEEDBACK_TYPES:
        raise ValueError("Unsupported feedback type")
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO feedback_events (job_id, feedback_type, note)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (job_id, feedback_type, note),
            )
            row = cur.fetchone()
            if not row:
                raise DatabaseUnavailable("feedback event was not created")
            _record_audit_event(
                cur,
                job_id=job_id,
                event_type="feedback_recorded",
                actor_role="user",
                detail={"feedback_type": feedback_type, "has_note": bool(note)},
            )
        conn.commit()
    return str(row["id"])


def list_review_sessions(job_id: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    with connect() as conn:
        with conn.cursor() as cur:
            if job_id:
                try:
                    cur.execute(
                        """
                        SELECT
                            id,
                            job_id,
                            reviewer_role,
                            reviewer_language,
                            meaning_score,
                            sign_choice_score,
                            grammar_score,
                            nonmanual_score,
                            fingerspelling_score,
                            timing_score,
                            understandability_score,
                            notes,
                            blocking_issue,
                            created_at
                        FROM review_sessions
                        WHERE job_id = %s
                        ORDER BY created_at DESC
                        LIMIT %s
                        """,
                        (job_id, limit),
                    )
                except Exception as exc:
                    if _is_invalid_text_representation(exc):
                        return []
                    raise
            else:
                cur.execute(
                    """
                    SELECT
                        id,
                        job_id,
                        reviewer_role,
                        reviewer_language,
                        meaning_score,
                        sign_choice_score,
                        grammar_score,
                        nonmanual_score,
                        fingerspelling_score,
                        timing_score,
                        understandability_score,
                        notes,
                        blocking_issue,
                        created_at
                    FROM review_sessions
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (limit,),
                )
            return [_stringify_id(row, extra_uuid_fields=("job_id",)) for row in cur.fetchall()]


def create_review_session(
    *,
    job_id: str,
    reviewer_role: str,
    reviewer_language: str,
    meaning_score: int | None = None,
    sign_choice_score: int | None = None,
    grammar_score: int | None = None,
    nonmanual_score: int | None = None,
    fingerspelling_score: int | None = None,
    timing_score: int | None = None,
    understandability_score: int | None = None,
    notes: str | None = None,
    blocking_issue: bool = False,
) -> dict[str, Any] | None:
    with connect() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute(
                    """
                    INSERT INTO review_sessions (
                        job_id,
                        reviewer_role,
                        reviewer_language,
                        meaning_score,
                        sign_choice_score,
                        grammar_score,
                        nonmanual_score,
                        fingerspelling_score,
                        timing_score,
                        understandability_score,
                        notes,
                        blocking_issue
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING
                        id,
                        job_id,
                        reviewer_role,
                        reviewer_language,
                        meaning_score,
                        sign_choice_score,
                        grammar_score,
                        nonmanual_score,
                        fingerspelling_score,
                        timing_score,
                        understandability_score,
                        notes,
                        blocking_issue,
                        created_at
                    """,
                    (
                        job_id,
                        reviewer_role,
                        reviewer_language,
                        meaning_score,
                        sign_choice_score,
                        grammar_score,
                        nonmanual_score,
                        fingerspelling_score,
                        timing_score,
                        understandability_score,
                        notes,
                        blocking_issue,
                    ),
                )
            except Exception as exc:
                if _is_invalid_text_representation(exc):
                    return None
                raise
            row = cur.fetchone()
            if row:
                _record_audit_event(
                    cur,
                    job_id=job_id,
                    event_type="review_session_created",
                    actor_role=reviewer_role,
                    detail={
                        "reviewer_language": reviewer_language,
                        "blocking_issue": blocking_issue,
                        "meaning_score": meaning_score,
                        "understandability_score": understandability_score,
                    },
                )
        conn.commit()
    if not row:
        return None
    return _stringify_id(row, extra_uuid_fields=("job_id",))


def attach_rendered_video(
    job_id: str,
    *,
    output_uri: str,
    output_status: str = "ready",
    render_adapter: str = "external_upload",
) -> dict[str, Any] | None:
    with connect() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute(
                    """
                    UPDATE translation_jobs
                    SET output_uri = %s, output_status = %s, render_adapter = %s, updated_at = now()
                    WHERE id = %s
                    RETURNING
                        id,
                        input_type,
                        input_text,
                        detected_language,
                        status,
                        output_kind,
                        output_status,
                        confidence,
                        warnings,
                        review_status,
                        publish_status,
                        risk_domains,
                        source_ids,
                        fallback_count,
                        unknown_token_count,
                        output_uri,
                        render_adapter,
                        created_at,
                        updated_at
                    """,
                    (output_uri, output_status, render_adapter, job_id),
                )
            except Exception as exc:
                if _is_invalid_text_representation(exc):
                    return None
                raise
            row = cur.fetchone()
            if row:
                cur.execute(
                    """
                    UPDATE translation_jobs
                    SET publish_status = %s
                    WHERE id = %s
                    """,
                    ("final_review_pending", job_id),
                )
                row["publish_status"] = "final_review_pending"
                _record_audit_event(
                    cur,
                    job_id=job_id,
                    event_type="rendered_video_attached",
                    actor_role="operator",
                    detail={"output_uri": output_uri, "render_adapter": render_adapter},
                )
        conn.commit()
    if not row:
        return None
    return _stringify_id(row)


def update_publish_status(
    job_id: str,
    *,
    publish_status: str,
    actor_role: str = "reviewer",
    note: str | None = None,
) -> dict[str, Any] | None:
    if publish_status not in VALID_PUBLISH_STATUSES:
        raise ValueError("Unsupported publish status")
    with connect() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute(
                    """
                    UPDATE translation_jobs
                    SET publish_status = %s, updated_at = now()
                    WHERE id = %s
                    RETURNING
                        id,
                        input_type,
                        input_text,
                        detected_language,
                        status,
                        output_kind,
                        output_status,
                        confidence,
                        warnings,
                        review_status,
                        publish_status,
                        risk_domains,
                        source_ids,
                        fallback_count,
                        unknown_token_count,
                        output_uri,
                        render_adapter,
                        created_at,
                        updated_at
                    """,
                    (publish_status, job_id),
                )
            except Exception as exc:
                if _is_invalid_text_representation(exc):
                    return None
                raise
            row = cur.fetchone()
            if row:
                _record_audit_event(
                    cur,
                    job_id=job_id,
                    event_type="publish_status_updated",
                    actor_role=actor_role,
                    detail={"publish_status": publish_status, "note": note or ""},
                )
        conn.commit()
    if not row:
        return None
    return _stringify_id(row)


def list_audit_events(job_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    with connect() as conn:
        with conn.cursor() as cur:
            if job_id:
                try:
                    cur.execute(
                        """
                        SELECT id, job_id, event_type, actor_role, detail, created_at
                        FROM audit_events
                        WHERE job_id = %s
                        ORDER BY created_at DESC
                        LIMIT %s
                        """,
                        (job_id, limit),
                    )
                except Exception as exc:
                    if _is_invalid_text_representation(exc):
                        return []
                    raise
            else:
                cur.execute(
                    """
                    SELECT id, job_id, event_type, actor_role, detail, created_at
                    FROM audit_events
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (limit,),
                )
            return [_stringify_id(row, extra_uuid_fields=("job_id",)) for row in cur.fetchall()]


def review_metrics(limit: int = 500) -> dict[str, Any]:
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    count(*) AS total_jobs,
                    count(*) FILTER (WHERE review_status = 'pending_signer_review') AS pending_jobs,
                    count(*) FILTER (WHERE review_status = 'needs_edit') AS needs_edit_jobs,
                    count(*) FILTER (WHERE review_status = 'approved') AS approved_jobs,
                    count(*) FILTER (WHERE publish_status = 'publishable') AS publishable_jobs,
                    COALESCE(sum(fallback_count), 0) AS fallback_units,
                    COALESCE(sum(unknown_token_count), 0) AS unknown_tokens
                FROM (
                    SELECT *
                    FROM translation_jobs
                    ORDER BY created_at DESC
                    LIMIT %s
                ) recent_jobs
                """,
                (limit,),
            )
            totals = dict(cur.fetchone() or {})
            cur.execute(
                """
                SELECT
                    COALESCE(detected_language, 'unknown') AS language,
                    count(*) AS jobs,
                    COALESCE(sum(fallback_count), 0) AS fallback_units,
                    COALESCE(sum(unknown_token_count), 0) AS unknown_tokens
                FROM (
                    SELECT *
                    FROM translation_jobs
                    ORDER BY created_at DESC
                    LIMIT %s
                ) recent_jobs
                GROUP BY COALESCE(detected_language, 'unknown')
                ORDER BY jobs DESC, language ASC
                """,
                (limit,),
            )
            by_language = [dict(row) for row in cur.fetchall()]
    return {"limit": limit, "totals": totals, "by_language": by_language}


def review_coverage_report(*, limit_jobs: int = 500, limit_terms: int = 50) -> dict[str, Any]:
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                WITH recent_jobs AS (
                    SELECT id, detected_language
                    FROM translation_jobs
                    ORDER BY created_at DESC
                    LIMIT %s
                ),
                fallback_units AS (
                    SELECT
                        COALESCE(rj.detected_language, 'unknown') AS language,
                        spu.source_token,
                        spu.kind
                    FROM sign_plan_units spu
                    JOIN recent_jobs rj ON rj.id = spu.job_id
                    WHERE spu.kind <> 'gloss'
                )
                SELECT
                    language,
                    source_token,
                    kind,
                    count(*) AS hits
                FROM fallback_units
                GROUP BY language, source_token, kind
                ORDER BY hits DESC, language ASC, source_token ASC
                LIMIT %s
                """,
                (limit_jobs, limit_terms),
            )
            top_fallbacks = [dict(row) for row in cur.fetchall()]
    return {
        "limit_jobs": limit_jobs,
        "limit_terms": limit_terms,
        "top_fallbacks": top_fallbacks,
    }


def list_lexicon_suggestions(
    job_id: str | None = None,
    status: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    if status and status not in VALID_LEXICON_SUGGESTION_STATUSES:
        raise ValueError("Unsupported lexicon suggestion status")
    with connect() as conn:
        with conn.cursor() as cur:
            conditions: list[str] = []
            params: list[Any] = []
            if job_id:
                conditions.append("job_id = %s")
                params.append(job_id)
            if status:
                conditions.append("status = %s")
                params.append(status)
            where_sql = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            try:
                cur.execute(
                    f"""
                    SELECT
                        id,
                        job_id,
                        unit_position,
                        source_token,
                        suggested_gloss,
                        suggested_language,
                        suggested_clip_id,
                        reason,
                        status,
                        created_by_role,
                        created_at,
                        updated_at
                    FROM lexicon_suggestions
                    {where_sql}
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (*params, limit),
                )
            except Exception as exc:
                if job_id and _is_invalid_text_representation(exc):
                    return []
                raise
            return [_stringify_id(row, extra_uuid_fields=("job_id",)) for row in cur.fetchall()]


def create_lexicon_suggestion(
    *,
    job_id: str,
    unit_position: int,
    source_token: str,
    suggested_gloss: str,
    suggested_language: str,
    suggested_clip_id: str | None = None,
    reason: str | None = None,
    created_by_role: str,
) -> dict[str, Any] | None:
    if created_by_role not in VALID_REVIEWER_ROLES:
        raise ValueError("Unsupported reviewer role")
    with connect() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute(
                    """
                    INSERT INTO lexicon_suggestions (
                        job_id,
                        unit_position,
                        source_token,
                        suggested_gloss,
                        suggested_language,
                        suggested_clip_id,
                        reason,
                        created_by_role
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING
                        id,
                        job_id,
                        unit_position,
                        source_token,
                        suggested_gloss,
                        suggested_language,
                        suggested_clip_id,
                        reason,
                        status,
                        created_by_role,
                        created_at,
                        updated_at
                    """,
                    (
                        job_id,
                        unit_position,
                        source_token,
                        suggested_gloss,
                        suggested_language,
                        suggested_clip_id,
                        reason,
                        created_by_role,
                    ),
                )
            except Exception as exc:
                if _is_invalid_text_representation(exc):
                    return None
                raise
            row = cur.fetchone()
            if row:
                _record_audit_event(
                    cur,
                    job_id=job_id,
                    event_type="lexicon_suggestion_created",
                    actor_role=created_by_role,
                    detail={
                        "unit_position": unit_position,
                        "source_token": source_token,
                        "suggested_gloss": suggested_gloss,
                        "suggested_language": suggested_language,
                    },
                )
        conn.commit()
    if not row:
        return None
    return _stringify_id(row, extra_uuid_fields=("job_id",))


def _record_audit_event(
    cur: Any,
    *,
    job_id: str,
    event_type: str,
    actor_role: str,
    detail: dict[str, Any] | None = None,
) -> None:
    cur.execute(
        """
        INSERT INTO audit_events (job_id, event_type, actor_role, detail)
        VALUES (%s, %s, %s, %s)
        """,
        (job_id, event_type, actor_role, json.dumps(detail or {}, ensure_ascii=False)),
    )


def _stringify_id(row: dict[str, Any], extra_uuid_fields: tuple[str, ...] = ()) -> dict[str, Any]:
    result = dict(row)
    result["id"] = str(result["id"])
    for field in extra_uuid_fields:
        if result.get(field) is not None:
            result[field] = str(result[field])
    return result
