import os
import unittest
from unittest import mock

from qsign_translator import db
from qsign_translator.lexicon import load_default_lexicon
from qsign_translator.planner import SignPlanner


class FakeCursor:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[object, ...]]] = []
        self.rows: list[dict[str, object]] = [
            {"id": "job-1", "job_id": "job-1", "review_status": "pending_signer_review"}
        ]

    def __enter__(self) -> "FakeCursor":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def execute(self, query: str, params: tuple[object, ...] = ()) -> None:
        self.calls.append((query, params))

    def fetchone(self) -> dict[str, str]:
        return {"id": "job-1"}

    def fetchall(self) -> list[dict[str, object]]:
        return self.rows


class FakeConnection:
    def __init__(self, cursor: FakeCursor) -> None:
        self.cursor_instance = cursor
        self.committed = False

    def __enter__(self) -> "FakeConnection":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def cursor(self) -> FakeCursor:
        return self.cursor_instance

    def commit(self) -> None:
        self.committed = True


class InvalidTextRepresentation(Exception):
    sqlstate = "22P02"


class InvalidUuidCursor(FakeCursor):
    def execute(self, query: str, params: tuple[object, ...] = ()) -> None:
        super().execute(query, params)
        raise InvalidTextRepresentation("invalid uuid")


class DatabaseTests(unittest.TestCase):
    def test_readiness_without_database_url_is_explicit(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            result = db.readiness()
        self.assertFalse(result["configured"])
        self.assertFalse(result["ok"])

    def test_record_translation_job_writes_job_and_units(self) -> None:
        planner = SignPlanner(load_default_lexicon())
        plan = planner.plan("Привет Александр")
        cursor = FakeCursor()
        connection = FakeConnection(cursor)

        with mock.patch("qsign_translator.db.connect", return_value=connection):
            job_id = db.record_translation_job(plan)

        self.assertEqual(job_id, "job-1")
        self.assertTrue(connection.committed)
        self.assertEqual(len(cursor.calls), 2 + len(plan.units))
        job_params = cursor.calls[0][1]
        self.assertEqual(job_params[0], "text")
        self.assertEqual(job_params[2], "ru")
        self.assertEqual(cursor.calls[0][0].count("%s"), len(job_params))
        self.assertEqual(job_params[3], plan.job_status)
        self.assertEqual(job_params[4], plan.output_kind)
        self.assertEqual(job_params[5], plan.output_status)
        self.assertEqual(job_params[8], "pending_signer_review")
        self.assertEqual(job_params[11], plan.fallback_count)
        unit_params = cursor.calls[1][1]
        self.assertEqual(unit_params[0], "job-1")
        self.assertEqual(unit_params[1], 1)

    def test_record_feedback_rejects_unknown_type(self) -> None:
        with self.assertRaises(ValueError):
            db.record_feedback("job-1", "unknown")

    def test_record_feedback_writes_event(self) -> None:
        cursor = FakeCursor()
        connection = FakeConnection(cursor)

        with mock.patch("qsign_translator.db.connect", return_value=connection):
            feedback_id = db.record_feedback("job-1", "good")

        self.assertEqual(feedback_id, "job-1")
        self.assertTrue(connection.committed)
        self.assertEqual(len(cursor.calls), 2)
        self.assertIn("INSERT INTO feedback_events", cursor.calls[0][0])
        self.assertEqual(cursor.calls[0][1], ("job-1", "good", None))

    def test_list_translation_jobs_rejects_unknown_review_status(self) -> None:
        with self.assertRaises(ValueError):
            db.list_translation_jobs(review_status="bad")

    def test_list_translation_jobs_filters_by_review_status(self) -> None:
        cursor = FakeCursor()
        connection = FakeConnection(cursor)

        with mock.patch("qsign_translator.db.connect", return_value=connection):
            rows = db.list_translation_jobs(
                review_status="pending_signer_review", limit=10
            )

        self.assertEqual(rows[0]["id"], "job-1")
        self.assertEqual(cursor.calls[0][1], ("pending_signer_review", 10))

    def test_get_translation_job_treats_invalid_uuid_as_missing(self) -> None:
        cursor = InvalidUuidCursor()
        connection = FakeConnection(cursor)

        with mock.patch("qsign_translator.db.connect", return_value=connection):
            row = db.get_translation_job("not-a-uuid")

        self.assertIsNone(row)

    def test_update_review_status_writes_allowed_status(self) -> None:
        cursor = FakeCursor()
        connection = FakeConnection(cursor)

        with mock.patch("qsign_translator.db.connect", return_value=connection):
            row = db.update_review_status("job-1", "approved")

        self.assertEqual(row["id"], "job-1")
        self.assertTrue(connection.committed)
        self.assertEqual(cursor.calls[0][1], ("approved", "job-1"))

    def test_update_review_status_rejects_unknown_status(self) -> None:
        with self.assertRaises(ValueError):
            db.update_review_status("job-1", "bad")

    def test_update_review_status_treats_invalid_uuid_as_missing(self) -> None:
        cursor = InvalidUuidCursor()
        connection = FakeConnection(cursor)

        with mock.patch("qsign_translator.db.connect", return_value=connection):
            row = db.update_review_status("not-a-uuid", "approved")

        self.assertIsNone(row)

    def test_list_feedback_events_filters_by_job(self) -> None:
        cursor = FakeCursor()
        connection = FakeConnection(cursor)

        with mock.patch("qsign_translator.db.connect", return_value=connection):
            rows = db.list_feedback_events(job_id="job-1", limit=10)

        self.assertEqual(rows[0]["job_id"], "job-1")
        self.assertEqual(cursor.calls[0][1], ("job-1", 10))

    def test_list_feedback_events_treats_invalid_uuid_as_empty(self) -> None:
        cursor = InvalidUuidCursor()
        connection = FakeConnection(cursor)

        with mock.patch("qsign_translator.db.connect", return_value=connection):
            rows = db.list_feedback_events(job_id="not-a-uuid", limit=10)

        self.assertEqual(rows, [])

    def test_create_review_session_writes_event(self) -> None:
        cursor = FakeCursor()
        connection = FakeConnection(cursor)

        with mock.patch("qsign_translator.db.connect", return_value=connection):
            row = db.create_review_session(
                job_id="job-1",
                reviewer_role="native_signer",
                reviewer_language="ru",
                meaning_score=4,
                understandability_score=5,
                notes="Looks usable after one correction.",
                blocking_issue=False,
            )

        self.assertEqual(row["id"], "job-1")
        self.assertTrue(connection.committed)
        self.assertIn("INSERT INTO review_sessions", cursor.calls[0][0])
        self.assertEqual(cursor.calls[0][1][0], "job-1")
        self.assertEqual(cursor.calls[0][1][1], "native_signer")

    def test_list_review_sessions_filters_by_job(self) -> None:
        cursor = FakeCursor()
        connection = FakeConnection(cursor)

        with mock.patch("qsign_translator.db.connect", return_value=connection):
            rows = db.list_review_sessions(job_id="job-1", limit=10)

        self.assertEqual(rows[0]["job_id"], "job-1")
        self.assertEqual(cursor.calls[0][1], ("job-1", 10))

    def test_list_review_sessions_treats_invalid_uuid_as_empty(self) -> None:
        cursor = InvalidUuidCursor()
        connection = FakeConnection(cursor)

        with mock.patch("qsign_translator.db.connect", return_value=connection):
            rows = db.list_review_sessions(job_id="not-a-uuid", limit=10)

        self.assertEqual(rows, [])

    def test_attach_rendered_video_updates_output_fields(self) -> None:
        cursor = FakeCursor()
        connection = FakeConnection(cursor)

        with mock.patch("qsign_translator.db.connect", return_value=connection):
            row = db.attach_rendered_video(
                "job-1",
                output_uri="/v1/jobs/job-1/rendered-video",
                output_status="ready",
                render_adapter="external_upload",
            )

        self.assertEqual(row["id"], "job-1")
        self.assertTrue(connection.committed)
        self.assertIn("UPDATE translation_jobs", cursor.calls[0][0])
        self.assertEqual(
            cursor.calls[0][1],
            ("/v1/jobs/job-1/rendered-video", "ready", "external_upload", "job-1"),
        )

    def test_update_publish_status_rejects_unknown_status(self) -> None:
        with self.assertRaises(ValueError):
            db.update_publish_status("job-1", publish_status="bad")

    def test_update_publish_status_writes_allowed_status(self) -> None:
        cursor = FakeCursor()
        connection = FakeConnection(cursor)

        with mock.patch("qsign_translator.db.connect", return_value=connection):
            row = db.update_publish_status(
                "job-1", publish_status="publishable", note="final video approved"
            )

        self.assertEqual(row["id"], "job-1")
        self.assertTrue(connection.committed)
        self.assertIn("UPDATE translation_jobs", cursor.calls[0][0])
        self.assertEqual(cursor.calls[0][1], ("publishable", "job-1"))

    def test_list_audit_events_filters_by_job(self) -> None:
        cursor = FakeCursor()
        connection = FakeConnection(cursor)

        with mock.patch("qsign_translator.db.connect", return_value=connection):
            rows = db.list_audit_events(job_id="job-1", limit=10)

        self.assertEqual(rows[0]["job_id"], "job-1")
        self.assertEqual(cursor.calls[0][1], ("job-1", 10))


if __name__ == "__main__":
    unittest.main()
