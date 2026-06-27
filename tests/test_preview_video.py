from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from qsign_translator.preview_video import PreviewVideoUnavailable
from qsign_translator.preview_video import build_review_video


class PreviewVideoTests(unittest.TestCase):
    def test_build_review_video_renders_mp4_with_ffmpeg(self) -> None:
        job = {
            "id": "job-1",
            "input_text": "привет помощь",
            "units": [
                {
                    "position": 1,
                    "kind": "gloss",
                    "source_token": "привет",
                    "gloss": "HELLO",
                },
                {
                    "position": 2,
                    "kind": "gloss",
                    "source_token": "помощь",
                    "gloss": "HELP",
                },
            ],
        }
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_root = Path(tmp_dir)
            static_root = tmp_root / "static"
            asset_dir = static_root / "assets"
            asset_dir.mkdir(parents=True, exist_ok=True)
            (asset_dir / "signing-avatar.png").write_bytes(b"fake-png")
            output_root = tmp_root / "out"

            def fake_run(command, check, capture_output, text):  # noqa: ANN001
                self.assertIn("ffmpeg", command[0])
                self.assertIn("-vf", command)
                self.assertIn("subtitles=", command[command.index("-vf") + 1])
                Path(command[-1]).write_bytes(b"fake-mp4")
                return mock.Mock(returncode=0)

            with (
                mock.patch(
                    "qsign_translator.preview_video.shutil.which",
                    return_value="/usr/bin/ffmpeg",
                ),
                mock.patch(
                    "qsign_translator.preview_video.subprocess.run",
                    side_effect=fake_run,
                ),
            ):
                artifact = build_review_video(
                    job, static_root=static_root, output_root=output_root
                )
                self.assertEqual(artifact.kind, "review_storyboard")
                self.assertEqual(artifact.unit_count, 2)
                self.assertTrue(artifact.path.exists())
                self.assertGreater(artifact.path.stat().st_size, 0)

    def test_build_review_video_requires_ffmpeg(self) -> None:
        job = {
            "id": "job-1",
            "units": [{"position": 1, "kind": "gloss", "source_token": "привет"}],
        }
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_root = Path(tmp_dir)
            static_root = tmp_root / "static"
            asset_dir = static_root / "assets"
            asset_dir.mkdir(parents=True, exist_ok=True)
            (asset_dir / "signing-avatar.png").write_bytes(b"fake-png")
            with mock.patch(
                "qsign_translator.preview_video.shutil.which", return_value=None
            ):
                with self.assertRaises(PreviewVideoUnavailable):
                    build_review_video(
                        job, static_root=static_root, output_root=tmp_root / "out"
                    )


if __name__ == "__main__":
    unittest.main()
