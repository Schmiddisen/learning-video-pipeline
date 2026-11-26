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


def test_rwkv_checkpoint_conversion_without_torch(tmp_path, monkeypatch):
    """A .pth is a zip with a pickle + raw float32 storages; read it like torch.save writes it."""
    import collections
    import io
    import pickle
    import struct
    import types
    import zipfile

    from lvp import rwkv_weights

    torch = types.ModuleType("torch")
    utils = types.ModuleType("torch._utils")

    class FloatStorage:
        pass

    def _rebuild_tensor_v2(*a):
        return a

    FloatStorage.__module__, FloatStorage.__qualname__ = "torch", "FloatStorage"
    _rebuild_tensor_v2.__module__ = "torch._utils"
    _rebuild_tensor_v2.__qualname__ = "_rebuild_tensor_v2"
    torch.FloatStorage, utils._rebuild_tensor_v2 = FloatStorage, _rebuild_tensor_v2
    monkeypatch.setitem(sys.modules, "torch", torch)
    monkeypatch.setitem(sys.modules, "torch._utils", utils)

    class T:
        def __init__(self, key, offset, shape, stride):
            self.args = (key, offset, shape, stride)

        def __reduce__(self):
            key, offset, shape, stride = self.args
            return (_rebuild_tensor_v2, (("storage", FloatStorage, key, "cpu", 6), offset, shape,
                                         stride, False, collections.OrderedDict()))  # fmt: skip

    class P(pickle.Pickler):
        def persistent_id(self, obj):
            return obj if isinstance(obj, tuple) and obj and obj[0] == "storage" else None

    state = collections.OrderedDict(a=T("0", 0, (2, 2), (2, 1)), b=T("0", 4, (2,), (1,)))
    buf = io.BytesIO()
    P(buf, protocol=2).dump(state)
    pth = tmp_path / "m.pth"
    with zipfile.ZipFile(pth, "w") as z:
        z.writestr("m/data.pkl", buf.getvalue())
        z.writestr("m/data/0", struct.pack("<6f", 1, 2, 3, 4, 5, 6))
    manifest, blob = rwkv_weights._read_pth(pth)
    got = [(m["name"], m["shape"], m["offset"]) for m in manifest]
    assert got == [("a", [2, 2], 0), ("b", [2], 4)]
    assert struct.unpack("<6f", blob) == (1, 2, 3, 4, 5, 6)


def test_rwkv_js_is_valid_and_exports():
    import shutil

    import pytest

    node = shutil.which("node")
    if not node:
        pytest.skip("node not installed")
    js = ROOT / "src/lvp/player/rwkv.js"
    code = f"console.log(Object.keys(require({str(js)!r})).join(','))"
    out = subprocess.run([node, "-e", code], capture_output=True, text=True, check=True)
    assert out.stdout.strip() == "Model,Process,Memory,hashCode"


def test_library_merge_keeps_other_courses(tmp_path, monkeypatch):
    import json

    from lvp import player

    monkeypatch.setattr(player, "OUT", tmp_path)
    src = tmp_path / "old.json"
    src.write_text(json.dumps({"format": 1, "courses": [
        {"slug": "", "title": "Krypto", "path": ""},
        {"slug": "paper", "title": "Old title", "path": "courses/paper/"}]}))  # fmt: skip
    player._merge_library(src, "paper", "Attention", "en")
    player._merge_library(tmp_path / "library.json", "bayes", "Bayes", "en")
    lib = json.loads((tmp_path / "library.json").read_text())
    assert [(c["slug"], c["title"]) for c in lib["courses"]] == [
        ("", "Krypto"), ("paper", "Attention"), ("bayes", "Bayes")]  # fmt: skip
    assert lib["courses"][1]["path"] == "courses/paper/"


def test_rwkv_js_matches_fork_test_vectors():
    """SM118 in rwkv.js against the RWKV Anki fork's published vectors. Needs a checkout of
    JSchoreels/anki (its weights are not ours to ship): set LVP_RWKV_FORK=/path/to/anki."""
    import os
    import shutil

    import pytest

    fork, node = os.environ.get("LVP_RWKV_FORK"), shutil.which("node")
    if not fork or not node:
        pytest.skip("set LVP_RWKV_FORK to a checkout of JSchoreels/anki (and install node)")
    script = ROOT / "tests" / "rwkv_vectors.js"
    out = subprocess.run([node, str(script), fork, "sm118"], capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    assert float(out.stdout.split()[-1]) < 1e-5, out.stdout
