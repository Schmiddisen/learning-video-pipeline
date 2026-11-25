---
name: feedback
description: Apply viewer feedback on a rendered video in one step – "2.2 at 9:15 refers to the slide", "the question at 4:30 is too easy", "this part repeats video 1.3", a screenshot of a layout bug – by locating the exact line, fixing it, re-recording only what changed and re-verifying. Use whenever the user reports something they noticed while watching.
---

# Apply watch feedback

1. **Locate:** `uv run lvp-locate <scene file> <mm:ss>` (add `--quality k60` etc. if the user
   watched a specific render; default is the newest build). It prints the section, chapter and
   the exact narration line with its line number. For a screenshot without a timestamp, find
   the on-screen text in the scene file.
2. **Understand the class of problem** – it is rarely only this spot:
   - references the source / repeats an earlier video / restates → search the whole course
     (`uv run lvp-dump`) for the same pattern and fix all occurrences;
   - weak question → check the other questions of that video against
     `../../references/didactics.md` (learning loop);
   - layout → check whether `lvp-check` should have caught it; if not, improve the check
     (that is how EDGE, TIGHT and BLANK were born).
3. **Fix** the scene file(s). Moving a bookmark is free; changed words need re-recording.
4. **Check:** `uv run lvp-check <files>`, then `uv run lvp-narrate <files>` (cost preview) →
   `--pay` within the user's budget.
5. **Verify:** `LVP_VOICE=real uv run lvp-build <file> -q l --fps 15` → sync verified; look at
   the fixed spot (`ffmpeg -ss <t> -i build/videos/<f>_l.mp4 -frames:v 1 spot.png`).
6. **Learn:** if the problem was systematic, add one line to the project's notes (and propose
   a line for the plugin's `references/pitfalls.md` upstream).
7. Commit, push, and tell the user exactly which videos to re-render.
