"""Cryptography pack: Alice, Bob and Eve, keys, a bank, the public channel.

from lvp.packs.crypto import alice, bob, eve, KeyIcon, Channel, ALICE, EVE, SECRET
"""

from __future__ import annotations

from manim import (
    DOWN,
    LEFT,
    ORIGIN,
    RIGHT,
    UP,
    Circle,
    DashedLine,
    Line,
    Rectangle,
    Triangle,
    VGroup,
)

from lvp.i18n import t
from lvp.style import (
    ACCENT,
    MUTED,
    NEGATIVE,
    POSITIVE,
    PRIMARY,
    SPECIAL,
    TEAL,
    THEME,
    Person,
    label,
)

# The classic cast keeps fixed roles across every video of a crypto course.
ALICE, BOB, EVE = PRIMARY, POSITIVE, NEGATIVE
SECRET = ACCENT  # keys, private values
PUBLIC = SPECIAL  # public values, servers
ACCESS = TEAL


def alice() -> Person:
    return Person("Alice", ALICE)


def bob() -> Person:
    return Person("Bob", BOB)


def eve() -> Person:
    return Person("Eve", EVE)


class KeyIcon(VGroup):
    """A simple key: bow (ring), shaft and two teeth."""

    def __init__(self, color: str = ACCENT, scale: float = 1.0, **kw) -> None:
        w = 5
        bow = Circle(radius=0.18, color=color, stroke_width=w)
        shaft = Line(bow.get_right(), bow.get_right() + RIGHT * 0.55, color=color, stroke_width=w)
        t1 = Line(ORIGIN, DOWN * 0.13, color=color, stroke_width=w).move_to(
            shaft.get_end() + LEFT * 0.05 + DOWN * 0.065
        )
        t2 = t1.copy().shift(LEFT * 0.15)
        super().__init__(bow, shaft, t1, t2, **kw)
        self.scale(scale)


class Channel(VGroup):
    """The public channel between two people, drawn as a dashed line."""

    def __init__(self, left, right, **kw) -> None:
        line = DashedLine(
            left.get_right() + RIGHT * 0.2,
            right.get_left() + LEFT * 0.2,
            color=MUTED,
            dash_length=0.12,
        )
        text = t("channel_terminal") if THEME.name == "terminal" else t("channel")
        tag = label(text, size=20, color=MUTED).next_to(line, UP, buff=0.1)
        # left quarter, not the middle: Eve always steps onto the middle of the channel
        tag.set_x(line.get_left()[0] + line.width * 0.25)
        super().__init__(line, tag, **kw)


class Bank(VGroup):
    """A small bank building with a name tag."""

    def __init__(self, color: str = SPECIAL, name: str = "Bank", **kw) -> None:
        roof = (
            Triangle(color=color, stroke_width=4)
            .stretch_to_fit_width(1.3)
            .stretch_to_fit_height(0.45)
        )
        base = Rectangle(width=1.2, height=0.12, color=color, stroke_width=4)
        cols = VGroup(*(Line(UP * 0.3, DOWN * 0.3, color=color, stroke_width=5) for _ in range(4)))
        cols.arrange(RIGHT, buff=0.22)
        roof.next_to(cols, UP, buff=0.04)
        base.next_to(cols, DOWN, buff=0.04)
        body = VGroup(roof, cols, base)
        if THEME.shape == "disc":
            roof.set_fill(color, 1)
            base.set_fill(color, 1)
        tag = label(name, size=26, color=color).next_to(body, DOWN, buff=0.18)
        super().__init__(body, tag, **kw)
        self.body = body
