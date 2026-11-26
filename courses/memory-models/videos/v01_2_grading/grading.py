"""Video 1.2 – How to grade a fortune teller: log loss, calibration and AUC.  (source: S1)"""

# Beats
#   S0  hook: a fortune teller who says "90 %" for every card – and you do remember 90 %.
#       Good or bad? (misconception first) → title, pretest
#   S1  log loss: −ln of the probability given to what happened; 0.105 / 2.303 / 0.693 / 4.605;
#       why log and not distance; Ada scores 0.33 without looking at a card
#   S2  calibration: groups, average prediction vs average outcome; RMSE(bins); Ada is off by
#       5 points per group; the toy exploit and the real RMSE-BINS-EXPLOIT (0.0135 / LL 4.608);
#       check about S1
#   S3  AUC: pairs remembered × forgotten, 5/6; Ada = 0.5; scale doesn't matter; check about S2
#   S4  the benchmark: 9,999 collections, ~350 M reviews, train older / test newer per user;
#       the scoreboard; check about S3
#   S5  new angle: a scheduler needs both calibration and ranking; recall
# Opening: misconception first. Building: one character (Ada) graded three ways.
# Numbers: srs-benchmark README, no same-day reviews; every derived number computed in Python.

from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    Create,
    DashedLine,
    Dot,
    FadeIn,
    FadeOut,
    Indicate,
    Line,
    MathTex,
    Rectangle,
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
    SPECIAL,
    Card,
    LessonScene,
    Person,
    label,
)

SERIES = "Memory Models · Video 1.2"


def ada_row(n: int = 5) -> VGroup:
    """Ada and her identical forecasts."""
    ada = Person("Ada", SPECIAL)
    cards = VGroup(*(Card("90 %", SPECIAL, pad=0.2) for _ in range(n))).arrange(RIGHT, buff=0.3)
    return VGroup(ada, cards).arrange(RIGHT, buff=0.7)


class S0Hook(LessonScene):
    def construct(self) -> None:
        q = question("Someone predicts every review you do.\nHow do you grade them?")
        q.move_to(UP * 2.4)
        self.opening(SERIES, q)
        card = Card(label("perro  →  ?", size=34), PRIMARY, pad=0.35).move_to(LEFT * 3.6)
        pred = label("model: 90 %", size=32, color=ACCENT).next_to(card, RIGHT, buff=0.8)
        res = VGroup(tick(size=0.45), label("remembered", size=30, color=POSITIVE))
        res.arrange(RIGHT, buff=0.25).next_to(pred, RIGHT, buff=0.8)
        with self.voiceover(
            '<bookmark mark="c"/>Before every review, <bookmark mark="p"/>a model makes a '
            "prediction: ninety percent, you will remember this one.",
            hold="step",
        ):
            self.at("c", FadeIn(card, shift=UP * 0.1), run_time=0.6)
            self.at("p", FadeIn(pred, shift=UP * 0.1), run_time=0.6)
        with self.voiceover(
            'Then you press a button, and <bookmark mark="r"/>the truth arrives: remembered, '
            "or forgotten.",
            hold="step",
        ):
            self.at("r", FadeIn(res, shift=UP * 0.1))
        self.clear_stage()
        row = ada_row().move_to(UP * 0.4)
        with self.voiceover(
            'Now meet <bookmark mark="a"/>Ada, a fortune teller who says ninety percent. '
            '<bookmark mark="e"/>For every card, every day.',
            hold="step",
        ):
            self.at("a", FadeIn(row[0], shift=UP * 0.1))
            self.at("e", FadeIn(row[1], lag_ratio=0.2), run_time=1.0)
        you = label("you remember 90 % of your reviews", size=30).move_to(DOWN * 1.5)
        with self.voiceover(
            'And say you really do <bookmark mark="y"/>remember ninety percent of your reviews.',
            hold="step",
        ):
            self.at("y", FadeIn(you, shift=UP * 0.1))
        verdict = label("good or bad?", size=34, color=ACCENT, weight="BOLD").move_to(DOWN * 2.6)
        with self.voiceover(
            'On average, she is exactly right. <bookmark mark="g"/>Is she a good fortune teller?',
            hold="question",
        ):
            self.at("g", FadeIn(verdict, shift=UP * 0.1))
        self.title_card(
            "How to grade a fortune teller",
            say="Three ways to grade her, each catching something the others miss. "
            "Then a scoreboard of real models, graded on three hundred fifty million reviews.",
        )
        self.pretest(
            [
                "A model says 99 % and you forget the card.\n"
                "How harshly should a fair score punish that?",
                "To choose which card you review next,\nwhat must a model get right?",
            ]
        )


