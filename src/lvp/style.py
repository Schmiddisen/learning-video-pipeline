"""House style for learning videos: themes, palette roles and building blocks.

The theme comes from ``lvp.toml`` ([video] theme) or ``LVP_THEME``: ``paper`` (default, warm
printed textbook), ``night`` (dark 3Blue1Brown-like) or ``terminal`` (phosphor HUD). Scenes use
the role names exported here (PRIMARY, POSITIVE, NEGATIVE, ACCENT, SPECIAL, TEAL), so the same
scene renders in every theme. Domain props (people, keys, channels …) live in ``lvp.packs``.
"""

from __future__ import annotations

import json
import os
import re
import shutil
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from manim import (
    DL,
    DOWN,
    DR,
    LEFT,
    RIGHT,
    UL,
    UP,
    UR,
    Circle,
    Create,
    Dot,
    FadeIn,
    FadeOut,
    Group,
    Line,
    MathTex,
    NumberPlane,
    Rectangle,
    RoundedRectangle,
    Square,
    Text,
    VGroup,
    Wait,
    Write,
    config,
)
from manim_voiceover import VoiceoverScene

from lvp.i18n import t
from lvp.locks import file_lock
from lvp.project import settings as _settings
from lvp.voice import get_speech_service


@dataclass(frozen=True)
class Theme:
    name: str
    bg: str
    fg: str
    muted: str
    primary: str  # blue: the main actor / the thing being explained
    positive: str  # green: correct, safe, the good path
    negative: str  # red: wrong, attack, failure
    accent: str  # amber: highlights, secrets, the key idea
    special: str  # purple: a second family of objects
    font: str
    shape: str  # "ring" | "disc" | "box"
    stroke: float = 6
    fill_opacity: float = 0.15
    teal: str = "#2B7A78"  # sixth colour


THEMES = {
    "night": Theme(
        name="night",
        bg="#0E1117",
        fg="#E8E6E3",
        muted="#7A8193",
        primary="#58C4DD",
        positive="#83C167",
        negative="#FC6255",
        accent="#F4D345",
        special="#C792EA",
        font="Inter",
        teal="#4FD1C5",
        shape="ring",
    ),
    "paper": Theme(
        name="paper",
        bg="#F3EDE2",
        fg="#1F2430",
        muted="#6E665A",
        primary="#1F5FA8",
        positive="#2E7D4F",
        negative="#C0392B",
        accent="#A86A00",
        special="#7B3F8C",
        font="IBM Plex Serif",
        shape="disc",
        stroke=4,
        fill_opacity=1.0,
    ),
    "terminal": Theme(
        name="terminal",
        bg="#04070A",
        fg="#C8FFD8",
        muted="#3E6B55",
        primary="#00E5FF",
        positive="#A6FF00",
        negative="#FF2E88",
        accent="#FFC400",
        special="#9D8CFF",
        font="IBM Plex Mono",
        teal="#00FFC8",
        shape="box",
        stroke=3,
        fill_opacity=0.06,
    ),
}

THEMES["nacht"], THEMES["papier"] = THEMES["night"], THEMES["paper"]  # German aliases
THEME = THEMES[(os.environ.get("LVP_THEME") or _settings().theme).lower()]

BG, FG, MUTED = THEME.bg, THEME.fg, THEME.muted
PRIMARY, POSITIVE, NEGATIVE = THEME.primary, THEME.positive, THEME.negative
ACCENT, SPECIAL, TEAL = THEME.accent, THEME.special, THEME.teal
FONT = THEME.font

config.background_color = BG
MathTex.set_default(color=FG)


from lvp.project import BUILD, FONTS_DIR, TEX_CACHE  # noqa: E402


def _register_fonts() -> None:
    """Bundled DejaVu fonts (fonts/) as fallback for glyphs IBM Plex lacks (⊕, ⇒, ε, ᵏ …).
    Without them Pango draws a box with the code point on PCs without a fallback font."""
    import manimpango

    for f in sorted(FONTS_DIR.glob("*.ttf")):
        manimpango.register_font(str(f))


_register_fonts()


def label(text: str, size: float = 32, color: str = FG, **kw) -> Text:
    from lvp.glyphs import MISSING_MONO, MISSING_SERIF

    kw.setdefault("font", FONT)
    mono = "Mono" in kw["font"]
    missing = MISSING_MONO if mono else MISSING_SERIF
    fallback = "DejaVu Sans Mono" if mono else "DejaVu Sans"
    odd = {c for c in text if ord(c) in missing}
    if odd:
        t2f = dict(kw.pop("t2f", {}))
        t2f.update({c: fallback for c in odd})
        kw["t2f"] = t2f
    t = Text(text, font_size=size, color=color, **kw)
    if t.width > config.frame_width - 1.2:  # safety net: never wider than the safe area
        t.scale_to_fit_width(config.frame_width - 1.2)
    return t


