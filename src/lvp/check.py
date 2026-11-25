"""Check videos without rendering a single frame (free, ~20 s per section, all in parallel).

    uv run lvp-check                         # all videos
    uv run lvp-check videos/v01_3/zwei_schluessel.py

Runs every section as a Manim dry run and reports layout problems (overlapping or cut-off text)
and sync problems (text that appears after it is spoken, titles never spoken).
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from lvp.build import ROOT, _last_error, sections

LOGS = {"layout": ROOT / "build" / "layout_audit.log", "sync": ROOT / "build" / "sync_audit.log"}


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Dry-run layout + sync check (no rendering).")
    ap.add_argument("files", nargs="*", type=Path)
    ap.add_argument("-j", "--jobs", type=int, default=os.cpu_count() or 4)
    args = ap.parse_args(argv)
    files = [f.resolve() for f in args.files] or sorted((ROOT / "videos").glob("v*/*.py"))
    jobs = [(f, s) for f in files for s in sections(f)]
    for log in LOGS.values():
        log.unlink(missing_ok=True)
    env = {**os.environ, "LVP_LAYOUT": "1", "PYTHONWARNINGS": "ignore"}
    env.setdefault("LVP_VOICE", "real")
    env["LVP_VOICE_DRYRUN"] = "1"  # recorded narration only – never pays

    def run(job):
        f, s = job
        cmd = ["manim", "-v", "ERROR", "--progress_bar", "none", "-ql", "--dry_run", str(f), s]
        return job, subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True)  # noqa: S603

    from lvp.narrate import unrecorded

    missing = unrecorded(files)
    if missing:
        print(f"[!] narration: {len(missing)} line(s) not recorded – they play as SILENCE:")
        for name, line, text in missing[:12]:
            print(f"    {name}:{line}  {text[:70]}")
    print(f"Checking {len(jobs)} sections ...", flush=True)
    failed = 0
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        for (f, s), res in pool.map(run, jobs):
            if res.returncode:
                failed += 1
                print(f"  {f.parent.name}/{s}: FAILED – {_last_error(res)}")
    total = 0
    for kind, log in LOGS.items():
        lines = sorted(set(log.read_text(encoding="utf-8").splitlines())) if log.exists() else []
        total += len(lines)
        print(f"\n[{'!' if lines else '✓'}] {kind}: {len(lines)} issue(s)")
        for line in lines:
            print("    " + line)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
