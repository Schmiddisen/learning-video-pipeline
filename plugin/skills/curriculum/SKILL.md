---
name: curriculum
description: Plan what to teach and in which order – a concept map of the source, a video plan (which video covers what, 8–12 min each), and a coverage map proving nothing from the source is missing. Use after ingest, before writing scripts, or when the user asks "what will the videos cover".
---

# Plan the curriculum

Read first: `learner.md`, `material/digest/INDEX.md`, the digests and summaries of the part
being planned, `../../references/didactics.md` (relative to this skill's folder).

## Produce `plan/<part>/curriculum.md`
1. **Concept list** from the source: every definition, mechanism, formula, number, example,
   historical case and exam hint – with its source location (slide/page/timestamp).
2. **Prerequisites** between concepts; mark what earlier parts already taught (those get a
   one-line callback later, never a re-explanation).
3. **Video plan:** group concepts into videos of 8–12 minutes (≈ 1,100–1,500 spoken words,
   3–6 sections of 2–4 minutes). For each video: title, one-sentence promise, sections, the
   opening idea (vary across videos – see the toolbox), and what it deliberately leaves out.
4. **Source errors:** wrong numbers, swapped terms, outdated claims – note the correction.
5. **Additions:** facts not in the source that make it click (real incidents, numbers) – mark
   them as additions.

## Produce `plan/<part>/coverage.md`
A table: source item (with location) → video/section, card id, or exercise question. Every
row must point somewhere. Gaps go to the user with a recommendation (cover / skip and why).

Show the user the video plan (titles + promises, 5–10 lines) and wait for approval before
scripts are written – changing a plan is cheap, changing recorded videos is not.
