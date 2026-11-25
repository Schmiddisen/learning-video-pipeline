---
name: player
description: Publish the course as an interactive study player (a private Claude artifact) – videos with live transcript; the video's questions as real input graded by Claude; draw on the frame and ask Claude about that exact moment; explain-back after each video; flashcard review (FSRS) linked to the moments that teach each card, with a direct Anki bridge in the desktop app; hands-on labs Claude designs per section (Python/JavaScript in the browser); exam practice across videos. Use when the user wants to study the course, asks for "the player", or after videos are rendered.
---

# Interactive study player

## 1. Export (free)
Every video needs a build (`lvp-build`; 480p is plenty to watch).
```bash
uv run lvp-player --clean                 # all built videos → build/player/
uv run lvp-player --only-data             # after changing cards/labs/learner.md: data + page only
```
Writes `build/player/`: `index.html`, `app.js`, `review.js`, `labs.js`, `exam.js`,
`lab-worker.js`, `fsrs.js` (the page; ts-fsrs is bundled, MIT), `course.json` (timeline per video, cards linked to their moment,
authored labs, the learner profile), `videos/*.mp4` (≤ 14 MB each) and `pyodide/` (Python
for the labs, downloaded once; `--no-python` for JavaScript-only labs). Older builds work
too: text, word timings and question times are reconstructed.

## 2. Publish as an artifact
Load the `artifact-capabilities` skill first. Publish `build/player/index.html` with:
- `files`: every other file in `build/player/` at its relative path (`course.json`,
  `app.js`, `review.js`, `labs.js`, `exam.js`, `lab-worker.js`, `fsrs.js`, `pyodide/<each file>`,
  `videos/<id>.mp4`)
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
- dictation works on desktop Chromium and the desktop app.

Re-run 1–2 (same URL) when videos change; the learner's progress is kept. Use the `coach`
skill to read how the learner is doing and adapt the course.