class S1LogLoss(LessonScene):
    def construct(self) -> None:
        self.chapter("1", "The price of confident mistakes")
        head = VGroup(
            label("prediction", size=24, color=MUTED),
            label("what happened", size=24, color=MUTED),
            label("p given to it", size=24, color=MUTED),
            label("penalty", size=24, color=MUTED),
        )
        data = [
            ("90 %", "remembered", POSITIVE, "0.9", "0.105"),
            ("90 %", "forgotten", NEGATIVE, "0.1", "2.303"),
            ("50 %", "either", FG, "0.5", "0.693"),
            ("99 %", "forgotten", NEGATIVE, "0.01", "4.605"),
        ]
        xs = [-4.6, -1.6, 1.5, 4.3]
        for h, x in zip(head, xs, strict=True):
            h.move_to([x, 2.3, 0])
        rows = []
        for i, (p, what, col, given, pen) in enumerate(data):
            y = 1.4 - i * 0.85
            r = VGroup(
                label(p, size=30).move_to([xs[0], y, 0]),
                label(what, size=30, color=col).move_to([xs[1], y, 0]),
                label(given, size=30).move_to([xs[2], y, 0]),
                label(pen, size=30, color=ACCENT, weight="BOLD").move_to([xs[3], y, 0]),
            )
            rows.append(r)
        with self.voiceover(
            "Start with the most natural idea: "
            '<bookmark mark="s"/>look at the probability the model gave to what actually happened.',
            hold="step",
        ):
            self.at("s", FadeIn(head[:3]), FadeIn(rows[0][:3]), FadeIn(rows[1][:3]))
        formula = MathTex(r"\text{penalty} = -\ln\big(p_{\text{given to what happened}}\big)")
        formula.scale(0.8).move_to(DOWN * 2.6)
        with self.voiceover(
            'High is good, so turn it into a <bookmark mark="k"/>penalty: '
            '<bookmark mark="l"/>minus the natural log of that probability.',
            hold="step",
        ):
            self.at("k", FadeIn(head[3]), run_time=0.5)
            self.at("l", FadeIn(formula, shift=UP * 0.1))
        with self.voiceover(
            'Ninety percent, and you remember: <bookmark mark="a"/>a penalty of zero point one.',
            hold="step",
        ):
            self.at("a", FadeIn(rows[0][3]))
        with self.voiceover(
            'Ninety percent, and you forget: <bookmark mark="b"/>two point three. '
            "About twenty-two times as much.",
            hold="reveal",
        ):
            self.at("b", FadeIn(rows[1][3]))
        with self.voiceover(
            '<bookmark mark="c"/>A coin flip, fifty percent, costs zero point six nine, '
            "whatever happens.",
            hold="step",
        ):
            self.at("c", FadeIn(rows[2]))
        with self.voiceover(
            '<bookmark mark="d"/>And ninety-nine percent on a card you forget: four point six.',
            hold="reveal",
        ):
            self.at("d", FadeIn(rows[3]))
        note = label("each extra 9 of confidence: +2.3 when wrong", size=26, color=NEGATIVE)
        note.move_to(DOWN * 1.75)
        with self.voiceover(
            'Every extra nine of confidence <bookmark mark="n"/>adds another two point three '
            "when it turns out wrong. There is no ceiling.",
            hold="insight",
        ):
            self.at("n", FadeIn(note, shift=UP * 0.1))
        self.clear_stage()
        why = (
            VGroup(
                label("score by plain distance |outcome − p|:", size=28),
                label("best move = round everything to 0 or 1", size=28, color=NEGATIVE),
                label("score by −ln p:", size=28),
                label("best move = say what you believe", size=28, color=POSITIVE),
            )
            .arrange(DOWN, aligned_edge=LEFT, buff=0.3)
            .move_to(UP * 0.3)
        )
        why[2].shift(DOWN * 0.3)
        why[3].shift(DOWN * 0.3)
        with self.voiceover(
            "Why a log, and not the plain distance between prediction and outcome? "
            '<bookmark mark="d"/>Under plain distance, a model scores best by rounding every '
            "prediction to zero or one.",
            hold="step",
        ):
            self.at("d", FadeIn(why[:2], shift=UP * 0.1))
        with self.voiceover(
            '<bookmark mark="l"/>Under the log, its best move is to say exactly what it believes.',
            hold="insight",
        ):
            self.at("l", FadeIn(why[2:], shift=UP * 0.1))
        honest = label(
            "true chance 70 %:   say 70 % → 0.61 on average,   say 90 % → 0.76",
            size=26,
            color=ACCENT,
        ).next_to(why, DOWN, buff=0.7)
        with self.voiceover(
            'Try it: <bookmark mark="h"/>a card you truly remember seven times in ten. '
            "Saying seventy percent costs zero point six one on average; "
            "bragging ninety costs zero point seven six.",
            hold="insight",
        ):
            self.at("h", FadeIn(honest, shift=UP * 0.1))
        self.clear_stage()
        ll = (
            MathTex(
                r"\text{log loss} = -\frac{1}{N}\sum_{i=1}^{N}"
                r"\Big[\,y_i \ln p_i + (1-y_i)\ln(1-p_i)\Big]"
            )
            .scale(0.9)
            .move_to(UP * 1.9)
        )
        ys = label("y = 1 remembered,  y = 0 forgotten", size=26, color=MUTED)
        ys.next_to(ll, DOWN, buff=0.35)
        with self.voiceover(
            'Average that penalty over every review, <bookmark mark="f"/>and you have log loss. '
            "Lower is better.",
            hold="step",
        ):
            self.at("f", FadeIn(ll, shift=UP * 0.1))
        with self.voiceover(
            '<bookmark mark="y"/>The y only picks which log counts: p when you remembered, '
            "one minus p when you forgot.",
            hold="step",
        ):
            self.at("y", FadeIn(ys))
        ada = Person("Ada", SPECIAL).move_to(LEFT * 5.2 + DOWN * 1.2)
        calc = (
            VGroup(
                label("9 in 10:  −ln 0.9 = 0.105", size=28),
                label("1 in 10:  −ln 0.1 = 2.303", size=28),
                label("log loss = 0.9 × 0.105 + 0.1 × 2.303 ≈ 0.33", size=28, color=ACCENT),
            )
            .arrange(DOWN, aligned_edge=LEFT, buff=0.25)
            .move_to(RIGHT * 0.6 + DOWN * 1.4)
        )
        with self.voiceover(
            '<bookmark mark="g"/>Now grade our fortune teller. <bookmark mark="a"/>Nine reviews '
            'in ten cost her zero point one; <bookmark mark="b"/>one in ten costs two point three.',
            hold="step",
        ):
            self.at("g", FadeIn(ada, shift=UP * 0.1))
            self.at("a", FadeIn(calc[0]))
            self.at("b", FadeIn(calc[1]))
        with self.voiceover(
            'Her log loss is <bookmark mark="c"/>zero point three three: far better than a '
            "coin's zero point six nine.",
            hold="reveal",
        ):
            self.at("c", FadeIn(calc[2], shift=UP * 0.1))
        with self.voiceover("And she has not looked at a single card.", hold="insight"):
            self.play(Indicate(ada, color=ACCENT), run_time=0.8)


