"""Estimated word timings for narration, without any speech model.

Each narration block is its own recording, so sentence start/end are exact. Inside a block we
estimate when each word is spoken:

* the speech segments come from the audio itself (ffmpeg ``silencedetect``), so pauses after
  commas and full stops are respected and no word is placed inside a pause;
* words are spread over the *speech time* in proportion to their syllable count.

The result is in manim-voiceover's ``word_boundaries`` format, which makes
``<bookmark mark="x"/>`` + ``self.wait_until_bookmark("x")`` work.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

RES = 10_000_000  # manim-voiceover's AUDIO_OFFSET_RESOLUTION
_VOWELS = re.compile(r"[aeiouyäöü]+", re.I)
_WORD = re.compile(r"\S+")


def syllables(word: str) -> int:
    """Rough syllable count (vowel groups; English silent final e); digits count per digit."""
    digits = sum(c.isdigit() for c in word)
    groups = len(_VOWELS.findall(word))
    if groups > 1 and re.search(r"[^aeiouy]e$", word.lower()):  # "make", "phrase"
        groups -= 1
    return max(1, groups + digits)


def speech_segments(audio: Path, noise_db: int = -35, min_silence: float = 0.12) -> list[tuple]:
    """(start, end) of speech in seconds, from ffmpeg silencedetect."""
    cmd = [
        "ffmpeg", "-hide_banner", "-nostats", "-i", str(audio),
        "-af", f"silencedetect=noise={noise_db}dB:d={min_silence}", "-f", "null", "-",
    ]  # fmt: skip
    out = subprocess.run(cmd, capture_output=True, text=True, check=True).stderr  # noqa: S603
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", out)
    dur = int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3])
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", out)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", out)]
    silences = list(zip(starts, ends + [dur] * (len(starts) - len(ends)), strict=False))
    segs, t = [], 0.0
    for s, e in silences:
        if s > t + 0.02:
            segs.append((t, s))
        t = max(t, e)
    if dur > t + 0.02:
        segs.append((t, dur))
    return segs or [(0.0, dur)]


def _speech_time_to_real(x: float, segs: list[tuple]) -> float:
    """Map a position on the concatenated speech timeline to real time (pauses skipped)."""
    for s, e in segs:
        if x < e - s - 1e-6:
            return s + x
        x -= e - s
    return segs[-1][1]


def _anchors(words: list[str], cum: list[float], segs: list[tuple]) -> list[tuple[int, float]]:
    """Match each real pause to the nearest punctuation boundary -> (word index, speech pos)."""
    total_w, total_t = cum[-1], sum(e - s for s, e in segs)
    bounds = [i + 1 for i, w in enumerate(words[:-1]) if w[-1] in ",.;:!?–—"]
    anchors, pos, last = [(0, 0.0)], 0.0, 0
    for s, e in segs[:-1]:
        pos += e - s
        g = pos / total_t
        best = min(
            (b for b in bounds if b > last), key=lambda b: abs(cum[b] / total_w - g), default=None
        )
        if best is not None and abs(cum[best] / total_w - g) < 0.15:
            anchors.append((best, pos))
            last = best
    anchors.append((len(words), total_t))
    return anchors


def word_boundaries(text: str, segs: list[tuple]) -> list[dict]:
    """Estimated onset of every word of ``text`` within the speech segments."""
    matches = list(_WORD.finditer(text))
    if not matches:
        return []
    segs = [(s, e) for s, e in segs if e - s >= 0.1] or segs  # drop clicks/breaths
    words = [m.group() for m in matches]
    cum = [0.0]
    for w in words:
        cum.append(cum[-1] + syllables(w))
    anchors = _anchors(words, cum, segs)
    out = []
    for (i0, p0), (i1, p1) in zip(anchors, anchors[1:], strict=False):
        span_w = cum[i1] - cum[i0] or 1
        for i in range(i0, i1):
            pos = p0 + (p1 - p0) * (cum[i] - cum[i0]) / span_w
            out.append(
                {
                    "audio_offset": int(_speech_time_to_real(pos, segs) * RES),
                    "text_offset": matches[i].start(),
                    "word_length": len(words[i]),
                    "text": words[i],
                    "boundary_type": "Word",
                }
            )
    out.append(
        {
            "audio_offset": int(segs[-1][1] * RES),
            "text_offset": len(text),
            "word_length": 0,
            "text": "",
            "boundary_type": "Word",
        }
    )
    return out


def silent_plan(text: str, syl_per_sec: float = 4.6) -> tuple[float, list[tuple]]:
    """Duration and pseudo speech segments for a silent draft (pauses at punctuation)."""
    segs, t = [], 0.0
    for chunk in re.split(r"(?<=[,.;:!?–])\s+", text):
        n = sum(syllables(w) for w in chunk.split())
        d = max(0.4, n / syl_per_sec)
        segs.append((t, t + d))
        t += d + (0.45 if chunk.rstrip().endswith((".", "!", "?")) else 0.25)
    return segs[-1][1] + 0.1, segs