def _brackets(mob, color: str, arm: float = 0.18, buff: float = 0.08) -> VGroup:
    """Four corner brackets around a mobject (terminal look)."""
    corners = VGroup()
    for corner, dx, dy in ((UL, 1, -1), (UR, -1, -1), (DL, 1, 1), (DR, -1, 1)):
        p = mob.get_corner(corner) + (corner * buff)
        corners.add(
            Line(p, p + RIGHT * dx * arm, color=color, stroke_width=3),
            Line(p, p + UP * dy * arm, color=color, stroke_width=3),
        )
    return corners


# --- Characters ------------------------------------------------------------------------
class Person(VGroup):
    """Avatar with the person's initial and name; its shape depends on the theme."""

    def __init__(self, name: str, color: str, radius: float = 0.55, **kw) -> None:
        t = THEME
        if t.shape == "disc":
            shadow = Circle(radius=radius, stroke_width=0).set_fill(FG, 1).shift(DR * 0.06)
            body = Circle(radius=radius, color=FG, stroke_width=t.stroke).set_fill(color, 1)
            initial = label(name[0], size=radius * 72, color=BG, weight="BOLD")
            parts = [shadow, body, initial]
            name_t = label(name, size=26, color=FG, slant="ITALIC")
        elif t.shape == "box":
            body = Square(side_length=radius * 1.9, color=color, stroke_width=t.stroke)
            body.set_fill(color, t.fill_opacity)
            initial = label(name[0], size=radius * 66, color=color, weight="BOLD")
            parts = [body, initial, _brackets(body, color)]
            name_t = label(f"> {name.lower()}", size=22, color=color)
        else:
            body = Circle(radius=radius, color=color, stroke_width=t.stroke)
            body.set_fill(color, t.fill_opacity)
            initial = label(name[0], size=radius * 70, color=color, weight="BOLD")
            parts = [body, initial]
            name_t = label(name, size=26, color=color)
        name_t.next_to(body, DOWN, buff=0.18)
        super().__init__(*parts, name_t, **kw)
        self.body, self.name_text, self.color_ = body, name_t, color


# --- Objects -----------------------------------------------------------------------------
class Card(VGroup):
    """Box holding a value or message (e.g. a number sent over the channel)."""

    def __init__(self, content, color: str = FG, pad: float = 0.25, **kw) -> None:
        if isinstance(content, str):
            content = label(content, size=30, color=color)
        w, h = content.width + 2 * pad, content.height + 2 * pad
        if THEME.shape == "disc":
            shadow = Rectangle(width=w, height=h, stroke_width=0).set_fill(color, 0.9)
            box = Rectangle(width=w, height=h, color=color, stroke_width=3).set_fill(BG, 1)
            shadow.move_to(box).shift(DR * 0.07)
            parts = [shadow, box]
        elif THEME.shape == "box":
            box = Rectangle(width=w, height=h, stroke_width=0).set_fill(color, 0.07)
            parts = [box, _brackets(box, color, arm=0.14, buff=0.02)]
        else:
            box = RoundedRectangle(
                corner_radius=0.12, width=w, height=h, color=color, stroke_width=3
            )
            box.set_fill(color, opacity=0.08)
            parts = [box]
        content.move_to(box)
        super().__init__(*parts, content, **kw)


def backdrop() -> VGroup:
    """Subtle theme-specific background texture (empty for 'night')."""
    if THEME.name == "paper":
        dots = VGroup(
            *(
                Dot([x * 0.5, y * 0.5, 0], radius=0.012, color=MUTED, fill_opacity=0.35)
                for x in range(-15, 16)
                for y in range(-8, 9)
            )
        )
        return VGroup(dots)
    if THEME.name == "terminal":
        grid = NumberPlane(
            x_range=[-8, 8, 0.5],
            y_range=[-4.5, 4.5, 0.5],
            background_line_style={
                "stroke_color": MUTED,
                "stroke_width": 1,
                "stroke_opacity": 0.18,
            },
            axis_config={"stroke_opacity": 0},
        )
        hud = label(f"{_settings().title.upper()}  //", size=16, color=MUTED).to_corner(
            DL, buff=0.25
        )
        return VGroup(grid, hud)
    return VGroup()


