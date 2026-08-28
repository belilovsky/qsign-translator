"""Fail-closed boundary for a future id.qdev.run review integration.

QSign does not parse or trust browser tokens itself.  A production deployment
may call ``map_verified_claims`` only after its server-side OIDC client has
performed signature, issuer, audience, nonce, state and PKCE validation.  The
adapter maps only an accepted reviewer role and never returns a subject or any
other identity attribute to the QSign application layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


REVIEWER_ROLE = "reviewer"


@dataclass(frozen=True)
class OIDCReviewAdapter:
    """Deny-by-default role mapping for already verified OIDC claims."""

    mode: str = "documented"
    issuer: str = "https://id.qdev.run"
    audience: str | None = None
    provider_accepted: bool = False

    def map_verified_claims(self, claims: Mapping[str, Any]) -> dict[str, str] | None:
        """Map a verified identity to the sole portable QSign review role.

        This intentionally accepts no provider claim until the protected
        acceptance gate is recorded.  Caller-side verification remains
        mandatory, so this class cannot accidentally turn an unverified JWT
        into review access.
        """

        if self.mode != "active" or not self.provider_accepted:
            return None
        if claims.get("iss") != self.issuer or not str(claims.get("sub") or "").strip():
            return None
        audiences = claims.get("aud")
        accepted_audience = self.audience is None or audiences == self.audience or (
            isinstance(audiences, list) and self.audience in audiences
        )
        if not accepted_audience:
            return None
        roles = claims.get("roles")
        if not isinstance(roles, list) or REVIEWER_ROLE not in roles:
            return None
        return {"role": REVIEWER_ROLE, "method": "oidc"}