def plot_point(v_x: float, v_y: float, origin, size: float = 5.0):
    """Map (predicted, remembered) in [0.5, 1] to the calibration plot."""
    return origin + RIGHT * (v_x - 0.5) / 0.5 * size + UP * (v_y - 0.5) / 0.5 * size


class S2Calibration(LessonScene):
    def construct(self) -> None:
        self.chapter("2", "Does 90 % mean 90 %?")
        o = LEFT * 5.6 + DOWN * 2.8
        x_axis = Line(o, o + RIGHT * 5.0, color=FG, stroke_width=3)
        y_axis = Line(o, o + UP * 5.0, color=FG, stroke_width=3)
        diag = DashedLine(o, o + RIGHT * 5.0 + UP * 5.0, color=MUTED, stroke_width=3)
        x_lab = label("predicted", size=22, color=MUTED).next_to(x_axis, DOWN, buff=0.15)
        y_lab = label("remembered", size=22, color=MUTED).next_to(y_axis, UP, buff=0.12)
        y_lab.align_to(y_axis, LEFT)
        lo = label("50 %", size=20, color=MUTED).next_to(o, DOWN, buff=0.15).shift(LEFT * 0.2)
        hi = label("100 %", size=20, color=MUTED).next_to(x_axis.get_end(), DOWN, buff=0.15)
        plot = VGroup(x_axis, y_axis, diag, x_lab, y_lab, lo, hi)
        intro = label("when it says 90 %,\ndo you remember 90 %?", size=30, color=ACCENT)
        intro.move_to(RIGHT * 3.6 + UP * 2.4)
        with self.voiceover(
            "Log loss blends two questions into one number. The first is calibration: "
            '<bookmark mark="c"/>when a model says ninety percent, do you remember ninety '
            "percent of those cards?",
            hold="step",
        ):
            self.at("c", FadeIn(intro, shift=UP * 0.1))
        with self.voiceover(
            'Gather reviews into groups, <bookmark mark="g"/>and plot each group\'s average '
            "prediction against how often you actually remembered.",
            hold="step",
        ):
            self.at("g", Create(plot), run_time=1.2)
        with self.voiceover(
            'A calibrated model <bookmark mark="d"/>lands on the diagonal.', hold="step"
        ):
            self.at("d", Indicate(diag, color=ACCENT, scale_factor=1.0), run_time=0.8)
        p_all = Dot(plot_point(0.9, 0.9, o), radius=0.12, color=SPECIAL)
        l_all = label("all reviews", size=22, color=SPECIAL).next_to(p_all, RIGHT, buff=0.25)
        with self.voiceover(
            'Put <bookmark mark="o"/>all of Ada\'s reviews into one group, and she lands right '
            "on it: ninety predicted, ninety remembered.",
            hold="step",
        ):
            self.at("o", FadeIn(p_all, scale=0.5), FadeIn(l_all))
        groups = label("groups: interval length,\nnumber of reviews, lapses", size=26)
        groups.next_to(intro, DOWN, buff=0.5)
        with self.voiceover(
            "So the benchmark groups more cleverly: "
            '<bookmark mark="b"/>by interval length, number of reviews and lapses. '
            "Cards that should behave alike.",
            hold="step",
        ):
            self.at("b", FadeIn(groups, shift=UP * 0.1))
        p_s = Dot(plot_point(0.9, 0.95, o), radius=0.12, color=PRIMARY)
        l_s = label("short intervals", size=22, color=PRIMARY).next_to(p_s, LEFT, buff=0.25)
        p_l = Dot(plot_point(0.9, 0.85, o), radius=0.12, color=PRIMARY)
        l_l = label("long intervals", size=22, color=PRIMARY).next_to(p_l, RIGHT, buff=0.25)
        with self.voiceover(
            '<bookmark mark="s"/>Short intervals: you remember ninety-five percent. '
            '<bookmark mark="l"/>Long intervals: eighty-five.',
            hold="step",
        ):
            self.at("s", FadeOut(p_all), FadeOut(l_all), FadeIn(p_s, scale=0.5), FadeIn(l_s))
            self.at("l", FadeIn(p_l, scale=0.5), FadeIn(l_l), run_time=0.6)
        mid = plot_point(0.9, 0.9, o)
        gap_s = Line(mid, p_s.get_center(), color=NEGATIVE, stroke_width=6)
        gap_l = Line(mid, p_l.get_center(), color=NEGATIVE, stroke_width=6)
        off = label("Ada: off by 5 points in each group", size=26, color=NEGATIVE)
        off.next_to(groups, DOWN, buff=0.5)
        with self.voiceover(
            'Ada says ninety for both, <bookmark mark="e"/>so she misses each group by five '
            "points.",
            hold="reveal",
        ):
            self.at("e", Create(gap_s), Create(gap_l), FadeIn(off, shift=UP * 0.1))
        rmse = MathTex(
            r"\text{RMSE(bins)} = \sqrt{\sum_b \tfrac{n_b}{N}\,(\bar p_b - \bar y_b)^2}"
        ).scale(0.8)
        rmse.next_to(off, DOWN, buff=0.45)
        val = label("Ada: 0.05", size=28, color=ACCENT, weight="BOLD").next_to(rmse, DOWN, buff=0.3)
        with self.voiceover(
            '<bookmark mark="w"/>Square each gap, weight it by the size of its group, average, '
            "and take the root.",
            hold="step",
        ):
            self.at("w", FadeIn(rmse, shift=UP * 0.1))
        with self.voiceover(
            'That is R-M-S-E over bins. <bookmark mark="v"/>Ada\'s is zero point zero five. '
            "Lower is better.",
            hold="reveal",
        ):
            self.at("v", FadeIn(val, shift=UP * 0.1))

        # the exploit
        self.clear_stage()
        heads = VGroup(*(tick(size=0.4) for _ in range(9)), cross(size=0.4))
        heads.arrange(RIGHT, buff=0.85).move_to(UP * 1.9)
        cap = label("one group: 10 reviews, 9 remembered", size=28).next_to(heads, UP, buff=0.45)
        preds = VGroup(
            *(
                label("0 %" if i == 0 else "100 %", size=22, color=NEGATIVE if i in (0, 9) else FG)
                for i in range(10)
            )
        )
        for p, h in zip(preds, heads, strict=True):
            p.next_to(h, DOWN, buff=0.4)
        with self.voiceover(
            "Because it only looks at group averages, this metric can be gamed. "
            '<bookmark mark="t"/>Take a group of ten reviews, nine remembered.',
            hold="step",
        ):
            self.at("t", FadeIn(cap), FadeIn(heads, lag_ratio=0.05), run_time=1.0)
        with self.voiceover(
            'Predict one hundred percent for nine of them <bookmark mark="z"/>and zero for one. '
            "But put the zero on a card you remembered.",
            hold="step",
        ):
            self.at("z", FadeIn(preds, lag_ratio=0.05), run_time=1.0)
        avg = label("average prediction 90 % = 90 % remembered", size=28, color=POSITIVE)
        avg.next_to(preds, DOWN, buff=0.5)
        with self.voiceover(
            '<bookmark mark="p"/>The average is still ninety: a perfect score for the group, '
            "with two predictions certain, and wrong.",
            hold="reveal",
        ):
            self.at("p", FadeIn(avg, shift=UP * 0.1))
        ex = VGroup(
            label("RMSE-BINS-EXPLOIT", size=28, color=NEGATIVE, weight="BOLD"),
            label("RMSE(bins)  0.0135  – best of all models", size=26),
            label("log loss  4.608", size=26, color=NEGATIVE),
        ).arrange(DOWN, buff=0.2)
        ex_card = Card(ex, NEGATIVE, pad=0.3).move_to(DOWN * 2.2)
        with self.voiceover(
            'The benchmark includes <bookmark mark="x"/>a baseline built to exploit this metric. '
            "Its R-M-S-E over bins is zero point zero one three five, better than every real "
            "model.",
            hold="step",
        ):
            self.at("x", FadeOut(avg), FadeIn(ex_card, shift=UP * 0.1))
        with self.voiceover(
            'Its log loss is <bookmark mark="l"/>four point six: the score of saying '
            "ninety-nine percent and being wrong, on every single review.",
            hold="insight",
        ):
            self.at("l", Indicate(ex[2], color=NEGATIVE))
        with self.voiceover(
            "One number can be gamed. That is why the benchmark always reports three.",
            hold="reveal",
        ):
            pass
        self.checkpoint(
            "Model A says 99 %, model B says 60 % – and you forget.\n"
            "How many times larger is A's log-loss penalty?",
            "About 5 times:  −ln 0.01 ≈ 4.6  vs.  −ln 0.4 ≈ 0.92",
        )


