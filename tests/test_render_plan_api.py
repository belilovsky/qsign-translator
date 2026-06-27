from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

try:
    from fastapi.testclient import TestClient

    from qsign_translator.api import app
except Exception as exc:  # pragma: no cover - optional API extra
    TestClient = None
    import_error = exc
else:
    import_error = None


@unittest.skipIf(
    TestClient is None, f"API dependencies are not installed: {import_error!r}"
)
class RenderPlanApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_render_plan_reports_resolved_and_missing_segments(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            clip_dir = Path(tmp_dir) / "clips"
            clip_dir.mkdir(parents=True, exist_ok=True)
            (clip_dir / "rsl_hello.mp4").write_bytes(b"fake")
            job = {
                "id": "job-1",
                "status": "review_required",
                "review_status": "approved",
                "output_kind": "sign_plan_preview",
                "output_status": "not_rendered",
                "units": [
                    {
                        "position": 1,
                        "kind": "gloss",
                        "source_token": "привет",
                        "gloss": "HELLO",
                        "clip_id": "rsl_hello",
                    },
                    {
                        "position": 2,
                        "kind": "dactyl",
                        "source_token": "александр",
                        "gloss": "DACTYL_A",
                        "clip_id": None,
                    },
                ],
            }
            with (
                mock.patch(
                    "qsign_translator.api.db.get_translation_job", return_value=job
                ),
                mock.patch(
                    "qsign_translator.api.settings", mock.Mock(asset_root=tmp_dir)
                ),
            ):
                response = self.client.get("/v1/jobs/job-1/render-plan")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["job_id"], "job-1")
        self.assertEqual(data["target_output_kind"], "avatar_video")
        self.assertEqual(data["adapter"]["adapter_status"], "partial_assets")
        self.assertFalse(data["adapter"]["publish_ready"])
        self.assertEqual(data["pipeline_status"], "approved_but_asset_incomplete")
        self.assertIn("missing_render_assets", data["publish_gate"]["blockers"])
        self.assertEqual(
            data["publish_gate"]["next_step"], "attach_or_generate_missing_assets"
        )
        self.assertEqual(data["summary"]["resolved_segments"], 1)
        self.assertEqual(data["summary"]["missing_segments"], 1)
        self.assertEqual(data["segments"][0]["asset_key"], "clips/rsl_hello.mp4")
        self.assertEqual(data["missing"][0]["reason"], "no_clip_id")

    def test_render_plan_returns_not_found_for_unknown_job(self) -> None:
        with mock.patch(
            "qsign_translator.api.db.get_translation_job", return_value=None
        ):
            response = self.client.get("/v1/jobs/missing/render-plan")
        self.assertEqual(response.status_code, 404)

    def test_render_plan_reports_uploaded_render_when_available(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            job = {
                "id": "job-1",
                "status": "review_required",
                "review_status": "approved",
                "publish_status": "publishable",
                "output_kind": "sign_plan_preview",
                "output_status": "ready",
                "output_uri": "/v1/jobs/job-1/rendered-video",
                "units": [
                    {
                        "position": 1,
                        "kind": "dactyl",
                        "source_token": "александр",
                        "gloss": "DACTYL_A",
                        "clip_id": None,
                    },
                ],
            }
            with (
                mock.patch(
                    "qsign_translator.api.db.get_translation_job", return_value=job
                ),
                mock.patch(
                    "qsign_translator.api.settings", mock.Mock(asset_root=tmp_dir)
                ),
            ):
                response = self.client.get("/v1/jobs/job-1/render-plan")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["pipeline_status"], "ready_for_publish")
        self.assertTrue(data["adapter"]["uploaded_render_available"])
        self.assertTrue(data["publish_gate"]["ready"])
        self.assertEqual(data["publish_gate"]["next_step"], "publishable_now")


if __name__ == "__main__":
    unittest.main()
