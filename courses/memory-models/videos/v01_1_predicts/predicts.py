"""Video 1.1 – What a scheduler actually predicts.  (srs-benchmark, Anki fork FAQ)"""

# Beats
#   S0  hook: two cards, both "due today" (S = 3 d seen 3 d ago; S = 20 d seen 60 d ago) –
#       are they equally urgent? pretest on desired retention and on what FSRS sees
#   S1  retrievability R = P(recall now); power forgetting curve; stability S = day R hits 90 %;
#       one shape stretched: R = (1 + 19/81 · t/S)^(-1/2), R(S) = 9/10 exactly
#   S2  the viewer invents the rule: review when R reaches desired retention; DR 95/90/80 %
#       → 0.46 S / S / 2.4 S; 99 % ≈ 11× as often; per-card DR; the hook resolved (90 % vs 77 %)
#       check (about S1): t = 2S for two very different cards → same R
#   S3  FSRS = hand-written rules + 21/34 fitted numbers per user; it sees only this card's
#       intervals and grades (+ same-day reviews); not siblings, deck, today's load, answer time
#       check (about S2): S = 20 d, DR 90 → 80 % → about 48 d
#   S4  cliffhanger: two forecasts, one review – how would you know whose guess is better? recall
# Opening: a puzzle in the learner's own queue. Building: let them invent the rule (S2), concrete
# numbers before the formula. Ending: cliffhanger into 1.2 (no metrics taught here).
#
# Numbers (FSRS-4.5+ curve, C = -0.5, F = 19/81): R(S) = (100/81)^-0.5 = 0.9;
# interval(DR) = S · (DR^-2 - 1) · 81/19 → 0.95: 0.461 S, 0.8: 2.398 S, 0.99: 0.0866 S;
# 1/0.0866 ≈ 11.6 reviews as often;
# R(60 d, S = 20 d) = 0.766; R(2S) = (119/81)^-0.5 = 0.825. FSRS-6 learns the decay and sets
# F = 0.9^(-1/decay) - 1, so R(S) = 0.9 still holds.

from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    UR,
    Arrow,
    Axes,
    Create,
    DashedLine,
    Dot,
    FadeIn,
    FadeOut,
    GrowArrow,
    MathTex,
    Transform,
    VGroup,
)

from lvp.props import cross, question, tick
from lvp.style import (
    ACCENT,
    FG,
    MUTED,
    NEGATIVE,
    POSITIVE,
    PRIMARY,
    TEAL,
    Card,
    LessonScene,
    label,
)

SERIES = "Memory Models · Video 1.1"

F, C = 19 / 81, -0.5


def recall_prob(t: float, s: float) -> float:
    """FSRS-4.5+ power forgetting curve; R(S) = 0.9."""
    return (1 + F * t / s) ** C


def interval(dr: float, s: float) -> float:
    """Days until R falls to desired retention dr."""
    return s * (dr ** (1 / C) - 1) / F


def word_card(front: str, back: str, color: str) -> Card:
    content = VGroup(label(front, size=32, color=color),
                     label(back, size=22, color=MUTED)).arrange(DOWN, buff=0.12)  # fmt: skip
    return Card(content, color, pad=0.25)


def recall_axes(x_max: float = 60) -> tuple[Axes, VGroup]:
    ax = Axes(
        x_range=[0, x_max, 10],
        y_range=[0, 1, 0.1],
        x_length=8.4,
        y_length=4.4,
        tips=False,
        axis_config={"color": MUTED, "stroke_width": 2},
    )
    ticks = VGroup()
    for x in range(0, int(x_max) + 1, 10):
        ticks.add(label(str(x), size=20, color=MUTED).next_to(ax.c2p(x, 0), DOWN, buff=0.15))
    for y, txt in ((0.5, "50 %"), (1.0, "100 %")):
        ticks.add(label(txt, size=20, color=MUTED).next_to(ax.c2p(0, y), LEFT, buff=0.15))
    xl = label("days since last review", size=22, color=MUTED)
    xl.next_to(ax.x_axis, DOWN, buff=0.55)
    yl = label("chance of recall", size=22, color=MUTED).next_to(ax.c2p(0, 1), UP, buff=0.25)
    yl.align_to(ax.c2p(0, 1), LEFT).shift(LEFT * 0.4)
    return ax, VGroup(ticks, xl, yl)


