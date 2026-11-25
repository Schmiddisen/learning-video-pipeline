"""Record narration for a video without rendering any video.

Reads every ``self.voiceover("...")`` text from a scene file, checks which lines are not yet in
``voice_cache/`` and prints the expected cost. Only with ``--pay`` does it call the TTS API.

    uv run --extra video lvp-narrate videos/v01_3/zwei_schluessel.py          # list + cost, free
    uv run --extra video lvp-narrate videos/v01_3/zwei_schluessel.py --pay    # record missing lines
"""

from __future__ import annotations

import argparse
import ast
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from manim_voiceover.helper import remove_bookmarks


def _string(node: ast.expr) -> str:
    """Plain string literal, also joined with ``+`` (no names, no f-strings)."""
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return _string(node.left) + _string(node.right)
    value = ast.literal_eval(node)
    if not isinstance(value, str):
        raise ValueError(value)
    return value


def voiceover_texts(scene_file: Path) -> list[tuple[int, str]]:
    """(line, text) of every ``self.voiceover(<string>)`` call, in file order."""
    tree = ast.parse(scene_file.read_text(encoding="utf-8"))
    found = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
            continue
        # every helper that speaks: voiceover("…") and title_card(…, say="…")
        arg = None
        if node.func.attr == "voiceover" and node.args:
            arg = node.args[0]
        else:
            arg = next((k.value for k in node.keywords if k.arg == "say"), None)
        if arg is None:
            continue
        try:
            text = _string(arg)
        except ValueError:
            print(f"[!] line {node.lineno}: text from a variable – not checked")
            continue
        if text:
            found.append((node.lineno, text))
    return sorted(found)


def unrecorded(scene_files: list[Path]) -> list[tuple[str, int, str]]:
    """(file, line, text) of every spoken line that has no recording in voice_cache/."""
    from lvp import voice

    svc = voice.OpenRouterTTSService()
    todo = []
    for f in scene_files:
        for line, text in voiceover_texts(f):
            spoken = voice.apply_pronunciation(remove_bookmarks(text))
            data = {"input_text": spoken, "model": svc.model, "voice": svc.voice}
            if not (voice.VOICE_CACHE / f"{svc.get_audio_basename(data)}.mp3").exists():
                todo.append((f.name, line, text))
    return todo


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Record narration only (no video render).")
    ap.add_argument("scene_files", type=Path, nargs="+")
    ap.add_argument("--pay", action="store_true", help="actually call the paid TTS API")
    ap.add_argument("-j", "--jobs", type=int, default=4, help="parallel TTS requests")
    args = ap.parse_args(argv)

    os.environ.pop("LVP_VOICE_DRYRUN", None)
    os.environ["LVP_STRICT_PAY"] = "1"  # report unpaid lines instead of silencing them
    from lvp import voice  # after env setup

    svc = voice.OpenRouterTTSService()
    todo: list[tuple[str, int, str]] = []
    total = 0
    for f in args.scene_files:
        texts = voiceover_texts(f)
        total += len(texts)
        for line, text in texts:
            spoken = voice.apply_pronunciation(remove_bookmarks(text))
            data = {"input_text": spoken, "model": svc.model, "voice": svc.voice}
            if not (voice.VOICE_CACHE / f"{svc.get_audio_basename(data)}.mp3").exists():
                todo.append((f.name, line, text))

    chars = sum(len(voice.apply_pronunciation(remove_bookmarks(t))) for _, _, t in todo)
    est = chars / voice.CHARS_PER_SECOND / 60 * voice.USD_PER_MINUTE
    print(f"{total} lines, {len(todo)} not recorded yet ({chars} chars, ~${est:.3f}).")
    for name, line, text in todo:
        print(f"  {name}:{line}  {remove_bookmarks(text)[:90]}")
    if not todo or not args.pay:
        if todo:
            print("Dry run – nothing paid. Add --pay to record (ask the user first).")
        return 0

    os.environ.setdefault("LVP_RUN_ID", "narrate-" + time.strftime("%Y%m%d-%H%M%S"))
    before = voice.key_usage()

    def record(item):
        name, line, text = item
        try:
            svc.generate_from_text(text, cache_dir=str(voice.VOICE_CACHE))
            return f"  ok   {name}:{line}"
        except Exception as e:  # noqa: BLE001 - report and continue
            return f"  FAIL {name}:{line}  {e}"

    failed = 0
    with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
        for msg in pool.map(record, todo):
            print(msg, flush=True)
            failed += "FAIL" in msg
    time.sleep(5)  # usage endpoint lags a little
    print(f"Key usage: +${voice.key_usage() - before:.4f} (estimate was ~${est:.3f})")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
