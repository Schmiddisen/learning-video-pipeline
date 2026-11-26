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

from lvp.project import BUILD, CARDS, ROOT, VIDEOS, settings

OUT = BUILD / "player"
FORMAT = 2
PAGE = Path(__file__).with_name("player")  # index.html, app.js, review.js, labs.js, lab-worker.js
PYODIDE = "0.27.7"
PYODIDE_FILES = ("pyodide.js", "pyodide.asm.js", "pyodide.asm.wasm", "python_stdlib.zip",
                 "pyodide-lock.json")  # fmt: skip


def _probe(path: Path) -> float:
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0"]
    return float(subprocess.run([*cmd, str(path)], capture_output=True, text=True,  # noqa: S603
                                check=True).stdout.strip())  # fmt: skip


def _plan_dir(scene: Path, quality: str | None) -> Path | None:
    own = re.compile(re.escape(scene.stem) + r"_[a-z]\d*")  # "x_l15", not "x_more_l15"
    dirs = [d for d in BUILD.glob(f"plan/{scene.stem}_*") if own.fullmatch(d.name)]
    dirs.sort(key=lambda d: d.stat().st_mtime)
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


def _match(audio: str, candidates: list[str], start: int, used: set[int] | None = None) -> int:
    """Index of the candidate whose text the audio file name was made from.

    Searches forward from ``start`` first, then anywhere unused; -1 if no line matches (the
    scene file changed after the build)."""
    used = used or set()
    slug = _norm(re.sub(r"-[0-9a-f]{8}.*$", "", Path(audio).name))[:24]
    order = [*range(start, len(candidates)), *range(0, min(start, len(candidates)))]
    for i in order:
        if slug and i not in used and _norm(candidates[i]).startswith(slug):
            return i
    return -1


def _from_slug(audio: str) -> str:
    """Readable start of a line from its audio file name (when the script has changed since)."""
    words = re.sub(r"-[0-9a-f]{8}.*$", "", Path(audio).name).split("-")
    return (" ".join(words).capitalize() + " …") if words and words[0] else ""


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
        cursor, quizzes, used = 0, [], set()
        for e in entries:
            if "chapter" in e:
                info["chapters"].append({"t": round(t0 + e["t"], 2), "title": e["chapter"]})
            elif "voice" in e:
                audio = Path(e["audio"])
                text = e.get("text")
                if text is None and texts.get(name):
                    i = _match(audio.name, texts[name], cursor, used)
                    if i >= 0:
                        text, cursor = texts[name][i], i + 1
                        used.add(i)
                    else:
                        text = _from_slug(audio.name)
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
            # questions a scene draws itself (not via the helpers) still appear in the plan's
            # on-screen text: take the moment each question's text first shows up
            screens = [(e["t"], " ".join(e["screen"])) for e in entries if "screen" in e]
            for q in quizzes:
                want = " ".join(q["q"].split())
                hit = next((ts for ts, text in screens if want and want in text), None)
                if hit is not None:
                    q["t"] = round(t0 + hit, 2)
                    q.pop("estimated", None)
                    if q.get("a"):
                        a = " ".join(q["a"].split())
                        shown = next((ts for ts, text in screens if ts > hit and a in text), None)
                        if shown is not None:
                            q["answer_t"] = round(t0 + shown, 2)
        info["quizzes"] += quizzes
        t0 += end
    info["duration"] = round(_probe(video), 2)
    info["file"] = f"videos/{vid}.mp4"
    _encode(video, OUT / info["file"], info["duration"], max_mb)
    mb = (OUT / info["file"]).stat().st_size / 1e6
    print(f"[✓] {vid}: {len(info['lines'])} lines, {len(info['quizzes'])} questions, "
          f"{len(info['screens'])} screen states, {mb:.1f} MB")  # fmt: skip
    return info


def _tokens(text: str) -> set[str]:
    return {w for w in re.findall(r"\w{4,}", text.lower())}


def cards_for(cards_dir: Path, videos: list[dict]) -> list[dict]:
    """Flashcards from cards/*.yaml, each linked to its video and the moment that teaches it.

    A tag ``v3.2`` means the second video of part 3 (folders ``v03_*``, also ``v03a_*``…).
    """
    import yaml

    by_part: dict[int, list[dict]] = {}
    for v in videos:
        m = re.match(r"v(\d+)", v["id"])
        if m:
            by_part.setdefault(int(m.group(1)), []).append(v)
    out: list[dict] = []
    for f in sorted(cards_dir.glob("*.yaml")):
        data = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        deck = data.get("deck", f.stem)
        for c in data.get("cards", []):
            card = {"id": str(c["id"]), "deck": deck, "tags": [str(t) for t in c.get("tags", [])]}
            for k in ("front", "back", "cloze", "extra"):
                if c.get(k):
                    card[k] = str(c[k]).strip()
            for tag in card["tags"]:
                m = re.fullmatch(r"v(\d+)\.(\d+)", tag)
                if m and int(m.group(2)) <= len(by_part.get(int(m.group(1)), [])):
                    video = by_part[int(m.group(1))][int(m.group(2)) - 1]
                    want = _tokens(" ".join(card.get(k, "") for k in ("front", "back", "cloze")))
                    best = max(video["lines"], key=lambda ln: len(want & _tokens(ln["text"])),
                               default=None)  # fmt: skip
                    card["video"] = video["id"]
                    if best and want & _tokens(best["text"]):
                        card["t"] = best["t"]
                    break
            out.append(card)
    return out


