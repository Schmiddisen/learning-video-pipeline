---
name: produce
description: Turn reviewed scripts into finished videos – narration cost preview, paid recording after approval, 480p render with measured sync verification, vision critic, fixes, and hand-over for the user's final 4K render. Use after the review skill passed, or when the user says "record", "render", "make the video".
---

# Produce videos

Preconditions: `lvp-check` clean and the `review` skill done for these scripts. Never record
unreviewed narration – every change after recording costs money again.

1. **Cost preview (free):** `uv run lvp-narrate <files>` – lists unrecorded lines and the
   estimated cost. Tell the user the amount; **ask before paying** unless they gave a budget
   for this run (respect `lvp.toml [budget]`; `voice_cache/FROZEN` blocks all spending).
2. **Record:** `uv run lvp-narrate <files> --pay -j 4`. Then `uv run lvp-narrate <files>` must
   say `0 not recorded`. Commit `voice_cache/`.
3. **Render and verify** each video at 480p:
   `LVP_VOICE=real uv run lvp-build <file> -q l --fps 15`
   It ends with `[✓] sync verified in the final file` – any `SYNC CHECK FAILED` is a bug: read
   `../../references/pitfalls.md` (rendering) before chasing it. Don't edit files while a
   build runs; render videos one after another.
4. **Look:** contact sheets (`ffmpeg -i build/videos/<f>_l.mp4 -vf
   "fps=1/8,scale=427:240,tile=4x4" sheet_%02d.png`) and the vision critic
   `uv run lvp-critic build/videos/<f>_l.mp4` (~$0.02, report in `build/critic/`). Fix real
   problems (clipping, collisions, unreadable text); ignore fades caught mid-transition.
5. **Companion:** if cards changed, `uv run lvp-anki` (writes `cards/*.apkg` in the current
   format plus `all_decks.apkg`).
6. **Hand over:** commit and push, then update the study player (`player` skill) – that is
   where the learner watches, answers, reviews and practises. For a 4K file to keep:
   `uv run lvp` → choose quality → `a` / `v2` / `4-7` (recorded narration only, never pays).
   Ask them to report problems as "video at mm:ss: what's wrong" – the `feedback` skill
   handles that – or simply to keep using the player: the `coach` skill reads what they
   struggle with.
