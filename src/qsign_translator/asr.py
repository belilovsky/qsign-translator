from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Transcript:
    text: str
    language: str | None
    confidence: float | None


class AsrUnavailable(RuntimeError):
    pass


class FasterWhisperAsr:
    """Optional adapter for faster-whisper.

    The dependency is intentionally optional so repository tests remain light.
    """

    def __init__(self, model_name: str = "large-v3", device: str = "auto") -> None:
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise AsrUnavailable("Install qsign-translator[asr] to use faster-whisper") from exc

        self.model = WhisperModel(model_name, device=device)

    def transcribe(self, audio_path: str | Path) -> Transcript:
        segments, info = self.model.transcribe(str(audio_path), vad_filter=True)
        text = " ".join(segment.text.strip() for segment in segments).strip()
        return Transcript(
            text=text,
            language=getattr(info, "language", None),
            confidence=getattr(info, "language_probability", None),
        )