class S0Hook(LessonScene):
    def construct(self) -> None:
        a = word_card("Hund", "dog", TEAL)
        b = word_card("Fernweh", "longing for far-off places", PRIMARY)
        cards = VGroup(a, b).arrange(RIGHT, buff=1.6).move_to(UP * 0.6)
        head = label("today's queue", size=26, color=MUTED, slant="ITALIC").next_to(
            cards, UP, buff=0.6
        )
        self.opening(SERIES, head)
        with self.voiceover(
            'Two cards are in <bookmark mark="q"/>today\'s review queue.', hold="step"
        ):
            self.at("q", FadeIn(cards, shift=UP * 0.1))
        da = label("interval 3 days\nlast seen 3 days ago", size=22, color=FG).next_to(
            a, DOWN, buff=0.4
        )
        db = label("interval 20 days\nlast seen 60 days ago", size=22, color=FG).next_to(
            b, DOWN, buff=0.4
        )
        with self.voiceover(
            '<bookmark mark="a"/>One came back after three days, right on time. '
            '<bookmark mark="b"/>The other was due forty days ago, while you were travelling.',
            hold="step",
        ):
            self.at("a", FadeIn(da, shift=UP * 0.1))
            self.at("b", FadeIn(db, shift=UP * 0.1))
        due = VGroup(*(label("due", size=26, color=ACCENT, weight="BOLD").next_to(c, UR, buff=0.1)
                       for c in (a, b)))  # fmt: skip
        with self.voiceover('Anki shows both as <bookmark mark="d"/>due.', hold="step"):
            self.at("d", FadeIn(due), FadeOut(head))
        with self.voiceover(
            "You make this call more often than you think – "
            "every evening the queue is longer than your time.",
            hold="step",
        ):
            self.play(due.animate.set_opacity(0.85), run_time=0.3)
        q = question("Are they equally urgent?\nIf you only had time for one, which first?")
        q.to_edge(DOWN, buff=0.6)
        with self.voiceover(
            "Are they equally urgent? "
            '<bookmark mark="w"/>If you only had time for one, which would you pick – and why?',
            hold="question",
        ):
            self.at("w", FadeIn(q, shift=UP * 0.1))
        self.title_card(
            "What a scheduler actually predicts",
            say="Behind the word due sits one number. We'll draw it, "
            "turn it into a schedule, and see what FSRS can and can't use to compute it.",
        )
        self.pretest(
            [
                "Desired retention goes from 90 % to 95 %.\n"
                "Do intervals shrink by a few percent – or by about half?",
                "You reviewed a card's reverse side yesterday.\nDoes FSRS use that for this card?",
            ]
        )


