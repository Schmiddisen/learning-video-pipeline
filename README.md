# Learning Video Pipeline

Turn any course material – lecture slides, recordings, papers, book chapters – into **short,
narrated, 3Blue1Brown-style explainer videos** with built-in retrieval practice, plus **Anki
decks** and **exercise companions**, all driven by [Claude Code](https://claude.com/claude-code).

What sets it apart: audio/video sync is measured on the finished file, a review gate catches
repetition across videos before any narration is paid for, questions are placed the way the
learning-science evidence suggests, and narration is cached so a line is never paid twice.

**What you get per part of your course**

- 2–4 videos of 8–12 minutes, each with a "guess first" question, a quick check after every
  section (about the *previous* section, so you actually have to remember), and recall
  questions at the end
- a study player (a private Claude artifact): Claude grades your answers and sends you back to
  the exact moment you missed, answers questions about whatever you circle on screen, asks you
  to explain each video back, schedules flashcards that unlock as you watch (and syncs them
  with Anki), designs a hands-on lab for every section and builds mixed exam practice
- chapter markers, narration in your language, sync verified on the finished file
- an Anki deck sized to your review budget, exercise hints (hint → method → solution), mixed
  practice across parts
- a coverage map proving nothing from the source was dropped

## Install

You need [Claude Code](https://claude.com/claude-code), [uv](https://docs.astral.sh/uv/) and
ffmpeg. Narration uses Gemini TTS via [OpenRouter](https://openrouter.ai) (about $0.10 per
10-minute video, set `OPENROUTER_API_KEY`); without a key everything works with silent drafts.

In Claude Code:

```
/plugin marketplace add Schmiddisen/learning-video-pipeline
/plugin install lvp@learning-video-pipeline
```

Then, in an empty folder: **`/lvp:setup`** – it installs the engine, creates the project and
asks a few questions about you (goal, what you already know, depth, language, budget).

## Use

| Say / run | What happens |
|---|---|
| `/lvp:lecture 03 material/slides/03.pdf` | the whole pipeline for one part, stopping at two gates: the video plan and the narration cost |
| `/lvp:ingest` · `/lvp:curriculum` · `/lvp:script` · `/lvp:review` · `/lvp:produce` · `/lvp:companion` | the individual steps |
| `/lvp:feedback 2.2 at 9:15 refers to the slide` | finds the exact line, fixes it (and its siblings across the course), re-records only what changed, re-verifies |
| `/lvp:player` | publishes the course as a study player: the video's questions graded by Claude, circle anything on the picture and ask about that moment, explain-back, flashcards (FSRS or the RWKV neural memory model, synced with Anki) that unlock as you watch, hands-on labs, exam practice |
| `/lvp:player` again, in another course's repo | adds that course to the **same** player: one app, a course switcher, progress per course |
| `/lvp:lab` | designs verified hands-on labs for any subject: code to build or break the idea, or worked problems step by step – shown in the player's Lab tab |
| `/lvp:coach` | reads how you are actually doing in the player and adapts: targeted cards and labs, fixes to confusing videos, a note with focus moments in your Today panel |
| `uv run lvp` | render menu for your final videos (4K/1080p/480p, one, a range or all) – uses recorded narration only, never pays |

## How it works

```
material/ ──ingest──► digests ──curriculum──► video plan + coverage map   (gate 1)
                                   │
                              script (silent drafts, lvp-check)
                                   │
                              review: all scripts together                   ← most valuable step
                                   │
                              produce: cost preview (gate 2) → record → 480p render
                                       → measured sync check → vision critic → your 4K render
                                   │
                              companion: Anki, exercise hints, mixed practice
```

Two layers:

- **`plugin/`** – the Claude Code plugin: skills for each step, a scene-writer and a
  script-reviewer agent, and the references (teaching style, scene API, pitfalls).
- **`src/lvp/`** – the engine (Python, Manim): scene base class with narration sync, themes,
  props, the learning-loop cards, parallel chunked rendering, PCM-exact stitching, sync
  verification, layout/sync checks, vision critic, narration cache with spend caps, Anki
  export. Commands: `lvp-init`, `lvp-check`, `lvp-build`, `lvp-narrate`, `lvp-critic`,
  `lvp-dump`, `lvp-locate`, `lvp-player`, `lvp-anki`, `lvp-digest`, `lvp-transcribe`, `lvp`.

## A project

```
my-course/
  lvp.toml      language, theme, voice, speed, budget, pronunciation fixes
  learner.md    who is learning – every skill reads it
  material/     your sources (kept out of git if not yours to publish)
  plan/         curriculum and coverage maps
  videos/       one Manim scene file per video
  cards/        Anki cards (YAML → .apkg)
  exercises/    companions and practice
  voice_cache/  recorded narration – commit it, never pay twice
  tex_cache/    rendered formulas – commit it, no LaTeX needed when rendering
```

## Status

Early (0.1). The engine has produced a full course; the generic packaging is new. See
[docs/ROADMAP.md](docs/ROADMAP.md) and [docs/research/](docs/research/). Issues and pull
requests welcome.

MIT licence. Bundles the DejaVu fonts (free licence, `src/lvp/fonts/LICENSE-DejaVu.txt`).