# --- Scene base ----------------------------------------------------------------------------
_STOP = {
    # frequent 5+ letter function words (English, German) – never a cue for on-screen text
    "there", "their", "which", "would", "about", "these", "those", "every", "other",
    "diese", "dieser", "einen", "einem", "einer", "nicht", "werden", "aber", "durch",
}  # fmt: skip
# recurring character names (domain packs) are not narration cues; extend via _NAMES.update()
_NAMES: set[str] = {"alice", "bob", "carol", "dan", "eve", "frank"}
AUDIT_LOG = BUILD / "sync_audit.log"


def _words(text: str) -> list[str]:
    import re as _re

    return [w for w in _re.findall(r"[\w-]{5,}", text.lower()) if w not in _STOP]


def _stem(word: str) -> str:
    for end in ("en", "es", "e", "n", "s"):
        if word.endswith(end) and len(word) - len(end) >= 5:
            return word[: -len(end)]
    return word


def _audit(scene, tracker, animations, t_end: float) -> None:
    """Log text visible after it is spoken (LATE) or bold titles never spoken (UNSPOKEN)."""
    seen = scene.__dict__.setdefault("_audited", set())
    spoken = [
        (wb["text"].lower().strip(".,:;!?–„“\"'()"), tracker.start_t + wb["audio_offset"] / 1e7)
        for wb in tracker.data["word_boundaries"]
        if wb.get("text")
    ]
    block = " ".join(w for w, _ in spoken)
    for anim in animations:
        mob = getattr(anim, "mobject", None)
        if mob is None or isinstance(anim, FadeOut):  # leaving the screen: nothing to check
            continue
        for m in mob.get_family():
            if not isinstance(m, Text) or id(m) in seen or not m.text.strip():
                continue
            seen.add(id(m))
            raw = getattr(m, "original_text", None) or m.text  # m.text has spaces stripped
            words = [w for w in _words(raw) if w not in _NAMES]
            # whole words (minus simple word endings), spoken within 4 s before visibility
            stems = {_stem(w) for w in words}
            hits = [t for sw, t in spoken if _stem(sw) in stems and t_end - 4.0 <= t]
            name = f"{type(scene).__name__}: '{m.text[:40]}'"
            # late only if the word is never said again once the text is up: an earlier mention
            # (a list row that repeats a word from the line above) doesn't make the row late
            # one word: must be up on the word; a multi-word caption that sums up the sentence
            # may follow it, but not by more than 1.5 s
            slack = 0.25 if len(words) <= 1 else 1.5
            if hits and max(hits) + slack < t_end:
                line = f"LATE     {name} visible {t_end:.1f}s, spoken {max(hits):.1f}s"
            elif (
                not hits
                and m.weight == "BOLD"
                and m.font_size >= 30
                and words
                and words[0][:6] not in block
            ):
                line = f"UNSPOKEN {name} (bold title not mentioned in this narration block)"
            else:
                continue
            AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
            with AUDIT_LOG.open("a", encoding="utf-8") as f:
                f.write(line + "\n")


def _timeline(scene, line: str) -> None:
    """LVP_TIMELINE=dir: write a readable timeline per section (narration, words, texts shown)."""
    out = os.environ.get("LVP_TIMELINE")
    if out and not CHUNK_MODE:
        f = Path(out) / f"{type(scene).__name__}.txt"
        f.parent.mkdir(parents=True, exist_ok=True)
        with f.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")


_BOOKMARK = re.compile(r"<bookmark[^>]*/>")


def _plan(scene, entry: dict) -> None:
    """LVP_PLAN=dir: machine-readable plan of the final pass, for lvp-build's sync verification."""
    out = os.environ.get("LVP_PLAN")
    if out and not CHUNK_MODE:
        f = Path(out) / f"{type(scene).__name__}.jsonl"
        f.parent.mkdir(parents=True, exist_ok=True)
        with f.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")


# --- parallel-safe text cache -----------------------------------------------------------------
# Manim caches every Text as an SVG in media/texts/ and reuses a file as soon as it *exists*.
# Parallel render processes needing the same new text read each other's half-written file
# ("ParseError: no element found"). Fix: one cross-process lock around creating/checking text
# SVGs (cheap: cached texts take microseconds), plus a per-process temp file name for the
# parse step (Manim uses one fixed name per SVG).
def _svg_ok(path: Path) -> bool:
    import xml.etree.ElementTree as _ET

    try:
        _ET.parse(path)  # noqa: S314 - Manim's own generated SVGs
        return True
    except (_ET.ParseError, OSError):
        return False


