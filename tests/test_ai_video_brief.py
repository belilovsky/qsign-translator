from __future__ import annotations

import unittest

from qsign_translator.ai_video_brief import build_ai_video_batch_brief, build_ai_video_brief


class AIVideoBriefTests(unittest.TestCase):
    def test_builds_prompt_package_with_fallback_rules(self) -> None:
        job = {
            "id": "job-1",
            "input_text": "Привет Александр",
            "detected_language": "ru",
            "review_status": "pending_signer_review",
            "risk_domains": ["emergency"],
            "units": [
                {"position": 1, "kind": "gloss", "source_token": "привет", "gloss": "HELLO", "clip_id": "rsl_hello"},
                {"position": 2, "kind": "dactyl", "source_token": "александр", "gloss": "DACTYL_A", "clip_id": None},
            ],
        }
        render_plan = {
            "pipeline_status": "awaiting_signer_review",
            "publish_gate": {"blockers": ["needs_signer_approval", "missing_render_assets"]},
            "summary": {"resolved_segments": 1, "missing_segments": 1},
        }

        brief = build_ai_video_brief(job, render_plan)

        self.assertEqual(brief["job_id"], "job-1")
        self.assertEqual(brief["format_version"], "qsign-ai-video-brief/v1")
        self.assertEqual(brief["summary"]["resolved_segments"], 1)
        self.assertEqual(brief["summary"]["missing_segments"], 1)
        self.assertEqual(brief["summary"]["fallback_units"], 1)
        self.assertEqual(brief["summary"]["pipeline_status"], "awaiting_signer_review")
        self.assertIn("needs_signer_approval", brief["summary"]["publish_blockers"])
        self.assertEqual(brief["video_spec"]["fps"], 25)
        self.assertEqual(brief["units"][1]["kind"], "dactyl")
        self.assertIn("Finger-spell", brief["units"][1]["instruction"])
        self.assertIn("High-risk domains present", brief["prompts"]["master_prompt"])
        self.assertIn("Do not generate multiple people", brief["prompts"]["negative_prompt"])
        self.assertIn("Unknown terms must remain dactyl", brief["prompts"]["operator_task"])
        self.assertIn("exports", brief)
        self.assertIn("universal_prompt", brief["exports"])
        self.assertIn("operator_handoff", brief["exports"])
        self.assertIn("json_payload", brief["exports"])
        self.assertIn("render_contract", brief["exports"])
        self.assertIn("QSign AI Video Brief", brief["exports"]["universal_prompt"]["text"])
        self.assertIn("Operator handoff", brief["exports"]["operator_handoff"]["text"])
        self.assertIn("QSign render contract", brief["exports"]["render_contract"]["text"])
        self.assertIn("\"format_version\": \"qsign-ai-video-brief/v1\"", brief["exports"]["json_payload"]["text"])
        self.assertIn("batch_render", brief)
        self.assertEqual(brief["batch_render"]["scene_count"], 1)
        self.assertIn("Batch storyboard", brief["exports"]["batch_storyboard"]["text"])
        self.assertIn("Do not publish or distribute as final output", brief["qa_checklist"][-1])

    def test_builds_batch_brief_for_multiple_jobs(self) -> None:
        jobs_with_render_plans = [
            (
                {
                    "id": "job-1",
                    "input_text": "Привет",
                    "detected_language": "ru",
                    "review_status": "pending_signer_review",
                    "risk_domains": [],
                    "units": [
                        {"position": 1, "kind": "gloss", "source_token": "привет", "gloss": "HELLO", "clip_id": "rsl_hello"},
                    ],
                },
                {"summary": {"resolved_segments": 1, "missing_segments": 0}},
            ),
            (
                {
                    "id": "job-2",
                    "input_text": "Александр",
                    "detected_language": "ru",
                    "review_status": "needs_edit",
                    "risk_domains": [],
                    "units": [
                        {"position": 1, "kind": "dactyl", "source_token": "александр", "gloss": "DACTYL_A", "clip_id": None},
                    ],
                },
                {"summary": {"resolved_segments": 0, "missing_segments": 1}},
            ),
        ]

        brief = build_ai_video_batch_brief(jobs_with_render_plans, title="Demo batch")

        self.assertEqual(brief["format_version"], "qsign-ai-video-batch-brief/v1")
        self.assertEqual(brief["summary"]["scene_count"], 2)
        self.assertEqual(brief["summary"]["fallback_units"], 1)
        self.assertEqual(brief["summary"]["review_required_scene_count"], 2)
        self.assertEqual(brief["batch_render"]["scene_count"], 2)
        self.assertEqual(brief["batch_render"]["scenes"][0]["start_time_seconds"], 0.0)
        self.assertGreater(brief["batch_render"]["scenes"][1]["start_time_seconds"], 3.0)
        self.assertIn("batch_storyboard", brief["exports"])
        self.assertIn("scene_prompts", brief["exports"])
        self.assertIn("render_contract", brief["exports"])
        self.assertIn("QSign Batch AI Video Brief", brief["exports"]["batch_storyboard"]["text"])
        self.assertIn("QSign batch render contract", brief["exports"]["render_contract"]["text"])


if __name__ == "__main__":
    unittest.main()
