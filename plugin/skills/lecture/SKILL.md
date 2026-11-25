---
name: lecture
description: Run the whole pipeline for one part of a course (a lecture, a chapter, a paper) – ingest, curriculum, scripts, review, narration, render, companion – stopping at the two approval gates (video plan, narration cost). Use when the user says "do lecture 5", "make videos for this PDF", or hands over a new source without further instructions.
---

# One part, end to end

Usage idea: "/lvp:lecture 05 material/slides/05_hashing.pdf"

1. If there is no `lvp.toml`: run the `setup` skill first.
2. `ingest` the new source(s).
3. `curriculum` for this part → **Gate 1: show the video plan, wait for approval.**
4. `script` – the videos of this part (parallel `scene-writer` agents for 3+ videos, disjoint
   files), each `lvp-check` clean.
5. `review` – this part's scripts together with all earlier parts (repetition is across the
   course).
6. `produce` – cost preview → **Gate 2: confirm the amount** (skip if within an agreed
   budget) → record → 480p verify → critic → fixes.
7. `companion` – cards for this part, exercise companion if exercises exist; for topics
   where doing beats reading, an authored lab in `labs/` (the player designs more on demand).
8. `player` – export and republish the study player (same URL as before; only the new
   videos and data are uploaded).
9. Commit, push, and report in a few lines: videos (titles, lengths), cost, the player link,
   what to render in 4K, anything left open. Suggest the `coach` skill after a week of use.

Keep the user informed at each step with one line; don't wait for confirmation except at the
two gates.