class S3Auc(LessonScene):
    def construct(self) -> None:
        self.chapter("3", "Ranking, not probability")
        row = ada_row().move_to(UP * 0.6)
        with self.voiceover(
            "The second question: can the model tell the cards you will remember "
            'from the ones you will forget? <bookmark mark="a"/>Ada cannot.',
            hold="step",
        ):
            self.at("a", FadeIn(row, shift=UP * 0.1))
        with self.voiceover("She gives every card the same ninety percent.", hold="step"):
            self.play(Indicate(row[1], color=ACCENT), run_time=0.8)
        self.clear_stage()
        rem = VGroup(*(Card(v, POSITIVE, pad=0.18) for v in ("95 %", "80 %", "70 %")))
        forg = VGroup(*(Card(v, NEGATIVE, pad=0.18) for v in ("75 %", "40 %")))
        ys = [1.0, -0.2, -1.4]
        xs = [0.6, 2.6]
        for c, y in zip(rem, ys, strict=True):
            c.move_to([-1.6, y, 0])
        for c, x in zip(forg, xs, strict=True):
            c.move_to([x, 2.2, 0])
        rem_lab = label("remembered", size=26, color=POSITIVE).next_to(rem, LEFT, buff=0.5)
        forg_lab = label("forgotten", size=26, color=NEGATIVE).next_to(forg, RIGHT, buff=0.5)
        with self.voiceover(
            'Here is a sharper model on five reviews. <bookmark mark="r"/>Three you remembered, '
            '<bookmark mark="f"/>two you forgot.',
            hold="step",
        ):
            self.at("r", FadeIn(rem, lag_ratio=0.2), FadeIn(rem_lab))
            self.at("f", FadeIn(forg, lag_ratio=0.2), FadeIn(forg_lab))
        cells = VGroup()
        marks = VGroup()
        for i, y in enumerate(ys):
            for j, x in enumerate(xs):
                box = Rectangle(width=1.3, height=0.9, color=MUTED, stroke_width=2)
                box.move_to([x, y, 0])
                cells.add(box)
                ok = (95, 80, 70)[i] > (75, 40)[j]
                marks.add((tick(size=0.4) if ok else cross(size=0.4)).move_to(box))
        with self.voiceover(
            'Pair every remembered review <bookmark mark="p"/>with every forgotten one: six pairs.',
            hold="step",
        ):
            self.at("p", Create(cells, lag_ratio=0.1), run_time=1.0)
        bad = marks[4]
        good = VGroup(*(m for k, m in enumerate(marks) if k != 4))
        with self.voiceover(
            "In each pair, did the remembered card get the higher prediction? "
            '<bookmark mark="y"/>Five times, yes.',
            hold="step",
        ):
            self.at("y", FadeIn(good, lag_ratio=0.15), run_time=1.2)
        with self.voiceover(
            'Once, no: <bookmark mark="n"/>seventy percent against seventy-five.', hold="step"
        ):
            self.at("n", FadeIn(bad, scale=0.6))
        auc = label("AUC = 5 / 6 ≈ 0.83", size=32, color=ACCENT, weight="BOLD")
        auc.move_to(DOWN * 2.7)
        with self.voiceover(
            'Five out of six pairs in the right order: <bookmark mark="a"/>an A-U-C of zero '
            "point eight three.",
            hold="reveal",
        ):
            self.at("a", FadeIn(auc, shift=UP * 0.1))
        self.clear_stage()
        scale = (
            VGroup(
                label("1.0  perfect order", size=30, color=POSITIVE),
                label("0.5  coin flip – and Ada: every pair a tie", size=30, color=SPECIAL),
            )
            .arrange(DOWN, aligned_edge=LEFT, buff=0.35)
            .move_to(UP * 1.6)
        )
        with self.voiceover(
            "Over the whole data set, that is the chance a random remembered review was rated "
            'above a random forgotten one. <bookmark mark="o"/>One means a perfect order.',
            hold="step",
        ):
            self.at("o", FadeIn(scale[0], shift=UP * 0.1))
        with self.voiceover(
            '<bookmark mark="h"/>A half means a coin flip, and that is Ada: every pair is a tie, '
            "and a tie counts half.",
            hold="insight",
        ):
            self.at("h", FadeIn(scale[1], shift=UP * 0.1))
        squash = label("90 %  80 %  70 %   →   55 %  54 %  53 %:  same order, same AUC", size=26)
        squash.next_to(scale, DOWN, buff=0.8)
        with self.voiceover(
            'And A-U-C ignores the scale: <bookmark mark="q"/>squeeze every prediction toward '
            "fifty percent, and as long as the order stays, so does the A-U-C.",
            hold="reveal",
        ):
            self.at("q", FadeIn(squash, shift=UP * 0.1))
        with self.voiceover(
            "A high A-U-C means the model knows which of two cards is weaker, "
            "even if it cannot say by how much.",
            hold="step",
        ):
            self.play(Indicate(squash, color=PRIMARY, scale_factor=1.03), run_time=0.8)
        split = VGroup(
            Card(label("log loss", size=28), ACCENT),
            Card(label("RMSE(bins)", size=28), ACCENT),
            Card(label("AUC", size=28), PRIMARY),
        ).arrange(RIGHT, buff=0.6)
        split.next_to(squash, DOWN, buff=0.8)
        tags = VGroup(
            label("calibration", size=24, color=ACCENT).next_to(split[:2], DOWN, buff=0.25),
            label("ranking", size=24, color=PRIMARY).next_to(split[2], DOWN, buff=0.25),
        )
        with self.voiceover(
            'So the three numbers split the work: <bookmark mark="c"/>log loss and R-M-S-E '
            'grade calibration, <bookmark mark="r"/>A-U-C grades ranking.',
            hold="insight",
        ):
            self.at("c", FadeIn(split[:2]), FadeIn(tags[0]))
            self.at("r", FadeIn(split[2]), FadeIn(tags[1]))
        self.checkpoint(
            "One group: 400 reviews, the model says 95 %, you remember 85 %.\n"
            "The other 1,600 reviews are spot on. RMSE(bins)?",
            "√(400 · 0.10² / 2000) = √0.002 ≈ 0.045",
        )


