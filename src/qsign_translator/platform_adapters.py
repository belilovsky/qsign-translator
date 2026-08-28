"""Fail-closed QazStack adapters for QSign's staged platform integration.

The adapters deliberately operate on public-safe metadata only.  A local
QSign plan remains authoritative even when a remote language-routing provider
is configured: provider output is evidence for shadow comparison, never a
replacement for sign planning, review, media, or publication decisions.
"""

from __future__ import annotations

import json
import socket
from dataclasses import dataclass
from typing import Any, Callable, Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


CANONICAL_LOCALES = frozenset({"kk", "ru", "en"})
LANGUAGE_ALIASES = {
    "ru": "ru", "rus": "ru", "russian": "ru",
    "kk": "kk", "kz": "kk", "kazakh": "kk", "kazak": "kk",
    "en": "en", "eng": "en", "english": "en", "us": "en",
}
AUTO_LANGUAGE_ALIASES = frozenset({"", "auto", "detect", "detect_language", "unknown", "mixed"})
PRIVATE_FIELD_MARKERS = frozenset({
    "text", "input", "note", "notes", "reviewer", "identity", "session",
    "token", "cookie", "media", "video", "audio", "gesture", "biometric",
    "upload", "raw", "clip", "body", "payload",
})


def normalize_platform_locale(value: str | None) -> str | None:
    """Return a canonical QazStack locale, or ``None`` for automatic routing."""

    if value is None:
        return None
    normalized = str(value).strip().lower()
    if normalized in AUTO_LANGUAGE_ALIASES:
        return None
    return LANGUAGE_ALIASES.get(normalized)


def require_public_safe_mapping(value: Mapping[str, Any], *, allowed: set[str]) -> dict[str, Any]:
    """Copy an envelope only when it has the exact approved metadata fields."""

    unexpected = set(value) - allowed
    private = {key for key in value if key.lower() in PRIVATE_FIELD_MARKERS}
    if unexpected or private:
        raise ValueError("private or unsupported platform envelope field")
    return {key: value[key] for key in allowed if key in value}


def normalize_source_metadata(value: Mapping[str, Any]) -> dict[str, str | None]:
    """Project source data to the cross-product rights/provenance boundary."""

    allowed = {"id", "url", "language", "status", "license"}
    source = require_public_safe_mapping(value, allowed=allowed)
    source_id = str(source.get("id") or "").strip()
    url = str(source.get("url") or "").strip()
    if not source_id or not url.startswith(("https://", "http://")):
        raise ValueError("source metadata requires a stable id and HTTP(S) URL")
    locale = normalize_platform_locale(source.get("language"))
    if source.get("language") is not None and locale is None:
        raise ValueError("source metadata language must be kk, ru, or en")
    status = str(source.get("status") or "unknown").strip().lower()
    license_value = source.get("license")
    return {
        "id": source_id,
        "url": url,
        "language": locale,
        "status": status or "unknown",
        "license": str(license_value).strip() if license_value is not None else None,
    }


def reviewed_activity_envelope(value: Mapping[str, Any]) -> dict[str, str]:
    """Return minimal activity evidence without job, reviewer, or review content."""

    allowed = {"activity_id", "activity_type", "status", "occurred_at"}
    envelope = require_public_safe_mapping(value, allowed=allowed)
    if set(envelope) != allowed or not all(str(envelope[key]).strip() for key in allowed):
        raise ValueError("reviewed activity evidence requires four non-empty public-safe fields")
    return {key: str(envelope[key]).strip() for key in sorted(allowed)}


def asset_evidence_envelope(value: Mapping[str, Any]) -> dict[str, str]:
    """Return non-media provenance metadata; raw and derived media are excluded."""

    allowed = {"asset_id", "source_id", "rights_status", "license", "derivative_of"}
    envelope = require_public_safe_mapping(value, allowed=allowed)
    if not {"asset_id", "source_id", "rights_status", "license"}.issubset(envelope):
        raise ValueError("asset evidence requires id, source, rights status, and license")
    return {key: str(item).strip() for key, item in envelope.items() if item is not None}


