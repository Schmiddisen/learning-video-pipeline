"""Generic props for any topic: icons, definition boxes, packets, ticks, crosses, questions."""

from __future__ import annotations

from manim import (
    DOWN,
    LEFT,
    RIGHT,
    Dot,
    Ellipse,
    Line,
    Polygon,
    Rectangle,
    RoundedRectangle,
    VGroup,
    VMobject,
)

from lvp.style import ACCENT, BG, FG, MUTED, NEGATIVE, POSITIVE, Card, label

OK = POSITIVE


class EyeIcon(VGroup):
    def __init__(self, color: str = NEGATIVE, **kw) -> None:
        outline = Ellipse(width=0.5, height=0.26, color=color, stroke_width=4)
        pupil = Dot(radius=0.07, color=color)
        super().__init__(outline, pupil, **kw)


class Badge(VGroup):
    """Small pill with text, e.g. 'passive' / 'active' next to a character."""

    def __init__(self, text: str, color: str = NEGATIVE, **kw) -> None:
        t = label(text, size=20, color=color)
        box = RoundedRectangle(
            corner_radius=0.15, width=t.width + 0.3, height=t.height + 0.18, color=color
        ).set_stroke(width=2)
        t.move_to(box)
        super().__init__(box, t, **kw)


def tick(color: str = OK, size: float = 0.35) -> VMobject:
    return VGroup(
        Line([-0.5, 0, 0], [-0.15, -0.4, 0], color=color, stroke_width=8),
        Line([-0.15, -0.4, 0], [0.55, 0.45, 0], color=color, stroke_width=8),
    ).scale(size)


def cross(color: str = NEGATIVE, size: float = 0.35) -> VMobject:
    return VGroup(
        Line([-0.45, -0.45, 0], [0.45, 0.45, 0], color=color, stroke_width=8),
        Line([-0.45, 0.45, 0], [0.45, -0.45, 0], color=color, stroke_width=8),
    ).scale(size)


def bolt(color: str = ACCENT, height: float = 0.6) -> VMobject:
    pts = [
        [0.1, 0.5, 0],
        [-0.15, 0.0, 0],
        [0.05, 0.0, 0],
        [-0.1, -0.5, 0],
        [0.2, 0.1, 0],
        [0, 0.1, 0],
    ]
    return Polygon(*pts, color=color, stroke_width=3).set_fill(color, 1).scale_to_fit_height(height)


def _wrap(text: str, width: int) -> str:
    """Greedy word wrap so long definitions break instead of shrinking."""
    lines, cur = [], ""
    for word in text.split():
        if cur and len(cur) + 1 + len(word) > width:
            lines.append(cur)
            cur = word
        else:
            cur = f"{cur} {word}".strip()
    return "\n".join([*lines, cur])


class DefBox(VGroup):
    """Definition box: term on top, one-sentence definition below, colour bar on the left."""

    def __init__(self, term: str, text: str, color: str = FG, width: float = 9.0, **kw) -> None:
        head = label(term, size=34, color=color, weight="BOLD")
        body = label(_wrap(text, 52), size=28, color=FG, line_spacing=0.9)
        inner = VGroup(head, body).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        if inner.width > width - 0.9:
            inner.scale_to_fit_width(width - 0.9)
        box = Rectangle(width=width, height=inner.height + 0.6, color=color, stroke_width=3)
        box.set_fill(BG, 0.92)
        bar = Rectangle(width=0.14, height=box.height, stroke_width=0).set_fill(color, 1)
        bar.move_to(box.get_left() + RIGHT * 0.07)
        inner.move_to(box).align_to(box, LEFT).shift(RIGHT * 0.45)
        super().__init__(box, bar, head, body, **kw)


def fit(mob, margin: float = 0.25):
    """Shift a mobject so it lies fully inside the frame."""
    from manim import config

    hw, hh = config.frame_width / 2 - margin, config.frame_height / 2 - margin
    dx = max(0, -hw - mob.get_left()[0]) - max(0, mob.get_right()[0] - hw)
    dy = max(0, -hh - mob.get_bottom()[1]) - max(0, mob.get_top()[1] - hh)
    return mob.shift([dx, dy, 0])


class Packet(Card):
    """A small numbered packet travelling along a channel."""

    def __init__(self, text: str, color: str = FG, **kw) -> None:
        super().__init__(label(text, size=22, color=color), color=color, pad=0.12, **kw)


def question(text: str, color: str = FG) -> VGroup:
    """A question banner for predict-before-reveal moments."""
    q = label(text, size=30, color=color, slant="ITALIC")
    mark = label("?", size=60, color=ACCENT, weight="BOLD").next_to(q, LEFT, buff=0.3)
    return VGroup(mark, q)


__all__ = [
    "OK",
    "Badge",
    "DefBox",
    "fit",
    "EyeIcon",
    "Packet",
    "bolt",
    "cross",
    "question",
    "tick",
    "MUTED",
]