def labs_for(labs_dir: Path, videos: list[dict]) -> list[dict]:
    """Authored labs from labs/*.yaml (optional – the player can also design labs itself)."""
    import yaml

    out = []
    for f in sorted(labs_dir.glob("*.yaml")):
        for lab in (yaml.safe_load(f.read_text(encoding="utf-8")) or {}).get("labs", []):
            vid = str(lab.get("video", ""))
            m = re.fullmatch(r"v(\d+)\.(\d+)", vid)
            if m:  # "v2.2" → the second video of part 2
                part = [v for v in videos if re.match(rf"v0*{m.group(1)}\D", v["id"])]
                vid = part[int(m.group(2)) - 1]["id"] if int(m.group(2)) <= len(part) else vid
            out.append({**lab, "video": vid})
    return out


def _pyodide(dst: Path) -> bool:
    """Python for the labs: Pyodide's core files next to the page (downloaded once, cached)."""
    import tarfile
    import urllib.request

    cache = Path.home() / ".cache" / "lvp" / f"pyodide-{PYODIDE}"
    if not all((cache / n).exists() for n in PYODIDE_FILES):
        url = f"https://registry.npmjs.org/pyodide/-/pyodide-{PYODIDE}.tgz"
        print(f"[…] downloading Pyodide {PYODIDE} for the labs (once, ~14 MB)")
        cache.mkdir(parents=True, exist_ok=True)
        tgz = cache / "pyodide.tgz"
        try:
            urllib.request.urlretrieve(url, tgz)  # noqa: S310 - fixed https URL
            with tarfile.open(tgz) as t:
                for n in PYODIDE_FILES:
                    src = t.extractfile(f"package/{n}")
                    if src:
                        (cache / n).write_bytes(src.read())
        except OSError as e:
            print(f"[!] Pyodide download failed ({e}) – labs will offer JavaScript only")
            return False
        finally:
            tgz.unlink(missing_ok=True)
    dst.mkdir(parents=True, exist_ok=True)
    for n in PYODIDE_FILES:  # .zip is not a type artifact hosting serves: ship it as .wasm
        shutil.copy2(cache / n, dst / n.replace("python_stdlib.zip", "python_stdlib.wasm"))
    (dst / "python_stdlib.zip").unlink(missing_ok=True)
    return True


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
    ap.add_argument("--cards", type=Path, help="flashcard folder (default: cards/)")
    ap.add_argument("--labs", type=Path, help="authored labs folder (default: labs/)")
    ap.add_argument("--no-python", action="store_true", help="skip Pyodide (labs: JavaScript)")
    ap.add_argument("--only-data", action="store_true",
                    help="rewrite course.json and the page only (videos exported)")  # fmt: skip
    args = ap.parse_args(argv)
    if not shutil.which("ffmpeg"):
        raise SystemExit("ffmpeg is needed (https://ffmpeg.org)")
    if args.clean and OUT.exists():
        shutil.rmtree(OUT)
    files = [f.resolve() for f in args.files] or sorted(VIDEOS.glob("v*/*.py"))
    old = OUT / "course.json"
    if args.only_data and old.exists():
        videos = json.loads(old.read_text(encoding="utf-8"))["videos"]
    else:
        videos = [v for f in files if (v := export_video(f, args.quality, args.max_mb))]
    s = settings()
    title = args.title or s.title
    cards = cards_for(args.cards or CARDS, videos) if (args.cards or CARDS).exists() else []
    learner_md = ROOT / "learner.md"
    learner = learner_md.read_text(encoding="utf-8")[:4000] if learner_md.exists() else ""
    labs_dir = args.labs or ROOT / "labs"
    labs = labs_for(labs_dir, videos) if labs_dir.exists() else []
    python = not args.no_python and _pyodide(OUT / "pyodide")
    course = {"format": FORMAT, "title": title, "language": s.language, "videos": videos,
              "cards": cards, "labs": labs, "learner": learner, "python": python}  # fmt: skip
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "course.json").write_text(json.dumps(course, ensure_ascii=False), encoding="utf-8")
    for f in PAGE.iterdir():
        if f.suffix in (".html", ".js"):
            text = f.read_text(encoding="utf-8").replace("__COURSE_TITLE__", html.escape(title))
            (OUT / f.name).write_text(text, encoding="utf-8")
    total = sum(f.stat().st_size for f in OUT.rglob("*") if f.is_file()) / 1e6
    linked = sum("t" in c for c in cards)
    print(f"[✓] {OUT / 'course.json'}: {len(videos)} videos, {len(cards)} cards "
          f"({linked} linked to a moment), {total:.0f} MB in total")  # fmt: skip
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
