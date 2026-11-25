"""Fast tests that need no rendering (run: uv run pytest)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_syllables_english_and_german():
    from lvp.timing import syllables

    assert syllables("make") == 1
    assert syllables("encryption") == 3
    assert syllables("Schlüssel") == 2
    assert syllables("2026") >= 4


def test_init_creates_project(tmp_path):
    from lvp.init import main

    assert main([str(tmp_path / "course"), "--title", "Test", "--language", "de"]) == 0
    p = tmp_path / "course"
    for f in ("lvp.toml", "manim.cfg", "pyproject.toml", "learner.md", ".gitignore",
              "videos/v01_example/example.py"):  # fmt: skip
        assert (p / f).exists(), f
    assert 'language = "de"' in (p / "lvp.toml").read_text()


def test_settings_read_from_project(tmp_path):
    (tmp_path / "lvp.toml").write_text(
        '[course]\ntitle = "X"\nlanguage = "de"\n[voice]\nspeed = 1.3\n'
        '[pronunciation]\nSQL = "sequel"\n'
    )
    code = (
        "from lvp.project import settings; s = settings(); "
        "print(s.language, s.voice_speed, s.pronunciation['SQL'])"
    )
    out = subprocess.run([sys.executable, "-c", code], cwd=tmp_path, capture_output=True,
                         text=True, check=True).stdout  # fmt: skip
    assert out.split() == ["de", "1.3", "sequel"]


def test_dump_lists_narration_and_questions(tmp_path):
    from lvp.dump import dump

    f = tmp_path / "v01_x" / "x.py"
    f.parent.mkdir()
    f.write_text(
        '"""Video 1.1 – X"""\n'
        "class S0Hook:\n"
        "    def construct(self):\n"
        '        with self.voiceover("Hello " + \'<bookmark mark="a"/>world.\', hold="step"):\n'
        "            pass\n"
        '        self.pretest(["Why?"])\n'
        "class S1A:\n"
        "    def construct(self):\n"
        '        self.checkpoint("Q", "A")\n'
    )
    out = dump([f])
    assert "[SAY] Hello world." in out
    assert "[PRETEST] Why?" in out
    assert "[CHECK] Q  →  A" in out


def test_i18n_strings_complete():
    from lvp.i18n import STRINGS

    assert set(STRINGS["de"]) == set(STRINGS["en"])


def test_player_matches_audio_names_to_lines():
    from lvp.player import _match, _norm

    assert _norm("Schlüssel, 128 Bit!") == "schlussel128bit"
    lines = ["First we count people.", "Then the formula: P(A|B).", "Then the formula again."]
    audio = "then-the-formula-p-a-b-1a2b3c4d_adjusted.mp3"
    assert _match(audio, lines, 0) == 1
    assert _match("unknown-text-deadbeef.mp3", lines, 2) == -1  # script changed since
    assert _match(audio, lines, 0, used={1}) == -1  # a line is never used twice


def test_dump_keeps_question_order_within_a_list(tmp_path):
    from lvp.dump import dump

    f = tmp_path / "v.py"
    f.write_text('class S1A:\n    def construct(self):\n        self.recall(["Zeta?", "Alpha?"])\n')
    out = dump([f])
    assert out.index("Zeta?") < out.index("Alpha?")


def test_player_links_cards_and_labs_to_videos(tmp_path):
    from lvp.player import cards_for, labs_for

    odds = [{"t": 12.0, "text": "Odds multiply evidence"}, {"t": 40.0, "text": "A second test"}]
    videos = [
        {"id": "v02_1_intro", "duration": 100, "lines": [{"t": 5.0, "text": "Counting people"}]},
        {"id": "v02_2_odds", "duration": 100, "lines": odds},
    ]
    (tmp_path / "c.yaml").write_text(
        'deck: "D"\ncards:\n  - id: a\n    tags: [v2.2]\n    front: "Why do odds multiply?"\n'
        '    back: "Evidence multiplies them."\n',
        encoding="utf-8",
    )
    card = cards_for(tmp_path, videos)[0]
    assert card["video"] == "v02_2_odds" and card["t"] == 12.0
    (tmp_path / "l.yaml").write_text("labs:\n  - video: v2.1\n    title: T\n", encoding="utf-8")
    assert labs_for(tmp_path, videos)[0]["video"] == "v02_1_intro"