def _patch_text_cache() -> None:
    import svgelements as se
    from manim import config
    from manim.mobject.svg import svg_mobject as _svg
    from manim.mobject.text import text_mobject as _txt

    def locked(original):
        def _text2svg(self, *args, **kwargs):
            with file_lock(Path(config.media_dir) / "texts" / ".lvp-lock"):
                path = Path(original(self, *args, **kwargs))
                if not _svg_ok(path):  # empty/broken leftover: rebuild it once
                    path.unlink(missing_ok=True)
                    path = Path(original(self, *args, **kwargs))
            return str(path)

        return _text2svg

    from manim.mobject.text import tex_mobject as _tex

    _tex_original = _tex.tex_to_svg_file

    from manim.utils.tex_file_writing import generate_tex_file

    def tex_to_svg_file(expression, environment=None, tex_template=None):
        """LaTeX writes media/Tex/* in place (lock), and formulas come from the committed
        tex_cache/ first: the rendering PC may have no LaTeX; any machine with LaTeX fills the
        cache during lvp-check, and the folder is committed."""
        with file_lock(Path(config.media_dir) / "Tex" / ".lvp-lock"):
            template = tex_template or config["tex_template"]
            svg = generate_tex_file(expression, environment, template).with_suffix(".svg")
            cached = TEX_CACHE / svg.name
            if not svg.exists() and cached.exists():
                shutil.copyfile(cached, svg)
            if svg.exists():
                return svg
            try:
                svg = Path(_tex_original(expression, environment, tex_template))
            except FileNotFoundError as e:
                raise RuntimeError(
                    f"Formula not in tex_cache/ and LaTeX is not installed: {expression!r}. "
                    "Pull the latest version (Claude fills tex_cache/ in the cloud)."
                ) from e
            TEX_CACHE.mkdir(exist_ok=True)
            if not cached.exists():
                shutil.copyfile(svg, cached)
            return svg

    _tex.tex_to_svg_file = tex_to_svg_file

    _txt.Text._text2svg = locked(_txt.Text._text2svg)
    _txt.MarkupText._text2svg = locked(_txt.MarkupText._text2svg)

    # The real culprit: after every Text, manimpango's remove_last_M rewrites the cached SVG in
    # place - in every process, even when the file was cached long ago. Readers in other
    # processes then see a truncated file. Same regex, but write only when something changes
    # (once, right after creation) and only under the lock.
    import re as _re

    class _PangoUtils(_txt.PangoUtils):
        @staticmethod
        def remove_last_M(file_name: str) -> None:  # noqa: N802 - manimpango's name
            with file_lock(Path(config.media_dir) / "texts" / ".lvp-lock"):
                path = Path(file_name)
                content = path.read_text()
                fixed = _re.sub(r'Z M [^A-Za-z]*? "\/>', 'Z "/>', content)
                if fixed != content:
                    path.write_text(fixed)

    _txt.PangoUtils = _PangoUtils

    def generate_mobject(self):
        import xml.etree.ElementTree as _ET

        file_path = self.get_file_path()
        new_tree = self.modify_xml_tree(_ET.parse(file_path))  # noqa: S314 - own files
        tmp = file_path.with_name(f"{file_path.stem}_{os.getpid()}_{file_path.suffix}")
        new_tree.write(tmp)
        svg = se.SVG.parse(tmp)
        tmp.unlink(missing_ok=True)
        mobjects, mobject_dict = self.get_mobjects_from(svg)
        self.add(*mobjects)
        self.id_to_vgroup_dict = mobject_dict
        self.flip(RIGHT)
        return self

    _svg.SVGMobject.generate_mobject = generate_mobject


_patch_text_cache()


# --- frame-exact clock ------------------------------------------------------------------------
# Manim bug: a *rendered* animation advances the clock by the frames it wrote (ceil for
# animations, floor for still waits), a *cached or skipped* one by its exact duration. Narration
# is placed by that clock, so every reused animation shifts audio against picture by up to a
# frame – and with chunks every animation of the final pass is reused (worse at 30 fps).
# Fix: always advance by exactly the frames a render would write. Then the clock is identical
# in dry runs, chunks, cached and fresh renders, and audio placement matches the video.
def _patch_frame_clock() -> None:
    import numpy as np
    from manim.animation.animation import Wait
    from manim.renderer.cairo_renderer import CairoRenderer

    original = CairoRenderer.play

    def play(self, scene, *args, **kwargs):
        t0 = self.time
        original(self, scene, *args, **kwargs)
        dur = float(getattr(scene, "duration", 0.0) or 0.0)
        if abs((self.time - t0) - dur) > 1e-9:
            return  # rendered: the clock already counted real frames
        dt = 1 / self.camera.frame_rate
        anims = getattr(scene, "animations", None) or []
        frozen = len(anims) == 1 and isinstance(anims[0], Wait) and anims[0].is_static_wait
        frames = int(dur / dt) if frozen else len(np.arange(0, dur, dt))
        self.time = t0 + frames * dt

    CairoRenderer.play = play


