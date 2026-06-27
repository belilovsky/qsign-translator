from __future__ import annotations

import hashlib
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


class PreviewVideoUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class PreviewVideoArtifact:
    path: Path
    duration_seconds: float
    unit_count: int
    kind: str


def build_review_video(
    job: dict[str, object],
    *,
    static_root: Path,
    output_root: Path,
) -> PreviewVideoArtifact:
    """Собирает честное обзорное видео черновика.

    Это не сурдоперевод и не аватар с реальными жестами. Видео нужно, чтобы
    можно было открыть, скачать и проверить сам черновик по шагам.
    """

    ffmpeg_path = shutil.which("ffmpeg")
    if not ffmpeg_path:
        raise PreviewVideoUnavailable("ffmpeg is not installed")

    avatar_path = static_root / "assets" / "signing-avatar.png"
    if not avatar_path.exists():
        raise PreviewVideoUnavailable("preview avatar asset is missing")

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
        filter_value = _build_filter(subtitles_path)
        command = [
            ffmpeg_path,
            "-y",
            "-loop",
            "1",
            "-framerate",
            "25",
            "-i",
            str(avatar_path),
            "-vf",
            filter_value,
            "-t",
            f"{_duration_seconds(units):.3f}",
            "-pix_fmt",
            "yuv420p",
            "-c:v",
            "libx264",
            "-movflags",
            "+faststart",
            str(tmp_output),
        ]
        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as exc:
            stderr = (exc.stderr or "").strip()
            raise PreviewVideoUnavailable(f"ffmpeg failed: {stderr or exc}") from exc

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
        "FontSize=24,"
        "PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H64000000,"
        "BackColour=&H50000000,"
        "BorderStyle=3,"
        "Outline=1,"
        "Shadow=0,"
        "Alignment=2,"
        "MarginV=26"
    )
    return (
        "scale=1280:720:force_original_aspect_ratio=decrease,"
        "pad=1280:720:(ow-iw)/2:(oh-ih)/2:color=white,"
        f"subtitles={subtitle_value}:force_style='{style}'"
    )
