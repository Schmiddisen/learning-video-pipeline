---
name: review
description: Review all video scripts of a course together before narration – cross-video repetition, questions answered one line earlier or too easy, wrong answers, references to the source, undefined terms, coverage gaps – and apply the fixes. Use before every lvp-narrate --pay, after writing several videos, or when the viewer says something feels repetitive.
---

# Review scripts (the gate before money is spent)

On real courses this step finds dozens of problems that every per-video check missed.
Never record narration for scripts that haven't passed it.

1. **Dump everything in viewing order** (narration + every question):
   ```bash
   uv run lvp-dump > build/all_scripts.md
   ```
   Every narration block appears as `[SAY]`, on-screen questions as `[Q-ONSCREEN]`, and
   `[PRETEST]`, `[CHECK] q → a`, `[RECALL]` lines, grouped by file and section.
2. **Review** – for large courses split by part and use the `script-reviewer` agent, one per
   part; each reads the *whole* dump (repetition is across videos) but reports only for its
   files. Look for:
   - **A. Full repetitions:** an explanation, derivation, example, story or number already
     given earlier → cut, or a one-sentence callback (give the exact replacement sentence).
   - **B. Bad questions:** answered in the preceding sentences, trivial recall, duplicates
     (within or across videos), not about the previous section (checks), unclear, needs
     untaught content, wrong or disputable answer → a harder application/transfer question
     with its answer.
   - **C. Within-video restatements and recaps.**
   - **D.** References to the source ("the slide says"), terms used before they're taught,
     coverage gaps against `plan/*/coverage.md`.
3. **Apply** the fixes (or let each reviewer apply its own, disjoint files). When narration is
   cut, cut its visuals too; keep bookmarks valid.
4. `uv run lvp-check` must be clean again. Re-dump and spot-check that the worst items are gone.
5. Report a short summary (counts per category, the 3 most important fixes) and hand over to
   `produce`.
