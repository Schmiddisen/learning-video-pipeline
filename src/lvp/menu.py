"""Interactive render menu – no flags needed.

    uv run kk

Picks one or more videos (number, range "4-7", lecture "v2", or "a" for all) and a quality,
then renders them one after another with all CPU cores. Uses only the recorded narration in
voice_cache/ (LVP_VOICE_DRYRUN=1), so it never makes a paid API call.
"""

from __future__ import annotations

import ast
import os
import re
import sys
import time
from pathlib import Path

from lvp import build
from lvp.project import ROOT

QUALITIES = [
    ("4K, 60 fps  (final)", ["-q", "k", "--hevc"]),
    ("4K, 30 fps  (final, ~2x faster)", ["-q", "k", "--fps", "30", "--hevc"]),
    ("1080p, 60 fps", ["-q", "h", "--hevc"]),
    ("Preview 480p  (fast)", ["-q", "l"]),
]


def _title(doc: str) -> str:
    """'Video 2.1 – Title.  (source: slides 2–7)' → 'Video 2.1 – Title'."""
    first = re.split(r"\.?\s{2,}|\s+\(", doc.splitlines()[0])[0].strip()
    return first.rstrip(".")


def _videos() -> list[tuple[Path, str]]:
    found = []
    for f in sorted((ROOT / "videos").glob("v*/*.py")):
        if build.sections(f):
            doc = ast.get_docstring(ast.parse(f.read_text(encoding="utf-8"))) or f.stem
            found.append((f, _title(doc)))
    return found


def _output(f: Path, flags: list[str]) -> Path:
    q = flags[flags.index("-q") + 1]
    return ROOT / "build" / "videos" / f"{f.parent.name}_{f.stem}_{q}.mp4"


def _lecture(name: str) -> str:
    m = re.match(r"(?:Video|Part|Chapter|Lecture)?\s*(\d+)", name)
    return m[1] if m else ""


def _pick(raw: str, videos: list[tuple[Path, str]]) -> list[int]:
    """'a' = all, 'v2' = part 2, '4-7', '3,5', '12' → indices."""
    out: list[int] = []
    for tok in re.split(r"[,\s]+", raw.strip().lower()):
        if not tok:
            continue
        if tok in ("a", "alle", "all"):
            out += range(len(videos))
        elif tok.startswith("v") and tok[1:].isdigit():
            out += [i for i, (_, n) in enumerate(videos) if _lecture(n) == tok[1:]]
        elif re.fullmatch(r"\d+-\d+", tok):
            a, b = (int(x) for x in tok.split("-"))
            out += range(a - 1, b)
        elif tok.isdigit():
            out.append(int(tok) - 1)
        else:
            raise ValueError(tok)
    if not out or any(i < 0 or i >= len(videos) for i in out):
        raise ValueError(raw)
    return list(dict.fromkeys(out))


def _choose(title: str, options: list[str], default: int = 1) -> int:
    print(f"\n{title}")
    for i, opt in enumerate(options, 1):
        print(f"  {i}) {opt}")
    while True:
        raw = input(f"Choice [{default}]: ").strip() or str(default)
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return int(raw) - 1
        print("  Please enter a number from the list.")


QUALITY_KEYS = {"4k60": 0, "4k30": 1, "1080p": 2, "480p": 3}


def main(argv: list[str] | None = None) -> int:
    """Interactive menu; with --quality it runs without questions (the study player's
    'Render on this PC' button uses that)."""
    import argparse

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Render final videos (cached narration only).")
    ap.add_argument("--quality", choices=list(QUALITY_KEYS), help="run without questions")
    ap.add_argument("--videos", default="a", help="12, 4-7, v2, 4,6 or a (default: all)")
    ap.add_argument("--redo", action="store_true", help="also render videos that already exist")
    args = ap.parse_args(sys.argv[1:] if argv is None else argv)
    videos = _videos()
    if not videos:
        print("No videos found (videos/vNN_name/name.py).")
        return 1
    q = (
        QUALITY_KEYS[args.quality]
        if args.quality
        else _choose("Quality?", [name for name, _ in QUALITIES])
    )
    flags = QUALITIES[q][1]
    if args.quality:
        chosen = _pick(args.videos, videos)
    else:
        print("\nWhich videos?  (✓ = already rendered in this quality)")
        last = ""
        for i, (f, name) in enumerate(videos, 1):
            if _lecture(name) != last:
                last = _lecture(name)
                print(f"  -- Part {last} --")
            mark = "✓" if _output(f, flags).exists() else " "
            print(f"  {mark} {i:2d}) {name}")
        print("  Enter: number (12), range (4-7), part (v2), several (4,6) or a = all")
        while True:
            try:
                chosen = _pick(input(f"Choice [{len(videos)}]: ") or str(len(videos)), videos)
                break
            except ValueError:
                print("  Not recognised – e.g. 12, 4-7, v2, 4,6 or a.")
    # rendered and still current: the output is newer than its scene file (a pulled change makes
    # the scene file newer, so that video is rendered again)
    done = [
        i
        for i in chosen
        if _output(videos[i][0], flags).exists()
        and _output(videos[i][0], flags).stat().st_mtime >= videos[i][0].stat().st_mtime
    ]
    if (args.quality and not args.redo) or (
        len(chosen) > 1
        and done
        and input("Skip already rendered ones? [Y/n]: ").strip().lower() in ("", "j", "y")
    ):
        chosen = [i for i in chosen if i not in done]

    if not chosen:
        print("All chosen videos are already rendered and current – nothing to do.")
        return 0
    print(f"{len(chosen)} Video(s): " + ", ".join(videos[i][1] for i in chosen), flush=True)
    os.environ.setdefault("LVP_VOICE", "real")
    os.environ["LVP_VOICE_DRYRUN"] = "1"  # cached narration only – never pays
    jobs = os.cpu_count() or 4  # long sections are split into chunks: every thread gets work
    results = []
    t_all = time.monotonic()
    for n, i in enumerate(chosen, 1):
        f, name = videos[i]
        args = [str(f.relative_to(ROOT)), *flags, "-j", str(jobs)]
        print(f"\n[{n}/{len(chosen)}] {name}\nRunning: lvp-build {' '.join(args)}\n")
        t0 = time.monotonic()
        try:
            rc = build.main(args)
        except Exception as e:  # noqa: BLE001 - keep going with the next video
            print(f"[!] {name}: {e}")
            rc = 1
        results.append((name, rc, time.monotonic() - t0))
    if len(results) > 1:
        print(f"\nDone after {(time.monotonic() - t_all) / 60:.0f} min:")
        for name, rc, dt in results:
            print(f"  {'✓' if rc == 0 else '✗'} {name}  ({dt / 60:.0f} min)")
    ok = all(rc == 0 for _, rc, _ in results)
    if ok and len(chosen) == 1 and os.name == "nt" and not args.quality:
        out = _output(videos[chosen[0]][0], flags)
        if out.exists() and input("\nOpen the video? [Y/n]: ").strip().lower() in ("", "j", "y"):
            os.startfile(out)  # noqa: S606 - opens the rendered file
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