class S1Curve(LessonScene):
    def construct(self) -> None:
        self.chapter("1", "One number per card")
        card = word_card("Fernweh", "longing for far-off places", PRIMARY).move_to(UP * 1.5)
        with self.voiceover(
            '<bookmark mark="c"/>Take one card, and ask one question: if it showed up right now, '
            "would you get it?",
            hold="step",
        ):
            self.at("c", FadeIn(card, shift=UP * 0.1))
        rdef = (
            VGroup(
                label("retrievability", size=34, color=ACCENT, weight="BOLD"),
                label("R = probability you'd recall it now", size=30),
            )
            .arrange(DOWN, buff=0.2)
            .next_to(card, DOWN, buff=0.7)
        )
        with self.voiceover(
            "Nobody can know for sure. But a scheduler can put a probability on it, "
            '<bookmark mark="r"/>and that probability is called retrievability.',
            hold="reveal",
        ):
            self.at("r", FadeIn(rdef, shift=UP * 0.1))
        fc = label(
            "R = 0.9: of many cards in this state,\nyou'd recall about nine in ten",
            size=24,
            color=MUTED,
        ).next_to(rdef, DOWN, buff=0.5)
        with self.voiceover(
            "Any single review ends as a yes or a no. "
            '<bookmark mark="n"/>Ninety percent means: of many cards in this state, about nine in '
            "ten come back.",
            hold="reveal",
        ):
            self.at("n", FadeIn(fc, shift=UP * 0.1))

        ax, deco = recall_axes()
        plot = VGroup(ax, deco).move_to(DOWN * 0.35 + LEFT * 1.6)
        self.clear_stage()
        curve20 = ax.plot(
            lambda t: recall_prob(t, 20), x_range=[0, 60], color=PRIMARY, stroke_width=5
        )
        with self.voiceover(
            '<bookmark mark="p"/>Now plot R against the days since your last review.',
            hold="step",
        ):
            self.at("p", FadeIn(plot))
        with self.voiceover(
            '<bookmark mark="k"/>Right after a review it sits near one hundred percent, '
            "then slides – steeply at first, then with a long, slow tail.",
            hold="reveal",
        ):
            self.at("k", Create(curve20), run_time=2.5)
        why = label(
            "power curve,\nnot exponential",
            size=24,
            color=MUTED,
        ).move_to(RIGHT * 5.0 + UP * 1.4)
        with self.voiceover(
            'FSRS uses a <bookmark mark="w"/>power curve here, not an exponential. '
            "Average many memories that fade at different speeds, and you get "
            "exactly this kind of long tail.",
            hold="reveal",
        ):
            self.at("w", FadeIn(why, shift=UP * 0.1))
        line90 = DashedLine(ax.c2p(0, 0.9), ax.c2p(60, 0.9), color=ACCENT, stroke_width=3)
        l90 = label("90 %", size=20, color=ACCENT).next_to(ax.c2p(0, 0.9), LEFT, buff=0.15)
        drop = DashedLine(ax.c2p(20, 0.9), ax.c2p(20, 0), color=PRIMARY, stroke_width=2)
        dot20 = Dot(ax.c2p(20, 0.9), color=PRIMARY, radius=0.09)
        s20 = label("S = 20 days", size=26, color=PRIMARY, weight="BOLD").move_to(
            RIGHT * 4.9 + DOWN * 0.2
        )
        with self.voiceover(
            "To compare cards you want one number for how durable a memory is. "
            'FSRS takes the day the curve crosses <bookmark mark="l"/>ninety percent, '
            '<bookmark mark="s"/>and calls it stability.',
            hold="insight",
        ):
            self.at("l", Create(line90), FadeIn(l90), FadeOut(why))
            self.at("s", Create(drop), FadeIn(dot20), FadeIn(s20))
        half = label("not 50 %:\nyou'd never wait\nthat long", size=22, color=MUTED)
        half.move_to(RIGHT * 5.0 + UP * 1.5)
        with self.voiceover(
            '<bookmark mark="h"/>Why not a half-life, where it hits fifty percent? '
            "Because no sensible schedule lets a card sink that far; "
            "the part of the curve that matters is up near the top.",
            hold="reveal",
        ):
            self.at("h", FadeIn(half, shift=UP * 0.1))
        d10 = Dot(ax.c2p(10, recall_prob(10, 20)), color=PRIMARY, radius=0.07)
        d30 = Dot(ax.c2p(30, recall_prob(30, 20)), color=PRIMARY, radius=0.07)
        v10 = label("95 %", size=20, color=PRIMARY).next_to(d10, DOWN + LEFT, buff=0.08)
        v30 = label("86 %", size=20, color=PRIMARY).next_to(d30, DOWN, buff=0.12)
        with self.voiceover(
            'On this curve, <bookmark mark="a"/>ten days in you are at about ninety-five percent; '
            '<bookmark mark="b"/>thirty days in, about eighty-six.',
            hold="step",
        ):
            self.at("a", FadeIn(d10), FadeIn(v10))
            self.at("b", FadeIn(d30), FadeIn(v30))
        curve3 = ax.plot(lambda t: recall_prob(t, 3), x_range=[0, 60], color=TEAL, stroke_width=5)
        dot3 = Dot(ax.c2p(3, 0.9), color=TEAL, radius=0.09)
        s3 = label("S = 3 days", size=26, color=TEAL, weight="BOLD").next_to(s20, DOWN, buff=0.3)
        with self.voiceover(
            '<bookmark mark="t"/>A card with a stability of three days has the same curve, '
            "squeezed.",
            hold="reveal",
        ):
            self.at(
                "t",
                Create(curve3),
                FadeIn(dot3),
                FadeIn(s3),
                FadeOut(half),
                FadeOut(d10, v10, d30, v30),
                run_time=1.5,
            )
        formula = (
            MathTex(r"R(t) = \left(1 + \tfrac{19}{81}\cdot\tfrac{t}{S}\right)^{-1/2}", color=FG)
            .scale(0.9)
            .scale_to_fit_width(3.5)
            .move_to(RIGHT * 5.0 + DOWN * 1.6)
        )
        with self.voiceover(
            "Every card's curve is one shape, stretched: "
            '<bookmark mark="f"/>R depends only on t divided by S.',
            hold="reveal",
        ):
            self.at("f", FadeIn(formula, shift=UP * 0.1))
        self.clear_stage()
        big = (
            MathTex(r"R(t) = \left(1 + \tfrac{19}{81}\cdot\tfrac{t}{S}\right)^{-1/2}", color=FG)
            .scale(1.2)
            .move_to(UP * 1.4)
        )
        check = (
            MathTex(r"R(S) = \left(\tfrac{100}{81}\right)^{-1/2} = \tfrac{9}{10}", color=ACCENT)
            .scale(1.2)
            .next_to(big, DOWN, buff=0.8)
        )
        with self.voiceover(
            "This is the curve FSRS has used since version four point five. "
            '<bookmark mark="z"/>Put in t equal to S: you get a hundred over eighty-one, '
            "and its inverse square root is exactly nine tenths.",
            hold="insight",
        ):
            self.play(FadeIn(big), run_time=0.6)
            self.at("z", FadeIn(check, shift=UP * 0.1))
        six = label(
            "FSRS-6: the exponent is learned from your data;\n"
            "the 19/81 is adjusted so R(S) stays 90 %",
            size=24,
            color=MUTED,
        ).next_to(check, DOWN, buff=0.8)
        with self.voiceover(
            '<bookmark mark="six"/>FSRS-6 also learns the exponent from your reviews, and adjusts '
            "the constant so that the curve still passes ninety percent at S. "
            "Your data decides how flat the tail is.",
            hold="reveal",
        ):
            self.at("six", FadeIn(six, shift=UP * 0.1))
        self.clear_stage()
        ax2, deco2 = recall_axes()
        plot2 = VGroup(ax2, deco2).move_to(DOWN * 0.35)
        c_old = ax2.plot(
            lambda t: recall_prob(t, 10), x_range=[0, 60], color=PRIMARY, stroke_width=5
        )
        c_new = ax2.plot(
            lambda t: recall_prob(t, 30), x_range=[0, 60], color=POSITIVE, stroke_width=5
        )
        c_lap = ax2.plot(
            lambda t: recall_prob(t, 2), x_range=[0, 60], color=NEGATIVE, stroke_width=5
        )
        good = label("Good: S grows", size=26, color=POSITIVE).move_to(UP * 2.9 + RIGHT * 2.5)
        again = label("Again: S shrinks", size=26, color=NEGATIVE).next_to(good, DOWN, buff=0.2)
        with self.voiceover(
            "Each review moves S. "
            '<bookmark mark="g"/>A success stretches the curve, '
            '<bookmark mark="a"/>a lapse squeezes it.',
            hold="reveal",
        ):
            self.play(FadeIn(plot2), Create(c_old), run_time=1.0)
            self.at("g", Transform(c_old.copy(), c_new), FadeIn(good))
            self.at("a", Transform(c_old.copy(), c_lap), FadeIn(again))
        with self.voiceover(
            "How far it moves is where schedulers differ – we'll come back to that.",
            hold="step",
        ):
            self.play(c_old.animate.set_stroke(opacity=0.4), run_time=0.5)


