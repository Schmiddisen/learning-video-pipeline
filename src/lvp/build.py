"""Render every section scene of a video file and stitch them into one MP4.

Section scenes are classes named ``S<number><Name>`` and are rendered in file order.

    uv run --extra video lvp-build videos/v01_1/sicher.py            # draft, 480p, silent voice
    uv run --extra video lvp-build videos/v01_1/sicher.py -q h       # 1080p
    uv run --extra video lvp-build videos/v01_1/sicher.py --only S2Integritaet
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import time
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from pathlib import Path

from lvp.project import BUILD, ROOT
from lvp.verify import verify

OUT = BUILD / "videos"
AUDIO_RATE = 48_000
QUALITY_DIRS = {"l": "480p15", "m": "720p30", "h": "1080p60", "k": "2160p60"}


def _probe(path: Path, stream: str, field: str) -> str:
    cmd = ["ffprobe", "-v", "error", "-select_streams", stream,
           "-show_entries", f"stream={field}", "-of", "csv=p=0", str(path)]  # fmt: skip
    out = subprocess.run(cmd, capture_output=True, text=True)  # noqa: S603, S607
    return out.stdout.strip()


def _show_error(res: subprocess.CompletedProcess) -> None:
    """Last lines of a failed Manim run (the full traceback box is far too long)."""
    lines = [ln for ln in (res.stderr or res.stdout or "").splitlines() if ln.strip()]
    lines = [ln for ln in lines if "SoX" not in ln and "sox" not in ln]
    print("\n".join("      " + ln for ln in lines[-12:]))


def clean_svg_cache() -> int:
    """Delete empty/broken SVGs in Manim's text cache (left by interrupted renders).

    Manim reuses a cached SVG whenever the file exists, so one empty file breaks every render
    that shows this text ("ParseError: no element found") until it is deleted.
    """
    import xml.etree.ElementTree as ET  # noqa: N817

    removed = 0
    for sub in ("texts", "Tex"):
        for f in (ROOT / "media" / sub).glob("*.svg"):
            try:
                if ".tmp" in f.name or f.stem.endswith("_"):
                    raise ValueError("leftover temp file")
                ET.parse(f)  # noqa: S314 - Manim's own generated files
            except (ET.ParseError, ValueError, OSError):
                f.unlink(missing_ok=True)
                removed += 1
    return removed


def _last_error(res: subprocess.CompletedProcess) -> str:
    """One-line reason, e.g. 'PermissionError: ...' (full log goes to build/logs/)."""
    for ln in reversed((res.stderr or res.stdout or "").splitlines()):
        if re.match(r"\s*\w+(Error|Exception)\b", ln):
            return ln.strip()[:120]
    return f"exit code {res.returncode}"


def sections(scene_file: Path) -> list[str]:
    return re.findall(r"^class (S\d+\w*)\(", scene_file.read_text(encoding="utf-8"), re.M)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Render and stitch section scenes.")
    ap.add_argument("scene_file", type=Path)
    ap.add_argument("-q", "--quality", choices=list(QUALITY_DIRS), default="l")
    ap.add_argument("--only", nargs="*", help="render only these sections (still stitches all)")
    ap.add_argument("--verbose", action="store_true", help="show Manim's full log")
    ap.add_argument("--fps", type=int, help="override frame rate, e.g. 30 (≈2x faster than 60)")
    ap.add_argument(
        "-j", "--jobs", type=int, default=os.cpu_count() or 2,
        help="parallel Manim processes (default: all CPU threads)",
    )  # fmt: skip
    ap.add_argument(
        "--hevc", action="store_true",
        help="finish with an H.265 pass (much smaller file; GPU if available)",
    )  # fmt: skip
    ap.add_argument(
        "--no-chunks", dest="chunks", action="store_false",
        help="render each section in one process (no splitting into animation ranges)",
    )  # fmt: skip
    args = ap.parse_args(argv)

    scene_file = args.scene_file.resolve()
    names = sections(scene_file)
    if os.environ.get("LVP_VOICE", "silent").lower() != "silent":
        from lvp.narrate import unrecorded

        missing = unrecorded([scene_file])
        if missing:
            print(f"[!] {len(missing)} narration line(s) not recorded – they will be SILENT:")
            for _, line, text in missing[:8]:
                print(f"    line {line}: {text[:70]}")
    if not names:
        print(f"[!] no section scenes (class S0..., S1...) in {scene_file.name}")
        return 1
    todo = args.only or names
    env = dict(os.environ)
    env.setdefault("LVP_RUN_ID", time.strftime("%Y%m%d-%H%M%S"))  # shared spend cap across jobs
    if not args.verbose:
        env.setdefault("PYTHONWARNINGS", "ignore")  # pydub SyntaxWarnings etc.
    if n := clean_svg_cache():
        print(f"[✓] removed {n} broken file(s) from Manim's text cache")
    audit = ROOT / "build" / "sync_audit.log"
    audit.unlink(missing_ok=True)
    jobs = max(1, min(args.jobs, len(todo)))

    def manim(name: str, extra: list[str], env_extra: dict[str, str] | None = None):
        cmd = ["manim", f"-q{args.quality}", *extra, str(scene_file), name]
        if args.fps:
            cmd[2:2] = ["--fps", str(args.fps)]
        if not args.verbose:
            cmd[1:1] = ["-v", "ERROR", "--progress_bar", "none"]
        t0 = time.monotonic()
        res = subprocess.run(  # noqa: S603 - fixed command
            cmd, cwd=ROOT, env={**env, **(env_extra or {})},
            capture_output=not args.verbose, text=True,
        )  # fmt: skip
        return res, time.monotonic() - t0

    qdir = QUALITY_DIRS[args.quality]
    if args.fps:
        qdir = re.sub(r"p\d+$", f"p{args.fps}", qdir)
    media = ROOT / "media" / "videos" / scene_file.stem / qdir

    def n_partials(name: str) -> int:
        d = media / "partial_movie_files" / name
        return len(list(d.glob("*.mp4"))) if d.exists() else 0

    # 1) Count the animations of every section (dry run: no frames, a few seconds).
    counts_dir = ROOT / "build" / "counts"
    counts_dir.mkdir(parents=True, exist_ok=True)

    def count(name: str) -> int:
        f = counts_dir / f"{scene_file.stem}_{name}.txt"
        f.unlink(missing_ok=True)
        for _ in range(2):  # a count that fails just means: render this section unsplit
            manim(name, ["--dry_run"], {"LVP_COUNT_FILE": str(f)})
            if f.exists():
                return int(f.read_text())
        return 0

    with ThreadPoolExecutor(max_workers=jobs) as pool:
        counts = dict(zip(todo, pool.map(count, todo), strict=True))

    # 2) Split long sections into animation ranges so every core has work until the end
    #    (one long section used to leave 1-2 cores busy for most of the render).
    total = sum(counts.values())
    per = max(6, -(-total // (args.jobs * 3))) if args.chunks else 10**9
    chunks = {
        n: [(a, min(a + per, c) - 1) for a in range(0, c, per)] if c > per else []
        for n, c in counts.items()
    }
    n_chunks = sum(len(v) for v in chunks.values())
    print(
        f"{total} animations in {len(todo)} sections → {n_chunks} chunks, "
        f"{args.jobs} parallel jobs ...", flush=True,
    )  # fmt: skip

    reuse_dir = ROOT / "build" / "chunks" / f"{scene_file.stem}_{args.quality}{args.fps or ''}"
    shutil.rmtree(reuse_dir, ignore_errors=True)  # only this build's chunks may be reused
    reuse_dir.mkdir(parents=True)
    plan_dir = ROOT / "build" / "plan" / f"{scene_file.stem}_{args.quality}{args.fps or ''}"

    def final_env(n: str) -> dict[str, str]:
        (plan_dir / f"{n}.jsonl").unlink(missing_ok=True)  # a retry starts a fresh plan
        return {"LVP_PLAN": str(plan_dir)}

    t_start = time.monotonic()
    results: dict[str, subprocess.CompletedProcess] = {}
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        final_jobs: dict[str, Future] = {}
        left: dict[str, int] = {n: len(cs) for n, cs in chunks.items() if cs}
        before: dict[str, int] = {}
        chunk_jobs: dict[Future, str] = {}
        # largest pieces first, so the tail is short
        work = sorted(
            [(n, a, b) for n, cs in chunks.items() for a, b in cs]
            + [(n, 0, counts[n] - 1) for n in todo if not chunks[n]],
            key=lambda w: w[1] - w[2],
        )
        for n, a, b in work:
            if chunks[n]:
                hf = reuse_dir / f"{n}_{a:05}.json"
                env_c = {"LVP_CHUNK": "1", "LVP_HASH_FILE": str(hf)}
                fut = pool.submit(manim, n, ["-n", f"{a},{b}"], env_c)
                chunk_jobs[fut] = n
            else:
                final_jobs[n] = pool.submit(manim, n, [], final_env(n))
        for fut in as_completed(chunk_jobs):
            n = chunk_jobs[fut]
            res, _ = fut.result()
            if res.returncode:  # not fatal: the final pass renders whatever is missing
                reason = _last_error(res)
                print(f"  {n}: a chunk failed ({reason}) – the final pass fills the gap")
                log = ROOT / "build" / "logs" / f"{scene_file.stem}_{n}_chunk.log"
                log.parent.mkdir(parents=True, exist_ok=True)
                log.write_text((res.stdout or "") + (res.stderr or ""), encoding="utf-8")
                if args.verbose:
                    _show_error(res)
            left[n] -= 1
            if not left[n]:  # all chunks cached → final pass stitches and adds the narration
                before[n] = n_partials(n)
                reuse = {"LVP_REUSE": str(reuse_dir / f"{n}_*.json")}
                final_jobs[n] = pool.submit(manim, n, [], {**reuse, **final_env(n)})
        for n in todo:
            res, _ = final_jobs[n].result()
            results[n] = res
            if res.returncode:
                print(f"  {n}: failed – will retry on its own", flush=True)
                continue
            print(f"  {n}: done after {time.monotonic() - t_start:.0f} s", flush=True)
            redone = n_partials(n) - before.get(n, n_partials(n))
            if redone > max(3, counts[n] // 4):
                print(f"  [i] {n}: final pass re-rendered {redone} of {counts[n]} animations")

    # Retry failures one at a time (no parallel neighbours, so no shared-file contention).
    failed = None
    for n in [n for n in todo if results[n].returncode]:
        res, dt = manim(n, [], final_env(n))
        if res.returncode:
            print(f"  {n}: FAILED again")
            _show_error(res)
            failed = failed or res.returncode
        else:
            print(f"  {n}: retry ok ({dt:.0f} s)", flush=True)
    if failed:
        return failed
    if audit.exists():
        issues = audit.read_text(encoding="utf-8").splitlines()
        print(f"[!] sync audit: {len(issues)} issue(s) – text on screen vs. narration:")
        for line in issues:
            print("    " + line)
    else:
        print("[✓] sync audit: no late or unspoken text")

    parts = [media / f"{n}.mp4" for n in names]
    missing = [p.name for p in parts if not p.exists()]
    if missing:
        print(f"[!] not rendered yet: {missing}")
        return 1

    OUT.mkdir(parents=True, exist_ok=True)
    final = stitch(parts, OUT / f"{scene_file.parent.name}_{scene_file.stem}_{args.quality}.mp4")
    if not args.only:
        add_chapters(final, parts, plan_dir, names)
    if args.hevc:
        final = to_hevc(final)
    if not args.only:  # a partial re-render has no fresh plan for the other sections
        problems = verify(final, parts, plan_dir, names)
        if problems:
            print(f"[!] SYNC CHECK FAILED – {len(problems)} problem(s) in the final file:")
            for p in problems:
                print("    " + p)
    print(f"[✓] {final}  ({final.stat().st_size / 1e6:.0f} MB)")
    return 0


def stitch(parts: list[Path], final: Path) -> Path:
    """Join section videos sample-exactly.

    Audio is NOT taken from the section MP4s: every AAC stream starts with ~21 ms of encoder
    priming, and joining six of them pushed the narration 0.13 s late by the last section (found
    by verify). Instead: Manim's section WAVs (PCM), each trimmed/padded to its video's exact
    length in samples, joined, and encoded once. Video is joined by stream copy.
    """
    work = final.parent / "parts"
    work.mkdir(parents=True, exist_ok=True)
    wavs = []
    for part in parts:
        vdur = float(_probe(part, "v:0", "duration"))
        n = round(vdur * AUDIO_RATE)
        wav = work / f"{part.parent.name}_{part.stem}.wav"
        src = part.with_suffix(".wav")
        if src.exists():
            cmd = ["ffmpeg", "-v", "error", "-y", "-i", str(src)]
        else:
            cmd = ["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"anullsrc=r={AUDIO_RATE}"]
        cmd += ["-af", f"aresample={AUDIO_RATE},apad,atrim=end_sample={n}", "-ac", "1",
                "-c:a", "pcm_s16le", str(wav)]  # fmt: skip
        subprocess.run(cmd, check=True)  # noqa: S603, S607 - fixed command
        wavs.append(wav)

    def concat_list(files: list[Path], name: str) -> Path:
        listing = work / name
        listing.write_text("".join(f"file '{f.as_posix()}'\n" for f in files), encoding="utf-8")
        return listing

    video = work / f"{final.stem}_video.mp4"
    audio = work / f"{final.stem}_audio.wav"
    base = ["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i"]
    cmd_v = [*base, str(concat_list(parts, "video.txt")), "-an", "-c", "copy", str(video)]
    cmd_a = [*base, str(concat_list(wavs, "audio.txt")), "-c", "copy", str(audio)]
    subprocess.run(cmd_v, check=True)  # noqa: S603 - fixed command
    subprocess.run(cmd_a, check=True)  # noqa: S603 - fixed command
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", str(video), "-i", str(audio), "-map", "0:v",
           "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-movflags",
           "+faststart", str(final)]  # fmt: skip
    subprocess.run(cmd, check=True)  # noqa: S603, S607 - fixed command
    v, au = float(_probe(final, "v:0", "duration")), float(_probe(final, "a:0", "duration"))
    if abs(v - au) > 0.1:
        print(f"[!] audio/video length mismatch: video {v:.2f}s, audio {au:.2f}s")
    video.unlink(missing_ok=True)
    audio.unlink(missing_ok=True)
    return final


def add_chapters(final: Path, parts: list[Path], plan_dir: Path, names: list[str]) -> None:
    """Embed chapter markers (from chapter()/recall() calls in the plan) into the MP4, so every
    player can jump between topics. Idea from Chalkboard (github.com/nicglazkov/chalkboard)."""
    from lvp.i18n import t as _t

    marks, t = [(0.0, _t("intro"))], 0.0
    for name, part in zip(names, parts, strict=True):
        plan = plan_dir / f"{name}.jsonl"
        if plan.exists():
            for line in plan.read_text(encoding="utf-8").splitlines():
                e = json.loads(line)
                if "chapter" in e:
                    marks.append((t + e["t"], e["chapter"]))
        t += float(_probe(part, "v:0", "duration"))
    marks = [m for i, m in enumerate(marks) if i == 0 or m[0] - marks[i - 1][0] > 1.0]
    if len(marks) < 2:
        return
    meta = [";FFMETADATA1"]
    for i, (start, title) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else t
        clean = title.replace("=", "\\=").replace(";", "\\;").replace("#", "\\#")
        meta += ["[CHAPTER]", "TIMEBASE=1/1000", f"START={int(start * 1000)}",
                 f"END={int(end * 1000)}", f"title={clean}"]  # fmt: skip
    meta_file = final.with_suffix(".chapters.txt")
    meta_file.write_text("\n".join(meta) + "\n", encoding="utf-8")
    tmp = final.with_name(final.stem + "_ch.mp4")
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", str(final), "-i", str(meta_file), "-map", "0",
           "-map_metadata", "1", "-map_chapters", "1", "-c", "copy", "-movflags", "+faststart",
           str(tmp)]  # fmt: skip
    if subprocess.run(cmd).returncode == 0:  # noqa: S603, S607 - fixed command
        tmp.replace(final)
        print(f"[✓] {len(marks)} chapters embedded")
    meta_file.unlink(missing_ok=True)


def to_hevc(src: Path) -> Path:
    """Re-encode the finished video as H.265 (much smaller). GPU (NVENC) first, then CPU.

    Replaces the H.264 file only if the conversion worked; otherwise the H.264 file stays.
    """
    tmp = src.with_name(src.stem + "_hevc.mp4")
    encoders = [
        ("GPU (NVENC)", ["-c:v", "hevc_nvenc", "-preset", "p5", "-rc", "vbr", "-cq", "26",
                          "-b:v", "0"]),
        ("CPU (x265)", ["-c:v", "libx265", "-preset", "fast", "-crf", "24",
                         "-x265-params", "log-level=error"]),
    ]  # fmt: skip
    for name, opts in encoders:
        t0 = time.monotonic()
        print(f"H.265 pass on {name} ...", flush=True)
        cmd = ["ffmpeg", "-v", "error", "-y", "-i", str(src), *opts, "-pix_fmt", "yuv420p",
               "-tag:v", "hvc1", "-c:a", "copy", "-movflags", "+faststart", str(tmp)]  # fmt: skip
        res = subprocess.run(cmd, capture_output=True, text=True)  # noqa: S603, S607
        if res.returncode == 0 and tmp.exists() and tmp.stat().st_size > 0:
            before = src.stat().st_size
            tmp.replace(src)
            ratio = src.stat().st_size / before
            print(f"[✓] H.265: {ratio:.0%} of the H.264 size ({time.monotonic() - t0:.0f} s)")
            return src
        tmp.unlink(missing_ok=True)
        print(f"    {name} not available: {(res.stderr or '').strip().splitlines()[-1:]}")
    print("[!] H.265 pass failed – keeping the H.264 video")
    return src


if __name__ == "__main__":
    raise SystemExit(main())