_patch_frame_clock()


# --- chunked rendering (lvp-build) -------------------------------------------------------------
# lvp-build splits long sections into animation ranges (manim -n a,b) rendered by parallel
# processes. Chunk processes only fill the shared partial-movie cache: they must not combine a
# movie, prune the cache or write the sync audit. A final normal pass per section then finds
# every animation cached and only concatenates and mixes the audio.
CHUNK_MODE = bool(os.environ.get("LVP_CHUNK"))
# Chunks render from a *skipped-to* state; Manim then hashes some animations a little differently
# than a normal run would (float noise), so the final pass would redo up to a third of the work.
# Instead, each chunk records which partial file it made for which animation number, and the
# final pass reuses them by number (LVP_REUSE = JSON files written by this build's chunks).
REUSE = os.environ.get("LVP_REUSE")
if REUSE:
    import json as _json

    import manim.renderer.cairo_renderer as _cr

    _reuse: dict[int, str] = {}
    for _f in Path(REUSE).parent.glob(Path(REUSE).name):
        _reuse.update({int(k): v for k, v in _json.loads(_f.read_text()).items()})
    _hash_original = _cr.get_hash_from_play_call

    def _hash_by_index(scene, *args, **kwargs):
        return _reuse.get(scene.renderer.num_plays) or _hash_original(scene, *args, **kwargs)

    _cr.get_hash_from_play_call = _hash_by_index
if CHUNK_MODE:
    import manim.scene.scene_file_writer as _sfw

    _sfw.SceneFileWriter.combine_to_movie = lambda self: None
    # every chunk would write the same <Scene>.srt at the end: Windows refuses ("file in use")
    _sfw.SceneFileWriter.write_subcaption_file = lambda self: None
    _sfw.prune_segment_cache = lambda *a, **k: None


