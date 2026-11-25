"""The learning project the tools work on, and its settings (``lvp.toml``).

A project is a folder with an ``lvp.toml`` at its root. Every command finds it by walking up
from the current directory (or from ``LVP_PROJECT``), so the engine can be installed once and
used for any number of topics.

    my-topic/
      lvp.toml          settings: language, theme, voice, budget, pronunciation
      learner.md        who is learning (written by the setup skill, read by every skill)
      material/         sources: PDFs, slides, transcripts, notes (+ material/digest/)
      plan/             curriculum, coverage map, scripts
      videos/           one Manim scene file per video: videos/v01_name/name.py
      cards/            Anki cards as YAML (+ built .apkg)
      exercises/        practice sheets and exercise companions
      voice_cache/      paid narration (commit it: never pay twice)
      tex_cache/        rendered formulas (commit it: no LaTeX needed on the viewer's PC)
      build/            renders, logs, reports (not committed)
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path

MARKER = "lvp.toml"
PACKAGE_DIR = Path(__file__).resolve().parent


def find_root(start: Path | None = None) -> Path:
    """Project root: $LVP_PROJECT, else the nearest folder with an lvp.toml, else the cwd."""
    env = os.environ.get("LVP_PROJECT")
    if env:
        return Path(env).resolve()
    here = (start or Path.cwd()).resolve()
    for d in (here, *here.parents):
        if (d / MARKER).exists():
            return d
    return here


@dataclass
class Settings:
    title: str = "Untitled course"
    language: str = "en"  # narration + on-screen text: "en", "de", ...
    theme: str = "paper"  # paper | night | terminal
    tts_provider: str = "openrouter"  # openrouter | silent
    tts_model: str = "google/gemini-3.8-flash-tts"
    tts_voice: str = "Kore"
    voice_speed: float = 1.15  # applied locally with ffmpeg, free to change
    chars_per_second: float = 15.0  # speaking rate at speed 1.0, for silent drafts
    max_usd_per_run: float = 0.50  # spend cap for paid narration per command
    critic_model: str = "google/gemini-3.8-flash"
    pronunciation: dict[str, str] = field(default_factory=dict)  # word -> spoken spelling
    series: str = ""  # small tag in the corner of every video, e.g. "Statistics · Video {n}"


@cache
def settings() -> Settings:
    path = find_root() / MARKER
    data = tomllib.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    s = Settings()
    flat = {**data.get("course", {}), **data.get("video", {}), **data.get("voice", {}),
            **data.get("budget", {})}  # fmt: skip
    keys = {
        "title": "title", "language": "language", "theme": "theme", "provider": "tts_provider",
        "model": "tts_model", "voice": "tts_voice", "speed": "voice_speed",
        "chars_per_second": "chars_per_second", "max_usd_per_run": "max_usd_per_run",
        "critic_model": "critic_model", "series": "series",
    }  # fmt: skip
    for k, attr in keys.items():
        if k in flat:
            setattr(s, attr, type(getattr(s, attr))(flat[k]))
    s.pronunciation = dict(data.get("pronunciation", {}))
    # environment overrides (one-off runs, CI)
    s.theme = os.environ.get("LVP_THEME", s.theme)
    s.voice_speed = float(os.environ.get("LVP_VOICE_SPEED", s.voice_speed))
    s.max_usd_per_run = float(os.environ.get("LVP_MAX_USD", s.max_usd_per_run))
    return s


ROOT = find_root()
VIDEOS = ROOT / "videos"
MATERIAL = ROOT / "material"
CARDS = ROOT / "cards"
VOICE_CACHE = ROOT / "voice_cache"
TEX_CACHE = ROOT / "tex_cache"
BUILD = ROOT / "build"
FONTS_DIR = PACKAGE_DIR / "fonts"
