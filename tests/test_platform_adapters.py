from __future__ import annotations

import json
from pathlib import Path
import unittest

from qsign_translator.language import detect_language
from qsign_translator.planner import SignPlanner
from qsign_translator.lexicon import load_default_lexicon
from qsign_translator.platform_adapters import (
    LanguageRoutingAdapter,
    anonymized_language_features,
    asset_evidence_envelope,
    normalize_platform_locale,
    normalize_source_metadata,
    reviewed_activity_envelope,
)
from qsign_translator.identity import OIDCReviewAdapter


def successful_transport(_endpoint: str, payload: dict[str, int | str], _timeout: float, _api_key: str | None):
    return 200, {
        "profile": "qsign-language-routing.v1",
        "language": payload["local_candidate"],
        "quality": {"tier": "candidate"},
        "degradation": {"active": False},
    }


class PlatformAdapterTests(unittest.TestCase):
    def test_oidc_role_mapping_is_deny_by_default(self) -> None:
        claims = {"iss": "https://id.qdev.run", "aud": "qsign", "sub": "private-user", "roles": ["reviewer"]}
        self.assertIsNone(OIDCReviewAdapter(mode="documented", audience="qsign", provider_accepted=True).map_verified_claims(claims))
        self.assertIsNone(OIDCReviewAdapter(mode="active", audience="qsign", provider_accepted=True).map_verified_claims({**claims, "roles": ["admin"]}))
        self.assertEqual(
            OIDCReviewAdapter(mode="active", audience="qsign", provider_accepted=True).map_verified_claims(claims),
            {"role": "reviewer", "method": "oidc"},
        )
    def test_locale_aliases_are_canonical(self) -> None:
        self.assertEqual(normalize_platform_locale("kz"), "kk")
        self.assertEqual(normalize_platform_locale("RUS"), "ru")
        self.assertEqual(normalize_platform_locale("english"), "en")
        self.assertIsNone(normalize_platform_locale("auto"))
        self.assertIsNone(normalize_platform_locale("de"))

    def test_source_and_evidence_envelopes_reject_private_fields(self) -> None:
        self.assertEqual(
            normalize_source_metadata(
                {"id": "source-1", "url": "https://example.test/source-1", "language": "kz", "status": "reviewed", "license": "CC-BY"}
            )["language"],
            "kk",
        )
        self.assertEqual(
            reviewed_activity_envelope(
                {"activity_id": "a-1", "activity_type": "review", "status": "approved", "occurred_at": "2026-08-29T00:00:00Z"}
            )["status"],
            "approved",
        )
        self.assertEqual(
            asset_evidence_envelope(
                {"asset_id": "asset-1", "source_id": "source-1", "rights_status": "cleared", "license": "CC-BY"}
            )["rights_status"],
            "cleared",
        )
        with self.assertRaises(ValueError):
            normalize_source_metadata({"id": "source-1", "url": "https://example.test", "video": "private.mp4"})
        with self.assertRaises(ValueError):
            reviewed_activity_envelope(
                {"activity_id": "a-1", "activity_type": "review", "status": "approved", "occurred_at": "now", "reviewer": "person"}
            )

    def test_disabled_mode_never_uses_network_transport(self) -> None:
        def fail_transport(*_args):
            raise AssertionError("disabled adapter must not call a transport")

        result = LanguageRoutingAdapter(mode="disabled", transport=fail_transport).route("Привет", "ru")
        self.assertEqual(result, {"state": "disabled", "authoritative_route": "ru", "remote_called": False})

    def test_shadow_result_never_replaces_local_route_or_text(self) -> None:
        seen: dict[str, object] = {}

        def transport(_endpoint: str, payload: dict[str, int | str], _timeout: float, _api_key: str | None):
            seen.update(payload)
            return successful_transport(_endpoint, payload, _timeout, _api_key)

        result = LanguageRoutingAdapter(mode="shadow", endpoint="https://compute.example.test/route", transport=transport).route(
            "Сәлем, private input", "kk"
        )
        self.assertEqual(result["state"], "shadow_compared")
        self.assertEqual(result["authoritative_route"], "kk")
        self.assertTrue(result["agreement"])
        self.assertNotIn("text", seen)
        self.assertEqual(seen["profile"], "qsign-language-routing.v1")

    def test_remote_failures_and_malformed_responses_preserve_local_route(self) -> None:
        for status, response in [
            (401, {}), (403, {}), (429, {}), (500, {}), (0, {"_error": "timeout"}),
            (200, {"profile": "wrong", "language": "ru", "quality": {}, "degradation": {}}),
        ]:
            with self.subTest(status=status, response=response):
                result = LanguageRoutingAdapter(
                    mode="hybrid", endpoint="https://compute.example.test/route", transport=lambda *_: (status, response)
                ).route("Please help", "en")
                self.assertEqual(result["authoritative_route"], "en")
                self.assertTrue(result["remote_called"])
                self.assertIn(result["state"], {"remote_error", "malformed_response"})

    def test_goldset_preserves_local_language_and_review_safety(self) -> None:
        goldset = json.loads((Path(__file__).parent / "fixtures" / "qsign_language_routing_goldset.json").read_text())
        planner = SignPlanner(load_default_lexicon())
        for case in goldset["cases"]:
            with self.subTest(case=case["id"]):
                plan = planner.plan(case["text"])
                self.assertEqual(detect_language(case["text"]), case["expected_language"])
                self.assertEqual(plan.language, case["expected_language"])
                self.assertEqual(plan.review_gate, case["expected_review_gate"])

    def test_feature_payload_has_no_raw_text(self) -> None:
        payload = anonymized_language_features("Сәлем, private review text", "kk")
        self.assertNotIn("text", payload)
        self.assertEqual(payload["local_candidate"], "kk")
