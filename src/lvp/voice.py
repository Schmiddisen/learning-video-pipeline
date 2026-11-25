"""Narration for Manim scenes.

Two modes, chosen with the ``LVP_VOICE`` environment variable:

* ``silent`` (default): free. Generates silence timed from the text length so animations
  can be drafted and reviewed without spending money.
* ``real``: the TTS provider from ``lvp.toml`` (default: Gemini TTS via OpenRouter, voice
  "Kore"; key in OPENROUTER_API_KEY). Costs money - only for an approved script.

Generated narration is cached in ``voice_cache/`` (committed to git), so a line that
hasn't changed is never paid for twice.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import time
import urllib.error
import urllib.request
import wave
from pathlib import Path

import manim_voiceover.services.base as _vo_base
from manim import logger
from manim_voiceover.helper import remove_bookmarks
from manim_voiceover.services.base import SpeechService, initialize_speech_service

from lvp.locks import file_lock
from lvp.project import VOICE_CACHE, settings
from lvp.timing import silent_plan, speech_segments, word_boundaries

OPENROUTER_URL = "https://openrouter.ai/api/v1/audio/speech"
_S = settings()
DEFAULT_MODEL = _S.tts_model  # lvp.toml [voice] model
DEFAULT_VOICE = _S.tts_voice  # lvp.toml [voice] voice
SAMPLE_RATE = 24_000  # Gemini TTS returns 24 kHz mono 16-bit PCM

# Speaking rate at speed 1.0, for silent drafts and cost estimates.
CHARS_PER_SECOND = _S.chars_per_second

# Playback speed for narration (1.0 = as generated). Applied locally with ffmpeg, so changing
# it is free - the cached recordings are reused.
SPEED = _S.voice_speed

# Respellings so the voice pronounces technical terms correctly ([pronunciation] in lvp.toml).
# Subtitles and on-screen text keep the real spelling; only the text sent to the TTS changes.
PRONUNCIATION: dict[str, str] = dict(_S.pronunciation)


def apply_pronunciation(text: str) -> str:
    for word, spoken in sorted(PRONUNCIATION.items(), key=lambda kv: -len(kv[0])):
        text = re.sub(rf"\b{re.escape(word)}\b", spoken, text)
    return text


def _write_wav(path: Path, pcm: bytes) -> None:
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(pcm)


def _to_mp3(wav: Path, mp3: Path) -> None:
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", str(wav), "-ac", "1", "-b:a", "64k", str(mp3)]
    subprocess.run(cmd, check=True)  # noqa: S603, S607 - fixed args, ffmpeg from PATH


LOCK = VOICE_CACHE / ".lvp-lock"


def _ffmpeg_tempo(input_path: str, output_path: str, tempo: float) -> None:
    """Pitch-preserving speed change (replaces manim-voiceover's SoX dependency).

    Parallel render processes share these files, and manim-voiceover would rewrite each one on
    every render while other processes read it. So: create once per tempo, under a lock.
    """
    out, stamp = Path(output_path), Path(output_path + ".tempo")
    with file_lock(LOCK):
        if (
            out.exists()
            and out.stat().st_size
            and stamp.exists()
            and stamp.read_text() == str(tempo)
        ):
            return
        cmd = ["ffmpeg", "-v", "error", "-y", "-i", input_path, "-filter:a", f"atempo={tempo}"]
        subprocess.run([*cmd, output_path], check=True)  # noqa: S603, S607 - fixed args
        stamp.write_text(str(tempo))


_vo_base.adjust_speed = _ffmpeg_tempo

# manim-voiceover appends every line to cache.json and scans it for cached results. Parallel
# processes corrupt it (JSONDecodeError), and we never need it: recordings are found by their
# hashed file name in generate_from_text below.
_vo_base.append_voiceover_cache_entry = lambda *a, **k: None
SpeechService.get_cached_result = lambda self, *a, **k: None


def _silent_result(service, text: str, input_data: dict, cache_dir: Path, name: str) -> dict:
    """Silent placeholder audio with estimated word timings (used for drafts and dry runs)."""
    input_text = remove_bookmarks(text)
    duration, segs = silent_plan(input_text)
    with file_lock(LOCK):  # shared by parallel processes: write once, never while read
        if not (cache_dir / name).exists():
            _write_wav(cache_dir / name, b"\x00\x00" * int(duration * SAMPLE_RATE))
    return {
        "input_text": text,
        "input_data": input_data,
        "original_audio": name,
        "word_boundaries": word_boundaries(input_text, segs),
    }


def _unpaid(service, text, input_data, cache_dir: Path, base: str, why: str) -> dict:
    """A line that can't be recorded (no credit, frozen, cap): render it silent instead of
    failing the whole video. lvp-narrate (LVP_STRICT_PAY) still reports these as failures."""
    logger.warning(f"Narration not recorded ({why}) – silent placeholder for this line")
    return _silent_result(service, text, input_data, cache_dir, f"{base}.dryrun.wav")


# --- spending safety -------------------------------------------------------------------------
USD_PER_MINUTE = 0.025  # measured: 7 min of narration ≈ $0.16 key usage (conservative)
MAX_USD = _S.max_usd_per_run  # per command; lvp.toml [budget] or LVP_MAX_USD
LEDGER = VOICE_CACHE / "ledger.jsonl"
FROZEN = VOICE_CACHE / "FROZEN"
_spent_estimate = 0.0
_no_credit = ""  # set once paying failed: the rest of the run stays silent


def _check_budget(chars: int) -> float:
    if FROZEN.exists():
        raise RuntimeError(
            f"Paid narration is frozen ({FROZEN} exists). Remove it to allow spending."
        )
    est = chars / CHARS_PER_SECOND / 60 * USD_PER_MINUTE
    run = os.environ.get("LVP_RUN_ID")
    spent = _spent_estimate
    if run and LEDGER.exists():  # parallel render jobs share one cap per lvp-build run
        spent = sum(
            json.loads(line).get("est_usd", 0)
            for line in LEDGER.read_text(encoding="utf-8").splitlines()
            if line.strip() and json.loads(line).get("run") == run
        )
    if spent + est > MAX_USD:
        raise RuntimeError(
            f"Spend cap reached: ~${spent + est:.3f} > LVP_MAX_USD={MAX_USD}. "
            "Ask the user, then raise LVP_MAX_USD for this run."
        )
    return est


def _log_spend(base: str, chars: int, seconds: float, gen_id: str = "") -> None:
    global _spent_estimate
    usd = seconds / 60 * USD_PER_MINUTE
    _spent_estimate += usd
    entry = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "file": base, "chars": chars,
             "seconds": round(seconds, 2), "est_usd": round(usd, 4), "gen_id": gen_id,
             "run": os.environ.get("LVP_RUN_ID", "")}  # fmt: skip
    with file_lock(LOCK), LEDGER.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


class SilentService(SpeechService):
    """Free placeholder: silence with estimated duration and word timings."""

    def __init__(self, **kwargs: object) -> None:
        kwargs.setdefault("global_speed", SPEED)
        initialize_speech_service(self, kwargs)

    def generate_from_text(self, text, cache_dir=None, path=None, **kwargs):
        cache_dir = Path(cache_dir or self.cache_dir)
        input_data = {"input_text": remove_bookmarks(text), "service": "silent"}
        name = self.get_audio_basename(input_data) + ".wav"
        return _silent_result(self, text, input_data, cache_dir, name)


class OpenRouterTTSService(SpeechService):
    """Paid narration through OpenRouter's /audio/speech endpoint."""

    def __init__(self, model: str = DEFAULT_MODEL, voice: str = DEFAULT_VOICE, **kwargs) -> None:
        self.model = model
        self.voice = voice
        kwargs.setdefault("cache_dir", str(VOICE_CACHE))
        kwargs.setdefault("global_speed", SPEED)
        initialize_speech_service(self, kwargs)

    def _result(self, text: str, input_data: dict, cache_dir: Path, base: str) -> dict:
        mp3 = cache_dir / f"{base}.mp3"
        return {
            "input_text": text,
            "input_data": input_data,
            "original_audio": mp3.name,
            "word_boundaries": word_boundaries(remove_bookmarks(text), speech_segments(mp3)),
        }

    def generate_from_text(self, text, cache_dir=None, path=None, **kwargs):
        cache_dir = Path(cache_dir or self.cache_dir)
        input_text = remove_bookmarks(text)
        spoken = apply_pronunciation(input_text)
        input_data = {"input_text": spoken, "model": self.model, "voice": self.voice}
        base = self.get_audio_basename(input_data)
        if (cache_dir / f"{base}.mp3").exists():  # file name = hash of text + model + voice
            return self._result(text, input_data, cache_dir, base)

        if os.environ.get("LVP_VOICE_DRYRUN"):
            # No API call: silent placeholder (not cached as .mp3, so a real run still records it).
            logger.warning(f"TTS (would pay): {len(spoken)} chars")
            return _silent_result(self, text, input_data, cache_dir, f"{base}.dryrun.wav")

        global _no_credit
        if _no_credit:
            return _unpaid(self, text, input_data, cache_dir, base, _no_credit)
        try:
            _check_budget(len(spoken))
        except RuntimeError as e:  # frozen or spend cap
            if os.environ.get("LVP_STRICT_PAY"):
                raise
            _no_credit = str(e)
            return _unpaid(self, text, input_data, cache_dir, base, _no_credit)
        key = os.environ.get("OPENROUTER_API_KEY", "proxy-injected")
        body = {"model": self.model, "input": spoken, "voice": self.voice, "response_format": "pcm"}
        req = urllib.request.Request(  # noqa: S310 - fixed https URL
            OPENROUTER_URL,
            data=json.dumps(body).encode(),
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        )
        logger.info(f"TTS (paid): {len(spoken)} chars -> {self.model}/{self.voice}")
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:  # noqa: S310
                pcm = resp.read()
                gen_id = resp.headers.get("X-Generation-Id", "")
        except urllib.error.HTTPError as e:
            if e.code != 402 or os.environ.get("LVP_STRICT_PAY"):
                raise
            _no_credit = "OpenRouter: insufficient credits (HTTP 402)"
            return _unpaid(self, text, input_data, cache_dir, base, _no_credit)

        wav = cache_dir / f"{base}.wav"
        _write_wav(wav, pcm)
        _to_mp3(wav, cache_dir / f"{base}.mp3")
        wav.unlink()
        _log_spend(base, len(spoken), len(pcm) / 2 / SAMPLE_RATE, gen_id)
        return self._result(text, input_data, cache_dir, base)


def key_usage() -> float:
    """Total spend of *this* API key (the account credits endpoint includes other keys)."""
    req = urllib.request.Request(  # noqa: S310 - fixed https URL
        "https://openrouter.ai/api/v1/key",
        headers={
            "Authorization": f"Bearer {os.environ.get('OPENROUTER_API_KEY', 'proxy-injected')}"
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310
        return float(json.load(resp)["data"]["usage"])


def actual_cost(gen_id: str) -> float | None:
    """Exact cost of one generation, as billed by OpenRouter (may lag a few seconds)."""
    req = urllib.request.Request(  # noqa: S310 - fixed https URL
        f"https://openrouter.ai/api/v1/generation?id={gen_id}",
        headers={
            "Authorization": f"Bearer {os.environ.get('OPENROUTER_API_KEY', 'proxy-injected')}"
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310
            return float(json.load(resp)["data"]["total_cost"])
    except Exception:  # noqa: BLE001 - best effort
        return None


def get_speech_service() -> SpeechService:
    """LVP_VOICE=silent (default, free drafts) or LVP_VOICE=real (the provider in lvp.toml)."""
    mode = os.environ.get("LVP_VOICE", "silent").lower()
    if mode in ("real", "gemini", "openrouter"):
        if _S.tts_provider == "silent":
            return SilentService()
        logger.warning("LVP_VOICE=real: real narration, uncached lines cost money.")
        return OpenRouterTTSService()
    if mode != "silent":
        raise ValueError(f"Unknown LVP_VOICE={mode!r} (use 'silent' or 'real')")
    return SilentService()
