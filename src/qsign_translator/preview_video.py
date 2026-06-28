from __future__ import annotations

import hashlib
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


class PreviewVideoUnavailable(RuntimeError):
    pass


PREVIEW_WIDTH = 640
PREVIEW_HEIGHT = 360
PREVIEW_FONT_SIZE = 16
PREVIEW_FRAME_RATE = 10
FFMPEG_TIMEOUT_SECONDS = 8
PREVIEW_BACKGROUND_COLOR = "#eef5f1"


@dataclass(frozen=True)
class PreviewVideoArtifact:
    path: Path
    duration_seconds: float
    unit_count: int
    kind: str


def build_review_video(
    job: dict[str, object],
    *,
    output_root: Path,
) -> PreviewVideoArtifact:
    """Собирает честное обзорное видео черновика.

    Это не сурдоперевод и не аватар с реальными жестами. Видео нужно, чтобы
    можно было открыть, скачать и проверить сам черновик по шагам.
    """

    ffmpeg_path = shutil.which("ffmpeg")
    if not ffmpeg_path:
        raise PreviewVideoUnavailable("ffmpeg is not installed")

    units = list(job.get("units") or [])
    if not units:
        raise PreviewVideoUnavailable("translation job has no units")

    output_root.mkdir(parents=True, exist_ok=True)
    signature = _job_signature(job)
    output_path = output_root / f"{job.get('id', 'job')}-{signature}.mp4"
    if output_path.exists() and output_path.stat().st_size > 0:
        return PreviewVideoArtifact(
            path=output_path,
            duration_seconds=_duration_seconds(units),
            unit_count=len(units),
            kind="review_storyboard",
        )

    with tempfile.TemporaryDirectory(prefix="qsign-review-video-") as tmp_dir:
        workdir = Path(tmp_dir)
        subtitles_path = workdir / "captions.srt"
        subtitles_path.write_text(_build_srt(units), encoding="utf-8")
        tmp_output = workdir / "review.mp4"
        try:
            _render_preview_video(
                ffmpeg_path=ffmpeg_path,
                subtitles_path=subtitles_path,
                output_path=tmp_output,
                duration_seconds=_duration_seconds(units),
            )
        except PreviewVideoUnavailable as exc:
            raise PreviewVideoUnavailable(str(exc)) from exc

        if not tmp_output.exists() or tmp_output.stat().st_size == 0:
            raise PreviewVideoUnavailable("preview video was not created")
        tmp_output.replace(output_path)

    return PreviewVideoArtifact(
        path=output_path,
        duration_seconds=_duration_seconds(units),
        unit_count=len(units),
        kind="review_storyboard",
    )


def _job_signature(job: dict[str, object]) -> str:
    units = list(job.get("units") or [])
    payload = [
        str(job.get("id") or ""),
        str(job.get("input_text") or ""),
        str(job.get("review_status") or ""),
        str(job.get("updated_at") or ""),
        *(
            f"{unit.get('position')}|{unit.get('kind')}|{unit.get('source_token')}|{unit.get('gloss')}"
            for unit in units
        ),
    ]
    digest = hashlib.sha1("\n".join(payload).encode("utf-8")).hexdigest()
    return digest[:12]


def _render_preview_video(
    *,
    ffmpeg_path: str,
    subtitles_path: Path,
    output_path: Path,
    duration_seconds: float,
) -> None:
    primary_filter = _build_filter(subtitles_path)
    fallback_filter = _build_fallback_filter()
    primary_error: str | None = None
    for filter_value, kind in ((primary_filter, "storyboard"), (fallback_filter, "fallback")):
        command = [
            ffmpeg_path,
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"color=c={PREVIEW_BACKGROUND_COLOR}:s={PREVIEW_WIDTH}x{PREVIEW_HEIGHT}:r={PREVIEW_FRAME_RATE}",
            "-frames:v",
            str(max(1, int(duration_seconds * PREVIEW_FRAME_RATE))),
            "-framerate",
            str(PREVIEW_FRAME_RATE),
            "-vf",
            filter_value,
            "-t",
            f"{duration_seconds:.3f}",
            "-r",
            str(PREVIEW_FRAME_RATE),
            "-threads",
            "1",
            "-pix_fmt",
            "yuv420p",
            "-c:v",
            "mpeg4",
            "-q:v",
            "8",
            "-movflags",
            "+faststart",
            str(output_path),
        ]
        try:
            subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
                timeout=FFMPEG_TIMEOUT_SECONDS,
            )
            return
        except subprocess.CalledProcessError as exc:
            stderr = (exc.stderr or "").strip()
            message = f"ffmpeg {kind} render failed: {stderr or exc}"
        except subprocess.TimeoutExpired:
            message = f"ffmpeg {kind} render timed out"
        if kind == "storyboard":
            primary_error = message
            continue
        raise PreviewVideoUnavailable(primary_error or message)


def _duration_seconds(units: list[dict[str, object]]) -> float:
    return max(3.0, len(units) * 1.4)


def _build_srt(units: list[dict[str, object]]) -> str:
    blocks: list[str] = []
    segment_seconds = _duration_seconds(units) / max(1, len(units))
    for index, unit in enumerate(units, start=1):
        start = (index - 1) * segment_seconds
        end = index * segment_seconds
        lines = [_subtitle_line(unit, index, len(units))]
        if unit.get("kind") == "gloss" and unit.get("gloss"):
            lines.append(f"глосса: {unit['gloss']}")
        elif unit.get("kind") == "dactyl":
            lines.append("режим: дактиль, нужна словарная проверка")
        else:
            lines.append("режим: черновая подсказка, нужна ручная замена")
        blocks.append(
            "\n".join(
                [
                    str(index),
                    f"{_format_srt_time(start)} --> {_format_srt_time(end)}",
                    *lines,
                    "",
                ]
            )
        )
    return "\n".join(blocks)


def _subtitle_line(unit: dict[str, object], index: int, total: int) -> str:
    source_token = str(unit.get("source_token") or "без текста").strip() or "без текста"
    kind = str(unit.get("kind") or "unknown")
    if kind == "gloss":
        status = "словарный жест"
    elif kind == "dactyl":
        status = "по буквам"
    else:
        status = "нужна замена"
    return f"{index}/{total} • {source_token} • {status}"


def _format_srt_time(value: float) -> str:
    milliseconds = max(0, int(round(value * 1000)))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


def _build_filter(subtitles_path: Path) -> str:
    subtitle_value = subtitles_path.as_posix().replace("\\", "\\\\").replace(":", "\\:")
    style = (
        "FontName=DejaVu Sans,"
        f"FontSize={PREVIEW_FONT_SIZE},"
        "PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H64000000,"
        "BackColour=&H50000000,"
        "BorderStyle=3,"
        "Outline=1,"
        "Shadow=0,"
        "Alignment=2,"
        "MarginV=26"
    )
    return f"subtitles={subtitle_value}:force_style='{style}'"


def _build_fallback_filter() -> str:
    return "null"