class S2Rule(LessonScene):
    def construct(self) -> None:
        self.chapter("2", "From a curve to a due date")
        ax, deco = recall_axes()
        plot = VGroup(ax, deco).move_to(DOWN * 0.35 + LEFT * 1.6)
        curve = ax.plot(
            lambda t: recall_prob(t, 10), x_range=[0, 60], color=PRIMARY, stroke_width=5
        )
        stab = label("S = 10 days", size=26, color=PRIMARY, weight="BOLD").move_to(
            RIGHT * 4.9 + UP * 2.4
        )
        with self.voiceover(
            '<bookmark mark="c"/>A curve on its own schedules nothing. '
            "You still have to decide when the card comes back.",
            hold="step",
        ):
            self.at("c", FadeIn(plot), Create(curve), FadeIn(stab), run_time=1.2)
        q = question("When should\nit come back?").scale(0.8)
        q.move_to(RIGHT * 5.0 + UP * 1.2)
        with self.voiceover(
            '<bookmark mark="q"/>If you were designing the rule, what would it be?', hold="question"
        ):
            self.at("q", FadeIn(q, shift=UP * 0.1))

        def marker(dr: float, color: str):
            t = interval(dr, 10)
            h = DashedLine(ax.c2p(0, dr), ax.c2p(60, dr), color=color, stroke_width=3)
            v = DashedLine(ax.c2p(t, dr), ax.c2p(t, 0), color=color, stroke_width=2)
            d = Dot(ax.c2p(t, dr), color=color, radius=0.09)
            return VGroup(h, v, d)

        m90 = marker(0.9, ACCENT)
        dr_lab = label("desired retention", size=26, color=ACCENT, weight="BOLD").move_to(
            RIGHT * 4.9 + UP * 1.2
        )
        with self.voiceover(
            "The natural answer: pick a recall level you're willing to accept, "
            '<bookmark mark="m"/>and review when the curve gets down to it.',
            hold="step",
        ):
            self.at("m", Create(m90), FadeOut(q))
        with self.voiceover(
            'That level is your <bookmark mark="d"/>desired retention.', hold="step"
        ):
            self.at("d", FadeIn(dr_lab))
        rows = [(0.95, "95 %", "0.46 × S", "4.6 days"), (0.9, "90 %", "1 × S", "10 days"),
                (0.8, "80 %", "2.4 × S", "24 days")]  # fmt: skip
        table = VGroup(*(VGroup(label(a, size=24, color=ACCENT), label(b, size=24),
                                label(c, size=24, color=MUTED)).arrange(RIGHT, buff=0.3)
                         for _, a, b, c in rows))  # fmt: skip
        table.arrange(DOWN, aligned_edge=LEFT, buff=0.25).move_to(RIGHT * 4.9 + DOWN * 0.3)
        with self.voiceover(
            "At ninety percent, the interval is exactly S – "
            '<bookmark mark="r"/>which is why FSRS defines stability at that level.',
            hold="insight",
        ):
            self.at("r", FadeIn(table[1], shift=UP * 0.1))
        m95 = marker(0.95, NEGATIVE)
        with self.voiceover(
            'Raise it to <bookmark mark="u"/>ninety-five percent, and the interval drops to less '
            "than half of S.",
            hold="reveal",
        ):
            self.at("u", Create(m95), FadeIn(table[0], shift=UP * 0.1))
        m80 = marker(0.8, POSITIVE)
        with self.voiceover(
            'Lower it to <bookmark mark="o"/>eighty, and it grows to about two point four times S.',
            hold="reveal",
        ):
            self.at("o", Create(m80), FadeIn(table[2], shift=UP * 0.1))
        solve = MathTex(r"t = S\cdot\tfrac{81}{19}\left(\mathrm{DR}^{-2} - 1\right)", color=FG)
        solve.scale_to_fit_width(3.4).next_to(table, DOWN, buff=0.6)
        with self.voiceover(
            "All three come from one line: "
            '<bookmark mark="x"/>solve the curve for the day it reaches your desired retention.',
            hold="reveal",
        ):
            self.at("x", FadeIn(solve, shift=UP * 0.1))
        cost = label("99 %: interval 0.09 × S\n≈ 11× as often", size=24, color=NEGATIVE)
        cost.move_to(dr_lab)
        with self.voiceover(
            "So higher retention costs reviews, and the price climbs steeply near the top.",
            hold="step",
        ):
            self.play(table.animate.set_opacity(0.9), run_time=0.3)
        with self.voiceover(
            '<bookmark mark="e"/>At ninety-nine percent, this card would come back about eleven '
            "times as often as at ninety.",
            hold="insight",
        ):
            self.at("e", FadeIn(cost, shift=UP * 0.1), FadeOut(dr_lab))
        low = label("too low: more lapses,\neach one squeezes S", size=24, color=MUTED)
        low.move_to(cost)
        with self.voiceover(
            "Going low isn't free either: "
            '<bookmark mark="l"/>you forget more, and every lapse squeezes the curve and costs a '
            "relearn – so the workload doesn't keep falling as you turn the dial down.",
            hold="reveal",
        ):
            self.at("l", FadeOut(cost), FadeIn(low, shift=UP * 0.1))

        self.clear_stage()
        rare = word_card("Fernweh", "rare word", PRIMARY)
        core = word_card("Hund", "everyday word", TEAL)
        pair = VGroup(rare, core).arrange(RIGHT, buff=2.5).move_to(UP * 1.2)
        dr_r = label("80 %", size=34, color=ACCENT, weight="BOLD").next_to(rare, DOWN, buff=0.4)
        dr_c = label("95 %", size=34, color=ACCENT, weight="BOLD").next_to(core, DOWN, buff=0.4)
        with self.voiceover(
            "Nothing forces one setting for the whole collection.",
            hold="step",
        ):
            self.play(FadeIn(pair, shift=UP * 0.1), run_time=0.6)
        with self.voiceover(
            'A word you meet once a year might be fine at <bookmark mark="r"/>eighty percent; '
            '<bookmark mark="c"/>one you use every day may deserve ninety-five.',
            hold="reveal",
        ):
            self.at("r", FadeIn(dr_r, shift=UP * 0.1))
            self.at("c", FadeIn(dr_c, shift=UP * 0.1))
        note = label("per-card desired retention: video 1.4", size=24, color=MUTED).to_edge(
            DOWN, buff=0.9
        )
        with self.voiceover(
            "Some experimental Anki builds already set the level per card from rules like these – "
            '<bookmark mark="n"/>video one point four comes back to that.',
            hold="step",
        ):
            self.at("n", FadeIn(note))

        self.clear_stage()
        pred = Card(
            VGroup(
                label("predictor", size=30, color=PRIMARY, weight="BOLD"),
                label("R for this card, now", size=24),
            ).arrange(DOWN, buff=0.12),
            PRIMARY,
        )
        rule = Card(
            VGroup(
                label("rule", size=30, color=ACCENT, weight="BOLD"),
                label("review when R hits DR", size=24),
            ).arrange(DOWN, buff=0.12),
            ACCENT,
        )
        date = label("due date", size=30, weight="BOLD")
        VGroup(pred, rule, date).arrange(RIGHT, buff=1.2).move_to(UP * 0.3)
        arrows = VGroup(
            Arrow(pred.get_right(), rule.get_left(), buff=0.1, color=MUTED),
            Arrow(rule.get_right(), date.get_left(), buff=0.1, color=MUTED),
        )
        with self.voiceover(
            "Notice what moving the dial did not change: the curve. "
            '<bookmark mark="p"/>The prediction stays put; '
            '<bookmark mark="r"/>only the rule that reads it moves.',
            hold="reveal",
        ):
            self.at("p", FadeIn(pred, shift=UP * 0.1))
            self.at("r", GrowArrow(arrows[0]), FadeIn(rule, shift=UP * 0.1))
        with self.voiceover(
            "Every scheduler in this course has these two parts: "
            "something that predicts R, and a rule that turns R into "
            '<bookmark mark="d"/>a due date.',
            hold="insight",
        ):
            self.at("d", GrowArrow(arrows[1]), FadeIn(date))

        self.clear_stage()
        a = word_card("Hund", "S = 3 days, seen 3 days ago", TEAL)
        b = word_card("Fernweh", "S = 20 days, seen 60 days ago", PRIMARY)
        hook = VGroup(a, b).arrange(RIGHT, buff=1.2).move_to(UP * 1.4)
        ra = label("R = 90 %", size=40, color=TEAL, weight="BOLD").next_to(a, DOWN, buff=0.5)
        rb = label("R ≈ 77 %", size=40, color=NEGATIVE, weight="BOLD").next_to(b, DOWN, buff=0.5)
        with self.voiceover('<bookmark mark="h"/>Now the two cards from the start.', hold="step"):
            self.at("h", FadeIn(hook, shift=UP * 0.1))
        with self.voiceover(
            '<bookmark mark="a"/>The three-day card sits exactly at ninety percent: due, on time. '
            '<bookmark mark="b"/>The travel card has slid to about seventy-seven.',
            hold="reveal",
        ):
            self.at("a", FadeIn(ra, shift=UP * 0.1))
            self.at("b", FadeIn(rb, shift=UP * 0.1))
        point = label("“due” = R has reached your desired retention", size=28, color=ACCENT)
        point.to_edge(DOWN, buff=1.0)
        with self.voiceover(
            "Due only says the line has been crossed; "
            '<bookmark mark="p"/>the number says by how much. '
            "Everything else a scheduler does starts from that number.",
            hold="insight",
        ):
            self.at("p", FadeIn(point, shift=UP * 0.1))
        with self.voiceover(
            "With time for only one, the number points at the travel card – it's the one you're "
            "closer to losing. Sorting the queue by retrievability, which Anki offers, "
            "puts it first.",
            hold="reveal",
        ):
            self.play(b.animate.scale(1.08), rb.animate.scale(1.08), run_time=0.6)
        self.checkpoint(
            "Card A: stability 4 days, last seen 8 days ago.\n"
            "Card B: stability 40 days, last seen 80 days ago.\n"
            "Which are you more likely to recall?",
            "Neither: both are at t = 2S, and R depends only on t/S (≈ 82 % each)",
        )


