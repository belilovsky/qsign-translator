import unittest

from qsign_translator.language import detect_language, normalize_language_hint
from qsign_translator import SignPlanner
from qsign_translator.lexicon import load_default_lexicon


class LanguageTests(unittest.TestCase):
    def test_detects_english_text(self) -> None:
        self.assertEqual(detect_language("hello world"), "en")

    def test_detects_mixed_script_text(self) -> None:
        self.assertEqual(detect_language("Hello мир"), "mixed")

    def test_detects_kazakh_text(self) -> None:
        self.assertEqual(detect_language("Қалайсыз"), "kk")

    def test_normalize_language_hint_variants(self) -> None:
        self.assertEqual(normalize_language_hint("EN"), "en")
        self.assertEqual(normalize_language_hint("kz"), "kk")
        self.assertEqual(normalize_language_hint("Русский"), None)

    def test_planner_respects_language_hint_for_unknown_script(self) -> None:
        planner = SignPlanner(load_default_lexicon())
        plan = planner.plan("Hello", language_hint="en")
        self.assertEqual(plan.language, "en")
        self.assertEqual(plan.units[0].kind, "gloss")

    def test_planner_respects_kazakh_language_hint(self) -> None:
        planner = SignPlanner(load_default_lexicon())
        plan = planner.plan("Қалайсыз", language_hint="kk")
        self.assertEqual(plan.language, "kk")
        self.assertEqual(plan.units[0].kind, "gloss")

    def test_detects_kazakh_without_specific_chars_when_hint_tokens_present(self) -> None:
        self.assertEqual(detect_language("Мен керек"), "kk")

    def test_planner_respects_kazakh_language_for_common_kazakh_words(self) -> None:
        planner = SignPlanner(load_default_lexicon())
        plan = planner.plan("Мен аурухана")
        self.assertEqual(plan.language, "kk")


if __name__ == "__main__":
    unittest.main()
