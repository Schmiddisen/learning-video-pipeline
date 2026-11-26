---
name: player
description: Publish the course as an interactive study player (a private Claude artifact) – videos with live transcript; the video's questions as real input graded by Claude; draw on the frame and ask Claude about that exact moment; explain-back after each video; flashcard review (FSRS) linked to the moments that teach each card, with a direct Anki bridge in the desktop app; hands-on labs Claude designs per section (Python/JavaScript in the browser); exam practice across videos. Use when the user wants to study the course, asks for "the player", or after videos are rendered.
---

# Interactive study player

## 0. One player for all of the learner's courses
A learner installs **one** player (one artifact, one app). Every further course – a paper, a
book chapter, another lecture, from any repository or session – goes **into that player** as
a library entry, never into a second artifact unless the user asks for one.
- Find it first: `Artifact` `list`, and look for the learner's study player (ask the user if
  unsure which). If there is one, this course is added to it with a **slug** (short,
  lowercase, e.g. `attention-paper`); if there is none, this course becomes the player's
  first course (no slug).
- Layout of a player: the page and scripts at the root (shared by all courses, always the
  newest engine), the first course's `course.json` and `videos/` at the root, every further
  course in `courses/<slug>/` (`course.json`, `videos/`), and `library.json` listing them
  (`{"courses": [{"slug", "title", "language", "path"}]}`). The header shows a course switcher;
  each course keeps its own progress, cards and notes (records `<slug>~<key>`); model choice
  and review settings are shared.
- Budget: one artifact version holds 256 MB in total. Check the sizes in a `files` listing
  before adding a course; lower `--max-mb` (e.g. 6) for new courses when space runs short.

## 1. Export (free)
Every video needs a build (`lvp-build`; 480p is plenty to watch).
```bash
uv run lvp-player --clean                 # all built videos → build/player/
uv run lvp-player --only-data             # after changing cards/labs/learner.md: data + page only
uv run lvp-player --slug attention-paper --library /path/to/library.json   # into an existing player
```
For an existing player: `Artifact` `read` its URL first, then `read` with `path:
"library.json"` (saved locally). A player with a single course has none: write one that
lists the root course (`{"format": 1, "courses": [{"slug": "", "title": "<its title>",
"language": "<xx>", "path": ""}]}`) and pass it – without it the root course drops out of
the switcher. The export writes `build/player/courses/<slug>/` and the merged
`build/player/library.json`; entries of the other courses are kept.
Writes `build/player/`: `index.html`, `app.js`, `review.js`, `labs.js`, `exam.js`,
`lab-worker.js`, `fsrs.js` (the page; ts-fsrs is bundled, MIT), `course.json` (timeline per video, cards linked to their moment,
authored labs, the learner profile), `videos/*.mp4` (≤ 14 MB each) and `pyodide/` (Python
for the labs, downloaded once; `--no-python` for JavaScript-only labs), `rwkv.js`,
`rwkv-worker.js` and `rwkv_weights.wasm` (raw float32) + `rwkv_weights.json` (the RWKV memory
model: by default SM118, the "Small" two-head model of the RWKV Anki fork JSchoreels/anki,
~1.3 MB; `--rwkv-model srs-benchmark` for the srs-benchmark checkpoint, ~11 MB; downloaded once,
hash-checked, converted without torch; `--no-rwkv` to leave it out). The weights are for the
learner's own use only (trained on Anki's review dataset; shipping them in an app needs Anki's
permission) – never commit or share them. Older builds work too: text, word timings and question times
are reconstructed.

## 2. Publish as an artifact
**Adding to an existing player:** publish to its `url`, with `file_path`
`build/player/index.html` and `files`: `library.json`, the root scripts (`app.js`,
`review.js`, `labs.js`, `exam.js`, `local.js`, `lab-worker.js`, `fsrs.js`, `rwkv.js`,
`rwkv-worker.js` – newer engine, same contracts), and every file under `courses/<slug>/` at
its relative path. Do **not** send the root `course.json` or `videos/` of the other course,
and send `pyodide/` and `rwkv_weights.*` only if the `files` listing lacks them. Omit
`capabilities` (kept) and `icon`. Then stop here and go to 3.

**A new player** (the learner has none yet):
Load the `artifact-capabilities` skill first. Publish `build/player/index.html` with:
- `files`: every other file in `build/player/` at its relative path (`course.json`,
  `app.js`, `review.js`, `labs.js`, `exam.js`, `lab-worker.js`, `fsrs.js`, `rwkv.js`,
  `rwkv-worker.js`, `rwkv_weights.wasm`,
  `rwkv_weights.json`, `pyodide/<each file>`, `videos/<id>.mp4`)
- `capabilities`: `{"sample": {"images": true}, "db": {}, "user": {}, "dictation": {}, "desktop": {}}`
- `icon`: `"video"`, a one-sentence `description`.

One publish carries at most 64 MB: first the page, scripts, `course.json`, `pyodide/` and a
few videos, then the remaining videos in further publishes **to the same URL** (files not
named are kept). A version holds at most 256 MB; for bigger courses lower `--max-mb` or
publish one player per part. Later updates only send what changed (scripts, `course.json`).

## 3. Check and hand over
After the first publish: one `ArtifactData` `list` of `data/users/me` (empty until the
learner opens it). Tell the user:
- it is private; Claude features use their own Claude usage and ask once for permission;
- **Anki**: install the player as an app (Claude desktop app → artifact menu → Install as
  app), keep Anki open with AnkiConnect (add-on 2055492159), open Review → Connect to Anki.
  It matches the course's notes, sends reviews, can follow Anki's schedule, add missing
  cards and sync AnkiWeb (so AnkiDroid stays in step). Without it, review runs in the player;
  pending reviews go to Anki the next time it connects.
- **Scheduler** (Review → settings): FSRS, or RWKV – a neural memory model that replays the
  whole review history (Anki's review log when Anki's decks are on) in a worker and shows the
  cards most at risk first, at a chosen target recall; answers still go to Anki. Due cards
  are **live** by default, as RWKV-Instant in the RWKV Anki fork (JSchoreels/anki): eligible
  while predicted recall ≤ target, lowest recall ÷ target first, a card returns only after 5
  other answers and 30 s – the count is a snapshot and can fall faster than one per answer or
  rise. **Fixed per day** is the alternative (built once a day; one fewer per answer). The
  history replay follows the fork: graded revlog types 0–5 without cram (type 3, factor 0),
  from each card's last fresh start.
- dictation works on desktop Chromium and the desktop app.

Re-run 1–2 (same URL) when videos change; the learner's progress is kept. Use the `coach`
skill to read how the learner is doing and adapt the course.
