"""lvp-init: create a new learning project.

uv run lvp-init my-topic --title "Bayes in practice" --language en
"""

from __future__ import annotations

import argparse
from pathlib import Path

LVP_TOML = """\
[course]
title = "{title}"
language = "{language}"   # narration and on-screen text
series = "{title} · Video {{n}}"

[video]
theme = "paper"           # paper | night | terminal

[voice]
provider = "openrouter"   # openrouter (Gemini TTS, needs OPENROUTER_API_KEY) | silent
model = "google/gemini-3.8-flash-tts"
voice = "Kore"
speed = 1.15              # applied locally, free to change
chars_per_second = 15.0

[budget]
max_usd_per_run = 0.50    # paid narration per command; voice_cache/FROZEN blocks all spending

[pronunciation]
# respellings for the voice only, e.g.  SQL = "sequel"   "e.g." = "for example"
"""

MANIM_CFG = """\
[CLI]
# keep every rendered animation: long sections exceed Manim's default of 100,
# and lvp-build's parallel chunks share this cache
max_files_cached = -1

[video_encoder.options]
# flat paper-style graphics look the same with veryfast; crf 20 keeps text edges crisp
crf = 20
preset = veryfast
"""

GITIGNORE = """\
build/
media/
__pycache__/
*.pyc
.venv/
voice_cache/*.tempo
voice_cache/*.dryrun*
voice_cache/.lvp-lock
voice_cache/*_adjusted*
# source material you are not allowed to publish:
material/**/*.mp4
material/**/*.pdf
"""

PYPROJECT = """\
[project]
name = "{slug}"
version = "0.1.0"
requires-python = ">=3.11,<3.14"
dependencies = ["lvp @ git+https://github.com/Schmiddisen/learning-video-pipeline"]

[project.optional-dependencies]
material = ["lvp[material] @ git+https://github.com/Schmiddisen/learning-video-pipeline"]
transcribe = ["lvp[transcribe] @ git+https://github.com/Schmiddisen/learning-video-pipeline"]

[tool.uv]
package = false
"""

LEARNER_MD = """\
# Learner profile

(Filled in by the `setup` skill – every other skill reads this first.)

- Goal: exam / project / curiosity
- Deadline:
- Prior knowledge (use for analogies):
- Depth: overview / working knowledge / exam-ready / expert
- Video length: 6–10 min
- Tone: concise, never condescending
- Question difficulty: application and transfer
- Language: {language}
"""

EXAMPLE_SCENE = '''\
"""Video 1.1 – Example: why we square the errors.  Delete me once you have real videos."""

from manim import DOWN, UP, FadeIn

from lvp.props import question
from lvp.style import ACCENT, LessonScene, label

SERIES = "{title} · Video 1.1"


class S0Hook(LessonScene):
    def construct(self) -> None:
        q = question("Why square the errors instead of just adding them?").move_to(UP * 1.0)
        self.opening(SERIES, q)
        with self.voiceover(
            'Two predictions miss by plus three and minus three. <bookmark mark="s"/>Their sum '
            "is zero, as if both were perfect.",
            hold="question",
        ):
            self.at("s", FadeIn(label("3 + (−3) = 0", size=40, color=ACCENT).move_to(DOWN)))
        self.pretest(["What would happen if we added absolute values instead?"])
'''


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Create a learning-video project.")
    ap.add_argument("path", type=Path)
    ap.add_argument("--title", default="My course")
    ap.add_argument("--language", default="en")
    args = ap.parse_args(argv)
    root: Path = args.path
    if (root / "lvp.toml").exists():
        print(f"[!] {root} already is a project (lvp.toml exists).")
        return 1
    for d in ("material/digest", "plan", "videos/v01_example", "cards", "exercises",
              "voice_cache", "tex_cache"):  # fmt: skip
        (root / d).mkdir(parents=True, exist_ok=True)
    (root / "lvp.toml").write_text(LVP_TOML.format(title=args.title, language=args.language))
    (root / "manim.cfg").write_text(MANIM_CFG)
    if not (root / "pyproject.toml").exists():
        slug = "".join(c if c.isalnum() else "-" for c in root.resolve().name.lower()) or "course"
        (root / "pyproject.toml").write_text(PYPROJECT.format(slug=slug))
    (root / ".gitignore").write_text(GITIGNORE)
    (root / "learner.md").write_text(LEARNER_MD.format(language=args.language))
    (root / "videos/v01_example/example.py").write_text(EXAMPLE_SCENE.format(title=args.title))
    for d in ("voice_cache", "tex_cache", "cards", "exercises", "plan"):
        (root / d / ".gitkeep").touch()
    print(f"[✓] project created in {root.resolve()}")
    print("    next: cd into it, `uv sync`, then in Claude Code run /lvp:setup")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
