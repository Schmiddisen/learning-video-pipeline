"""lvp-player: package rendered videos for the interactive player (a Claude artifact).

Writes ``build/player/``: ``course.json`` with everything the player needs to know at any
moment – section, chapter, the narration line and its words, the text on screen, the
questions – plus one compact MP4 per video (below the artifact's file limit).

    uv run lvp-player                                  # every video that has a build
    uv run lvp-player videos/v02_2/x.py --quality l15  # one video, a specific build

The plugin's ``player`` skill publishes the result as an artifact.
"""

from __future__ import annotations

import argparse
import ast
import html
import json
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path

from lvp.project import BUILD, ROOT, VIDEOS, settings

OUT = BUILD / "player"
FORMAT = 1


def _probe(path: Path) -> float:
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0"]
    return float(subprocess.run([*cmd, str(path)], capture_output=True, text=True,  # noqa: S603
                                check=True).stdout.strip())  # fmt: skip


def _plan_dir(scene: Path, quality: str | None) -> Path | None:
    dirs = sorted(BUILD.glob(f"plan/{scene.stem}_*"), key=lambda d: d.stat().st_mtime)
    if quality:
        dirs = [d for d in dirs if d.name == f"{scene.stem}_{quality}"]
    return dirs[-1] if dirs else None


def _video_file(scene: Path, plan: Path) -> Path | None:
    letter = plan.name[len(scene.stem) + 1 :][:1]  # "l15" → "l"
    f = BUILD / "videos" / f"{scene.parent.name}_{scene.stem}_{letter}.mp4"
    return f if f.exists() else None


def _norm(text: str) -> str:
    """Lowercase ASCII letters and digits only ("Schlüssel, 128" → "schlussel128")."""
    flat = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", flat.lower())


def _section_lines(scene: Path) -> dict[str, list[str]]:
    """Section class → its spoken texts in file order (for builds made before plans had text)."""
    from lvp.dump import _string

    tree = ast.parse(scene.read_text(encoding="utf-8"))
    out: dict[str, list[str]] = {}
    for cls in tree.body:
        if not isinstance(cls, ast.ClassDef):
            continue
        found = []
        for n in ast.walk(cls):
            if not (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)):
                continue
            arg = n.args[0] if n.func.attr == "voiceover" and n.args else None
            arg = arg or next((k.value for k in n.keywords if k.arg == "say"), None)
            try:
                found.append((n.lineno, _string(arg))) if arg is not None else None
            except ValueError:
                continue
        out[cls.name] = [re.sub(r"<bookmark[^>]*/>", "", s).strip() for _, s in sorted(found)]
    return out


def _match(audio: str, candidates: list[str], start: int) -> int:
    """Index of the candidate whose text the audio file name was made from (fallback: next)."""
    slug = _norm(re.sub(r"-[0-9a-f]{8}.*$", "", Path(audio).name))[:24]
    for i in range(start, len(candidates)):
        if slug and _norm(candidates[i]).startswith(slug):
            return i
    return min(start, len(candidates) - 1)


def _words(text: str, audio: Path, t0: float) -> list[list]:
    from lvp.timing import speech_segments, word_boundaries

    if not audio.exists():
        return []
    try:
        wbs = word_boundaries(text, speech_segments(audio))
    except (subprocess.CalledProcessError, ValueError):
        return []
    return [[round(t0 + wb["audio_offset"] / 1e7, 2), wb["text"]] for wb in wbs]


def _estimated_quizzes(scene: Path, name: str, t0: float, end: float) -> list[dict]:
    """Question times for builds made before plans recorded them (from the helpers' timing)."""
    from lvp.dump import _items

    tree = ast.parse(scene.read_text(encoding="utf-8"))
    cls = next((c for c in tree.body if isinstance(c, ast.ClassDef) and c.name == name), None)
    if cls is None:
        return []
    items = [(k, s) for _, k, s in _items(cls) if k in ("PRETEST", "CHECK", "RECALL")]
    out: list[dict] = []
    t = t0 + end
    # helpers sit at the end of a section; walk backwards through their fixed timings
    for kind, s in reversed(items):
        if kind == "CHECK":
            q, _, a = s.partition("  →  ")
            t -= 0.5 + 3.5 + 0.5 + 5.0  # fade out, show answer, answer in, think
            out.append({"quiz": "check", "q": q, "a": a, "t": round(t, 2), "think": 5.0,
                        "answer_t": round(t + 5.5, 2), "estimated": True})  # fmt: skip
            t -= 0.5 + 0.6  # question in, deferred clear
        else:
            t -= 0.4 + 5.0
            out.append({"quiz": kind.lower(), "q": s, "t": round(t, 2), "think": 5.0,
                        "estimated": True})  # fmt: skip
            t -= 0.5
    return sorted(out, key=lambda q: q["t"])