BOARD = [
    ("RWKV-Instant", "0.2773", "0.0250", "0.8329"),
    ("RWKV-Curve", "0.3193", "0.0540", "0.7683"),
    ("GRU", "0.3328", "0.0549", "0.7324"),
    ("FSRS-7", "0.3401", "0.0634", "0.7167"),
    ("FSRS-6", "0.3460", "0.0653", "0.7034"),
    ("AVG", "0.3945", "0.1034", "0.4997"),
    ("HLR", "0.4694", "0.1275", "0.6369"),
    ("RMSE-BINS-EXPLOIT", "4.608", "0.0135", "0.6548"),
]


class S4Benchmark(LessonScene):
    def construct(self) -> None:
        self.chapter("4", "The exam: 350 million reviews")
        facts = (
            VGroup(
                label("9,999 collections", size=36, weight="BOLD"),
                label("349,923,850 graded reviews", size=36, weight="BOLD"),
                label("≈ 4,800 years at 200 reviews a day", size=28, color=MUTED),
            )
            .arrange(DOWN, buff=0.35)
            .move_to(UP * 1.5)
        )
        with self.voiceover(
            'Now the real exam. <bookmark mark="c"/>Nine thousand nine hundred ninety-nine '
            'Anki collections, <bookmark mark="r"/>about three hundred fifty million graded '
            "reviews.",
            hold="step",
        ):
            self.at("c", FadeIn(facts[0], shift=UP * 0.1))
            self.at("r", FadeIn(facts[1], shift=UP * 0.1))
        with self.voiceover(
            'At two hundred reviews a day, <bookmark mark="y"/>that is nearly five thousand '
            "years of one person's reviewing.",
            hold="reveal",
        ):
            self.at("y", FadeIn(facts[2], shift=UP * 0.1))
        bar_train = Rectangle(width=7.0, height=0.5, stroke_width=0).set_fill(PRIMARY, 0.8)
        bar_test = Rectangle(width=3.0, height=0.5, stroke_width=0).set_fill(ACCENT, 0.9)
        bars = VGroup(bar_train, bar_test).arrange(RIGHT, buff=0.08).move_to(DOWN * 1.4)
        t_lab = label("learn: older reviews", size=26, color=PRIMARY).next_to(bar_train, DOWN)
        e_lab = label("graded: newer", size=26, color=ACCENT).next_to(bar_test, DOWN)
        who = label("one user's reviews, in time order  →", size=24, color=MUTED)
        who.next_to(bars, UP, buff=0.25)
        with self.voiceover(
            "Each model is tested the way you would use it: "
            '<bookmark mark="t"/>for every user, it learns from the older reviews, '
            '<bookmark mark="n"/>and is graded on the newer ones.',
            hold="step",
        ):
            self.at("t", FadeIn(who), FadeIn(bar_train), FadeIn(t_lab))
            self.at("n", FadeIn(bar_test), FadeIn(e_lab))
        with self.voiceover(
            "If it could see the future, it would be graded on answers it had already seen.",
            hold="reveal",
        ):
            self.play(Indicate(bar_test, color=NEGATIVE, scale_factor=1.05), run_time=0.8)
        with self.voiceover(
            "A random shuffle would let a model learn from your answer to a card in March, "
            "then be tested on the same card in January.",
            hold="step",
        ):
            self.play(Indicate(bar_train, color=PRIMARY, scale_factor=1.02), run_time=0.8)

        # the scoreboard
        self.clear_stage()
        xs = [-3.6, 1.0, 3.3, 5.5]
        top = 2.9
        head = VGroup(*(
            label(t, size=24, color=MUTED).move_to([x, top, 0])
            for t, x in zip(("model", "log loss ↓", "RMSE(bins) ↓", "AUC ↑"), xs, strict=True)
        ))  # fmt: skip
        rows = VGroup()
        for i, cells in enumerate(BOARD):
            y = top - 0.75 - i * 0.62
            rows.add(VGroup(*(
                label(c, size=26).move_to([x, y, 0]) for c, x in zip(cells, xs, strict=True)
            )))  # fmt: skip
        with self.voiceover('<bookmark mark="s"/>Here is the scoreboard.', hold="step"):
            self.at("s", FadeIn(head), FadeIn(rows, lag_ratio=0.08), run_time=1.4)

        def frame(i: int, color: str) -> Rectangle:
            box = Rectangle(width=12.6, height=0.56, color=color, stroke_width=3)
            return box.move_to([0.45, rows[i].get_y(), 0])

        f_avg = frame(5, SPECIAL)
        with self.voiceover(
            'Near the bottom, <bookmark mark="a"/>AVG, which always predicts the average. '
            "Its A-U-C is zero point five. That is Ada.",
            hold="reveal",
        ):
            self.at("a", Create(f_avg))
        f_hlr = frame(6, PRIMARY)
        with self.voiceover(
            '<bookmark mark="h"/>H-L-R, an older model, has a worse log loss than AVG but a '
            "better A-U-C: it can rank cards, but its probabilities are off.",
            hold="reveal",
        ):
            self.at("h", FadeOut(f_avg), Create(f_hlr))
        f_ex = frame(7, NEGATIVE)
        with self.voiceover(
            '<bookmark mark="e"/>The exploit: the best R-M-S-E, and a log loss about '
            "ten times worse than anything else.",
            hold="reveal",
        ):
            self.at("e", FadeOut(f_hlr), Create(f_ex))
        f_fsrs = VGroup(frame(3, ACCENT), frame(4, ACCENT))
        with self.voiceover(
            '<bookmark mark="f"/>F-S-R-S six and seven, the hand-built curves from Video 1.1, '
            "sit at zero point three four.",
            hold="step",
        ):
            self.at("f", FadeOut(f_ex), Create(f_fsrs))
        f_gru = frame(2, ACCENT)
        with self.voiceover(
            '<bookmark mark="g"/>A small neural network, G-R-U, edges past them on all three '
            "metrics.",
            hold="step",
        ):
            self.at("g", FadeOut(f_fsrs), Create(f_gru))
        with self.voiceover(
            "R-M-S-E reads roughly as a typical miss in percentage points: "
            '<bookmark mark="m"/>about six and a half for F-S-R-S six.',
            hold="step",
        ):
            self.at("m", Indicate(rows[4][2], color=ACCENT))
        f_top = VGroup(frame(0, POSITIVE), frame(1, POSITIVE))
        with self.voiceover(
            '<bookmark mark="r"/>At the top, two versions of R-W-K-V. Instant leads every real '
            "model on all three metrics; Curve is second on log loss.",
            hold="reveal",
        ):
            self.at("r", FadeOut(f_gru), Create(f_top))
        with self.voiceover(
            '<bookmark mark="i"/>Instant misses by about two and a half.', hold="step"
        ):
            self.at("i", Indicate(rows[0][2], color=POSITIVE))
        with self.voiceover(
            "Zero point two eight against F-S-R-S seven's zero point three four is a large gap.",
            hold="step",
        ):
            self.play(Indicate(rows[0][1], color=POSITIVE), Indicate(rows[3][1], color=ACCENT))
        with self.voiceover(
            "Video 1.3 opens up what R-W-K-V is. Video 1.4 asks whether that lead is fair.",
            hold="reveal",
        ):
            pass
        self.checkpoint(
            "Remembered: 90 %, 60 %.   Forgotten: 70 %, 30 %.\nWhat is the AUC?",
            "3 of 4 pairs in the right order (60 % vs. 70 % is out of order): AUC = 0.75",
        )


