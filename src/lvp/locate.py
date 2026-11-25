"""lvp-locate: which narration line is playing at a timestamp of a rendered video?

The viewer says "2.2 at 9:15 references the slide" – this turns that into the exact section
and source line, using the plan the last build wrote (build/plan/…).

    uv run lvp-locate videos/v02_2/one_time_pad.py 9:15          # newest build of that video
    uv run lvp-locate videos/v02_2/one_time_pad.py 9:15 --quality k60
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from lvp.project import BUILD


def _seconds(ts: str) -> float:
    parts = [float(p) for p in ts.split(":")]
    return sum(p * 60**i for i, p in enumerate(reversed(parts)))


def _plan_dir(scene: Path, quality: str | None) -> Path:
    dirs = sorted(BUILD.glob(f"plan/{scene.stem}_*"), key=lambda d: d.stat().st_mtime)
    if quality:
        dirs = [d for d in dirs if d.name == f"{scene.stem}_{quality}"]
    if not dirs:
        raise SystemExit(f"No build plan for {scene.name} – render it once with lvp-build.")
    return dirs[-1]


def locate(scene: Path, when: float, quality: str | None = None) -> dict:
    from manim_voiceover.helper import remove_bookmarks

    from lvp import voice
    from lvp.build import sections
    from lvp.narrate import voiceover_texts

    plan = _plan_dir(scene, quality)
    t0 = 0.0
    for name in sections(scene):
        f = plan / f"{name}.jsonl"
        entries = [json.loads(x) for x in f.read_text(encoding="utf-8").splitlines() if x]
        end = next((e["end"] for e in reversed(entries) if "end" in e), 0.0)
        if when < t0 + end:
            break
        t0 += end
    else:
        raise SystemExit(f"{when:.0f} s is past the end of the video ({t0:.0f} s).")
    local = when - t0
    voices = [e for e in entries if "voice" in e and e["voice"] <= local]
    chapters = [e["chapter"] for e in entries if "chapter" in e and e["t"] <= local]
    # audio file name → narration line: same hashing as the speech services
    real, silent = voice.OpenRouterTTSService(), voice.SilentService()
    names: dict[str, tuple[int, str]] = {}
    for line, text in voiceover_texts(scene):
        plain = remove_bookmarks(text)
        spoken = voice.apply_pronunciation(plain)
        for base in (
            real.get_audio_basename(
                {"input_text": spoken, "model": real.model, "voice": real.voice}
            ),
            silent.get_audio_basename({"input_text": plain, "service": "silent"}),
        ):
            names[base] = (line, plain)
    hit = None
    if voices:
        audio = Path(voices[-1]["audio"]).name
        hit = next((v for b, v in names.items() if audio.startswith(b)), None)
    return {
        "plan": str(plan),
        "section": name,
        "chapter": chapters[-1] if chapters else None,
        "section_time": round(local, 1),
        "narration_started": round(voices[-1]["voice"], 1) if voices else None,
        "line": hit[0] if hit else None,
        "text": hit[1] if hit else None,
    }


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("scene_file", type=Path)
    ap.add_argument("timestamp", help="mm:ss or h:mm:ss or seconds")
    ap.add_argument("--quality", help="plan suffix, e.g. l15, k60 (default: newest build)")
    args = ap.parse_args(argv)
    r = locate(args.scene_file, _seconds(args.timestamp), args.quality)
    print(f"{args.scene_file}  @ {args.timestamp}  (plan {Path(r['plan']).name})")
    print(f"  section  {r['section']}" + (f"  · chapter “{r['chapter']}”" if r["chapter"] else ""))
    print(f"  {r['section_time']} s into the section")
    if r["line"]:
        print(f"  narration since {r['narration_started']} s, line {r['line']}:")
        print(f"    {r['text']}")
    else:
        print("  (no narration playing – a pause, question card or animation)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
