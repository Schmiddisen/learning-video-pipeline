"""Build Anki decks (.apkg) from lernen/karten/*.yaml.

    uv run lvp-anki              # all decks → lernen/karten/<name>.apkg
    uv run lvp-anki --check      # validate only

Each card's ``id`` becomes its Anki GUID, so re-importing an updated deck updates the cards and
keeps the review history.
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

import genanki
import yaml

from lvp.project import CARDS

SRC = CARDS
OUT = SRC  # next to the YAML and committed: the phone gets the decks from git

# Fixed IDs: changing them would make Anki treat the note types as new ones.
BASIC_ID, CLOZE_ID = 1_841_200_001, 1_841_200_002  # stable: re-imports update cards
CSS = """
.card { font-family: "IBM Plex Serif", Georgia, serif; font-size: 21px; line-height: 1.45;
        color: #2b2620; background: #f4efe4; text-align: left; max-width: 40em; margin: auto;
        padding: 0.6em; }
.nightMode.card, .night_mode .card { color: #e9e2d3; background: #22201c; }
.extra { margin-top: 1em; font-size: 0.85em; color: #6b6153; border-left: 3px solid #b08d57;
         padding-left: 0.6em; }
.nightMode .extra, .night_mode .extra { color: #b9ae9a; }
.cloze { font-weight: bold; color: #b5523b; }
.tag { font-size: 0.7em; color: #9a8f7c; }
"""
BASIC = genanki.Model(
    BASIC_ID,
    "LVP Basic",
    fields=[{"name": "Front"}, {"name": "Back"}, {"name": "Extra"}],
    templates=[
        {
            "name": "Card",
            "qfmt": "{{Front}}",
            "afmt": '{{FrontSide}}<hr id="answer">{{Back}}'
            '{{#Extra}}<div class="extra">{{Extra}}</div>{{/Extra}}',
        }
    ],
    css=CSS,
)
CLOZE = genanki.Model(
    CLOZE_ID,
    "LVP Cloze",
    fields=[{"name": "Text"}, {"name": "Extra"}],
    templates=[
        {
            "name": "Cloze",
            "qfmt": "{{cloze:Text}}",
            "afmt": '{{cloze:Text}}{{#Extra}}<div class="extra">{{Extra}}</div>{{/Extra}}',
        }
    ],
    css=CSS,
    model_type=genanki.Model.CLOZE,
)


def _html(text: str) -> str:
    """Plain text → HTML, keeping cloze markers intact."""
    return html.escape(str(text).strip(), quote=False).replace("\n", "<br>")


def _deck_id(name: str) -> int:
    """Stable id below 2**31 (some AnkiDroid code paths treat deck ids as 32-bit)."""
    return int(genanki.guid_for(name).encode().hex()[:12], 16) % (1 << 30) + (1 << 29)


def load(path: Path) -> tuple[str, list[dict]]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    deck, cards = data["deck"], data["cards"]
    errors, seen = [], set()
    for i, c in enumerate(cards):
        where = f"{path.name} card {i} ({c.get('id', '?')})"
        if "id" not in c:
            errors.append(f"{where}: missing id")
        elif c["id"] in seen:
            errors.append(f"{where}: duplicate id")
        seen.add(c.get("id"))
        if "cloze" in c:
            if not re.search(r"\{\{c\d+::", c["cloze"]):
                errors.append(f"{where}: cloze without {{{{c1::…}}}}")
        elif not (c.get("front") and c.get("back")):
            errors.append(f"{where}: needs front + back (or cloze)")
    if errors:
        raise SystemExit("\n".join(errors))
    return deck, cards


def build(path: Path) -> Path:
    deck_name, cards = load(path)
    deck = genanki.Deck(_deck_id(deck_name), deck_name)
    for c in cards:
        tags = [str(t).replace(" ", "_") for t in c.get("tags", [])]
        guid = genanki.guid_for(deck_name, c["id"])
        extra = _html(c.get("extra", ""))
        if "cloze" in c:
            note = genanki.Note(CLOZE, [_html(c["cloze"]), extra], tags=tags, guid=guid)
        else:
            fields = [_html(c["front"]), _html(c["back"]), extra]
            note = genanki.Note(BASIC, fields, tags=tags, guid=guid)
        deck.add_note(note)
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f"{path.stem}.apkg"
    legacy = out.with_suffix(".legacy.apkg")
    genanki.Package(deck).write_to_file(legacy)
    _modernize(legacy, out)
    legacy.unlink(missing_ok=True)
    return out


def bundle(packages: list[Path], out: Path) -> None:
    """All decks in one package (one import on the phone)."""
    import tempfile

    from anki.collection import (
        Collection,
        ExportAnkiPackageOptions,
        ImportAnkiPackageOptions,
        ImportAnkiPackageRequest,
    )

    with tempfile.TemporaryDirectory() as tmp:
        col = Collection(str(Path(tmp) / "collection.anki2"))
        try:
            for pkg in packages:
                col.import_anki_package(
                    ImportAnkiPackageRequest(
                        package_path=str(pkg), options=ImportAnkiPackageOptions()
                    )
                )
            col.export_anki_package(
                out_path=str(out),
                options=ExportAnkiPackageOptions(
                    with_scheduling=False, with_deck_configs=False, with_media=True, legacy=False
                ),
                limit=None,
            )
        finally:
            col.close()


def _modernize(src: Path, out: Path) -> None:
    """Re-export through Anki's own backend: genanki writes the 2014 package format
    (schema 11), which crashed AnkiDroid on import. Anki's exporter writes the current format,
    exactly like a deck exported from Anki Desktop."""
    import tempfile

    from anki.collection import (
        Collection,
        ExportAnkiPackageOptions,
        ImportAnkiPackageOptions,
        ImportAnkiPackageRequest,
    )

    with tempfile.TemporaryDirectory() as tmp:
        col = Collection(str(Path(tmp) / "collection.anki2"))
        try:
            col.import_anki_package(
                ImportAnkiPackageRequest(package_path=str(src), options=ImportAnkiPackageOptions())
            )
            col.fix_integrity()
            col.export_anki_package(
                out_path=str(out),
                options=ExportAnkiPackageOptions(
                    with_scheduling=False, with_deck_configs=False, with_media=True, legacy=False
                ),
                limit=None,
            )
        finally:
            col.close()


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Build Anki decks from lernen/karten/*.yaml")
    ap.add_argument("files", nargs="*", type=Path)
    ap.add_argument("--check", action="store_true", help="only validate the YAML")
    args = ap.parse_args(argv)
    built, total = [], 0
    for path in args.files or sorted(SRC.glob("*.yaml")):
        deck, cards = load(path)
        total += len(cards)
        if args.check:
            print(f"[✓] {path.name}: {len(cards)} cards ({deck})")
        else:
            built.append(build(path))
            print(f"[✓] {built[-1]}  ({len(cards)} cards)")
    if len(built) > 1 and not args.files:
        out = OUT / "all_decks.apkg"
        bundle(built, out)
        print(f"[✓] {out}  ({total} cards, all decks in one file)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
