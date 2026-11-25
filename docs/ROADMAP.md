# Roadmap

Roughly in order. ✓ = done.

## Workflow
- ✓ **One-step feedback** – `lvp-locate` maps "video at mm:ss" to the exact narration line;
  the `feedback` skill fixes, re-records and re-verifies.
- ✓ **Review gate** – the `review` skill reads all scripts together before any narration is
  paid for (`lvp-dump`).
- ✓ **One command per part** – the `lecture` skill with two approval gates.
- **Skimmable draft page** per part: narration, question cards and one frame per section on a
  single page, so the learner catches repetition and weak questions in two minutes instead of
  after watching.
- **Incremental renders** – re-render only sections whose code or narration changed.
- **Progress and analytics** – which videos were watched, which checks were answered wrong,
  which Anki cards lapse; feed weak spots back into the next revision.
- **Quality budget per video** – one config line for max narration spend and render time.

## Learning
- ✓ **Interactive player as a Claude artifact** (`lvp-player` + the `player` skill) – live
  transcript, the video's questions as real input with Claude's feedback, draw on the frame and
  ask Claude with full context, progress saved per learner.
- **Spaced re-watching** – 90-second "replays" of each video's key moments + recall
  questions at day 3 and day 10, generated from the existing scenes.
- **Exam mode** – mixed practice across all parts in exam style, seeded by weak cards.
- **Personal analogies** – the learner profile's prior knowledge drives examples.
- Measure learning: pre/post quiz per video, optional A/B against reading the source.

## Engine
- **More prop packs** (math, code, networking, biology); each course leaves a richer kit.
- **Content templates + router** – algorithm animation, proof steps, code walkthrough,
  timeline; picked per section.
- Shareable courses: a course is a git repo; videos replace the source.
- More TTS providers behind the same cache (ElevenLabs, OpenAI).
