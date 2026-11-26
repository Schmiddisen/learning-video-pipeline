# Pitfalls

Read before producing. Each line is a failure that cost a re-render, a re-recording or a
confused viewer in real courses.

## Content
- **Cross-video repetition is the #1 viewer complaint.** Typical: the same derivation
  re-explained in every later video, the same "how big is this number" computed four times,
  the same question asked in four videos. Always run the `review` skill over *all* scripts
  together before recording narration.
- **Questions answered one sentence earlier feel pointless.** Checks ask about the previous
  section; pretests never repeat the hook's on-screen question.
- **Referencing the source** ("the slide also mentions …") breaks the illusion that the video
  is the lesson.
- **Using a term before it is taught** (one video early) – check the order of introduction.
- **Wrong answers in questions** slip in easily; every answer must follow from what the videos
  taught, and the reviewer must recompute every number.

## Narration
- Never pay for narration of an unreviewed script. Draft silent (`LVP_VOICE=silent`), review,
  then `lvp-narrate --pay`.
- `lvp-narrate` and `lvp-check` list **unrecorded lines** (they would play as silence – the sync
  check cannot see a missing recording; a silent placeholder looks like a planned pause).
- TTS reads acronyms in the course language (an English acronym in German narration comes
  out as a German word): add respellings to `[pronunciation]` in `lvp.toml`; longer keys win
  over shorter ones, so `"X-API"` can differ from `"API"`.
- Moving a `<bookmark>` is free (bookmarks are stripped before the recording lookup); changing
  a single word means re-recording that line.
- OpenRouter refuses requests (HTTP 402) before the balance reaches zero. Unrecordable lines
  render silent instead of failing the build; `lvp-narrate` reports them.

## Rendering
- Render drafts at 480p/15 fps (`-q l --fps 15`, ~2 min per 10-min video on 4 cores); 4K only
  locally for the final version.
- Every build ends with a **measured** sync check of the final MP4. "narration x s early/late"
  on a single window: measure the onset before chasing a renderer bug (a window holding only a
  file's quiet lead-in gave a false alarm). "part off by 1 frame" within 1.5 frames is fine.
- Don't edit scene files (or the engine) while `lvp-build` runs: chunks and the final pass
  import them separately.
- Don't run two `lvp-check`s at once in one project: they share `build/*audit.log`.
- Glyphs: a render can look fine on one machine while another shows boxes (e.g. ⊕ on
  Windows without a fallback font). The engine maps missing glyphs to bundled DejaVu – always
  use `label()`, never `Text()`.
- Formulas: the rendering machine may have no LaTeX; commit `tex_cache/` after `lvp-check`.
- Contrast: pale accent text on paper is unreadable on phones; `lvp-critic` catches it.

## Workflow
- Viewers report problems as "2.2 at 9:15: …" – `lvp-locate` maps that to the exact section
  and narration line (the `feedback` skill).
- Keep the source material out of public repos (`.gitignore` covers material PDFs/videos).
- Commit `voice_cache/` (paid narration) and `tex_cache/`; never commit `build/` or `media/`.
- Adding a course to an existing player: the exported `index.html` carries the *new* course's
  title – restore the player's title before publishing. Compare the exported root scripts'
  hashes with the `files` listing first: another session may have published a newer engine
  meanwhile; send only `library.json`, `index.html` and `courses/<slug>/` unless yours is newer.
- Curriculum "additions" need the same number check as scripts: a claimed baseline value
  ("always predicting 0.89 gives 0.39") was wrong and only the scene writer caught it.
