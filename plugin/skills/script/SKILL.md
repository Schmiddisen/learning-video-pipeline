---
name: script
description: Write the scene files for one or more planned videos – narration, visuals, and the built-in retrieval practice – using the lvp engine. Use after the curriculum is approved, or when the user asks for a new video. Drafts are silent and free; nothing is recorded here.
---

# Write videos

Read first (relative to this skill's folder): `../../references/didactics.md`,
`../../references/scene-api.md`, `../../references/pitfalls.md`; then `learner.md`, the
curriculum and coverage of this part, and the scripts of the previous two videos (for variety
and to know what is already explained).

For each video `videos/vNN_slug/slug.py`:
1. **Beats first:** in a comment block at the top, list sections and their beats (problem →
   idea → mechanism → consequence) and the opening/ending technique.
2. **Write the sections** with the engine API: one clause per `voiceover` block, bookmarks on
   the words visuals belong to, `hold=` everywhere, the learning loop (`pretest` at the end of
   S0, `checkpoint` from S2 on about the previous section, `recall` at the end), `chapter()`
   per section, `title_card(..., say=roadmap)` after the hook.
3. **Explain once:** anything taught in an earlier video gets a one-sentence callback
   ("you know … from Video 1.2"), never a second derivation.
4. **Check (free):** `uv run lvp-check videos/vNN_slug/slug.py` → fix every layout issue,
   BLANK, UNSPOKEN and LATE > 2 s. Run `lvp-check` once after adding formulas (fills
   `tex_cache/`).
5. **Look at it:** `uv run lvp-build videos/vNN_slug/slug.py -q l --fps 15` (silent, 480p,
   ~2 min) and inspect contact sheets: `ffmpeg -i build/videos/<file>_l.mp4 -vf
   "fps=1/8,scale=427:240,tile=4x4" sheet_%02d.png`. Fix what looks wrong.

Several videos at once: write them in parallel with the `scene-writer` agent, one video per
agent and **disjoint files**; then always run the `review` skill over all scripts together.

Do not record narration here – the `review` skill comes first.
