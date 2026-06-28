import unittest

from qsign_translator import SignPlanner
from qsign_translator.language import detect_language
from qsign_translator.lexicon import load_default_lexicon


class SignPlannerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.planner = SignPlanner(load_default_lexicon())

    def test_detects_kazakh(self) -> None:
        self.assertEqual(detect_language("Сәлеметсіз бе, көмек керек"), "kk")

    def test_russian_known_and_dactyl_fallback(self) -> None:
        plan = self.planner.plan("Привет Александр")
        self.assertEqual(plan.language, "ru")
        self.assertEqual(plan.units[0].kind, "gloss")
        self.assertEqual(plan.units[0].gloss, "HELLO")
        self.assertEqual(plan.units[1].kind, "dactyl")
        self.assertIn("DACTYL_A", plan.units[1].gloss)

    def test_russian_phrase_lookup(self) -> None:
        plan = self.planner.plan("Привет меня зовут Александр")
        glosses = [unit.gloss for unit in plan.units]
        self.assertIn("ME NAME", glosses)
        self.assertEqual(len([unit for unit in plan.units if unit.source_token == "меня зовут"]), 1)

    def test_russian_polite_greeting_phrase_lookup(self) -> None:
        plan = self.planner.plan("Добрый день")
        self.assertEqual(len(plan.units), 1)
        self.assertEqual(plan.units[0].kind, "gloss")
        self.assertEqual(plan.units[0].gloss, "HELLO_FORMAL")

    def test_imported_slovo_token_is_matched(self) -> None:
        plan = self.planner.plan("Короткий")
        self.assertEqual(plan.language, "ru")
        self.assertEqual(len(plan.units), 1)
        self.assertEqual(plan.units[0].kind, "gloss")
        self.assertEqual(plan.units[0].gloss, "КОРОТКИЙ")
        self.assertEqual(plan.units[0].source, "slovo:archive_gloss")

    def test_kazakh_known_words(self) -> None:
        plan = self.planner.plan("Сәлеметсіз бе көмек керек")
        glosses = [unit.gloss for unit in plan.units]
        self.assertIn("HELLO_FORMAL", glosses)
        self.assertIn("QUESTION_NMM", glosses)
        self.assertIn("HELP", glosses)
        self.assertIn("NEED", glosses)

    def test_russian_alias_forms_reuse_reviewed_entries(self) -> None:
        plan = self.planner.plan("Мне нужно помочь")
        self.assertEqual([unit.kind for unit in plan.units], ["gloss", "gloss", "gloss"])
        self.assertEqual([unit.gloss for unit in plan.units], ["ME", "NEED", "HELP"])

    def test_common_gratitude_phrase_is_collapsed(self) -> None:
        plan = self.planner.plan("Спасибо большое")
        self.assertEqual(plan.fallback_count, 0)
        self.assertEqual([unit.gloss for unit in plan.units], ["THANK_YOU", "БОЛЬШОЙ"])

    def test_address_alias_and_conjunction_omit_reduce_noise(self) -> None:
        plan = self.planner.plan("Адрес и работа")
        self.assertEqual([unit.kind for unit in plan.units], ["gloss", "gloss"])
        self.assertEqual([unit.gloss for unit in plan.units], ["АДРЕС/УЛИЦА", "РАБОТА"])

    def test_common_service_forms_reuse_existing_glosses(self) -> None:
        plan = self.planner.plan("Я не понимаю")
        self.assertEqual(plan.fallback_count, 0)
        self.assertEqual([unit.gloss for unit in plan.units], ["ME", "НЕ", "ПОНИМАТЬ"])

    def test_u_menya_phrase_and_pain_alias_reduce_noise(self) -> None:
        plan = self.planner.plan("У меня болит голова")
        self.assertEqual(plan.fallback_count, 0)
        self.assertEqual([unit.gloss for unit in plan.units], ["ME", "БОЛЕТЬ", "ГОЛОВА"])

    def test_child_case_alias_and_nonsemantic_preposition_omit(self) -> None:
        plan = self.planner.plan("Нужна школа для ребенка")
        self.assertEqual(plan.fallback_count, 0)
        self.assertEqual([unit.gloss for unit in plan.units], ["NEED", "ШКОЛА", "РЕБЕНОК"])

    def test_plan_has_warning(self) -> None:
        data = self.planner.plan("Спасибо").to_dict()
        self.assertIn("native_signer_validation_required", data["warnings"])

    def test_high_risk_domain_requires_human_interpreter(self) -> None:
        data = self.planner.plan("Мне нужна скорая помощь").to_dict()
        self.assertTrue(data["risk"]["needs_human_interpreter"])
        self.assertIn("emergency", data["risk"]["domains"])
        self.assertIn("high_risk_domain_requires_human_interpreter", data["warnings"])

    def test_coverage_metadata(self) -> None:
        data = self.planner.plan("Привет Александр").to_dict()
        self.assertEqual(data["coverage"]["total"], 2)
        self.assertEqual(data["coverage"]["gloss"], 1)
        self.assertEqual(data["coverage"]["dactyl"], 1)
        self.assertEqual(data["metadata"]["fallback_count"], 1)
        self.assertEqual(data["metadata"]["unknown_token_count"], 1)
        self.assertEqual(data["metadata"]["job_status"], "review_required")
        self.assertEqual(data["metadata"]["review_status"], "pending_signer_review")
        self.assertEqual(data["metadata"]["output_kind"], "sign_plan_preview")
        self.assertEqual(data["metadata"]["output_status"], "not_rendered")
        self.assertFalse(data["metadata"]["publish_ready"])
        self.assertIn("seed", data["metadata"]["source_ids"])
        self.assertIn("fallback", data["metadata"]["source_ids"])

    def test_english_known_word_lookup(self) -> None:
        data = self.planner.plan("Hello thank you", language_hint="en").to_dict()
        self.assertEqual(data["language"], "en")
        self.assertEqual([unit["gloss"] for unit in data["units"]], ["HELLO", "THANK_YOU"])
        self.assertEqual([unit["kind"] for unit in data["units"]], ["gloss", "gloss"])

    def test_latin_kazakh_text_routes_to_kk(self) -> None:
        data = self.planner.plan("salam dostar").to_dict()
        self.assertEqual(data["language"], "kk")
        self.assertEqual(data["units"][0]["gloss"], "HELLO")
        self.assertIn("dactyl", [unit["kind"] for unit in data["units"]])

    def test_language_scopes_do_not_leak_cross_language_matches(self) -> None:
        data = self.planner.plan("Hello", language_hint="ru").to_dict()
        self.assertEqual(data["language"], "ru")
        self.assertEqual(data["units"][0]["kind"], "dactyl")
        self.assertEqual(data["units"][0]["source"], "fallback:dactyl")

    def test_mixed_script_input_is_deterministically_routed(self) -> None:
        data = self.planner.plan("Hello мен керек").to_dict()
        self.assertEqual(data["language"], "kk")
        self.assertIn("NEED", [unit.gloss for unit in self.planner.plan("Hello мен керек").units])

    def test_trace_explains_pipeline(self) -> None:
        data = self.planner.plan("Привет Александр").to_dict()
        trace = data["trace"]
        self.assertEqual(trace["summary"]["token_count"], 2)
        self.assertEqual(trace["summary"]["unit_count"], 2)
        self.assertEqual(trace["summary"]["fallback_units"], 1)
        self.assertEqual(trace["summary"]["review_gate"], "native_signer_review_required")
        self.assertEqual([stage["id"] for stage in trace["stages"]], [
            "input",
            "language",
            "normalization",
            "planning",
            "review",
            "output",
        ])
        self.assertEqual(trace["stages"][0]["summary"], "16 символов, 2 токена.")
        self.assertEqual(trace["stages"][3]["summary"], "Найдено 1, требует замены 1, всего 2 единицы.")
        self.assertEqual(trace["stages"][5]["summary"], "Видео-аватар пока не собран. Сейчас доступен только прозрачный черновик плана.")

    def test_unit_decisions_explain_matches_and_fallbacks(self) -> None:
        data = self.planner.plan("Привет Александр").to_dict()
        decisions = [unit["decision"] for unit in data["units"]]
        self.assertEqual(decisions[0]["type"], "token_lookup")
        self.assertEqual(decisions[0]["status"], "matched")
        self.assertEqual(decisions[1]["type"], "dactyl_fallback")
        self.assertEqual(decisions[1]["status"], "needs_review")


if __name__ == "__main__":
    unittest.main()
