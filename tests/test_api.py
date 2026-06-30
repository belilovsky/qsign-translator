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


def fake_mp4_bytes() -> bytes:
    return b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42isom"


@unittest.skipIf(TestClient is None, f"API dependencies are not installed: {import_error!r}")
class ApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_openapi_exposes_current_package_version(self) -> None:
        response = self.client.get("/openapi.json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["info"]["version"], "0.2.0")

    def test_head_routes_are_monitorable(self) -> None:
        for path in [
            "/",
            "/about",
            "/how-it-works",
            "/methodology",
            "/examples",
            "/sources",
            "/safety",
            "/languages/ru-rsl",
            "/languages/kk-krsl",
            "/languages/en-asl",
            "/api",
            "/developers",
            "/open-source",
            "/roadmap",
            "/faq",
            "/glossary",
            "/robots.txt",
            "/sitemap.xml",
            "/llms.txt",
            "/ai-context.md",
            "/ai-use.md",
            "/public-context.json",
            "/claims.json",
            "/humans.txt",
            "/security.txt",
            "/.well-known/security.txt",
            "/d491805d96a2b9f8c9b89725616e32f222a007cbc582d8a9158b6993d41b7141.txt",
            "/manifest.webmanifest",
            "/health",
            "/health/live",
            "/health/ready",
        ]:
            with self.subTest(path=path):
                response = self.client.head(path)
                self.assertLess(response.status_code, 500)

    def test_public_discovery_files_are_exposed(self) -> None:
        expected = {
            "/robots.txt": ("text/plain", "Sitemap: https://qsign.qdev.run/sitemap.xml"),
            "/sitemap.xml": ("application/xml", "https://qsign.qdev.run/"),
            "/llms.txt": ("text/plain", "QSign Translator"),
            "/ai-context.md": ("text/markdown", "QSign Translator public AI context"),
            "/ai-use.md": ("text/markdown", "QSign Translator AI Use Guidance"),
            "/public-context.json": ("application/json", "QSign Translator"),
            "/claims.json": ("application/json", "qsign-not-certified-interpreter"),
            "/humans.txt": ("text/plain", "Publisher: qdev.run"),
            "/security.txt": ("text/plain", "Policy: https://github.com/belilovsky/qsign-translator/blob/main/SECURITY.md"),
            "/.well-known/security.txt": (
                "text/plain",
                "Canonical: https://qsign.qdev.run/.well-known/security.txt",
            ),
            "/d491805d96a2b9f8c9b89725616e32f222a007cbc582d8a9158b6993d41b7141.txt": (
                "text/plain",
                "d491805d96a2b9f8c9b89725616e32f222a007cbc582d8a9158b6993d41b7141",
            ),
            "/manifest.webmanifest": ("application/manifest+json", "QSign Translator"),
        }
        for path, (content_type, marker) in expected.items():
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertIn(content_type, response.headers["content-type"])
                self.assertIn(marker, response.text)
                head_response = self.client.head(path)
                self.assertEqual(head_response.status_code, 200)
                self.assertIn(content_type, head_response.headers["content-type"])

    def test_public_context_lists_trust_files(self) -> None:
        response = self.client.get("/public-context.json")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["machine_readable"]["humans"], "https://qsign.qdev.run/humans.txt")
        self.assertEqual(
            data["machine_readable"]["security"],
            "https://qsign.qdev.run/.well-known/security.txt",
        )
        self.assertEqual(data["machine_readable"]["ai_use"], "https://qsign.qdev.run/ai-use.md")
        self.assertEqual(data["machine_readable"]["claims"], "https://qsign.qdev.run/claims.json")

    def test_robots_allows_search_and_ai_discovery(self) -> None:
        response = self.client.get("/robots.txt")
        self.assertEqual(response.status_code, 200)
        robots = response.text
        self.assertIn("User-agent: *", robots)
        self.assertIn("User-agent: OAI-SearchBot", robots)
        self.assertIn("User-agent: ChatGPT-User", robots)
        self.assertIn("User-agent: PerplexityBot", robots)
        self.assertIn("User-agent: Claude-SearchBot", robots)
        self.assertIn("Sitemap: https://qsign.qdev.run/sitemap.xml", robots)

    def test_index_contains_search_and_ai_metadata(self) -> None:
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html = response.text
        self.assertIn('<link rel="canonical" href="https://qsign.qdev.run/"', html)
        self.assertIn('property="og:title"', html)
        self.assertIn('name="twitter:card"', html)
        self.assertIn('type="application/ld+json"', html)
        self.assertIn("SoftwareApplication", html)
        self.assertIn("https://github.com/belilovsky/qsign-translator", html)

    def test_index_uses_avds4_static_primitives(self) -> None:
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html = response.text
        for marker in [
            "styles.css?v=20260630avds4",
            "avds-shell",
            "avds-topbar",
            "avds-nav",
            "avds-status-pill",
            "avds-button--primary",
            "avds-segmented__item",
            "avds-card",
            "avds-textarea",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)

    def test_avds4_bridge_tokens_are_available(self) -> None:
        css = Path("public/static/styles.css").read_text(encoding="utf-8")
        for marker in [
            "AV DS 4 compatibility bridge",
            "--color-bg-canvas",
            "--color-bg-surface",
            "--color-text-primary",
            "--color-accent",
            ".avds-button",
            ".avds-card",
            ".avds-table",
            ".avds-textarea",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, css)

    def test_public_content_pages_are_indexable(self) -> None:
        expected = {
            "/about": "О QSign Translator",
            "/how-it-works": "Как работает QSign Translator",
            "/methodology": "Методология QSign Translator",
            "/examples": "Примеры QSign Translator",
            "/sources": "Источники и словари QSign Translator",
            "/safety": "Безопасность QSign Translator",
            "/languages/ru-rsl": "Русский жестовый маршрут QSign",
            "/languages/kk-krsl": "Қазақша жест маршруты QSign",
            "/languages/en-asl": "QSign English route",
            "/api": "QSign API",
            "/developers": "QSign Developers",
            "/open-source": "Open-source QSign Translator",
            "/roadmap": "Roadmap QSign Translator",
            "/faq": "FAQ QSign Translator",
            "/glossary": "Глоссарий QSign",
        }
        for path, title_marker in expected.items():
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertIn("text/html", response.headers["content-type"])
                self.assertIn(title_marker, response.text)
                self.assertIn(f'href="https://qsign.qdev.run{path}"', response.text)
                self.assertIn("avds-shell", response.text)
                self.assertIn("avds-topbar", response.text)
                self.assertIn("avds-nav", response.text)

    def test_public_content_pages_have_social_and_breadcrumb_metadata(self) -> None:
        for path in [
            "/about",
            "/how-it-works",
            "/methodology",
            "/examples",
            "/sources",
            "/safety",
            "/languages/ru-rsl",
            "/languages/kk-krsl",
            "/languages/en-asl",
            "/api",
            "/developers",
            "/open-source",
            "/roadmap",
            "/faq",
            "/glossary",
        ]:
            with self.subTest(path=path):
                html = self.client.get(path).text
                self.assertIn('property="og:title"', html)
                self.assertIn('name="twitter:card"', html)
                self.assertIn("BreadcrumbList", html)
                if path.startswith("/languages/"):
                    self.assertIn('hreflang="ru"', html)
                    self.assertIn('hreflang="kk"', html)
                    self.assertIn('hreflang="en"', html)
                    self.assertIn('hreflang="x-default"', html)

    def test_sitemap_and_llms_list_public_content_pages(self) -> None:
        sitemap = self.client.get("/sitemap.xml").text
        llms = self.client.get("/llms.txt").text
        for path in [
            "/about",
            "/how-it-works",
            "/methodology",
            "/examples",
            "/sources",
            "/safety",
            "/languages/ru-rsl",
            "/languages/kk-krsl",
            "/languages/en-asl",
            "/api",
            "/developers",
            "/open-source",
            "/roadmap",
            "/faq",
            "/glossary",
            "/ai-context.md",
            "/ai-use.md",
            "/public-context.json",
            "/claims.json",
            "/humans.txt",
            "/.well-known/security.txt",
        ]:
            with self.subTest(path=path):
                self.assertIn(f"https://qsign.qdev.run{path}", llms)
                if path not in {"/humans.txt", "/.well-known/security.txt"}:
                    self.assertIn(f"https://qsign.qdev.run{path}", sitemap)

    def test_health_ready_head_returns_503_for_configured_but_unready_database(self) -> None:
        with (
            mock.patch("qsign_translator.api.settings", mock.Mock(database_url="postgres://db", review_token=None)),
            mock.patch(
                "qsign_translator.api.db.readiness",
                return_value={"configured": True, "ok": False, "reason": "db down"},
            ),
        ):
            response = self.client.head("/health/ready")
        self.assertEqual(response.status_code, 503)

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

    def test_text_translation_accepts_forced_language(self) -> None:
        with mock.patch(
            "qsign_translator.api.db.record_translation_job",
            side_effect=RuntimeError("database unavailable"),
        ):
            response = self.client.post(
                "/v1/translate/text",
                json={"text": "Сәлем көмек керек", "language": "kk"},
            )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["language"], "kk")
        self.assertEqual(data["coverage"]["fallback"], 0)

    def test_text_translation_supports_english_route(self) -> None:
        with mock.patch(
            "qsign_translator.api.db.record_translation_job",
            side_effect=RuntimeError("database unavailable"),
        ):
            response = self.client.post(
                "/v1/translate/text",
                json={"text": "I need help", "language": "en"},
            )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["language"], "en")
        self.assertEqual([unit["gloss"] for unit in data["units"]], ["ME", "NEED", "HELP"])

    def test_text_translation_reuses_new_russian_reviewed_aliases(self) -> None:
        with mock.patch(
            "qsign_translator.api.db.record_translation_job",
            side_effect=RuntimeError("database unavailable"),
        ):
            response = self.client.post(
                "/v1/translate/text",
                json={"text": "две вещи, которые реально повышают зрелость проекта."},
            )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["language"], "ru")
        self.assertEqual(data["coverage"]["fallback"], 0)
        self.assertEqual(
            [unit["gloss"] for unit in data["units"]],
            ["ДВА", "ВЕЩЬ", "КОТОРЫЙ", "РЕАЛЬНО", "ПОВЫШАТЬ", "ЗРЕЛОСТЬ", "ПРОЕКТ"],
        )

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
            mock.patch(
                "qsign_translator.api.db.get_translation_job",
                return_value={"id": "job-1"},
            ),
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
            mock.patch(
                "qsign_translator.api.db.get_translation_job",
                return_value={"id": "job-1"},
            ),
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
            ) as list_jobs,
        ):
            response = self.client.get(
                "/v1/review/jobs?review_status=pending_signer_review&publish_status=draft&detected_language=ru&q=%D0%9F%D1%80%D0%B8%D0%B2%D0%B5%D1%82",
                headers={"x-qsign-review-token": "secret"},
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 1)
        self.assertEqual(response.json()["items"][0]["id"], "job-1")
        list_jobs.assert_called_once_with(
            review_status="pending_signer_review",
            publish_status="draft",
            detected_language="ru",
            search_query="Привет",
            limit=50,
        )

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

    def test_review_login_sets_cookie_session(self) -> None:
        with mock.patch(
            "qsign_translator.api.settings",
            mock.Mock(
                review_token="secret",
                review_session_secret="session-secret",
                review_cookie_name="qsign_review_session",
                review_cookie_secure=False,
            ),
        ):
            response = self.client.post(
                "/v1/review/login",
                json={"token": "secret", "role": "linguist"},
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["actor"]["role"], "linguist")
        self.assertIn("qsign_review_session=", response.headers.get("set-cookie", ""))

    def test_review_me_accepts_cookie_session(self) -> None:
        settings_mock = mock.Mock(
            review_token="secret",
            review_session_secret="session-secret",
            review_cookie_name="qsign_review_session",
            review_cookie_secure=False,
        )
        with mock.patch("qsign_translator.api.settings", settings_mock):
            login_response = self.client.post(
                "/v1/review/login",
                json={"token": "secret", "role": "operator"},
            )
            cookie = login_response.cookies.get("qsign_review_session")
            self.client.cookies.set("qsign_review_session", cookie)
            response = self.client.get("/v1/review/me")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["actor"]["role"], "operator")

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
                headers={
                    "x-qsign-review-token": "secret",
                    "content-type": "application/octet-stream",
                },
            )
        self.assertEqual(response.status_code, 415)

    def test_review_job_rendered_video_upload_attaches_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            with (
                mock.patch("qsign_translator.api.settings", mock.Mock(review_token="secret")),
                mock.patch("qsign_translator.api.UPLOADED_RENDER_ROOT", Path(tmp_dir)),
                mock.patch(
                    "qsign_translator.api.db.get_translation_job",
                    return_value={"id": "job-1"},
                ),
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
                    content=fake_mp4_bytes(),
                    headers={
                        "x-qsign-review-token": "secret",
                        "content-type": "video/mp4",
                    },
                )
                self.assertTrue((Path(tmp_dir) / "job-1.mp4").exists())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["output_status"], "ready")

    def test_review_job_rendered_video_upload_rejects_fake_mp4_payload(self) -> None:
        with (
            mock.patch("qsign_translator.api.settings", mock.Mock(review_token="secret")),
            mock.patch(
                "qsign_translator.api.db.get_translation_job",
                return_value={"id": "job-1"},
            ),
        ):
            response = self.client.post(
                "/v1/review/jobs/job-1/rendered-video",
                content=b"fake-mp4",
                headers={
                    "x-qsign-review-token": "secret",
                    "content-type": "video/mp4",
                },
            )
        self.assertEqual(response.status_code, 415)

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
                return_value=[
                    {
                        "id": "session-1",
                        "job_id": "job-1",
                        "reviewer_role": "native_signer",
                    }
                ],
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
                return_value={
                    "id": "session-1",
                    "job_id": "job-1",
                    "reviewer_role": "native_signer",
                },
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

    def test_review_audit_endpoint_lists_events(self) -> None:
        with (
            mock.patch("qsign_translator.api.settings", mock.Mock(review_token="secret")),
            mock.patch(
                "qsign_translator.api.db.list_audit_events",
                return_value=[{"id": "audit-1", "job_id": "job-1", "event_type": "job_created"}],
            ),
        ):
            response = self.client.get(
                "/v1/review/audit?job_id=job-1",
                headers={"x-qsign-review-token": "secret"},
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 1)
        self.assertEqual(response.json()["items"][0]["event_type"], "job_created")

    def test_review_system_status_endpoint_returns_service_snapshot(self) -> None:
        with (
            mock.patch("qsign_translator.api.settings", mock.Mock(review_token="secret")),
            mock.patch(
                "qsign_translator.api.db.readiness",
                return_value={"configured": True, "ok": True, "sources": 1, "lexicon_entries": 2},
            ),
            mock.patch(
                "qsign_translator.api.db.review_metrics",
                return_value={"totals": {"total_jobs": 5}, "by_language": []},
            ),
            mock.patch("qsign_translator.api.shutil.which", return_value="/usr/bin/ffmpeg"),
            mock.patch("qsign_translator.api.default_lexicon_path", return_value=Path(__file__)),
        ):
            response = self.client.get(
                "/v1/review/system-status",
                headers={"x-qsign-review-token": "secret"},
            )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["services"]["ffmpeg"]["installed"])

    def test_review_coverage_report_endpoint_returns_payload(self) -> None:
        with (
            mock.patch("qsign_translator.api.settings", mock.Mock(review_token="secret")),
            mock.patch(
                "qsign_translator.api.db.review_coverage_report",
                return_value={"top_fallbacks": [{"source_token": "Александр", "hits": 3}]},
            ),
        ):
            response = self.client.get(
                "/v1/review/coverage-report?limit_jobs=100&limit_terms=20",
                headers={"x-qsign-review-token": "secret"},
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["report"]["top_fallbacks"][0]["source_token"], "Александр")

    def test_review_lexicon_candidates_endpoint_creates_item(self) -> None:
        with (
            mock.patch("qsign_translator.api.settings", mock.Mock(review_token="secret")),
            mock.patch("qsign_translator.api.db.get_translation_job", return_value={"id": "job-1"}),
            mock.patch(
                "qsign_translator.api.db.create_lexicon_suggestion",
                return_value={"id": "cand-1", "job_id": "job-1", "source_token": "Александр"},
            ),
        ):
            response = self.client.post(
                "/v1/review/lexicon-candidates",
                json={
                    "job_id": "job-1",
                    "unit_position": 1,
                    "source_token": "Александр",
                    "suggested_gloss": "ALEXANDER",
                    "suggested_language": "ru",
                    "reason": "Нужна ручная фиксация.",
                },
                headers={"x-qsign-review-token": "secret"},
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["item"]["id"], "cand-1")

    def test_review_publish_status_endpoint_updates_state(self) -> None:
        with (
            mock.patch("qsign_translator.api.settings", mock.Mock(review_token="secret")),
            mock.patch(
                "qsign_translator.api.db.update_publish_status",
                return_value={"id": "job-1", "publish_status": "publishable"},
            ),
        ):
            response = self.client.patch(
                "/v1/review/jobs/job-1/publish-status",
                json={"publish_status": "publishable", "note": "ok"},
                headers={"x-qsign-review-token": "secret"},
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["publish_status"], "publishable")


if __name__ == "__main__":
    unittest.main()
