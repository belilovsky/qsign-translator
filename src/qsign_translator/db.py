from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

from .planner import SignPlan
from .settings import get_settings


class DatabaseUnavailable(RuntimeError):
    pass


VALID_FEEDBACK_TYPES = {"good", "wrong_sign", "unclear_sign", "missing_sign", "offensive"}
VALID_REVIEW_STATUSES = {"pending_signer_review", "approved", "rejected", "needs_edit"}
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
        return {"configured": False, "ok": False, "reason": "DATABASE_URL is not configured"}
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
                        risk_domains,
                        source_ids,
                        fallback_count,
                        unknown_token_count,
                        output_uri,
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
    limit: int = 50,
) -> list[dict[str, Any]]:
    if review_status and review_status not in VALID_REVIEW_STATUSES:
        raise ValueError("Unsupported review status")
    with connect() as conn:
        with conn.cursor() as cur:
            if review_status:
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
                        risk_domains,
                        source_ids,
                        fallback_count,
                        unknown_token_count,
                        created_at,
                        updated_at
                    FROM translation_jobs
                    WHERE review_status = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (review_status, limit),
                )
            else:
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
                        risk_domains,
                        source_ids,
                        fallback_count,
                        unknown_token_count,
                        created_at,
                        updated_at
                    FROM translation_jobs
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (limit,),
                )
            return [_stringify_id(row) for row in cur.fetchall()]


def update_review_status(job_id: str, review_status: str) -> dict[str, Any] | None:
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
        conn.commit()
    return str(row["id"])


def _stringify_id(row: dict[str, Any], extra_uuid_fields: tuple[str, ...] = ()) -> dict[str, Any]:
    result = dict(row)
    result["id"] = str(result["id"])
    for field in extra_uuid_fields:
        if result.get(field) is not None:
            result[field] = str(result[field])
    return result
