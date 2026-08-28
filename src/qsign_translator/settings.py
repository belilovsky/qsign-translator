from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
import tempfile


@dataclass(frozen=True)
class Settings:
    environment: str
    database_url: str | None
    asset_root: str
    generated_media_root: str
    model_cache: str
    review_token: str | None
    review_session_secret: str | None
    review_cookie_name: str
    review_cookie_secure: bool
    qazcompute_language_routing_mode: str
    qazcompute_language_routing_endpoint: str | None
    qazcompute_language_routing_api_key: str | None
    qazcompute_language_routing_timeout_seconds: float
    identity_mode: str
    identity_issuer: str
    identity_audience: str | None
    identity_provider_accepted: bool


def get_settings() -> Settings:
    environment = os.environ.get("QSIGN_ENV", "local")
    return Settings(
        environment=environment,
        database_url=os.environ.get("DATABASE_URL"),
        asset_root=os.environ.get("QSIGN_ASSET_ROOT", "/assets"),
        generated_media_root=os.environ.get(
            "QSIGN_GENERATED_MEDIA_ROOT",
            str(Path(tempfile.gettempdir()) / "qsign-generated-media"),
        ),
        model_cache=os.environ.get("QSIGN_MODEL_CACHE", "/models"),
        review_token=os.environ.get("QSIGN_REVIEW_TOKEN"),
        review_session_secret=os.environ.get("QSIGN_REVIEW_SESSION_SECRET"),
        review_cookie_name=os.environ.get("QSIGN_REVIEW_COOKIE_NAME", "qsign_review_session"),
        review_cookie_secure=os.environ.get("QSIGN_REVIEW_COOKIE_SECURE", "").lower()
        not in {"0", "false", "no"}
        if os.environ.get("QSIGN_REVIEW_COOKIE_SECURE") is not None
        else environment != "local",
        qazcompute_language_routing_mode=os.environ.get(
            "QSIGN_QAZCOMPUTE_LANGUAGE_ROUTING_MODE", "disabled"
        ).strip().lower(),
        qazcompute_language_routing_endpoint=os.environ.get(
            "QSIGN_QAZCOMPUTE_LANGUAGE_ROUTING_ENDPOINT"
        ) or None,
        qazcompute_language_routing_api_key=os.environ.get(
            "QSIGN_QAZCOMPUTE_LANGUAGE_ROUTING_API_KEY"
        ) or None,
        qazcompute_language_routing_timeout_seconds=float(
            os.environ.get("QSIGN_QAZCOMPUTE_LANGUAGE_ROUTING_TIMEOUT_SECONDS", "1.0")
        ),
        identity_mode=os.environ.get("QSIGN_IDENTITY_MODE", "documented").strip().lower(),
        identity_issuer=os.environ.get("QSIGN_IDENTITY_ISSUER", "https://id.qdev.run").strip(),
        identity_audience=os.environ.get("QSIGN_IDENTITY_AUDIENCE") or None,
        identity_provider_accepted=os.environ.get("QSIGN_IDENTITY_PROVIDER_ACCEPTED", "").lower()
        in {"1", "true", "yes"},
    )
