# The evidence behind the design

Why the videos contain guess-first questions, delayed checks and closing recall questions,
and why the companion material looks the way it does. Effect sizes are from meta-analyses
where available. Most evidence comes from classroom and lab studies with text or recorded
lectures; transferring it to narrated animations is plausible but not directly tested.

## Adopted

| Technique | Evidence | In the pipeline |
|---|---|---|
| **Pretesting** – a question before the content | St. Hilaire et al. 2024 (k = 97): g = 0.54 for the asked content, g = 0.04 for other content; Boustani & Shanks 2022: g = 0.34 | `pretest()` at the end of each hook, on the video's core concepts |
| **Interpolated testing** – retrieval questions between segments, with feedback | Szpunar, Khan & Schacter 2013: 90 % vs 68 % on the final test, d = 1.38, mind-wandering halved; Chan, Meissner & Davis 2018: g = 0.44 (video/text 0.77); Yang et al. 2021 (222 classroom studies): g ≈ 0.50, 0.54 with feedback; cloze 0.77 > short answer 0.64 > MC 0.57 > free recall 0.24 | `checkpoint(q, a)` after each section, asking about the previous one |
| **Segmenting**, system-paced | Rey et al. 2019: g ≈ 0.32–0.36; designer-set segments 0.41 vs learner-set 0.20 | sections of 2–4 min, chapter cards, chapter markers in the MP4 |
| **Interleaving** of problem types (not vocabulary) | Brunmair & Richter 2019: g = 0.42 overall, maths 0.34, word lists −0.39 | mixed practice sheets across parts |
| **Spaced repetition** with a modern scheduler | FSRS benchmark (srs-benchmark, ~10k collections) predicts forgetting clearly better than SM-2; Anki manual: 20 new cards/day ≈ 200 reviews/day | Anki decks sized to the review budget; FSRS at 0.90 retention recommended |
| **Playback speed** up to ~1.5× | Murphy et al. 2022; Tharumalingam et al. 2025 (24 studies): small, often non-significant costs up to 1.5× | narration at 1.15× by default, adjustable |

## Production techniques (measured with model judges, not learners)

- **Discrete anchor grid** as the placement API (Code2Video ablation: element layout score
  45 → 83). → `place(m, "B2")`.
- **Deterministic layout checks first**; vision-model critics miss short occlusions
  (Manimator: automatic layout score 0.853 vs 0.52 from humans). → `lvp-check` is the gate,
  `lvp-critic` a second opinion.
- **Planning before code** matters most (Code2Video: −41 quiz points without the planner).
  → curriculum and beats before scenes.
- Retry with the error text helps; retrieval over the Manim docs did not help consistently
  (TheoremExplainAgent).

## Do generated videos help people learn?

Direct evidence is thin. The largest study with real learners (LLM2Manim, 100 students,
within-subject, expert review in the loop) found 83 % vs 78 % against slides (d = 0.67 for
the gain), not yet replicated. For orientation: video *replacing* other teaching g = 0.28,
video *added* to teaching g = 0.80 (Noetel et al. 2021). Hence the design: videos plus
cards plus exercise companions, and – on the roadmap – a simple pre/post quiz so each learner
can see whether it works for their material.

## Not adopted

More critic rounds, retrieval over Manim docs, learner personas simulated by models,
talking-head avatars, pixel video models (they cannot keep a formula or a protocol step
exact).
