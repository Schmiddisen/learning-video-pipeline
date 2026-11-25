"""Verify sync in the *finished* video file – measured, not assumed.

lvp-build's final pass of each section writes a plan (build/plan/...): when each narration block
starts, which audio file it plays, and how long the section is. This module checks the final MP4
against that plan:

1. Picture: every stitched part must be exactly as long as planned (±1 frame). Manim writes frames
   deterministically (and style.py keeps its clock frame-exact), so then every frame is in place.
2. Sound: rebuild the *expected* narration from the plan, cross-correlate it with the actual
   audio track in 6-second windows and report the offset of each window (10 ms resolution).

Only audio is decoded, so this takes seconds even for a 4K video.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import numpy as np

RATE = 8000  # Hz for decoding
HOP = 80  # samples per envelope frame → 100 frames/s (10 ms)
FPS_ENV = RATE // HOP
WINDOW, STEP, MAX_LAG = 6.0, 3.0, 2.0  # seconds
LIMIT = 0.12  # seconds of allowed offset


def _decode(path: Path) -> np.ndarray:
    cmd = ["ffmpeg", "-v", "error", "-i", str(path), "-vn", "-ac", "1", "-ar", str(RATE),
           "-f", "s16le", "-"]  # fmt: skip
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout  # noqa: S603, S607
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0


def _envelope(x: np.ndarray) -> np.ndarray:
    n = len(x) // HOP
    frames = x[: n * HOP].reshape(n, HOP)
    return np.log1p(100 * np.sqrt((frames**2).mean(axis=1)))


def _probe(path: Path) -> tuple[float, float]:
    """(duration, frame duration) of the video stream."""
    cmd = ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
           "stream=duration,r_frame_rate", "-of", "json", str(path)]  # fmt: skip
    out = subprocess.run(cmd, capture_output=True, text=True).stdout  # noqa: S603, S607
    st = json.loads(out)["streams"][0]
    num, den = (int(x) for x in st["r_frame_rate"].split("/"))
    return float(st["duration"]), den / num


def verify(final: Path, parts: list[Path], plan_dir: Path, names: list[str]) -> list:
    """Return a list of problems (empty = in sync). Prints a short report."""
    problems: list[str] = []
    offsets, t = [], 0.0
    expected: list[tuple[float, Path]] = []
    for name, part in zip(names, parts, strict=True):
        plan_file = plan_dir / f"{name}.jsonl"
        if not plan_file.exists():
            problems.append(f"{name}: no plan recorded – cannot verify")
            return problems
        entries = [json.loads(line) for line in plan_file.read_text(encoding="utf-8").splitlines()]
        end = next((e["end"] for e in reversed(entries) if "end" in e), None)
        real, frame = _probe(part)
        if end is not None and abs(real - end) > frame * 1.5:  # ±1 frame (+ container rounding)
            problems.append(f"{name}: picture is {real - end:+.2f}s off the plan ({real:.2f}s)")
        offsets.append(t)
        expected += [(t + e["voice"], Path(e["audio"])) for e in entries if "voice" in e]
        t += real

    actual = _envelope(_decode(final))
    exp = np.zeros_like(actual)
    for start, audio in expected:
        env = _envelope(_decode(audio))
        i = round(start * FPS_ENV)
        j = min(len(exp), i + len(env))
        if i < len(exp):
            exp[i:j] = np.maximum(exp[i:j], env[: j - i])

    w, s, m = int(WINDOW * FPS_ENV), int(STEP * FPS_ENV), int(MAX_LAG * FPS_ENV)
    worst = 0.0
    part_problems, problems = problems, []
    bad: list[tuple[float, str]] = []
    for a in range(m, len(actual) - w - m, s):
        ref = exp[a : a + w]
        # skip windows with (almost) no planned speech: a sentence onset at the very edge of a
        # window (e.g. after a silent question card) can't be timed reliably and once showed
        # up as a false "0.3 s early"
        if ref.std() < 0.05 or (ref > 0.3).sum() < 1.5 * FPS_ENV:
            continue
        ref = ref - ref.mean()
        best, best_lag = -1.0, 0
        for lag in range(-m, m + 1):
            seg = actual[a + lag : a + lag + w]
            seg = seg - seg.mean()
            denom = np.linalg.norm(seg) * np.linalg.norm(ref)
            c = float(seg @ ref / denom) if denom else 0.0
            if c > best:
                best, best_lag = c, lag
        lag_s = best_lag / FPS_ENV
        when = a / FPS_ENV
        if best < 0.5:
            bad.append((when, "audio doesn't match the plan"))
        elif abs(lag_s) > LIMIT:
            side = "early" if lag_s < 0 else "late"
            bad.append((when, f"narration {abs(lag_s):.1f}s {side}"))
        worst = max(worst, abs(lag_s))
    # merge neighbouring windows with the same finding into one line: "4:59–10:58: …"
    for when, msg in bad:
        if problems and problems[-1][2] == msg and when - problems[-1][1] <= STEP + 0.01:
            problems[-1][1] = when
        else:
            problems.append([when, when, msg])
    problems = [
        f"{_mmss(a)}{'' if a == b else '–' + _mmss(b + WINDOW)}: {msg}" for a, b, msg in problems
    ] + part_problems
    if not problems:
        print(f"[✓] sync verified in the final file: narration within {worst * 1000:.0f} ms "
              f"of the plan, all {len(parts)} parts frame-exact")  # fmt: skip
    return problems


def _mmss(t: float) -> str:
    return f"{int(t // 60)}:{t % 60:04.1f}"
