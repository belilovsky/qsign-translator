from __future__ import annotations

import tempfile
from pathlib import Path
import unittest
from unittest import mock

try:
    from fastapi.testclient import TestClient

    from qsign_translator.api import app
    from qsign_translator.asr import AsrUnavailable
except Exception as exc:  # pragma: no cover - optional API extra
    TestClient = None
    import_error = exc
else:
    import_error = None


@unittest.skipIf(TestClient is None, f"API dependencies are not installed: {import_error!r}")
class ApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_openapi_exposes_current_package_version(self) -> None:
        response = self.client.get("/openapi.json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["info"]["version"], "0.2.0")

    def test_head_routes_are_monitorable(self) -> None:
        for path in ["/", "/health", "/health/live", "/health/ready"]:
            with self.subTest(path=path):
                response = self.client.head(path)
                self.assertLess(response.status_code, 500)

    def test_audio_rejects_unsupported_type(self) -> None:
        response = self.client.post(
            "/v1/transcribe/audio",
            content=b"hello",
            headers={"content-type": "text/plain"},
        )
        self.assertEqual(response.status_code, 415)

    def test_audio_reports_unavailable_as_capability_status(self) -> None:
        with mock.patch(
            "qsign_translator.api.FasterWhisperAsr",
            side_effect=AsrUnavailable("missing asr backend"),
        ):
            response = self.client.post(
                "/v1/transcribe/audio",
                content=b"not real mp3",
                headers={"content-type": "audio/mpeg"},
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "asr_unavailable")

    def test_text_translation_survives_missing_database(self) -> None:
        with mock.patch(
            "qsign_translator.api.db.record_translation_job",
            side_effect=RuntimeError("database unavailable"),
        ):
            response = self.client.post(
                "/v1/translate/text",
                json={"text": "Привет Александр"},
            )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["metadata"]["persisted"])
        self.assertIn("persistence_error", data["metadata"])
        self.assertGreaterEqual(len(data["units"]), 1)

    def test_text_translation_returns_job_metadata_when_persisted(self) -> None:
        with mock.patch("qsign_translator.api.db.record_translation_job", return_value="job-1"):
            response = self.client.post(
                "/v1/translate/text",
                json={"text": "Мне нужна скорая помощь"},
            )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["metadata"]["persisted"])
        self.assertEqual(data["metadata"]["job_id"], "job-1")
        self.assertEqual(data["metadata"]["job_status"], "review_required")
        self.assertEqual(data["metadata"]["review_status"], "pending_signer_review")
        self.assertEqual(data["metadata"]["output_kind"], "sign_plan_preview")
        self.assertEqual(data["metadata"]["output_status"], "not_rendered")
        self.assertGreater(data["metadata"]["fallback_count"], 0)
        self.assertEqual(data["trace"]["summary"]["review_gate"], "human_interpreter_required")
        self.assertEqual(data["trace"]["stages"][-1]["id"], "output")
        self.assertIn("decision", data["units"][0])

    def test_translation_job_endpoint_returns_not_found(self) -> None:
        with mock.patch("qsign_translator.api.db.get_translation_job", return_value=None):
            response = self.client.get("/v1/jobs/00000000-0000-0000-0000-000000000000")
        self.assertEqual(response.status_code, 404)

    def test_translation_job_endpoint_returns_job(self) -> None:
        with mock.patch(
            "qsign_translator.api.db.get_translation_job",
            return_value={"id": "job-1", "units": [{"position": 1, "gloss": "HELLO"}]},
        ):
            response = self.client.get("/v1/jobs/job-1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], "job-1")
        self.assertEqual(response.json()["units"][0]["gloss"], "HELLO")

    def test_feedback_endpoint_records_event(self) -> None:
        with (
            mock.patch("qsign_translator.api.db.get_translation_job", return_value={"id": "job-1"}),
            mock.patch("qsign_translator.api.db.record_feedback", return_value="feedback-1"),
        ):
            response = self.client.post(
                "/v1/feedback",
                json={"job_id": "job-1", "feedback_type": "good"},
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["feedback_id"], "feedback-1")

    def test_feedback_endpoint_returns_not_found_for_missing_job(self) -> None:
        with mock.patch("qsign_translator.api.db.get_translation_job", return_value=None):
            response = self.client.post(
                "/v1/feedback",
                json={"job_id": "missing", "feedback_type": "good"},
            )
        self.assertEqual(response.status_code, 404)

    def test_feedback_endpoint_rejects_unknown_type(self) -> None:
        with (
            mock.patch("qsign_translator.api.db.get_translation_job", return_value={"id": "job-1"}),
            mock.patch(
                "qsign_translator.api.db.record_feedback",
                side_effect=ValueError("Unsupported feedback type"),
            ),
        ):
            response = self.client.post(
                "/v1/feedback",
                json={"job_id": "job-1", "feedback_type": "unknown"},
            )
        self.assertEqual(response.status_code, 400)

    def test_review_jobs_endpoint_lists_jobs(self) -> None:
        with (
            mock.patch("qsign_translator.api.settings", mock.Mock(review_token="secret")),
            mock.patch(
                "qsign_translator.api.db.list_translation_jobs",
                return_value=[{"id": "job-1", "review_status": "pending_signer_review"}],
            ),
        ):
            response = self.client.get(
                "/v1/review/jobs?review_status=pending_signer_review",
                headers={"x-qsign-review-token": "secret"},
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 1)
        self.assertEqual(response.json()["items"][0]["id"], "job-1")

    def test_review_jobs_endpoint_requires_configured_token(self) -> None:
        with mock.patch("qsign_translator.api.settings", mock.Mock(review_token=None)):
            response = self.client.get("/v1/review/jobs")
        self.assertEqual(response.status_code, 503)

    def test_review_jobs_endpoint_rejects_bad_token(self) -> None:
        with mock.patch("qsign_translator.api.settings", mock.Mock(review_token="secret")):
            response = self.client.get(
                "/v1/review/jobs",
                headers={"x-qsign-review-token": "wrong"},
            )
        self.assertEqual(response.status_code, 403)

    def test_review_jobs_endpoint_rejects_bad_status(self) -> None:
        with (
            mock.patch("qsign_translator.api.settings", mock.Mock(review_token="secret")),
            mock.patch(
                "qsign_translator.api.db.list_translation_jobs",
                side_effect=ValueError("Unsupported review status"),
            ),
        ):
            response = self.client.get(
                "/v1/review/jobs?review_status=bad",
                headers={"x-qsign-review-token": "secret"},
            )
        self.assertEqual(response.status_code, 400)

    def test_review_job_endpoint_updates_status(self) -> None:
        with (
            mock.patch("qsign_translator.api.settings", mock.Mock(review_token="secret")),
            mock.patch(
                "qsign_translator.api.db.update_review_status",
                return_value={"id": "job-1", "review_status": "approved"},
            ),
        ):
            response = self.client.patch(
                "/v1/review/jobs/job-1",
                json={"review_status": "approved"},
                headers={"x-qsign-review-token": "secret"},
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["review_status"], "approved")

    def test_review_job_rendered_video_upload_requires_mp4(self) -> None:
        with mock.patch("qsign_translator.api.settings", mock.Mock(review_token="secret")):
            response = self.client.post(
                "/v1/review/jobs/job-1/rendered-video",
                content=b"bad",
                headers={"x-qsign-review-token": "secret", "content-type": "application/octet-stream"},
            )
        self.assertEqual(response.status_code, 415)

    def test_review_job_rendered_video_upload_attaches_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            with (
                mock.patch("qsign_translator.api.settings", mock.Mock(review_token="secret")),
                mock.patch("qsign_translator.api.UPLOADED_RENDER_ROOT", Path(tmp_dir)),
                mock.patch("qsign_translator.api.db.get_translation_job", return_value={"id": "job-1"}),
                mock.patch(
                    "qsign_translator.api.db.attach_rendered_video",
                    return_value={
                        "id": "job-1",
                        "output_status": "ready",
                        "output_uri": "/v1/jobs/job-1/rendered-video",
                        "render_adapter": "external_upload",
                    },
                ),
            ):
                response = self.client.post(
                    "/v1/review/jobs/job-1/rendered-video",
                    content=b"fake-mp4",
                    headers={"x-qsign-review-token": "secret", "content-type": "video/mp4"},
                )
                self.assertTrue((Path(tmp_dir) / "job-1.mp4").exists())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["output_status"], "ready")

    def test_review_feedback_endpoint_lists_events(self) -> None:
        with (
            mock.patch("qsign_translator.api.settings", mock.Mock(review_token="secret")),
            mock.patch(
                "qsign_translator.api.db.list_feedback_events",
                return_value=[{"id": "feedback-1", "job_id": "job-1", "feedback_type": "good"}],
            ),
        ):
            response = self.client.get(
                "/v1/review/feedback?job_id=job-1",
                headers={"x-qsign-review-token": "secret"},
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["items"][0]["feedback_type"], "good")

    def test_review_sessions_endpoint_lists_items(self) -> None:
        with (
            mock.patch("qsign_translator.api.settings", mock.Mock(review_token="secret")),
            mock.patch(
                "qsign_translator.api.db.list_review_sessions",
                return_value=[{"id": "session-1", "job_id": "job-1", "reviewer_role": "native_signer"}],
            ),
        ):
            response = self.client.get(
                "/v1/review/sessions?job_id=job-1",
                headers={"x-qsign-review-token": "secret"},
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 1)
        self.assertEqual(response.json()["items"][0]["reviewer_role"], "native_signer")

    def test_review_sessions_endpoint_creates_session_and_updates_status(self) -> None:
        with (
            mock.patch("qsign_translator.api.settings", mock.Mock(review_token="secret")),
            mock.patch(
                "qsign_translator.api.db.get_translation_job",
                return_value={"id": "job-1", "review_status": "pending_signer_review"},
            ),
            mock.patch(
                "qsign_translator.api.db.create_review_session",
                return_value={"id": "session-1", "job_id": "job-1", "reviewer_role": "native_signer"},
            ),
            mock.patch(
                "qsign_translator.api.db.update_review_status",
                return_value={"id": "job-1", "review_status": "approved"},
            ),
        ):
            response = self.client.post(
                "/v1/review/sessions",
                json={
                    "job_id": "job-1",
                    "reviewer_role": "native_signer",
                    "reviewer_language": "ru",
                    "review_status": "approved",
                    "meaning_score": 5,
                    "notes": "Approved after native review.",
                },
                headers={"x-qsign-review-token": "secret"},
            )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["review_status"], "approved")
        self.assertEqual(data["session"]["id"], "session-1")

    def test_review_sessions_endpoint_returns_not_found_for_missing_job(self) -> None:
        with (
            mock.patch("qsign_translator.api.settings", mock.Mock(review_token="secret")),
            mock.patch("qsign_translator.api.db.get_translation_job", return_value=None),
        ):
            response = self.client.post(
                "/v1/review/sessions",
                json={
                    "job_id": "missing",
                    "reviewer_role": "native_signer",
                    "reviewer_language": "ru",
                },
                headers={"x-qsign-review-token": "secret"},
            )
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
