from __future__ import annotations

import io
import json
import runpy
import unittest
from contextlib import redirect_stdout
from unittest import mock

from qsign_translator import cli
from qsign_translator.asr import AsrUnavailable, FasterWhisperAsr


class CliTests(unittest.TestCase):
    def test_main_renders_compact_json_for_argument_text(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            exit_code = cli.main(["Привет", "помощь"])

        self.assertEqual(exit_code, 0)
        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload["language"], "ru")
        self.assertEqual([unit["gloss"] for unit in payload["units"]], ["HELLO", "HELP"])

    def test_main_supports_pretty_output_and_forced_language(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            exit_code = cli.main(["--pretty", "--language", "en", "I", "need", "help"])

        self.assertEqual(exit_code, 0)
        rendered = buffer.getvalue()
        self.assertIn('\n  "language": "en"', rendered)
        payload = json.loads(rendered)
        self.assertEqual([unit["gloss"] for unit in payload["units"]], ["ME", "NEED", "HELP"])

    def test_main_reads_stdin_when_text_argument_is_missing(self) -> None:
        buffer = io.StringIO()
        fake_stdin = io.StringIO("Сәлем көмек керек")
        with redirect_stdout(buffer), mock.patch("sys.stdin", fake_stdin):
            exit_code = cli.main([])

        self.assertEqual(exit_code, 0)
        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload["language"], "kk")
        self.assertEqual([unit["gloss"] for unit in payload["units"]], ["HELLO", "HELP", "NEED"])

    def test_main_requires_non_empty_text(self) -> None:
        fake_stdin = io.StringIO("   ")
        with mock.patch("sys.stdin", fake_stdin), self.assertRaises(SystemExit) as exc:
            cli.main([])

        self.assertEqual(exc.exception.code, 2)

    def test_python_module_entrypoint_invokes_cli_main(self) -> None:
        with mock.patch("qsign_translator.cli.main", return_value=7) as mocked_main:
            with self.assertRaises(SystemExit) as exc:
                runpy.run_module("qsign_translator", run_name="__main__")

        self.assertEqual(exc.exception.code, 7)
        mocked_main.assert_called_once_with()


class AsrAdapterTests(unittest.TestCase):
    def test_faster_whisper_adapter_raises_clear_error_when_dependency_is_missing(self) -> None:
        real_import = __import__

        def guarded_import(name: str, *args: object, **kwargs: object):
            if name == "faster_whisper":
                raise ImportError("missing faster_whisper")
            return real_import(name, *args, **kwargs)

        with mock.patch("builtins.__import__", side_effect=guarded_import):
            with self.assertRaises(AsrUnavailable) as exc:
                FasterWhisperAsr()

        self.assertIn("qsign-translator[asr]", str(exc.exception))


if __name__ == "__main__":
    unittest.main()