def export_video(scene: Path, quality: str | None, max_mb: float) -> dict | None:
    from lvp.build import sections

    plan = _plan_dir(scene, quality)
    video = _video_file(scene, plan) if plan else None
    if not plan or not video:
        print(f"[–] {scene.relative_to(ROOT)}: no build yet (run lvp-build first)")
        return None
    texts = _section_lines(scene)
    tree = ast.parse(scene.read_text(encoding="utf-8"))
    title = (ast.get_docstring(tree) or scene.stem).splitlines()[0]
    vid = f"{scene.parent.name}_{scene.stem}"
    info: dict = {"id": vid, "title": title, "source": str(scene.relative_to(ROOT)),
                  "sections": [], "chapters": [], "lines": [], "screens": [],
                  "quizzes": []}  # fmt: skip
    t0 = 0.0
    for name in sections(scene):
        f = plan / f"{name}.jsonl"
        if not f.exists():
            print(f"[!] {vid}: {name} missing in {plan.name}")
            return None
        entries = [json.loads(x) for x in f.read_text(encoding="utf-8").splitlines() if x]
        end = next((e["end"] for e in reversed(entries) if "end" in e and "voice" not in e), 0.0)
        info["sections"].append({"name": name, "t": round(t0, 2), "end": round(t0 + end, 2)})
        cursor, quizzes = 0, []
        for e in entries:
            if "chapter" in e:
                info["chapters"].append({"t": round(t0 + e["t"], 2), "title": e["chapter"]})
            elif "voice" in e:
                audio = Path(e["audio"])
                text = e.get("text")
                if text is None and texts.get(name):
                    i = _match(audio.name, texts[name], cursor)
                    text, cursor = texts[name][i], i + 1
                start = t0 + e["voice"]
                stop = t0 + e["end"] if "end" in e else start + (
                    _probe(audio) if audio.exists() else 3.0)  # fmt: skip
                words = (
                    [[round(t0 + w[0], 2), w[1]] for w in e["words"]]
                    if "words" in e
                    else _words(text or "", audio, start)
                )
                line = {"t": round(start, 2), "end": round(stop, 2), "section": name}
                info["lines"].append(line | {"text": text or "", "words": words})
            elif "screen" in e:
                info["screens"].append({"t": round(t0 + e["t"], 2), "texts": e["screen"]})
            elif "quiz" in e:
                q = {k: v for k, v in e.items() if k not in ("t", "answer_t")}
                q["t"] = round(t0 + e["t"], 2)
                if "answer_t" in e:
                    q["answer_t"] = round(t0 + e["answer_t"], 2)
                quizzes.append(q | {"section": name})
        if not quizzes:  # older build: estimate from the scene file
            quizzes = [q | {"section": name} for q in _estimated_quizzes(scene, name, t0, end)]
        info["quizzes"] += quizzes
        t0 += end
    info["duration"] = round(_probe(video), 2)
    info["file"] = f"videos/{vid}.mp4"
    _encode(video, OUT / info["file"], info["duration"], max_mb)
    mb = (OUT / info["file"]).stat().st_size / 1e6
    print(f"[✓] {vid}: {len(info['lines'])} lines, {len(info['quizzes'])} questions, "
          f"{len(info['screens'])} screen states, {mb:.1f} MB")  # fmt: skip
    return info


def _encode(src: Path, dst: Path, duration: float, max_mb: float) -> None:
    """H.264 + AAC that starts playing at once (faststart) and stays below max_mb."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() and dst.stat().st_mtime > src.stat().st_mtime and \
            dst.stat().st_size < max_mb * 1e6:  # fmt: skip
        return
    base = ["ffmpeg", "-v", "error", "-y", "-i", str(src), "-map", "0:v", "-map", "0:a",
            "-map_metadata", "-1", "-map_chapters", "-1",
            "-c:a", "aac", "-b:a", "80k", "-ac", "1", "-movflags", "+faststart",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "slow"]  # fmt: skip
    subprocess.run([*base, "-crf", "27", "-tune", "animation", str(dst)], check=True)  # noqa: S603
    if dst.stat().st_size < max_mb * 1e6:
        return
    kbps = int(max_mb * 8e3 / duration * 0.92) - 80  # total budget minus audio
    subprocess.run([*base, "-b:v", f"{kbps}k", "-maxrate", f"{kbps * 2}k",  # noqa: S603
                    "-bufsize", f"{kbps * 4}k", str(dst)], check=True)  # fmt: skip


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("files", nargs="*", type=Path)
    ap.add_argument("--quality", help="plan suffix, e.g. l15 (default: newest build per video)")
    ap.add_argument("--max-mb", type=float, default=14.0, help="size limit per video file")
    ap.add_argument("--clean", action="store_true", help="remove build/player first")
    ap.add_argument("--title", help="course title shown in the player (default: lvp.toml)")
    args = ap.parse_args(argv)
    if not shutil.which("ffmpeg"):
        raise SystemExit("ffmpeg is needed (https://ffmpeg.org)")
    if args.clean and OUT.exists():
        shutil.rmtree(OUT)
    files = [f.resolve() for f in args.files] or sorted(VIDEOS.glob("v*/*.py"))
    videos = [v for f in files if (v := export_video(f, args.quality, args.max_mb))]
    s = settings()
    title = args.title or s.title
    course = {"format": FORMAT, "title": title, "language": s.language, "videos": videos}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "course.json").write_text(json.dumps(course, ensure_ascii=False), encoding="utf-8")
    page = (Path(__file__).with_name("player.html")).read_text(encoding="utf-8")
    (OUT / "index.html").write_text(page.replace("__COURSE_TITLE__", html.escape(title)),
                                    encoding="utf-8")  # fmt: skip
    total = sum(f.stat().st_size for f in OUT.rglob("*") if f.is_file()) / 1e6
    print(f"[✓] {OUT / 'course.json'}: {len(videos)} videos, {total:.0f} MB in total")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
