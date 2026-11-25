---
name: setup
description: Start a new learning project or (re)configure one – installs the lvp engine, scaffolds the project and interviews the learner (goal, prior knowledge, depth, language, voice, budget) into learner.md and lvp.toml. Use when the user wants to learn a new topic with videos, says "set up", or no lvp.toml exists yet.
---

# Set up a learning project

The project is a folder with `lvp.toml`. Everything else in this plugin reads `learner.md`
and `lvp.toml` first, so this interview decides how every video, card and question will feel.

## 1. Check the machine (fix or explain what's missing)
- `uv --version` (install: https://docs.astral.sh/uv/), `ffmpeg -version`.
- Manim needs Cairo/Pango (on Windows and macOS the wheels bring them; on Linux install
  `libcairo2-dev libpango1.0-dev`). LaTeX is optional – formulas are cached in `tex_cache/`.
- A narration key: `OPENROUTER_API_KEY` (Gemini TTS, about $0.015 per 1,000 characters ≈ $0.10
  for a 10-minute video). Without it everything works with silent narration.

## 2. Scaffold
If there is no `lvp.toml` in the working directory or a parent:
```bash
uvx --from git+https://github.com/Schmiddisen/learning-video-pipeline lvp-init <folder> --title "<course>" --language <en|de|…>
cd <folder> && uv sync
```
Then `git init` and commit (the project is the user's repo; `voice_cache/` and `tex_cache/` get
committed, source material stays out – see `.gitignore`).

## 3. Interview (short, one round, recommend defaults)
Ask only what you can't infer from the material or the conversation:
1. **Goal and deadline** – exam on a date / project / curiosity.
2. **Prior knowledge** – what they already know well (becomes the source of analogies: a
   programming background → "a probability distribution is like a histogram that sums to one").
3. **Depth** – overview / working knowledge / exam-ready / expert.
4. **Language** of narration and on-screen text; **voice speed** (default 1.15).
5. **Video length** (default 8–12 min, sections of 2–4 min) and **look** (`paper` theme default,
   `night`, `terminal`).
6. **Budget** – max spend per command (default $0.50) and overall.
7. **Taste** – anything they love or hate in explainer videos (pace, humour, history, maths).

Write the answers into `learner.md` (free text, concrete) and the settings into `lvp.toml`.
Confirm in two lines what you set, then suggest the next step: put sources into `material/`
and run the `ingest` skill (or `lecture` for the whole pipeline).
