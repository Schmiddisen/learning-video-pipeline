---
name: companion
description: Build the material around the videos – Anki flashcards (YAML → .apkg in the current format, sized to the review budget), exercise companions with graded hints, mixed practice across parts, and thinking questions. Use after videos for a part exist, when the user starts exercises, or asks for cards or practice.
---

# Companion material

Read `learner.md`, the part's coverage map and `../../references/didactics.md` (companion).

## Anki cards – `cards/NN_part.yaml`
```yaml
deck: "Course::02 Part title"
cards:
  - id: p2-base-rate             # never change an id: re-imports update the card
    tags: [v2.2, bayes]
    front: A 99 % accurate test is positive for a 1-in-1000 disease. Why is "sick" still unlikely?
    back: False positives from the 999 healthy people outnumber the one true positive.
  - id: p2-bayes-formula
    cloze: "Bayes: P(A|B) = {{c1::P(B|A) · P(A) / P(B)}}"
```
- One idea per card; "why / what happens if" over definitions; cloze for formulas.
- Size to the budget: ~30–45 cards per 90-minute source (FSRS at 0.90 retention:
  20 new/day ≈ 200 reviews/day). Prune rather than pad.
- `uv run lvp-anki --check` (validate) then `uv run lvp-anki` → `cards/*.apkg` + `all_decks.apkg`.
- Tell the user: import `all_decks.apkg` (desktop or AnkiDroid), enable FSRS, desired retention
  0.90, bury new and review siblings on.

## Exercise companions – `exercises/NN_companion.md`
For each task of the course's exercises: **Hint 1** (direction), **Hint 2** (method or code
skeleton), then the **worked solution**, each in `<details>`. Check every number. Note
errors in the official sheet.

## Mixed practice – `exercises/mixed_AA_BB.md`
10–12 questions that interleave problem types from several parts ("first decide which tool or
definition applies"), answers in `<details>`.
