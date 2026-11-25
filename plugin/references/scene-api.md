# Writing scenes with the lvp engine

One video = one file `videos/vNN_slug/slug.py` with section classes `S0Hook`, `S1Name`, …,
`SnOutro`. Each section is its own scene (rendered in parallel, stitched, then
verified). Docstring line 1 is the title shown in the render menu:

```python
"""Video 2.3 – The test that lies: Bayes' theorem.  (source: chapter 4.2)"""

from manim import DOWN, LEFT, RIGHT, UP, FadeIn, FadeOut, GrowArrow, Arrow
from lvp.style import (
    ACCENT,
    FG,
    MUTED,
    NEGATIVE,
    POSITIVE,
    PRIMARY,
    SPECIAL,
    Card,
    LessonScene,
    label,
)
from lvp.props import DefBox, cross, question, tick

SERIES = "Probability · Video 2.3"


class S0Hook(LessonScene):
    def construct(self) -> None:
        q = question("Positive test – how likely are you sick?").move_to(UP * 2)
        self.opening(SERIES, q)  # calm 2.5 s start + series tag
        with self.voiceover(
            'The test is ninety-nine percent accurate. <bookmark mark="g"/>Make a guess.',
            hold="question",
        ):
            self.at("g", FadeIn(label("99 %?  50 %?  9 %?", color=ACCENT)))
        self.title_card(
            "The test that lies", say="First we count people, then we find the formula."
        )
        self.pretest(["Why does the rarity of a disease matter for a single test result?"])


class S1Rules(LessonScene):
    def construct(self) -> None:
        self.chapter("1", "A thousand people")
        ...


class S2Formula(LessonScene):
    def construct(self) -> None:
        self.chapter("2", "From counting to a formula")
        ...
        self.checkpoint(
            "Same test, 1 in 100 people sick. Roughly how many positives are real?",  # about S1!
            "About half: 1 true positive vs. about 1 false one per 100",
        )
```

## Narration and sync (the core contract)

- **One sentence or clause per `with self.voiceover("…", hold=…):` block.** Strings may be
  concatenated across lines.
- Put `<bookmark mark="x"/>` right before the word an animation belongs to and call
  `self.at("x", anim, run_time=…)` inside the block. `at` starts 0.5 s early so the object is
  visible *on* the word. Animations without a bookmark play at the start of the block.
- `hold=` after every block: `none` 0.2 · `step` 0.6 · `reveal` 1.2 · `insight` 2.0 ·
  `question` 4.0 (thinking time) · `chapter` 2.5.
- On-screen text appears when its words are spoken (the sync audit flags LATE text and bold
  titles never mentioned). Never read long on-screen text aloud word for word.
- Narration text is what the voice says: write numbers/symbols as spoken words where the voice
  would stumble; fix systematic mispronunciations in `lvp.toml [pronunciation]`.

## Scene helpers (`LessonScene`)

| Call | What it does |
|---|---|
| `opening(series, *mobjects)` | calm start, series tag top-left (first section only) |
| `chapter("2", "Title")` | chapter card; stays until the next animation (no blank screen); becomes an MP4 chapter |
| `title_card(title, subtitle="", say="roadmap")` | video title; with `say` the title stays up while the roadmap is spoken |
| `clear_stage()` | old picture fades out *together with* the next animation; `now=True` only before a deliberate silent pause |
| `pretest([q, …])` | "Guess first" cards, end of S0 |
| `checkpoint(q, a)` | "Quick check", end of section, asks about the previous section |
| `recall([q1, q2, q3])` | closing retrieval block, last section |
| `place(m, "B2")` / `place(m, "A1", "C3")` | 6×6 anchor grid (rows A–F top→bottom, columns 1–6): centre in a cell / fit into an area. Prefer this over raw coordinates. |
| `self.keep` | list of mobjects that survive clears and chapter cards |

## Building blocks

- `label(text, size=32, color=FG, **Text kwargs)` – always use instead of `Text`: theme font,
  glyph fallback (⊕ ⇒ ε … from bundled DejaVu), never wider than the safe area.
- `Card(content_or_str, color, pad)` – boxed value; `DefBox(title, text, color, width)` –
  definition box; `question(text)` – "?" + italic question; `tick()`, `cross()`, `bolt()`,
  `Packet`, `EyeIcon`, `Badge`, `fit(mob)`; `Person(name, color)` – avatar for any character.
- Colours: roles only – `PRIMARY` (main actor), `POSITIVE`, `NEGATIVE`, `ACCENT` (highlight /
  the key idea), `SPECIAL`, `TEAL`, plus `FG`, `MUTED`, `BG`. Never hard-code hex colours:
  themes switch them.
- Formulas: `MathTex(r"...")`. They are cached in `tex_cache/` (commit it) so viewers' PCs need
  no LaTeX; run `lvp-check` once after adding a formula to fill the cache.
- Domain packs: optional recurring props for one subject, under `src/lvp/packs/`. The bundled
  example is `lvp.packs.crypto` (a fixed cast of characters, keys, a channel). Add a pack when
  a course needs recurring props (and upstream it if it's general).

## Layout rules (enforced by `lvp-check`)

- Nothing within 0.2 units of the frame border (EDGE), nothing off screen (OFFSCREEN).
- No partial overlaps of text with text or shapes (OVERLAP); no two texts touching on one line
  (TIGHT); no narration > 2 s over an empty screen (BLANK).
- Frame is 14.2 × 8 units; keep body text ≥ 22 pt; at most ~60 characters per line (use \n).

## Checking and producing

- `uv run lvp-check [files]` – free dry run: layout, blank screens, sync audit, unrecorded lines.
- `uv run lvp-narrate files` – cost preview; `--pay` records (ask the user first).
- `LVP_VOICE=real uv run lvp-build videos/v02_3/x.py -q l --fps 15` – 480p render with real
  narration; ends with a **measured** sync check of the final file (failure = bug).
- `uv run lvp-critic build/videos/…_l.mp4` – vision model reviews frames (~$0.02/video).
- `uv run lvp` – menu for the user's final 4K renders (cached narration only, never pays).
- `uv run lvp-player` – package builds for the interactive player (the `player` skill). The
  plan each build writes records narration text, word times, on-screen text and question
  times; the question helpers above are what make the player stop and ask.
