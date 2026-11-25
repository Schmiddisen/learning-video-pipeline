# Developing the Learning Video Pipeline

Two layers: `src/lvp/` (engine, Python/Manim) and `plugin/` (Claude Code plugin: skills,
agents, references). `.claude-plugin/marketplace.json` makes this repo its own marketplace.

- Python via uv: `uv sync`, `uv run pytest`, `uv run ruff check .`, `uv run ruff format .`.
- Engine changes must keep the contracts the references describe (`plugin/references/
  scene-api.md`): `LessonScene` helpers, `lvp.toml` keys, CLI names. Update the reference in
  the same commit.
- Test end to end in a scratch project: `uv run lvp-init /tmp/x && cd /tmp/x &&
  uv run --project <repo> lvp-check && LVP_VOICE=silent uv run --project <repo> lvp-build
  videos/v01_example/example.py -q l --fps 15` → must end with "sync verified".
- Never commit course material that isn't ours; example content must be original.
- New lessons from real courses go into `plugin/references/pitfalls.md`.