class LessonScene(VoiceoverScene):
    """Base scene: theme, backdrop and narration service (silent unless LVP_VOICE=real)."""

    #: Breathing room after every narration block (seconds), overridable via LVP_PAUSE.
    pause = float(os.environ.get("LVP_PAUSE", "0.8"))

    #: Hold after a narration block, by what the block did (from the claudia.gallery research).
    HOLDS = {
        "none": 0.2,
        "step": 0.6,
        "reveal": 1.2,
        "insight": 2.0,
        "question": 4.0,
        "chapter": 2.5,
    }

    def setup(self) -> None:
        super().setup()
        self.set_speech_service(get_speech_service())
        self._backdrop = backdrop()
        self.add(self._backdrop)
        self.keep: list = []  # mobjects that survive chapter cards and stage clears

    @contextmanager
    def voiceover(self, text: str, pause: float | None = None, hold: str | None = None, **kw):
        """Narration block followed by a hold, so ideas can land.

        ``hold`` names what the block did: none, step, reveal, insight, question, chapter.
        Inside the block, place animations on words with ``<bookmark mark="x"/>`` in the text and
        ``self.wait_until_bookmark("x")`` before the animation.
        """
        with super().voiceover(text, **kw) as tracker:
            self._tracker = tracker
            _timeline(
                self,
                f"VOICE {tracker.start_t:7.2f}–{tracker.end_t:7.2f}  {tracker.data['input_text']}",
            )
            for wb in tracker.data.get("word_boundaries", []):
                _timeline(
                    self, f"  word {tracker.start_t + wb['audio_offset'] / 1e7:7.2f}  {wb['text']}"
                )
            audio = Path(self.speech_service.cache_dir) / tracker.data["final_audio"]
            _plan(
                self,
                {
                    "voice": float(tracker.start_t),
                    "audio": str(audio),
                    # for lvp-player: what is said, when it ends, and when each word is spoken
                    "end": float(tracker.end_t),
                    "text": _BOOKMARK.sub("", text).strip(),
                    "words": [
                        [round(float(tracker.start_t) + wb["audio_offset"] / 1e7, 2), wb["text"]]
                        for wb in tracker.data.get("word_boundaries", [])
                    ],
                },
            )
            if os.environ.get("LVP_LAYOUT") and not self._stage_visible():
                self._blank_from = float(tracker.start_t)  # narration starts on an empty screen
            yield tracker
        self._check_blank(float(tracker.end_t))
        self._tracker = None
        if pause is None:
            pause = self.HOLDS[hold] if hold else self.pause
        self.wait(pause)

    def _stage_visible(self) -> bool:
        from lvp import layout

        return any(
            layout._visible(m)
            for m in self.mobjects
            if m is not self._backdrop and m not in self.keep
        )

    def _check_blank(self, now: float) -> None:
        """lvp-check: narration over an empty screen for more than 2 s is a bug (BLANK)."""
        start = self.__dict__.pop("_blank_from", None)
        if start is not None and now - start > 2.0:
            from lvp import layout

            layout.LOG.parent.mkdir(parents=True, exist_ok=True)
            with layout.LOG.open("a", encoding="utf-8") as f:
                f.write(
                    f"{type(self).__name__}: BLANK     {now - start:.1f}s narration over an "
                    f"empty screen at {start:.1f}s\n"
                )

    def at(self, mark: str, *animations, **kw) -> None:
        """Wait until the narration reaches ``<bookmark mark=mark/>``, then play the animations."""
        lead = kw.pop("lead", 0.5)  # start a little early so the object is visible on the word
        tracker = getattr(self, "_tracker", None)
        if tracker is not None:
            t = tracker.time_until_bookmark(mark, buff=-lead)
            if t > 0:
                self.wait(t)
        else:
            self.wait_until_bookmark(mark)
        if animations:
            self.play(*animations, **kw)

    def opening(self, series: str, *mobjects) -> None:
        """Calm start before the first word (~2.5 s): empty paper, series tag, first objects.

        Starting the narration in the very first second feels abrupt to viewers.
        """
        self.wait(0.6)
        tag = label(series, size=22, color=MUTED, slant="ITALIC").to_corner(UL, buff=0.4)
        self.play(FadeIn(tag), *(FadeIn(m, shift=UP * 0.15) for m in mobjects), run_time=1.2)
        self.wait(0.8)

    # --- sync audit ------------------------------------------------------------------------
    def play(self, *animations, **kwargs):
        pending = self.__dict__.get("_pending_out")
        if pending and not all(isinstance(a, Wait) for a in animations):
            self._pending_out = None
            busy = {
                id(f)
                for a in animations
                if getattr(a, "mobject", None) is not None
                for f in a.mobject.get_family()
            }
            animations = (
                *animations,
                *(FadeOut(m) for m in pending if m in self.mobjects and id(m) not in busy),
            )
        if not self.__dict__.get("_recall_marked"):
            for a in animations:
                mob = getattr(a, "mobject", None)
                if isinstance(a, FadeOut) or mob is None:
                    continue
                if any(
                    isinstance(m, Text) and getattr(m, "original_text", "") == t("recall")
                    for m in mob.get_family()
                ):
                    self._recall_marked = True
                    _plan(self, {"chapter": t("recall"), "t": float(self.renderer.time)})
                    break
        if "_blank_from" in self.__dict__ and not all(isinstance(a, Wait) for a in animations):
            self._check_blank(float(self.renderer.time))
        super().play(*animations, **kwargs)
        tracker = getattr(self, "_tracker", None)
        if not CHUNK_MODE and tracker is not None and "word_boundaries" in tracker.data:
            _audit(self, tracker, animations, float(self.renderer.time))
        if os.environ.get("LVP_TIMELINE"):
            for anim in animations:
                mob = getattr(anim, "mobject", None)
                if mob is None:
                    continue
                txt = [m.text for m in mob.get_family() if isinstance(m, Text) and m.text.strip()]
                if txt:
                    _timeline(
                        self,
                        f"  SHOW {float(self.renderer.time):7.2f}  "
                        f"{type(anim).__name__}: {' | '.join(txt)[:80]}",
                    )
        if os.environ.get("LVP_PLAN") and not CHUNK_MODE:
            self._plan_screen()
        if os.environ.get("LVP_LAYOUT"):  # lvp-check
            from lvp import layout

            ignore = {id(m) for m in self._backdrop.get_family()}
            layout.check(self, ignore)

    def _plan_screen(self) -> None:
        """Record the on-screen text whenever it changes (lvp-player shows it to Claude)."""
        from lvp import layout

        texts: list[str] = []
        seen: set[int] = set()
        for m in self.mobjects:
            if m is self._backdrop:
                continue
            for f in m.get_family():
                if id(f) in seen:
                    continue
                if isinstance(f, MathTex):
                    seen.update(id(x) for x in f.get_family())
                    s = f.get_tex_string() if hasattr(f, "get_tex_string") else f.tex_string
                elif isinstance(f, Text):
                    s = getattr(f, "original_text", None) or f.text
                else:
                    continue
                seen.add(id(f))
                s = " ".join(str(s).split())
                if s and s not in texts and layout._visible(f):
                    texts.append(s)
        if texts != self.__dict__.get("_last_screen"):
            self._last_screen = texts
            _plan(self, {"screen": texts, "t": float(self.renderer.time)})

    def tear_down(self) -> None:
        pending = [m for m in (self.__dict__.pop("_pending_out", None) or []) if m in self.mobjects]
        if pending:  # a deferred clear at the very end of a section: fade out now
            from contextlib import suppress

            from manim.utils.exceptions import EndSceneEarlyException

            with suppress(EndSceneEarlyException):  # chunk (-n a,b) ended before this fade
                self.play(*(FadeOut(m) for m in pending), run_time=0.6)
        super().tear_down()
        hash_file = os.environ.get("LVP_HASH_FILE")  # lvp-build chunks: number → partial file
        if hash_file:
            done = {i: h for i, h in enumerate(self.renderer.animations_hashes) if h}
            Path(hash_file).write_text(json.dumps(done), encoding="utf-8")
        _plan(self, {"end": float(self.renderer.time)})
        count_file = os.environ.get("LVP_COUNT_FILE")  # lvp-build: number of animations
        if count_file:
            Path(count_file).write_text(str(self.renderer.num_plays), encoding="utf-8")

    def chapter(self, number: str, title: str) -> None:
        """Short chapter card between topics: clears the stage, shows number + title."""
        stage = Group(*(m for m in self.mobjects if m is not self._backdrop and m not in self.keep))
        if stage:
            self.play(FadeOut(stage), run_time=0.6)
        num = label(number, size=30, color=MUTED)
        t = label(title, size=46, weight="BOLD")
        if t.width > config.frame_width - 2.0:  # long titles: keep a margin to the frame edge
            t.scale_to_fit_width(config.frame_width - 2.0)
        g = VGroup(num, t).arrange(DOWN, buff=0.2)
        line = (
            Line(LEFT, RIGHT, color=ACCENT, stroke_width=4)
            .match_width(t)
            .next_to(t, DOWN, buff=0.15)
        )
        _plan(self, {"chapter": f"{number}. {title}", "t": float(self.renderer.time)})
        self.play(FadeIn(g, shift=UP * 0.2), Create(line), run_time=0.8)
        self.wait(1.2)
        # The card stays until the first real animation (fades out together with it), so the
        # chapter's first sentence never plays over an empty screen.
        self._pending_out = [g, line]

    def clear_stage(self, run_time: float = 0.6, now: bool = False) -> None:
        """Clear the stage. By default the old picture stays until the next real animation and
        fades out together with it, so the next sentence never starts on an empty screen
        (lvp-check BLANK). ``now=True`` fades immediately (e.g. right before a still pause)."""
        stage = [m for m in self.mobjects if m is not self._backdrop and m not in self.keep]
        if not stage:
            return
        if now:
            self.play(FadeOut(Group(*stage)), run_time=run_time)
        else:
            self._pending_out = [*(self.__dict__.get("_pending_out") or []), *stage]

    def pretest(self, questions: list[str], seconds: float = 5.0) -> None:
        """Guess before learning (pretesting, g ≈ 0.5 for the asked content): silent cards with
        thinking time. Answers come in the video itself. Call at the end of the hook (S0)."""
        from lvp.props import question

        head = label(t("pretest"), size=34, weight="BOLD", color=ACCENT).to_edge(UP, buff=0.8)
        hint = label(t("pretest_hint"),
                     size=22, color=MUTED).next_to(head, DOWN, buff=0.25)  # fmt: skip
        self.play(FadeIn(head), FadeIn(hint), run_time=0.5)
        for q in questions:
            qq = question(q).move_to(UP * 0.2)
            self.play(FadeIn(qq, shift=UP * 0.2), run_time=0.5)
            _plan(self, {"quiz": "pretest", "q": q, "t": float(self.renderer.time),
                         "think": seconds})  # fmt: skip
            self.wait(seconds)
            self.play(FadeOut(qq), run_time=0.4)
        self.play(FadeOut(head), FadeOut(hint), run_time=0.5)

    def checkpoint(self, q: str, a: str, think: float = 5.0, show: float = 3.5) -> None:
        """Retrieval question with feedback between segments (interpolated testing, the best
        supported technique for lecture videos): question, thinking time, then the answer.
        Ask about the *previous* section, not the one just finished: retrieval only trains
        memory after some forgetting – a question answered one sentence ago is just an echo.
        Prefer application/transfer over repeating a sentence from the video."""
        from lvp.props import question

        self.clear_stage()
        head = label(t("checkpoint"), size=30, weight="BOLD", color=ACCENT).to_edge(UP, buff=0.9)
        qq = question(q).move_to(UP * 0.9)
        self.play(FadeIn(head), FadeIn(qq, shift=UP * 0.2), run_time=0.5)
        asked = float(self.renderer.time)
        self.wait(think)
        ans = label(a, size=28, color=POSITIVE).next_to(qq, DOWN, buff=0.7)
        if ans.width > 12.5:
            ans.scale_to_fit_width(12.5)
        self.play(FadeIn(ans, shift=UP * 0.15), run_time=0.5)
        _plan(self, {"quiz": "check", "q": q, "a": a, "t": asked, "think": think,
                     "answer_t": float(self.renderer.time)})  # fmt: skip
        self.wait(show)
        self.play(FadeOut(head), FadeOut(qq), FadeOut(ans), run_time=0.5)

    # --- anchor grid (Code2Video): place by named cell instead of raw coordinates --------
    GRID_ROWS, GRID_COLS = "ABCDEF", 6

    def cell(self, name: str) -> np.ndarray:
        """Centre of grid cell 'A1'…'F6' (rows top→bottom, columns left→right, full frame)."""
        r, c = self.GRID_ROWS.index(name[0].upper()), int(name[1:]) - 1
        w, h = config.frame_width, config.frame_height
        return np.array([(-w / 2) + (c + 0.5) * w / self.GRID_COLS,
                         (h / 2) - (r + 0.5) * h / len(self.GRID_ROWS), 0])  # fmt: skip

    def place(self, mob, first: str, last: str | None = None, margin: float = 0.85):
        """place(m, "B2") centres m in a cell; place(m, "A1", "C3") fits m into that area."""
        a = self.cell(first)
        b = self.cell(last or first)
        mob.move_to((a + b) / 2)
        if last:
            w = abs(b[0] - a[0]) + config.frame_width / self.GRID_COLS
            h = abs(b[1] - a[1]) + config.frame_height / len(self.GRID_ROWS)
            if mob.width > w * margin or mob.height > h * margin:
                mob.scale(min(w * margin / mob.width, h * margin / mob.height))
        return mob

    def recall(self, questions: list[str], seconds: float = 5.0) -> None:
        """Closing retrieval block: numbered questions, one at a time, silent thinking time."""
        head = label(t("recall"), size=34, weight="BOLD", color=ACCENT).to_edge(UP, buff=0.8)
        self.play(FadeIn(head), run_time=0.5)
        for i, text in enumerate(questions, 1):
            qq = VGroup(label(f"{i}", size=48, color=ACCENT, weight="BOLD"), label(text, size=30))
            qq.arrange(RIGHT, buff=0.5).move_to(UP * 0.2)
            self.play(FadeIn(qq, shift=UP * 0.2), run_time=0.5)
            _plan(self, {"quiz": "recall", "q": text, "t": float(self.renderer.time),
                         "think": seconds})  # fmt: skip
            self.wait(seconds)
            self.play(FadeOut(qq), run_time=0.4)
        self.play(FadeOut(head), run_time=0.6)
        self.wait(0.5)

    def title_card(self, title: str, subtitle: str = "", say: str = "", hold: str = "chapter"):
        """Show a title on a cleared stage. Without `say` the scene comes back afterwards; with
        `say` the title stays visible while that sentence (the roadmap) is spoken – never
        narrate over an empty screen."""
        stage = Group(*(m for m in self.mobjects if m is not self._backdrop and m not in self.keep))
        if stage:
            self.play(FadeOut(stage), run_time=0.4)
        if say:
            shown = self._show_title(title, subtitle, fade=False)
            with self.voiceover(say, hold=hold):
                pass
            self.play(*(FadeOut(m) for m in shown), run_time=0.6)
            return
        self._show_title(title, subtitle)
        if stage:
            self.play(FadeIn(stage), run_time=0.4)

    def _show_title(self, title: str, subtitle: str, fade: bool = True):
        if THEME.name == "terminal":
            title = f"$ {title.lower()}_"
        t = label(title, size=56, weight="BOLD")
        if t.width > config.frame_width - 2.0:
            t.scale_to_fit_width(config.frame_width - 2.0)
        group = VGroup(t)
        if subtitle:
            group.add(label(subtitle, size=28, color=MUTED).next_to(t, DOWN, buff=0.3))
        underline = (
            Line(LEFT, RIGHT, color=ACCENT, stroke_width=4)
            .match_width(t)
            .next_to(t, DOWN, buff=0.12)
        )
        self.play(Write(t), Create(underline), run_time=1.2)
        if subtitle:
            self.play(FadeIn(group[1], shift=UP * 0.2), run_time=0.6)
        self.wait(0.6)
        if not fade:
            return group, underline
        self.play(FadeOut(group), FadeOut(underline), run_time=0.6)
        return None