class S3Fsrs(LessonScene):
    def construct(self) -> None:
        self.chapter("3", "FSRS: a curve built by hand")
        rules = (
            VGroup(
                label("after Good: how much does S grow?", size=26),
                label("after Again: how far does S fall?", size=26),
                label("how do difficulty and current R change both?", size=26),
            )
            .arrange(DOWN, aligned_edge=LEFT, buff=0.3)
            .move_to(UP * 1.4)
        )
        with self.voiceover(
            "So where does S come from, and how does it move after each review?",
            hold="step",
        ):
            self.play(FadeIn(rules[0], shift=UP * 0.1), run_time=0.6)
        with self.voiceover(
            "In FSRS, people wrote those rules by hand: "
            '<bookmark mark="b"/>how much an Again cuts stability, '
            '<bookmark mark="c"/>and how the card\'s difficulty and its current recall shape both.',
            hold="reveal",
        ):
            self.at("b", FadeIn(rules[1], shift=UP * 0.1))
            self.at("c", FadeIn(rules[2], shift=UP * 0.1))
        with self.voiceover(
            "Difficulty is a second number each card carries, from one to ten: "
            "the harder the card, the less a success stretches its stability.",
            hold="reveal",
        ):
            self.play(rules[2].animate.set_color(ACCENT), run_time=0.4)
        params = (
            VGroup(
                Card(label("FSRS-6: 21 numbers", size=28, color=PRIMARY), PRIMARY),
                Card(label("FSRS-7: 34 numbers", size=28, color=PRIMARY), PRIMARY),
            )
            .arrange(RIGHT, buff=0.8)
            .next_to(rules, DOWN, buff=0.7)
        )
        with self.voiceover(
            "The structure is fixed. What's left open is a short list of numbers: "
            '<bookmark mark="s"/>twenty-one in FSRS-6, <bookmark mark="v"/>thirty-four in FSRS-7.',
            hold="reveal",
        ):
            self.at("s", FadeIn(params[0], shift=UP * 0.1))
            self.at("v", FadeIn(params[1], shift=UP * 0.1))
        first = label("FSRS-6: four of them = starting S after a first Again / Hard / Good / Easy",
                      size=22, color=MUTED).next_to(params, DOWN, buff=0.35)  # fmt: skip
        with self.voiceover(
            '<bookmark mark="w"/>Four of FSRS-6\'s numbers are simply the starting stability '
            "after your very first Again, Hard, Good or Easy.",
            hold="reveal",
        ):
            self.at("w", FadeIn(first, shift=UP * 0.1))
        fit_l = label("fitted to your own review history", size=28, color=ACCENT, weight="BOLD")
        fit_l.next_to(first, DOWN, buff=0.5)
        with self.voiceover(
            "When you press Optimize, those numbers are "
            '<bookmark mark="f"/>fitted to your own review history – your FSRS is not mine.',
            hold="insight",
        ):
            self.at("f", FadeIn(fit_l, shift=UP * 0.1))
        with self.voiceover(
            "The optimizer tries settings until the curves it predicts line up as well as possible "
            "with what actually happened in your past reviews. "
            "What as well as possible should mean is a question of its own – the next video's.",
            hold="reveal",
        ):
            self.play(fit_l.animate.scale(1.05), run_time=0.4)

        self.clear_stage()
        grades = [("Again", NEGATIVE), ("Good", POSITIVE), ("Good", POSITIVE), ("Hard", ACCENT),
                  ("Good", POSITIVE)]  # fmt: skip
        boxes = VGroup(*(Card(label(g, size=24, color=c), c, pad=0.18) for g, c in grades))
        boxes.arrange(RIGHT, buff=1.15).move_to(UP * 2.2)
        gaps = VGroup()
        for i, d in enumerate(("1 d", "4 d", "11 d", "19 d")):
            arr = Arrow(boxes[i].get_right(), boxes[i + 1].get_left(), buff=0.08, color=MUTED,
                        stroke_width=3, max_tip_length_to_length_ratio=0.25)  # fmt: skip
            gaps.add(VGroup(arr, label(d, size=22, color=MUTED).next_to(arr, UP, buff=0.1)))
        sees = label("FSRS sees: this card's gaps and grades (+ same-day reviews)", size=26,
                     color=PRIMARY).next_to(boxes, DOWN, buff=0.45)  # fmt: skip
        with self.voiceover(
            "Now look at what goes in. "
            '<bookmark mark="h"/>For each card, FSRS reads this card\'s own history: '
            "the days between reviews, the button you pressed, "
            '<bookmark mark="sd"/>and, since FSRS-5, reviews on the same day.',
            hold="reveal",
        ):
            self.at("h", FadeIn(boxes, lag_ratio=0.2), FadeIn(gaps, lag_ratio=0.2), run_time=1.2)
            self.at("sd", FadeIn(sees, shift=UP * 0.1))
        unseen = [
            ("s", "the reverse card, reviewed yesterday"),
            ("d", "the deck it lives in"),
            ("l", "your 300th review today – and you're tired"),
            ("t", "how long you hesitated before answering"),
        ]
        items = VGroup(*(VGroup(cross(size=0.28), label(txt, size=26, color=MUTED))
                         for _, txt in unseen))  # fmt: skip
        for row in items:
            row.arrange(RIGHT, buff=0.3)
        items.arrange(DOWN, aligned_edge=LEFT, buff=0.3).next_to(sees, DOWN, buff=0.6)
        with self.voiceover("That's all it gets.", hold="step"):
            self.play(sees.animate.set_color(ACCENT), run_time=0.4)
        with self.voiceover(
            'It doesn\'t know <bookmark mark="s"/>you reviewed the reverse card yesterday, '
            '<bookmark mark="d"/>which deck the card sits in, '
            '<bookmark mark="l"/>or that this is your three hundredth review today.',
            hold="reveal",
        ):
            self.at("s", FadeIn(items[0], shift=UP * 0.1))
            self.at("d", FadeIn(items[1], shift=UP * 0.1))
            self.at("l", FadeIn(items[2], shift=UP * 0.1))
        with self.voiceover(
            '<bookmark mark="t"/>It doesn\'t see how long you hesitated. '
            "Miss a card because you're exhausted, and to FSRS it looks like real forgetting.",
            hold="insight",
        ):
            self.at("t", FadeIn(items[3], shift=UP * 0.1))
        with self.voiceover(
            "That narrow view is a choice, not an oversight: few inputs and few numbers can be "
            "fitted to one person's history, even a short one, without wild guesses.",
            hold="reveal",
        ):
            self.play(sees.animate.scale(1.03), run_time=0.4)
        with self.voiceover(
            "A model could learn from all of this – if it read the whole collection at once. "
            "That model exists – a recurrent network called RWKV – "
            "and video one point three takes it apart.",
            hold="step",
        ):
            self.play(items.animate.set_opacity(0.8), run_time=0.4)
        self.checkpoint(
            "A card has stability 20 days. You lower its desired retention\n"
            "from 90 % to 80 %. Roughly when does it come back?",
            "After about 48 days: at 80 % the interval is ≈ 2.4 × S",
        )


