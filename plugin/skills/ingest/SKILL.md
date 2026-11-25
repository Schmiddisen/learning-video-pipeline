---
name: ingest
description: Turn source material (PDF slides, papers, book chapters, lecture recordings, transcripts, web pages, notes) into compact digests Claude can work from – text, slide contact sheets, transcripts and an index with token costs. Use after setup when new material lands in material/, or when the user hands over sources.
---

# Ingest material

Goal: Claude never reads raw 100-page PDFs or hour-long transcripts repeatedly. Everything
gets digested once into `material/digest/`, with `material/digest/INDEX.md` listing each file
and its size in tokens.

1. **Collect** sources into `material/` (subfolders by kind: `slides/`, `recordings/`,
   `exercises/`, `notes/`). Web pages: save as Markdown. Remind the user that copyrighted
   material must not be pushed to a public repo (`.gitignore` excludes PDFs and videos).
2. **Text digests:** `uv sync --extra material` then `uv run lvp-digest` – writes one Markdown
   file per PDF (per page, with "mostly graphic – render if needed" markers) and the index.
3. **Look at every slide:** text extraction misses diagrams, tables and formulas. Render
   contact sheets with `uv run lvp-digest sheets <pdf>` (2×2 pages per image) and read them.
   Note anything visual in the digest.
4. **Recordings:** `uv sync --extra transcribe` then
   `uv run lvp-transcribe material/recordings --language <xx>` (faster-whisper; GPU if
   available, `--extra gpu`). Put course vocabulary into `material/vocabulary.txt` first – it
   steers the spelling of technical terms. Transcripts carry timestamps; exam hints ("this is
   important", "will be in the exam") are the most valuable lines – collect them.
5. **Summaries:** for each source write a 10–20 line summary into
   `material/digest/summaries/` (use a cheap subagent for long sources).
6. Report: what was ingested, total size, anything unreadable, and the exam hints found.