class S5Outro(LessonScene):
    def construct(self) -> None:
        self.chapter("5", "What a scheduler needs")
        ada = Person("Ada", SPECIAL).move_to(LEFT * 4.6 + UP * 0.6)
        verdict = (
            VGroup(
                label("calibrated on average", size=28, color=POSITIVE),
                label("cannot rank a single card", size=28, color=NEGATIVE),
            )
            .arrange(DOWN, aligned_edge=LEFT, buff=0.3)
            .next_to(ada, RIGHT, buff=0.8)
        )
        with self.voiceover(
            '<bookmark mark="a"/>So, Ada: <bookmark mark="c"/>calibrated on average, '
            '<bookmark mark="r"/>unable to rank a single card.',
            hold="step",
        ):
            self.at("a", FadeIn(ada, shift=UP * 0.1))
            self.at("c", FadeIn(verdict[0]))
            self.at("r", FadeIn(verdict[1]))
        needs = (
            VGroup(
                label("calibration → when: the interval at your desired retention", size=28),
                label("ranking → what first: the order of today's cards", size=28),
            )
            .arrange(DOWN, aligned_edge=LEFT, buff=0.3)
            .move_to(DOWN * 2.0)
        )
        with self.voiceover(
            "A scheduler needs both. "
            '<bookmark mark="w"/>Calibration decides when a card reaches your desired '
            "retention, and so how long the interval is.",
            hold="step",
        ):
            self.at("w", FadeIn(needs[0], shift=UP * 0.1))
        with self.voiceover(
            '<bookmark mark="o"/>Ranking decides which card comes first when you cannot do '
            "them all.",
            hold="insight",
        ):
            self.at("o", FadeIn(needs[1], shift=UP * 0.1))
        with self.voiceover(
            "A model that ranks perfectly but says seventy where the truth is ninety "
            "would make every interval too short.",
            hold="insight",
        ):
            self.play(Indicate(needs[0], color=ACCENT), run_time=0.8)
        with self.voiceover(
            "So when someone tells you their model is better, ask which of the three numbers "
            "they mean.",
            hold="reveal",
        ):
            pass
        self.clear_stage()
        self.recall(
            [
                "A model has AUC 0.85 but a worse log loss than AVG.\n"
                "Would you let it set intervals? Order today's cards?",
                "HLR: worse log loss than AVG, but a higher AUC.\nWhat is each of them better at?",
                "Why must each user's test reviews\nbe newer than their training reviews?",
            ]
        )
