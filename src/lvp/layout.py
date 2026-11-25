"""Layout check run after every animation (lvp-check): finds the bugs that so far were only
visible after a render.

* OVERLAP – a text partly covers another text or an icon/shape. Full containment is fine
  (text inside its card, a label on a box); a *partial* overlap is almost always a mistake.
* OFFSCREEN – a text (partly) outside the frame.
* EDGE – a text closer than MARGIN to the frame border (looks clipped on many screens).
* TIGHT – two texts on the same line almost touch (gap < GAP): reads as one word on screen.

Only the state *after* each animation is checked, so cross-fades don't count.
"""

from __future__ import annotations

import numpy as np
from manim import Text, VMobject, config

from lvp.project import BUILD

LOG = BUILD / "layout_audit.log"
TOL = 0.04  # scene units; ignore touching edges
MARGIN = 0.2  # scene units of breathing room to the frame border
GAP = 0.08  # scene units between two texts side by side
SMALL = 1.6  # a group smaller than this (both sides) counts as one prop


def _box(m) -> np.ndarray:
    return np.array([m.get_left()[0], m.get_bottom()[1], m.get_right()[0], m.get_top()[1]])


def _visible(m) -> bool:
    fam = m.family_members_with_points()
    return bool(fam) and any(
        s.get_fill_opacity() > 0.05 or (s.get_stroke_opacity() > 0.05 and s.get_stroke_width() > 0)
        for s in fam
    )


def _inter(a: np.ndarray, b: np.ndarray) -> float:
    w = min(a[2], b[2]) - max(a[0], b[0])
    h = min(a[3], b[3]) - max(a[1], b[1])
    return w * h if w > TOL and h > TOL else 0.0


def _contains(outer: np.ndarray, inner: np.ndarray) -> bool:
    return (
        outer[0] - TOL <= inner[0]
        and outer[1] - TOL <= inner[1]
        and outer[2] + TOL >= inner[2]
        and outer[3] + TOL >= inner[3]
    )


def _name(m) -> str:
    return f"'{m.text[:30]}'" if isinstance(m, Text) else type(m).__name__


def check(scene, ignore: set[int]) -> None:
    texts, shapes = [], []
    text_parts: set[int] = set()
    for top in scene.mobjects:
        if id(top) in ignore:
            continue
        for m in top.get_family():
            if isinstance(m, Text) and m.text.strip():
                if _visible(m):
                    texts.append(m)
                text_parts.update(id(x) for x in m.get_family())
    for top in scene.mobjects:
        if id(top) in ignore:
            continue
        for m in top.get_family():
            if (
                isinstance(m, VMobject)
                and not m.submobjects
                and id(m) not in text_parts
                and m.has_points()
                and _visible(m)
            ):
                shapes.append(m)

    # parts of one small prop (packet, avatar, badge) are designed together: never report them
    parent: dict[int, object] = {}
    for top in scene.mobjects:
        for m in top.get_family():
            for sub in m.submobjects:
                parent[id(sub)] = m

    def small_groups(m) -> set[int]:
        out, p = set(), parent.get(id(m))
        while p is not None:
            if p.width < SMALL and p.height < SMALL:
                out.add(id(p))
            p = parent.get(id(p))
        return out

    seen = scene.__dict__.setdefault("_layout_seen", set())
    t = float(scene.renderer.time)
    w, h = config.frame_width / 2, config.frame_height / 2
    lines = []
    boxes = {id(m): _box(m) for m in texts + shapes}
    for i, a in enumerate(texts):
        ba = boxes[id(a)]
        if ba[0] < -w - TOL or ba[2] > w + TOL or ba[1] < -h - TOL or ba[3] > h + TOL:
            key = ("off", a.text)
            if key not in seen:
                seen.add(key)
                lines.append(f"OFFSCREEN {_name(a)} at {t:.1f}s")
        elif ba[0] < -w + MARGIN or ba[2] > w - MARGIN or ba[1] < -h + MARGIN or ba[3] > h - MARGIN:
            key = ("edge", a.text)
            if key not in seen:
                seen.add(key)
                lines.append(f"EDGE      {_name(a)} at {t:.1f}s")
        for b in texts[i + 1 :]:
            bb = boxes[id(b)]
            v = min(ba[3], bb[3]) - max(ba[1], bb[1])  # vertical overlap
            gap = max(ba[0], bb[0]) - min(ba[2], bb[2])  # horizontal gap
            if v > 0.5 * min(ba[3] - ba[1], bb[3] - bb[1]) and -TOL < gap < GAP:
                if small_groups(a) & small_groups(b) or parent.get(id(a)) is parent.get(id(b)):
                    continue
                key = ("tight", a.text, b.text)
                if key not in seen:
                    seen.add(key)
                    lines.append(f"TIGHT     {_name(a)} × {_name(b)} at {t:.1f}s")
        for b in texts[i + 1 :] + shapes:
            bb = boxes[id(b)]
            area = _inter(ba, bb)
            if not area or _contains(ba, bb) or _contains(bb, ba):
                continue
            if small_groups(a) & small_groups(b):
                continue
            # tiny shapes overlapping a big text (or vice versa) by a sliver: still report
            key = ("ov", a.text, _name(b))
            if key in seen:
                continue
            seen.add(key)
            lines.append(f"OVERLAP   {_name(a)} × {_name(b)} at {t:.1f}s")
    if lines:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOG.open("a", encoding="utf-8") as f:
            for line in lines:
                f.write(f"{type(scene).__name__}: {line}\n")
