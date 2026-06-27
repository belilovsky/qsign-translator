from __future__ import annotations

import json
from pathlib import Path
import unittest

from qsign_translator import SignPlanner
from qsign_translator.lexicon import load_default_lexicon


FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "phrase_coverage_cases.json"


class PhraseCoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.planner = SignPlanner(load_default_lexicon())
        cls.cases = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))["cases"]

    def test_phrase_coverage_expectations(self) -> None:
        for case in self.cases:
            with self.subTest(text=case["text"]):
                plan = self.planner.plan(case["text"])
                self.assertEqual(plan.language, case["expected_language"])
                self.assertEqual(plan.fallback_count, case["expected_fallback_count"])
                glosses = [unit.gloss for unit in plan.units]
                if case.get("require_exact_glosses"):
                    self.assertEqual(glosses, case["expected_glosses"])
                for required_gloss in case["expected_glosses"]:
                    self.assertIn(required_gloss, glosses)


if __name__ == "__main__":
    unittest.main()
