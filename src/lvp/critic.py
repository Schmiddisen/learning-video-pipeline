"""lvp-critic: a vision model looks at a rendered video and lists visual bugs.

Idea from Code2Video (planner/coder/*critic*) and Chalkboard (visual QA on rendered frames):
the code-level checks (lvp-check) see bounding boxes, not pixels. A vision model sees what a
viewer sees: clipped glyphs, labels on top of lines, unreadable contrast, empty frames, clutter.

    uv run --extra video lvp-critic build/videos/v02_1_sicher_definieren_l.mp4 [--every 4]

Contact sheets (4x4 frames, timestamp in each tile) are sent to a cheap vision model via
OpenRouter (~$0.002 per sheet). The report lands in build/critic/<video>.md. Costs go to
voice_cache/ledger.jsonl like narration; LVP_CRITIC_MAX_USD (default 0.25) caps a run.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path

from lvp.locks import file_lock
from lvp.project import ROOT, settings

MODEL = os.environ.get("LVP_CRITIC_MODEL", settings().critic_model)
URL = "https://openrouter.ai/api/v1/chat/completions"
LEDGER = ROOT / "voice_cache" / "ledger.jsonl"
MAX_USD = float(os.environ.get("LVP_CRITIC_MAX_USD", "0.25"))

PROMPT = """You review still frames of an explainer video (3Blue1Brown style).
Each tile shows its timestamp top-left in red – that stamp is NOT part of the video.
Report only real problems a viewer would see:
- text overlapping text, lines, arrows or shapes (letters touching or crossing something)
- text or objects cut off at the frame border
- unreadable text (too small, too pale, poor contrast)
- wrong or broken characters (boxes instead of letters, broken formulas)
- arrows pointing into nothing or at the wrong object
- unbalanced layout (everything crammed into one corner, heavy clutter)
Ignore: transitions (half faded objects), deliberately empty tiles at the end, the small grey
series line top-left. The on-screen language is {language}; judge spelling in that language.
Write "problem" and "fix" in English.
Answer ONLY with JSON: {{"issues": [{{"t": "MM:SS", "severity": "high|medium|low",
"problem": "...", "fix": "..."}}]}} – an empty list if everything is fine."""


def _sheets(video: Path, every: float, out: Path) -> list[Path]:
    vf = (
        f"fps=1/{every},scale=480:270,"
        "drawtext=text='%{pts\\:hms}':x=4:y=4:fontsize=16:fontcolor=red,tile=4x4"
    )
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", str(video), "-vf", vf, str(out / "s_%02d.png")]
    subprocess.run(cmd, check=True)  # noqa: S603, S607
    return sorted(out.glob("s_*.png"))


def _ask(png: Path, offset: str) -> tuple[list, float]:
    img = base64.b64encode(png.read_bytes()).decode()
    body = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": PROMPT.format(language=settings().language)
                        + f"\nThis sheet starts at {offset}.",
                    },
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img}"}},
                ],
            }
        ],
        "response_format": {"type": "json_object"},
        "reasoning": {"effort": "minimal", "exclude": True},  # thinking tokens cost 30x
        "max_tokens": 1200,
        "usage": {"include": True},
    }
    key = os.environ.get("OPENROUTER_API_KEY", "proxy-injected")
    req = urllib.request.Request(  # noqa: S310 - fixed https URL
        URL,
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=180) as resp:  # noqa: S310
        data = json.loads(resp.read())
    cost = float(data.get("usage", {}).get("cost", 0) or 0)
    text = data["choices"][0]["message"]["content"].strip().removeprefix("```json").strip("`")
    try:
        return json.loads(text).get("issues", []), cost
    except json.JSONDecodeError:
        return [{"t": offset, "severity": "low", "problem": f"unparsable: {text[:200]}"}], cost


def critique(video: Path, every: float = 4.0) -> Path:
    if (ROOT / "voice_cache" / "FROZEN").exists():
        raise SystemExit("Spending is frozen (voice_cache/FROZEN).")
    report = ROOT / "build" / "critic" / f"{video.stem}.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    spent, rows = 0.0, []
    with tempfile.TemporaryDirectory() as tmp:
        sheets = _sheets(video, every, Path(tmp))
        for i, png in enumerate(sheets):
            if spent >= MAX_USD:
                rows.append(("--", "high", f"stopped: LVP_CRITIC_MAX_USD={MAX_USD} reached", ""))
                break
            start = i * 16 * every
            offset = f"{int(start // 60):02d}:{int(start % 60):02d}"
            for attempt in range(3):  # transient network/provider errors: retry, then skip
                try:
                    issues, cost = _ask(png, offset)
                    break
                except Exception as e:  # noqa: BLE001
                    issues, cost = [{"t": offset, "severity": "low", "problem": f"skipped: {e}"}], 0
                    time.sleep(2 * (attempt + 1))
            spent += cost
            for it in issues:
                rows.append((it.get("t", "?"), it.get("severity", "?"), it.get("problem", ""),
                             it.get("fix", "")))  # fmt: skip
    with file_lock(LEDGER.with_suffix(".lock")), LEDGER.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "kind": "critic",
                            "video": video.name, "usd": round(spent, 5)}) + "\n")  # fmt: skip
    order = {"high": 0, "medium": 1, "low": 2}
    rows.sort(key=lambda r: (order.get(r[1], 3), r[0]))
    lines = [f"# Visual critic – {video.name}", "", f"Model {MODEL}, cost ${spent:.4f}", ""]
    lines += ["| t | severity | problem | fix |", "|---|---|---|---|"]
    lines += [f"| {t} | {s} | {p} | {fx} |" for t, s, p, fx in rows] or ["(no issues)"]
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    high = sum(1 for r in rows if r[1] == "high")
    print(f"[critic] {video.name}: {len(rows)} issue(s), {high} high, ${spent:.4f} → {report}")
    return report


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("videos", nargs="+", type=Path)
    ap.add_argument("--every", type=float, default=4.0, help="seconds between frames")
    args = ap.parse_args(argv)
    for v in args.videos:
        critique(v, args.every)


if __name__ == "__main__":
    main()
