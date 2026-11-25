"""Turn source material (PDFs, zips, transcripts) into compact text digests.

The digests are what Claude reads instead of the raw material, to keep context small:

* PDFs (slides, papers, exercise sheets) -> one Markdown file per PDF, text per page,
  repeated headers/footers removed, diagram-heavy pages flagged so they can be rendered as
  images only when needed
* transcripts -> plain paragraphs of about one minute with one timestamp each
* ``material/digest/INDEX.md`` -> what exists and roughly how many tokens each file costs

Usage:
    uv run --extra material lvp-digest            # build all digests
    uv run --extra material lvp-digest page slides_01.pdf 7     # render one page
    uv run --extra material lvp-digest sheets slides_01.pdf     # 2x2 contact sheets
"""

from __future__ import annotations

import argparse
import json
import re
import zipfile
from collections import Counter
from pathlib import Path

from lvp.project import MATERIAL, ROOT

OUT = MATERIAL / "digest"
TRANSCRIPTS = MATERIAL / "transcripts"
PAGE_RENDERS = ROOT / "build" / "pages"

TOKENS_PER_WORD = 1.6  # rough average (English ~1.3, German ~1.7)


def _tokens(text: str) -> int:
    return int(len(text.split()) * TOKENS_PER_WORD)


def _clean(text: str) -> list[str]:
    lines = [re.sub(r"\s+", " ", ln).strip() for ln in text.splitlines()]
    out: list[str] = []
    bullet = False
    for ln in lines:
        if not ln or re.fullmatch(r"\d{1,3}", ln):
            continue
        if ln in {"•", "▪", "–", "-", "o", "◦"}:  # bullet glyph on its own line
            bullet = True
            continue
        out.append(f"- {ln}" if bullet else ln)
        bullet = False
    return out


def digest_pdf(pdf: Path) -> str:
    import pymupdf

    doc = pymupdf.open(pdf)
    pages = [_clean(p.get_text()) for p in doc]
    # Lines repeated on many pages are headers/footers (course name, author, date).
    counts = Counter(ln for page in pages for ln in set(page))
    boiler = {ln for ln, n in counts.items() if len(pages) >= 5 and n >= 0.4 * len(pages)}

    out = [f"# {pdf.stem}", ""]
    if boiler:
        out += ["Removed on every page: " + " | ".join(sorted(boiler)), ""]
    for i, (page, raw) in enumerate(zip(pages, doc, strict=True), 1):
        body = [ln for ln in page if ln not in boiler]
        out.append(f"## S. {i}")
        if len(raw.get_images()) and len(" ".join(body).split()) < 40:
            out.append(f"[mostly graphic - render if needed: lvp-digest page '{pdf.name}' {i}]")
        out += body
        out.append("")
    return "\n".join(out)


def digest_zip(zf: Path) -> str:
    with zipfile.ZipFile(zf) as z:
        names = [f"- {i.filename} ({i.file_size} B)" for i in z.infolist() if not i.is_dir()]
    return f"# {zf.parent.name}/{zf.name}\n\n" + "\n".join(names) + "\n"


def digest_transcript(js: Path, block_seconds: float = 60.0) -> str:
    data = json.loads(js.read_text(encoding="utf-8"))
    out, buf, start = [f"# Transkript {js.stem}", ""], [], None
    for seg in data["segments"]:
        if start is None:
            start = seg["start"]
        buf.append(seg["text"])
        if seg["end"] - start >= block_seconds:
            out.append(f"[{int(start // 60):02}:{int(start % 60):02}] " + " ".join(buf))
            buf, start = [], None
    if buf:
        out.append(f"[{int(start // 60):02}:{int(start % 60):02}] " + " ".join(buf))
    return "\n\n".join(out) + "\n"


def build() -> None:
    index = ["# Digest index", "", "| File | ≈ tokens |", "|---|---|"]
    jobs: list[tuple[Path, str]] = []
    # every PDF and zip anywhere under material/ (except the digests), mirrored folder layout
    sources = (p for p in MATERIAL.rglob("*") if OUT not in p.parents and p.is_file())
    for src in sorted(sources):
        rel = src.relative_to(MATERIAL)
        if src.suffix.lower() == ".pdf":
            jobs.append((OUT / rel.with_suffix(".md"), digest_pdf(src)))
        elif src.suffix.lower() == ".zip":
            jobs.append((OUT / rel.with_name(f"{src.stem}_contents.md"), digest_zip(src)))
        elif src.suffix.lower() == ".json" and TRANSCRIPTS in src.parents:
            jobs.append((OUT / rel.with_suffix(".md"), digest_transcript(src)))

    for path, text in jobs:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
        index.append(f"| `{path.relative_to(OUT).as_posix()}` | {_tokens(text):,} |")
    (OUT / "INDEX.md").write_text("\n".join(index) + "\n", encoding="utf-8", newline="\n")
    print(f"Wrote {len(jobs)} digests to {OUT}")


def render_page(pdf_name: str, page: int, width: int = 1100) -> Path:
    import pymupdf

    matches = list(MATERIAL.rglob(pdf_name)) or [Path(pdf_name)]
    doc = pymupdf.open(matches[0])
    p = doc[page - 1]
    pix = p.get_pixmap(matrix=pymupdf.Matrix(width / p.rect.width, width / p.rect.width))
    PAGE_RENDERS.mkdir(parents=True, exist_ok=True)
    out = PAGE_RENDERS / f"{Path(pdf_name).stem}_S{page}.png"
    pix.save(out)
    print(out)
    return out


def render_sheets(pdf_name: str, per_sheet: int = 4, slide_width: int = 800) -> list[Path]:
    """Render all pages as 2x2 contact sheets, so slides can be looked at cheaply."""
    import pymupdf
    from PIL import Image, ImageDraw

    matches = list(MATERIAL.rglob(pdf_name)) or [Path(pdf_name)]
    doc = pymupdf.open(matches[0])
    imgs = []
    for p in doc:
        z = slide_width / p.rect.width
        pix = p.get_pixmap(matrix=pymupdf.Matrix(z, z))
        imgs.append(Image.frombytes("RGB", (pix.width, pix.height), pix.samples))
    h = max(i.height for i in imgs)
    PAGE_RENDERS.mkdir(parents=True, exist_ok=True)
    out = []
    for start in range(0, len(imgs), per_sheet):
        sheet = Image.new("RGB", (slide_width * 2 + 10, h * 2 + 10), "white")
        draw = ImageDraw.Draw(sheet)
        for k, im in enumerate(imgs[start : start + per_sheet]):
            x, y = (k % 2) * (slide_width + 10), (k // 2) * (h + 10)
            sheet.paste(im, (x, y))
            draw.rectangle([x, y, x + 64, y + 30], fill="black")
            draw.text((x + 6, y + 8), f"S. {start + k + 1}", fill="white")
        path = PAGE_RENDERS / f"{Path(pdf_name).stem}_sheet{start // per_sheet + 1:02}.png"
        sheet.save(path)
        out.append(path)
        print(path)
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd")
    pg = sub.add_parser("page", help="render one PDF page as PNG")
    pg.add_argument("pdf")
    pg.add_argument("page", type=int)
    sh = sub.add_parser("sheets", help="render all pages as 2x2 contact sheets")
    sh.add_argument("pdf")
    args = ap.parse_args(argv)
    if args.cmd == "page":
        render_page(args.pdf, args.page)
    elif args.cmd == "sheets":
        render_sheets(args.pdf)
    else:
        build()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
