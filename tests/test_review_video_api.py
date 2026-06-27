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


@unittest.skipIf(TestClient is None, f"API dependencies are not installed: {import_error!r}")
class ReviewVideoApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_review_video_returns_mp4_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            video_path = Path(tmp_dir) / "review.mp4"
            video_path.write_bytes(b"fake-mp4")
            job = {"id": "job-1", "units": [{"position": 1, "kind": "gloss", "source_token": "привет"}]}
            artifact = mock.Mock(path=video_path, duration_seconds=3.0, unit_count=1, kind="review_storyboard")
            with (
                mock.patch("qsign_translator.api.db.get_translation_job", return_value=job),
                mock.patch("qsign_translator.api.build_review_video", return_value=artifact),
            ):
                response = self.client.get("/v1/jobs/job-1/review-video")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "video/mp4")
        self.assertEqual(response.headers["x-qsign-preview-kind"], "review_storyboard")
        self.assertEqual(response.headers["x-qsign-preview-units"], "1")

    def test_review_video_head_returns_headers_without_body(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            video_path = Path(tmp_dir) / "review.mp4"
            video_path.write_bytes(b"fake-mp4")
            job = {"id": "job-1", "units": [{"position": 1, "kind": "gloss", "source_token": "привет"}]}
            artifact = mock.Mock(path=video_path, duration_seconds=3.0, unit_count=1, kind="review_storyboard")
            with (
                mock.patch("qsign_translator.api.db.get_translation_job", return_value=job),
                mock.patch("qsign_translator.api.build_review_video", return_value=artifact),
            ):
                response = self.client.head("/v1/jobs/job-1/review-video")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "video/mp4")
        self.assertEqual(response.headers["x-qsign-preview-kind"], "review_storyboard")
        self.assertEqual(response.headers["x-qsign-preview-units"], "1")
        self.assertEqual(response.content, b"")

    def test_review_video_returns_not_found_for_missing_job(self) -> None:
        with mock.patch("qsign_translator.api.db.get_translation_job", return_value=None):
            response = self.client.get("/v1/jobs/missing/review-video")
        self.assertEqual(response.status_code, 404)

    def test_review_video_head_returns_not_found_for_invalid_job_id(self) -> None:
        with mock.patch("qsign_translator.api.db.get_translation_job", return_value=None):
            response = self.client.head("/v1/jobs/not-a-uuid/review-video")
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
