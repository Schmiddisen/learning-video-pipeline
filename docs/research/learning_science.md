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

## The study player: what each feature is for

| Feature | Principle | Notes |
|---|---|---|
| The video stops at its own questions and takes a typed answer | retrieval practice with feedback; typing commits harder than "thinking about it" | answer shown after the attempt, then the video continues at the answer |
| Claude grades, links the moment to rewatch, offers one follow-up | elaborative feedback beats right/wrong (Shute 2008); a second retrieval attempt after feedback | one follow-up only – no endless drilling |
| "How sure?" before grading | hypercorrection: confident errors, once corrected, are remembered best (Butterfield & Metcalfe 2001) | feedback names the tempting wrong idea when a confident answer is wrong |
| Explain it back after each video | self-explanation / generative learning (Chi et al. 1994; Fiorella & Mayer 2016) | Claude lists solid, missing (with moments) and wrong |
| New practice question for the current part | testing new cases, not repeating sentences (transfer-appropriate processing) | never a definition recall |
| Flashcards unlock at the moment that teaches them; the video's checks return as cards | spacing + retrieval; no card before the idea was met | FSRS scheduling, retention 0.90 |
| Every card and miss links back to its video moment | dual coding; re-encoding with the original picture | "Watch the moment" on every card |
| Concept map (recall per concept tag) | metacognitive monitoring; learners misjudge what they know | ranked weakest first, one click to practise it |
| Labs designed per section | learning by doing; worked example → faded steps via graded hints | Claude's lab is shown only if its own solution passes its checks |
| Exam practice across videos | interleaving across topics (see above) + test-like retrieval | weighted to weak and long-ago videos |
| Socratic mode, mark-and-ask | the learner sets the question; guided discovery over telling when wanted | the frame and the marks go to Claude with the moment |
| Coach (outside the player) | closing the loop: material that fails many learners gets fixed | separates learner gaps from material problems |

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
video *added* to teaching g = 0.80 (Noetel et al. 2021). Hence the design: videos are
never the whole lesson – they come with retrieval, spacing, explanation and practice in one
place (the study player), and the coach checks with each learner's real data whether it
works for their material.

## Not adopted

More critic rounds, retrieval over Manim docs, learner personas simulated by models,
talking-head avatars, pixel video models (they cannot keep a formula or a protocol step
exact).
