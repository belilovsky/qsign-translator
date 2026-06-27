from __future__ import annotations

import unittest
from unittest import mock

try:
    from fastapi.testclient import TestClient

    from qsign_translator.api import app
except Exception as exc:  # pragma: no cover - optional API extra
    TestClient = None
    import_error = exc
else:
    import_error = None


@unittest.skipIf(TestClient is None, f"API dependencies are not installed: {import_error!r}")
class AIVideoBriefApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_ai_video_brief_returns_prompt_package(self) -> None:
        job = {
            "id": "job-1",
            "input_text": "Привет помощь",
            "detected_language": "ru",
            "review_status": "pending_signer_review",
            "risk_domains": [],
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
                    "kind": "gloss",
                    "source_token": "помощь",
                    "gloss": "HELP",
                    "clip_id": "rsl_help",
                },
            ],
        }
        with mock.patch("qsign_translator.api.db.get_translation_job", return_value=job):
            response = self.client.get("/v1/jobs/job-1/ai-video-brief")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["job_id"], "job-1")
        self.assertEqual(data["summary"]["language_route"], "ru")
        self.assertIn("master_prompt", data["prompts"])
        self.assertIn("negative_prompt", data["prompts"])
        self.assertIn("exports", data)
        self.assertIn("operator_handoff", data["exports"])
        self.assertEqual(len(data["units"]), 2)

    def test_ai_video_brief_returns_not_found(self) -> None:
        with mock.patch("qsign_translator.api.db.get_translation_job", return_value=None):
            response = self.client.get("/v1/jobs/missing/ai-video-brief")
        self.assertEqual(response.status_code, 404)

    def test_ai_video_batch_brief_returns_strict_batch_package(self) -> None:
        jobs = {
            "job-1": {
                "id": "job-1",
                "input_text": "Привет",
                "detected_language": "ru",
                "review_status": "pending_signer_review",
                "risk_domains": [],
                "units": [
                    {
                        "position": 1,
                        "kind": "gloss",
                        "source_token": "привет",
                        "gloss": "HELLO",
                        "clip_id": "rsl_hello",
                    },
                ],
            },
            "job-2": {
                "id": "job-2",
                "input_text": "Александр",
                "detected_language": "ru",
                "review_status": "needs_edit",
                "risk_domains": [],
                "units": [
                    {
                        "position": 1,
                        "kind": "dactyl",
                        "source_token": "александр",
                        "gloss": "DACTYL_A",
                        "clip_id": None,
                    },
                ],
            },
        }
        with mock.patch(
            "qsign_translator.api.db.get_translation_job",
            side_effect=lambda job_id: jobs.get(job_id),
        ):
            response = self.client.post(
                "/v1/ai-video-batch-brief",
                json={"job_ids": ["job-1", "job-2"], "title": "Demo batch"},
            )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["format_version"], "qsign-ai-video-batch-brief/v1")
        self.assertEqual(data["summary"]["scene_count"], 2)
        self.assertIn("batch_storyboard", data["exports"])
        self.assertEqual(len(data["batch_render"]["scenes"]), 2)

    def test_ai_video_batch_brief_returns_not_found_for_missing_job(self) -> None:
        with mock.patch("qsign_translator.api.db.get_translation_job", return_value=None):
            response = self.client.post(
                "/v1/ai-video-batch-brief",
                json={"job_ids": ["missing-job"]},
            )
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