class S4Outro(LessonScene):
    def construct(self) -> None:
        self.chapter("4", "Whose guess is better?")
        card = word_card("Fernweh", "one review, tomorrow", PRIMARY).move_to(UP * 2.0)
        f1 = Card(label("FSRS: 90 %", size=30, color=PRIMARY), PRIMARY)
        f2 = Card(label("whole-collection model: 70 %", size=30, color=TEAL), TEAL)
        fc = VGroup(f1, f2).arrange(RIGHT, buff=0.8).move_to(UP * 0.1)
        with self.voiceover(
            '<bookmark mark="c"/>Picture one review and two forecasts. '
            '<bookmark mark="a"/>FSRS says ninety percent. '
            '<bookmark mark="b"/>A model that reads your whole collection says seventy.',
            hold="step",
        ):
            self.at("c", FadeIn(card, shift=UP * 0.1))
            self.at("a", FadeIn(f1, shift=UP * 0.1))
            self.at("b", FadeIn(f2, shift=UP * 0.1))
        res = VGroup(tick(size=0.4), label("you press Good", size=30, color=POSITIVE)).arrange(
            RIGHT, buff=0.3
        )
        res.next_to(fc, DOWN, buff=0.7)
        with self.voiceover('<bookmark mark="g"/>You press Good.', hold="step"):
            self.at("g", FadeIn(res, shift=UP * 0.1), run_time=0.4)
        with self.voiceover(
            "Was FSRS right and the other model wrong? One review can't say: "
            "a seventy percent forecast expects you to remember, too.",
            hold="reveal",
        ):
            self.play(f2.animate.scale(1.04), run_time=0.4)
        many = label("× thousands of reviews", size=24, color=MUTED).next_to(res, DOWN, buff=0.35)
        with self.voiceover(
            '<bookmark mark="m"/>Over thousands of reviews a pattern would show. '
            "But what exactly would you count?",
            hold="reveal",
        ):
            self.at("m", FadeIn(many, shift=UP * 0.1))
        last = label(
            "how would you know whose guess is better?", size=32, color=ACCENT, weight="BOLD"
        )
        last.to_edge(DOWN, buff=0.9)
        with self.voiceover(
            "So with millions of reviews and two models, "
            '<bookmark mark="h"/>how would you know whose guess is better? That\'s the next video.',
            hold="chapter",
        ):
            self.at("h", FadeIn(last, shift=UP * 0.1))
        self.clear_stage()
        self.recall(
            [
                "A card's stability doubles after a review.\n"
                "Same desired retention – what happens to its next interval?",
                "A friend sets desired retention to 99 %.\n"
                "What happens to their workload, and why so much?",
                "Name two things that could change your recall\n"
                "of a card today that FSRS never sees.",
            ]
        )
