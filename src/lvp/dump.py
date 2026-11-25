"""lvp-dump: every narration line and every question of the course, in viewing order.

The input for the cross-video review (repetition, weak questions) – one file instead of 18
scene sources.

    uv run lvp-dump > build/all_scripts.md
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

from lvp.project import ROOT, VIDEOS

_BOOKMARK = re.compile(r"<bookmark[^>]*/>")


def _string(node: ast.expr) -> str:
    """A string literal, or several joined with + (no Manim import: stdout stays clean)."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return _string(node.left) + _string(node.right)
    if isinstance(node, ast.JoinedStr):
        raise ValueError("f-string")
    raise ValueError(type(node).__name__)


def _items(cls: ast.ClassDef) -> list[tuple[int, str, str]]:
    items: list[tuple[int, str, str]] = []

    def text(node) -> str | None:
        try:
            return _string(node)
        except ValueError:
            return None

    for n in ast.walk(cls):
        if (
            isinstance(n, ast.Assign)
            and isinstance(n.value, ast.List)
            and any(getattr(t, "id", "") == "qs" for t in n.targets)  # local recall lists
        ):
            items += [(e.lineno, "RECALL", s) for e in n.value.elts if (s := text(e))]
        if not isinstance(n, ast.Call):
            continue
        name = getattr(n.func, "attr", getattr(n.func, "id", ""))
        if name == "voiceover" and n.args and (s := text(n.args[0])):
            items.append((n.lineno, "SAY", s))
        elif name == "title_card":
            items += [(n.lineno, "SAY", s) for k in n.keywords if k.arg == "say"
                      if (s := text(k.value))]  # fmt: skip
        elif name == "question" and n.args and (s := text(n.args[0])):
            items.append((n.lineno, "Q-ONSCREEN", s))
        elif name == "checkpoint" and len(n.args) >= 2:
            q, a = text(n.args[0]), text(n.args[1])
            if q:
                items.append((n.lineno, "CHECK", f"{q}  →  {a}"))
        elif name in ("pretest", "recall") and n.args and isinstance(n.args[0], ast.List):
            items += [(e.lineno, name.upper(), s) for e in n.args[0].elts if (s := text(e))]
    return sorted(items, key=lambda x: x[0])  # stable: same-line items keep their order


def dump(files: list[Path]) -> str:
    out: list[str] = []
    for f in files:
        tree = ast.parse(f.read_text(encoding="utf-8"))
        title = (ast.get_docstring(tree) or f.stem).splitlines()[0]
        rel = f.resolve().relative_to(ROOT) if f.resolve().is_relative_to(ROOT) else f
        out.append(f"\n######## {rel} — {title}")
        for cls in tree.body:
            if isinstance(cls, ast.ClassDef) and re.match(r"S\d", cls.name):
                out.append(f"\n## {cls.name}")
                for _, kind, t in _items(cls):
                    out.append(f"[{kind}] " + _BOOKMARK.sub("", t).replace("\n", " / "))
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("files", nargs="*", type=Path)
    args = ap.parse_args(argv)
    files = args.files or sorted(VIDEOS.glob("v*/*.py"))
    print(dump(files), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
