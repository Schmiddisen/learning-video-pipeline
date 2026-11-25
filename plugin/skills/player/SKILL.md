---
name: player
description: Publish the course's rendered videos as an interactive player (a private Claude artifact) – the learner watches, the video pauses at its questions for a typed answer, and they can circle something on the picture and ask Claude, who knows the exact moment, the narration and the text on screen. Use when the user wants to watch the course with Claude at hand, asks for "the player", or after a batch of videos is rendered.
---

# Interactive player

What the learner gets: the videos with a live transcript (word by word), chapters and
question markers on the timeline; every pretest, check and recall question stops the video
and takes a typed answer (Claude can judge it); "Mark" lets them draw on the frame; "Ask"
sends Claude the frame (with the marks), the moment, the last lines, the on-screen text and
the whole narration. Progress and answers are saved to their account.

## 1. Export (free)
Every video needs a build (`lvp-build`, 480p is plenty for watching on a laptop or phone).
```bash
uv run lvp-player --clean            # all videos with a build → build/player/
```
It writes `build/player/index.html` (the page), `course.json` (timeline per video) and
`videos/*.mp4` (re-encoded to ≤ 14 MB each, the artifact's per-file limit). Builds made with
older engine versions work too: narration text, word timings and question times are
reconstructed (question times are then estimates – fine for pausing).

## 2. Publish as an artifact
Load the `artifact-capabilities` skill first (it is required before declaring capabilities).
Then publish `build/player/index.html` with the Artifact tool:
- `files`: `{"course.json": "build/player/course.json", "videos/<id>.mp4": "build/player/videos/<id>.mp4", …}`
- `capabilities`: `{"sample": {"images": true}, "db": {}, "user": {}, "dictation": {}}`
- `icon`: `"video"`; a one-sentence `description`.

One publish carries at most 64 MB: publish the page with `course.json` and the first videos,
then add the remaining videos in further publishes **to the same URL** (files not named are
kept). A version holds at most 256 MB – for larger courses lower `--max-mb` or publish one
artifact per part (`uv run lvp-player videos/v03_*/*.py`).

## 3. Check and hand over
After the first publish, read back the progress store once (`ArtifactData` `list` on
`data/users/…` is private – an empty result is expected) and open the page. Tell the user:
the artifact is private; asking Claude uses their own Claude usage; the first question asks
for permission; it works on claude.ai, in the desktop app (installable as its own window) and
on phones (dictation only on desktop Chromium/the desktop app).

Re-run steps 1–2 (same URL) whenever videos are re-rendered; progress is kept.
