# Related work

Open pipelines that turn documents or topics into explainer videos, and what this project
takes from them.

| Project | Idea | Used here |
|---|---|---|
| **Code2Video** (Show Lab NUS, 2025; github.com/showlab/Code2Video) | Planner → Coder → Critic for Manim; a 6×6 *visual anchor grid* instead of raw coordinates; "TeachQuiz" scores a video by how much a model learns from it | anchor grid (`place`), planning before code |
| **TheoremExplainAgent** (TIGER-Lab, ACL 2025) | planning agent + coding agent with retrieval over the Manim docs; main failure: hallucinated API | retry with error text; a written scene API reference instead of doc retrieval |
| **PhysicsSolutionAgent** (2026) | solution → plan → code, one screenshot-based refinement round | vision critic as a second opinion |
| **Chalkboard** (github.com/nicglazkov/chalkboard) | inline cue markers before words, pacing baked into the audio, fact validator, layout dry run, visual QA, chapter markers embedded in the MP4 | chapter markers; the dry run is `lvp-check` |
| **VideoAgent** (2025) | paper → personalised video; layout-aware PDF parsing (Docling); mixes slides and animations by content density | idea for a content-type router (roadmap) |
| **ExplainFlow** | every claim linked to its source passage | coverage map per part |
| **LLM2Manim** (2026) | human-in-the-loop, pedagogy-aware planning; the one sizeable learner study | approval gates (plan, cost) |
| **Paper2Video / PresentAgent / TeachMaster** | slides + narration + cursor or talking head; per-section mode routing | – (roadmap: cursor highlights synced to words) |

What this project adds that the others don't report: sync **measured** on the final file
(not assumed), a frame-exact render clock, a narration cache with spend caps, a review pass
over *all* scripts of a course for cross-video repetition and question quality, retrieval
practice placed by the evidence (pretest, lagged checks, recall), and companion material
(spaced-repetition decks, graded exercise hints).