def anonymized_language_features(text: str, local_route: str) -> dict[str, int | str]:
    """Derive a no-text routing payload for the QazCompute profile."""

    if local_route not in CANONICAL_LOCALES:
        raise ValueError("local language route must be canonical")
    return {
        "schema_version": "qsign-language-routing-features-v1",
        "profile": "qsign-language-routing.v1",
        "local_candidate": local_route,
        "character_count": len(text),
        "cyrillic_count": sum("\u0400" <= char <= "\u052f" for char in text),
        "latin_count": sum(("a" <= char.lower() <= "z") for char in text),
        "digit_count": sum(char.isdigit() for char in text),
    }


Transport = Callable[[str, dict[str, int | str], float, str | None], tuple[int, Mapping[str, Any]]]


def qazstack_transport(
    endpoint: str,
    payload: dict[str, int | str],
    timeout_seconds: float,
    api_key: str | None,
) -> tuple[int, Mapping[str, Any]]:
    """Small transport boundary used only after explicit provider configuration.

    No endpoint is inferred.  The caller supplies the approved QazStack
    transport URL and this function sends only the feature envelope above.
    """

    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-QazStack-Profile": "qsign-language-routing.v1",
    }
    if api_key:
        headers["X-API-Key"] = api_key
    request = Request(
        endpoint,
        data=body,
        headers=headers,
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310 - endpoint is explicit configuration
            decoded = json.loads(response.read().decode("utf-8"))
            return int(response.status), decoded if isinstance(decoded, dict) else {}
    except HTTPError as exc:
        return int(exc.code), {}
    except (TimeoutError, socket.timeout):
        return 0, {"_error": "timeout"}
    except (URLError, ValueError, json.JSONDecodeError):
        return 0, {"_error": "transport"}


@dataclass(frozen=True)
class LanguageRoutingAdapter:
    mode: str = "disabled"
    endpoint: str | None = None
    api_key: str | None = None
    timeout_seconds: float = 1.0
    transport: Transport = qazstack_transport

    def route(self, text: str, local_route: str) -> dict[str, object]:
        """Call a configured provider in shadow mode and retain the local route."""

        if self.mode == "disabled":
            return {"state": "disabled", "authoritative_route": local_route, "remote_called": False}
        if self.mode not in {"shadow", "hybrid"}:
            return {"state": "rejected_configuration", "authoritative_route": local_route, "remote_called": False}
        if not self.endpoint or not self.endpoint.startswith("https://"):
            return {"state": "not_configured", "authoritative_route": local_route, "remote_called": False}

        status, response = self.transport(
            self.endpoint,
            anonymized_language_features(text, local_route),
            self.timeout_seconds,
            self.api_key,
        )
        if status != 200:
            failure = response.get("_error") if isinstance(response, Mapping) else None
            return {
                "state": "remote_error",
                "authoritative_route": local_route,
                "remote_called": True,
                "error": failure or f"http_{status or 'unavailable'}",
            }
        remote_route = normalize_platform_locale(response.get("language") if isinstance(response, Mapping) else None)
        if (
            not isinstance(response, Mapping)
            or response.get("profile") != "qsign-language-routing.v1"
            or remote_route is None
            or not isinstance(response.get("quality"), Mapping)
            or not isinstance(response.get("degradation"), Mapping)
        ):
            return {
                "state": "malformed_response",
                "authoritative_route": local_route,
                "remote_called": True,
            }
        return {
            "state": "shadow_compared" if self.mode == "shadow" else "hybrid_compared",
            "authoritative_route": local_route,
            "remote_called": True,
            "remote_route": remote_route,
            "agreement": remote_route == local_route,
            "quality_tier": str(response["quality"].get("tier") or "unknown"),
            "degraded": bool(response["degradation"].get("active", True)),
        }
