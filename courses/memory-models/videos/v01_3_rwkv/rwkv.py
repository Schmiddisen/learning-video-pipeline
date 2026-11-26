"""Video 1.3 – A memory that reads your whole collection: how RWKV keeps a review log in a fixed-size state.  (sources: srs-benchmark, RWKV4Anki, RWKV-LM, Anki fork FAQ)"""

# Beats
#   S0  hook: 100,000 reviews – how much more work is review 100,000 than review 11?
#       (predict-before-reveal); transformer ≈ 10,000×, recurrent: the same. Pretest.
#   S1  recurrence: look-back-at-everything (attention, KV cache, ~5 billion comparisons)
#       vs one page of notes rewritten after each review (fixed state, constant memory)
#   S2  RWKV's WKV: key/value/receptance; a fading weighted average kept as two running
#       numbers; worked example with two decays (0.9 → 0.71, 0.1 → 0.10); half-lives;
#       sigmoid gate, channel mixing; version honesty; parallel training. Check (S1).
#   S3  what it sees: whole collection interleaved + extra inputs; one shared model,
#       2,762,884 params, 5,000 / 5,000 users; history → state, not weights. Check (S2).
#   S4  Curve vs Instant: a curve you can schedule with vs a "right now" number; odd
#       outputs; leaderboard callback. Check (S3).
#   S5  bridge into 1.4; recall.
# Opening: a computation the viewer guesses. Building: let them invent it (S1), worked
# example with real numbers (S2). Ending: open question that Video 1.4 answers.
#
# Numbers (verified): 99,999 / 10 ≈ 10,000; Σ comparisons = 100,000·99,999/2 ≈ 5.0e9;
# keep 0.9 over ✓✓✓✗: num 2.439, den 3.439 → 0.709; keep 0.1: 0.111 / 1.111 → 0.0999;
# half-life ln 0.5 / ln 0.99 = 69.0 steps, ln 0.5 / ln 0.9999 = 6,931 steps (÷200/day ≈ 35 days);
# checkpoint: keep 0.5 over ✗✓: num 1, den 1.5 → 0.67.

from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    ArcBetweenPoints,
    Arrow,
    Axes,
    Create,
    CurvedArrow,
    DashedLine,
    Dot,
    FadeIn,
    FadeOut,
    GrowArrow,
    GrowFromEdge,
    Indicate,
    LaggedStart,
    MathTex,
    Rectangle,
    Square,
    SurroundingRectangle,
    VGroup,
)

from lvp.props import question
from lvp.style import (
    ACCENT,
    FG,
    MUTED,
    NEGATIVE,
    POSITIVE,
    PRIMARY,
    SPECIAL,
    TEAL,
    Card,
    LessonScene,
    label,
)

SERIES = "Memory Models · Video 1.3"

# a short review log: True = remembered, False = forgotten
LOG = [True, True, False, True, True, True, False, True, True, True] * 4


def review_strip(n: int = 40, w: float = 0.2, h: float = 0.5) -> VGroup:
    """A review log as a row of thin bars: green remembered, red forgotten."""
    bars = VGroup(
        *(
            Rectangle(width=w, height=h, stroke_width=0).set_fill(
                POSITIVE if LOG[i % len(LOG)] else NEGATIVE, 0.85
            )
            for i in range(n)
        )
    )
    return bars.arrange(RIGHT, buff=0.06)


def token(text: str, ok: bool) -> Card:
    return Card(
        label(text, size=22, color=POSITIVE if ok else NEGATIVE),
        POSITIVE if ok else NEGATIVE,
        pad=0.12,
    )


class S0Hook(LessonScene):
    def construct(self) -> None:
        q = question(
            "Predicting your next review:\nhow much more work is review 100,000\nthan review 11?"
        )
        q.move_to(UP * 1.9)
        self.opening(SERIES, q)
        strip = review_strip().move_to(DOWN * 0.2)
        cap = label("your review log, oldest → newest", size=24, color=MUTED).next_to(
            strip, DOWN, buff=0.3
        )
        with self.voiceover(
            'Say your collection holds <bookmark mark="s"/>a hundred thousand reviews, '
            "every card, in the order you did them.",
            hold="step",
        ):
            self.at("s", Create(strip, lag_ratio=0.05), FadeIn(cap), run_time=1.5)
        with self.voiceover(
            "A model has to predict the next one, and it may use everything before it.",
            hold="step",
        ):
            self.play(Indicate(strip[-1], color=ACCENT, scale_factor=1.6), run_time=1.0)
        with self.voiceover(
            "How much more work is the hundred-thousandth prediction than the eleventh? Guess.",
            hold="question",
        ):
            pass
        t_row = label(
            "transformer: 99,999 look-backs vs 10  →  about 10,000× the work",
            size=26,
            color=NEGATIVE,
        )
        r_row = label(
            "recurrent model: one fixed-size update  →  the same work", size=26, color=POSITIVE
        )
        VGroup(t_row, r_row).arrange(DOWN, buff=0.3).move_to(DOWN * 2.6)
        with self.voiceover(
            'For <bookmark mark="t"/>a transformer, the kind of network behind chatbots, '
            "about ten thousand times more.",
            hold="reveal",
        ):
            self.at("t", FadeIn(t_row, shift=UP * 0.1))
        with self.voiceover(
            'For <bookmark mark="r"/>the model in this video: exactly the same.',
            hold="insight",
        ):
            self.at("r", FadeIn(r_row, shift=UP * 0.1))
        self.title_card(
            "A memory that reads your whole collection",
            say="First, why a fixed-size memory is possible at all; then RWKV's way of filling it, "
            "what it gets to read, and the two ways to ask it about a card.",
        )
        self.pretest(
            [
                "How could a model use 100,000 reviews\nwhile storing only a fixed set of numbers?",
                "A model trained only on other people's reviews –\nhow could it still adapt to you?",
            ]
        )


class S1Recurrence(LessonScene):
    def construct(self) -> None:
        self.chapter("1", "One page of notes")
        past = VGroup(
            *(Square(0.42, stroke_width=2, color=MUTED).set_fill(MUTED, 0.25) for _ in range(9))
        )
        past.arrange(RIGHT, buff=0.18)
        new = Square(0.42, stroke_width=3, color=ACCENT).set_fill(ACCENT, 0.8)
        row = VGroup(past, new).arrange(RIGHT, buff=0.5).move_to(UP * 1.2)
        new_l = label("review n", size=22, color=ACCENT).next_to(new, DOWN, buff=0.2)
        arcs = VGroup(
            *(
                ArcBetweenPoints(
                    new.get_top() + UP * 0.05,
                    p.get_top() + UP * 0.05,
                    angle=1.2,
                    color=ACCENT,
                    stroke_width=2,
                )
                for p in past
            )
        )
        with self.voiceover(
            'Start with the obvious design: <bookmark mark="l"/>to predict review number n, '
            "look back at every earlier review.",
            hold="step",
        ):
            self.play(FadeIn(row), FadeIn(new_l), run_time=0.6)
            self.at("l", Create(arcs, lag_ratio=0.1), run_time=1.2)
        cache = VGroup(
            *(
                Rectangle(width=0.42, height=0.16, stroke_width=1, color=PRIMARY).set_fill(
                    PRIMARY, 0.5
                )
                for _ in range(10)
            )
        )
        cache.arrange(UP, buff=0.04).move_to(DOWN * 1.6 + LEFT * 4.5, aligned_edge=DOWN)
        cache_l = label("KV cache:\none key and value\nper past review", size=24, color=PRIMARY)
        cache_l.next_to(cache, RIGHT, buff=0.4).align_to(cache, DOWN)
        with self.voiceover(
            "That's what a transformer does. Each new review is compared with all earlier ones, "
            '<bookmark mark="c"/>and their keys and values sit in a cache that grows with every review.',
            hold="reveal",
        ):
            self.at(
                "c",
                LaggedStart(*(GrowFromEdge(b, DOWN) for b in cache), lag_ratio=0.15),
                FadeIn(cache_l),
                run_time=1.5,
            )
        total = label(
            "replay 100,000 reviews  ≈  5,000,000,000 comparisons", size=28, color=NEGATIVE
        )
        total.move_to(DOWN * 2.9 + RIGHT * 1.6)
        with self.voiceover(
            'Replaying a hundred thousand reviews that way costs <bookmark mark="b"/>about five '
            "billion comparisons, and the cache holds all hundred thousand.",
            hold="insight",
        ):
            self.at("b", FadeIn(total, shift=UP * 0.1))
        self.clear_stage()

        page = VGroup(
            *(
                Square(0.5, stroke_width=2, color=PRIMARY).set_fill(PRIMARY, 0.15 + 0.08 * (i % 5))
                for i in range(12)
            )
        )
        page.arrange_in_grid(rows=3, cols=4, buff=0.08).move_to(RIGHT * 2.6 + UP * 0.6)
        page_l = label("state: a fixed list of numbers", size=24, color=PRIMARY).next_to(
            page, UP, buff=0.3
        )
        loop = CurvedArrow(
            page.get_right() + DOWN * 0.3 + RIGHT * 0.1,
            page.get_right() + UP * 0.3 + RIGHT * 0.1,
            angle=2.6,
            color=PRIMARY,
        )
        with self.voiceover(
            "The alternative is a single page of notes that you rewrite after every review.",
            hold="step",
        ):
            self.play(FadeIn(page), run_time=0.8)
        with self.voiceover(
            'That page is <bookmark mark="s"/>the state: a fixed list of numbers.',
            hold="step",
        ):
            self.at("s", FadeIn(page_l), Create(loop))
        rule = label("new state = f(old state, this review)", size=30, color=FG).move_to(
            DOWN * 1.4 + RIGHT * 1.6
        )
        stream = (
            VGroup(
                token("A ✓", True),
                token("C ✓", True),
                token("A ✗", False),
                token("B ✓", True),
                token("D ✓", True),
            )
            .arrange(RIGHT, buff=0.15)
            .move_to(LEFT * 3.8 + UP * 0.6)
        )
        stream_l = label("all cards, in time order", size=24, color=MUTED).next_to(
            stream, UP, buff=0.3
        )
        feed = Arrow(stream.get_right(), page.get_left(), buff=0.15, color=MUTED)
        with self.voiceover(
            'Each review updates it: <bookmark mark="f"/>the new state is a function of the old state '
            "and this review.",
            hold="step",
        ):
            self.at("f", FadeIn(rule, shift=UP * 0.1))
        with self.voiceover(
            'The reviews arrive <bookmark mark="o"/>in time order, all cards mixed, exactly as you did them.',
            hold="step",
        ):
            self.at("o", FadeIn(stream), FadeIn(stream_l), GrowArrow(feed))
        for i in range(2):
            tok = stream[-1 - i]
            self.play(
                tok.animate.move_to(page.get_center()).scale(0.3).set_opacity(0),
                *(
                    c.animate.set_fill(PRIMARY, 0.15 + 0.08 * ((j + i + 2) % 5))
                    for j, c in enumerate(page)
                ),
                run_time=0.7,
            )
        cost = (
            VGroup(
                label("100,000 reviews  →  100,000 cheap updates", size=26, color=POSITIVE),
                label("memory: the same page, always", size=26, color=POSITIVE),
            )
            .arrange(DOWN, buff=0.25)
            .move_to(DOWN * 2.7 + RIGHT * 1.6)
        )
        with self.voiceover(
            'A hundred thousand reviews are <bookmark mark="u"/>a hundred thousand cheap updates, '
            '<bookmark mark="m"/>and memory never grows.',
            hold="reveal",
        ):
            self.at("u", FadeIn(cost[0], shift=UP * 0.1))
            self.at("m", FadeIn(cost[1], shift=UP * 0.1))
        with self.voiceover(
            "That is a recurrent network. Its price is just as plain: one page can't hold everything.",
            hold="step",
        ):
            pass
        with self.voiceover(
            "That is less strange than it sounds: you don't remember every past review of a card "
            "either, only how well you know it now.",
            hold="step",
        ):
            pass
        with self.voiceover(
            "The whole design question is what to keep, and what to let fade.",
            hold="insight",
        ):
            self.play(page.animate.set_fill(PRIMARY, 0.08), run_time=1.2)
        self.clear_stage()
        fade = review_strip(40, w=0.22, h=0.8)
        for i, b in enumerate(fade):
            b.set_fill(opacity=0.08 + 0.9 * (i / 39) ** 2)
        fade.move_to(DOWN * 0.2)
        old = (
            label("last spring", size=24, color=MUTED)
            .next_to(fade, DOWN, buff=0.3)
            .align_to(fade, LEFT)
        )
        new = (
            label("this morning", size=24, color=FG)
            .next_to(fade, DOWN, buff=0.3)
            .align_to(fade, RIGHT)
        )
        with self.voiceover(
            'A hint: <bookmark mark="n"/>what you did this morning says more about your next review '
            '<bookmark mark="o"/>than what you did last spring, but last spring still says something.',
            hold="insight",
        ):
            self.at("n", FadeIn(fade), FadeIn(new), run_time=0.5)
            self.at("o", FadeIn(old), run_time=0.4)


class S2Wkv(LessonScene):
    def construct(self) -> None:
        self.chapter("2", "A weighted average that fades")
        rev = token("one review", True).move_to(UP * 2.7)
        kvr = (
            VGroup(
                Card(label("key  k", size=26, color=ACCENT), ACCENT, pad=0.15),
                Card(label("value  v", size=26, color=PRIMARY), PRIMARY, pad=0.15),
                Card(label("receptance  r", size=26, color=SPECIAL), SPECIAL, pad=0.15),
            )
            .arrange(RIGHT, buff=0.6)
            .move_to(UP * 1.2)
        )
        arrows = VGroup(*(Arrow(rev.get_bottom(), c.get_top(), buff=0.1, color=MUTED, stroke_width=3)
                          for c in kvr))  # fmt: skip
        with self.voiceover(
            "RWKV answers with one idea: an average of the past whose weights fade.",
            hold="step",
        ):
            self.play(FadeIn(rev), run_time=0.6)
        with self.voiceover(
            'From each review, a learned layer computes three vectors: <bookmark mark="k"/>a key, '
            '<bookmark mark="v"/>a value, <bookmark mark="r"/>and a receptance.',
            hold="step",
        ):
            self.at("k", FadeIn(kvr[0]), GrowArrow(arrows[0]), run_time=0.5)
            self.at("v", FadeIn(kvr[1]), GrowArrow(arrows[1]), run_time=0.5)
            self.at("r", FadeIn(kvr[2]), GrowArrow(arrows[2]), run_time=0.5)
        with self.voiceover(
            "The value is what this review has to say; e to the power of the key is how loudly it says it.",
            hold="step",
        ):
            self.play(Indicate(kvr[1], color=PRIMARY), Indicate(kvr[0], color=ACCENT), run_time=1.2)
        avg = MathTex(
            r"\text{out}_t = \frac{\sum_{i \le t} d^{\,t-i}\, e^{k_i}\, v_i}{\sum_{i \le t} d^{\,t-i}\, e^{k_i}}",
            font_size=46,
        ).move_to(DOWN * 0.6)
        dnote = label(
            "d = e^(−w) < 1: a learned decay, one per channel", size=24, color=MUTED
        ).next_to(avg, DOWN, buff=0.3)
        with self.voiceover(
            'Each channel outputs <bookmark mark="a"/>the average of all past values, weighted by that loudness, ',
            hold="none",
        ):
            self.at("a", FadeIn(avg))
        with self.voiceover(
            '<bookmark mark="d"/>and at every step, every old weight is multiplied again by a learned decay factor below one.',
            hold="reveal",
        ):
            self.at("d", FadeIn(dnote))
        with self.voiceover(
            "That looks as if it needs the whole history again. It doesn't.",
            hold="step",
        ):
            pass
        self.clear_stage()
        rec = MathTex(
            r"\text{num} &\leftarrow e^{-w}\,\text{num} + e^{k}\,v\\"
            r"\text{den} &\leftarrow e^{-w}\,\text{den} + e^{k}\\"
            r"\text{out} &= \text{num} / \text{den}",
            font_size=44,
        ).move_to(UP * 0.9)
        box = SurroundingRectangle(rec, color=ACCENT, buff=0.3)
        with self.voiceover(
            'Keep <bookmark mark="n"/>two running numbers per channel: a numerator and a denominator.',
            hold="step",
        ):
            self.at("n", FadeIn(rec), Create(box))
        with self.voiceover(
            "Each review: shrink both, add the new review, divide. That is the whole state of this channel.",
            hold="insight",
        ):
            self.play(Indicate(rec, color=ACCENT, scale_factor=1.05), run_time=1.0)
        self.clear_stage()

        # worked example: two channels, reviews ✓ ✓ ✓ ✗
        head = VGroup(
            *(
                label(s, size=30, color=POSITIVE if s == "✓" else NEGATIVE)
                for s in ("✓", "✓", "✓", "✗")
            )
        )
        xs = [-1.6, 0.6, 2.8, 5.0]
        for h, x in zip(head, xs, strict=True):
            h.move_to([x, 2.0, 0])
        h_l = label("value", size=24, color=MUTED).move_to([-4.6, 2.0, 0])
        vals = VGroup(*(label(s, size=24, color=MUTED) for s in ("1", "1", "1", "0")))
        for v, x in zip(vals, xs, strict=True):
            v.move_to([x, 1.45, 0])
        slow = ["1 / 1", "1.9 / 1.9", "2.71 / 2.71", "2.44 / 3.44"]
        fast = ["1 / 1", "1.1 / 1.1", "1.11 / 1.11", "0.11 / 1.11"]
        slow_l = label("keeps 0.9", size=26, color=TEAL).move_to([-4.6, 0.5, 0])
        fast_l = label("keeps 0.1", size=26, color=SPECIAL).move_to([-4.6, -0.6, 0])
        slow_c = VGroup(
            *(
                label(s, size=26, color=TEAL).move_to([x, 0.5, 0])
                for s, x in zip(slow, xs, strict=True)
            )
        )
        fast_c = VGroup(
            *(
                label(s, size=26, color=SPECIAL).move_to([x, -0.6, 0])
                for s, x in zip(fast, xs, strict=True)
            )
        )
        cols = label("num / den after each review", size=22, color=MUTED).move_to([1.7, -1.35, 0])
        slow_out = label("→ 0.71", size=30, color=TEAL, weight="BOLD").move_to([4.6, -2.3, 0])
        fast_out = label("→ 0.10", size=30, color=SPECIAL, weight="BOLD").move_to([4.6, -3.0, 0])
        so_l = label("slow channel: “mostly fine”", size=26, color=TEAL).next_to(
            slow_out, LEFT, buff=0.5
        )
        fo_l = label("fast channel: “just failed”", size=26, color=SPECIAL).next_to(
            fast_out, LEFT, buff=0.5
        )
        with self.voiceover(
            'Try it. Pretend <bookmark mark="v"/>a channel\'s value is one for a remembered card and zero '
            "for a forgotten one, and every key is zero, so each new weight starts at one.",
            hold="step",
        ):
            self.at("v", FadeIn(head), FadeIn(h_l), FadeIn(vals))
        with self.voiceover(
            '<bookmark mark="s"/>A channel that keeps nine tenths per step: after three successes, '
            '<bookmark mark="t"/>numerator and denominator are both two point seven one.',
            hold="step",
        ):
            self.at("s", FadeIn(slow_l), FadeIn(cols), FadeIn(slow_c[0]))
            self.at("t", FadeIn(slow_c[1]), FadeIn(slow_c[2]), run_time=0.8)
        with self.voiceover(
            'Then the failure: <bookmark mark="f"/>two point four four over three point four four, '
            '<bookmark mark="o"/>about zero point seven one.',
            hold="reveal",
        ):
            self.at("f", FadeIn(slow_c[3]))
            self.at("o", FadeIn(slow_out), FadeIn(so_l))
        with self.voiceover(
            '<bookmark mark="s"/>A channel that keeps one tenth ends at <bookmark mark="f"/>zero point one one '
            'over one point one one: <bookmark mark="o"/>zero point one.',
            hold="reveal",
        ):
            self.at("s", FadeIn(fast_l), FadeIn(fast_c[:3]), run_time=0.8)
            self.at("f", FadeIn(fast_c[3]))
            self.at("o", FadeIn(fast_out), FadeIn(fo_l))
        with self.voiceover(
            "Same four reviews. One channel says you just failed; the other says you're mostly fine.",
            hold="insight",
        ):
            self.play(Indicate(VGroup(slow_out, fast_out), color=ACCENT), run_time=1.0)
        self.clear_stage()

        ax = Axes(x_range=[0, 8000, 2000], y_range=[0, 1, 0.5], x_length=9, y_length=3.2,
                  axis_config={"color": MUTED, "include_ticks": False}).move_to(DOWN * 0.3)  # fmt: skip
        x_l = (
            label("reviews ago", size=22, color=MUTED)
            .next_to(ax.x_axis, DOWN, buff=0.25)
            .align_to(ax.x_axis, RIGHT)
        )
        y_l = (
            label("weight left", size=22, color=MUTED)
            .next_to(ax.y_axis, UP, buff=0.15)
            .align_to(ax.y_axis, LEFT)
        )
        fast_g = ax.plot(lambda x: 0.99**x, x_range=[0, 600], color=SPECIAL)
        slow_g = ax.plot(lambda x: 0.9999**x, x_range=[0, 8000], color=TEAL)
        half = DashedLine(ax.c2p(0, 0.5), ax.c2p(8000, 0.5), color=MUTED, stroke_width=2)
        f_t = label("keeps 0.99: half gone after ≈ 69 reviews – today", size=24, color=SPECIAL)
        s_t = label("keeps 0.9999: ≈ 6,900 reviews – a month at 200 a day", size=24, color=TEAL)
        VGroup(f_t, s_t).arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to(UP * 2.6)
        with self.voiceover(
            "Each channel learns its own decay.",
            hold="none",
        ):
            self.play(Create(ax), FadeIn(x_l), FadeIn(y_l), Create(half), run_time=0.8)
        with self.voiceover(
            '<bookmark mark="f"/>Keep ninety-nine hundredths per review, and half the weight is gone after '
            "about seventy reviews: roughly today.",
            hold="step",
        ):
            self.at("f", Create(fast_g), FadeIn(f_t))
        with self.voiceover(
            '<bookmark mark="s"/>Keep nine thousand nine hundred ninety-nine ten-thousandths, and it takes about '
            "six thousand nine hundred: a month, at two hundred reviews a day.",
            hold="step",
        ):
            self.at("s", Create(slow_g), FadeIn(s_t), run_time=1.5)
        with self.voiceover(
            "With many channels side by side, the state holds today, this week and this month at once.",
            hold="insight",
        ):
            pass
        self.clear_stage()

        gate = MathTex(r"\text{output} = \sigma(r)\cdot \text{out}", font_size=46).move_to(UP * 1.9)
        gate_l = label(
            "σ squashes r to between 0 and 1: how much passes on", size=24, color=SPECIAL
        )
        gate_l.next_to(gate, DOWN, buff=0.3)
        mix = Card(
            label(
                "channel mixing: a gated feed-forward layer,\nmixing channels within one step",
                size=24,
            ),
            MUTED,
            pad=0.2,
        )
        mix.move_to(DOWN * 0.4)
        with self.voiceover(
            'The <bookmark mark="g"/>receptance, squashed through a sigmoid to between zero and one, '
            "decides how much of that average passes on.",
            hold="step",
        ):
            self.at("g", FadeIn(gate), FadeIn(gate_l))
        with self.voiceover(
            'A second block, <bookmark mark="m"/>channel mixing, is a gated feed-forward layer that mixes '
            "channels within one step.",
            hold="step",
        ):
            self.at("m", FadeIn(mix, shift=UP * 0.1))
        honest = label(
            "simplified RWKV-4 core – the Anki model's exact version is not published",
            size=22,
            color=MUTED,
            slant="ITALIC",
        ).move_to(DOWN * 2.0)
        with self.voiceover(
            "The real formula also gives the newest review a separate learned bonus, "
            "and newer RWKV versions replace the two numbers with whole matrices.",
            hold="step",
        ):
            self.play(FadeIn(honest), run_time=0.6)
        with self.voiceover(
            "Which version the Anki model uses isn't published; what you've seen is the core they share.",
            hold="reveal",
        ):
            self.play(Indicate(honest, color=ACCENT, scale_factor=1.03), run_time=0.8)
        self.clear_stage()

        train = VGroup(
            label("training", size=30, color=PRIMARY, weight="BOLD"),
            label("all positions at once,\nlike a transformer", size=26),
        ).arrange(DOWN, buff=0.3)
        use = VGroup(
            label("in use", size=30, color=POSITIVE, weight="BOLD"),
            label("one review at a time,\nlike a recurrent network", size=26),
        ).arrange(DOWN, buff=0.3)
        VGroup(train, use).arrange(RIGHT, buff=2.0).move_to(UP * 0.2)
        why = label(
            "weights depend only on how many steps back: d^(t−i)", size=24, color=MUTED
        ).move_to(DOWN * 2.0)
        with self.voiceover(
            'One more consequence: <bookmark mark="w"/>a weight depends only on how far back a review lies.',
            hold="step",
        ):
            self.at("w", FadeIn(why))
        with self.voiceover(
            'So in <bookmark mark="t"/>training, all positions are computed at once, like a transformer; '
            '<bookmark mark="u"/>in use, it runs step by step, like a recurrent network.',
            hold="insight",
        ):
            self.at("t", FadeIn(train, shift=UP * 0.1), run_time=0.4)
            self.at("u", FadeIn(use, shift=UP * 0.1), run_time=0.4)
        self.checkpoint(
            "A collection grows from 50,000 to 100,000 reviews.\n"
            "What happens to a transformer's KV cache –\nand to a recurrent model's state?",
            "KV cache doubles (one entry per review); the state stays the same size",
        )


class S3Inputs(LessonScene):
    def construct(self) -> None:
        self.chapter("3", "What it gets to read")
        fsrs = VGroup(
            label("FSRS", size=30, color=MUTED, weight="BOLD"),
            label("one card:\nits intervals\nand grades", size=24, color=MUTED),
        ).arrange(DOWN, buff=0.3)
        self.place(fsrs, "B1", "D2")
        with self.voiceover(
            "FSRS, from Video 1.1, looks at one card at a time: its own intervals and grades.",
            hold="step",
        ):
            self.play(FadeIn(fsrs), run_time=0.6)
        head = label("RWKV: the whole collection, every card interleaved", size=28, color=PRIMARY)
        head.move_to(UP * 2.6 + RIGHT * 1.6)
        items = VGroup(
            label("interval and grade", size=24),
            label("how long you took to answer", size=24),
            label("new cards and reviews done today", size=24),
            label("sibling cards of the same note", size=24),
            label("deck and preset hierarchy", size=24),
            label("day of week, month, year", size=24),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        dots = VGroup(
            *(Dot(radius=0.06, color=PRIMARY).next_to(it, LEFT, buff=0.2) for it in items)
        )
        VGroup(dots, items).move_to(RIGHT * 1.9 + DOWN * 0.3)
        with self.voiceover(
            'RWKV reads <bookmark mark="h"/>the whole collection\'s log in time order, every card interleaved.',
            hold="step",
        ):
            self.at("h", FadeIn(head))
        with self.voiceover(
            '<bookmark mark="a"/>Each step carries the interval and the grade, '
            '<bookmark mark="b"/>how long you took to answer, '
            '<bookmark mark="c"/>how many new cards and reviews you\'ve done today, '
            '<bookmark mark="d"/>the card\'s siblings, <bookmark mark="e"/>its deck and preset, '
            '<bookmark mark="f"/>and the day of the week, month and year.',
            hold="reveal",
        ):
            for i, m in enumerate("abcdef"):
                self.at(m, FadeIn(items[i]), FadeIn(dots[i]), run_time=0.4)
        with self.voiceover(
            "So a slow answer on a sibling this morning can move the prediction for this card.",
            hold="insight",
        ):
            self.play(
                Indicate(VGroup(items[1], items[3]), color=ACCENT, scale_factor=1.05), run_time=1.0
            )
        self.clear_stage()

        model = Card(
            VGroup(
                label("one shared model", size=28, color=PRIMARY, weight="BOLD"),
                label("2,762,884 parameters", size=26),
            ).arrange(DOWN, buff=0.2),
            PRIMARY,
            pad=0.3,
        ).move_to(UP * 1.2)
        train = label("trained on\n5,000 users", size=24, color=MUTED).move_to(
            UP * 1.2 + LEFT * 4.9
        )
        test = label("tested on\n5,000 others", size=24, color=MUTED).move_to(
            UP * 1.2 + RIGHT * 4.9
        )
        a1 = Arrow(train.get_right(), model.get_left(), buff=0.15, color=MUTED)
        a2 = Arrow(model.get_right(), test.get_left(), buff=0.15, color=MUTED)
        with self.voiceover(
            'Here is the part that surprises FSRS users: <bookmark mark="m"/>there is one model, '
            "with two million seven hundred sixty-two thousand eight hundred eighty-four parameters, trained once.",
            hold="step",
        ):
            self.at("m", FadeIn(model))
        with self.voiceover(
            'It learned from <bookmark mark="a"/>five thousand users and was tested on '
            '<bookmark mark="b"/>five thousand others it had never seen.',
            hold="step",
        ):
            self.at("a", FadeIn(train), GrowArrow(a1))
            self.at("b", GrowArrow(a2), FadeIn(test))
        you = Card(
            label("your history → the state", size=26, color=ACCENT), ACCENT, pad=0.2
        ).move_to(DOWN * 1.0 + LEFT * 2.6)
        no = label("weights: never touched", size=26, color=NEGATIVE).move_to(
            DOWN * 1.0 + RIGHT * 2.9
        )
        with self.voiceover(
            'Your collection never touches its weights. <bookmark mark="s"/>Your history goes into the state.',
            hold="insight",
        ):
            self.play(FadeIn(no), run_time=0.5)
            self.at("s", FadeIn(you, shift=UP * 0.1))
        with self.voiceover(
            "The bet is that the way people forget is shared; what is yours is the history, "
            "and the state carries it.",
            hold="insight",
        ):
            self.play(Indicate(you, color=ACCENT, scale_factor=1.05), run_time=1.0)
        rev = label("FSRS: 21–34 parameters, fitted to you", size=24, color=MUTED).move_to(
            DOWN * 2.3
        )
        small = label(
            "Anki fork's Small model: 331,511 parameters, same principle", size=24, color=MUTED
        )
        small.move_to(DOWN * 3.0)
        with self.voiceover(
            '<bookmark mark="f"/>FSRS is the reverse: a few dozen parameters, fitted to you.',
            hold="step",
        ):
            self.at("f", FadeIn(rev))
        with self.voiceover(
            'The model in the experimental Anki fork is smaller, <bookmark mark="k"/>three hundred thirty-one '
            "thousand parameters, built the same way.",
            hold="reveal",
        ):
            self.at("k", FadeIn(small))
        self.checkpoint(
            "A channel keeps 0.5 per step; every key is 0.\n"
            "Values: first 0 (forgotten), then 1 (remembered).\nWhat does it output after both?",
            "num = 0.5·0 + 1 = 1,  den = 0.5·1 + 1 = 1.5  →  about 0.67",
        )


class S4CurveInstant(LessonScene):
    def construct(self) -> None:
        self.chapter("4", "A curve or a snapshot")
        ax_c = Axes(x_range=[0, 30, 10], y_range=[0, 1, 0.5], x_length=5.2, y_length=3.0,
                    axis_config={"color": MUTED, "include_ticks": False})  # fmt: skip
        ax_c.move_to(LEFT * 3.4 + DOWN * 0.3)
        curve = ax_c.plot(lambda t: 0.9 ** (t / 6), x_range=[0, 30], color=PRIMARY)
        c_title = label("RWKV-Curve", size=30, color=PRIMARY, weight="BOLD").next_to(
            ax_c, UP, buff=0.5
        )
        c_x = label("days from now", size=22, color=MUTED).next_to(ax_c.x_axis, DOWN, buff=0.25)
        c_y = label("recall", size=22, color=MUTED).next_to(ax_c.y_axis, UP, buff=0.1)
        dr = DashedLine(ax_c.c2p(0, 0.9), ax_c.c2p(30, 0.9), color=ACCENT, stroke_width=2)
        dr_l = (
            label("desired retention", size=20, color=ACCENT)
            .next_to(dr, DOWN, buff=0.1)
            .align_to(dr, RIGHT)
        )
        drop = DashedLine(ax_c.c2p(6, 0.9), ax_c.c2p(6, 0), color=ACCENT, stroke_width=2)
        iv = label("interval", size=22, color=ACCENT).next_to(ax_c.c2p(6, 0), DOWN, buff=0.15)
        with self.voiceover(
            "One model, two ways to ask it about a card.",
            hold="step",
        ):
            self.play(Create(ax_c), FadeIn(c_x), FadeIn(c_y), run_time=0.8)
        self.play(FadeIn(c_title), run_time=0.4)
        with self.voiceover(
            "RWKV-Curve outputs a whole forgetting curve for each card: "
            '<bookmark mark="r"/>recall against time from now.',
            hold="step",
        ):
            self.at("r", Create(curve), run_time=1.2)
        with self.voiceover(
            'That is what a scheduler needs: <bookmark mark="d"/>find where the curve crosses your desired '
            'retention, <bookmark mark="i"/>and that is the interval, the way FSRS does it.',
            hold="reveal",
        ):
            self.at("d", Create(dr), FadeIn(dr_l))
            self.at("i", Create(drop), FadeIn(iv))

        ax_i = Axes(x_range=[0, 30, 10], y_range=[0, 1, 0.5], x_length=5.2, y_length=3.0,
                    axis_config={"color": MUTED, "include_ticks": False})  # fmt: skip
        ax_i.move_to(RIGHT * 3.5 + DOWN * 0.3)
        i_title = label("RWKV-Instant", size=30, color=SPECIAL, weight="BOLD").next_to(
            ax_i, UP, buff=0.5
        )
        i_sub = label("add-on: “RWKV-P”", size=22, color=MUTED).next_to(i_title, DOWN, buff=0.12)
        now = Dot(ax_i.c2p(0, 0.93), radius=0.11, color=SPECIAL)
        now_l = label("right now", size=22, color=SPECIAL).next_to(now, RIGHT, buff=0.2)
        later = label("later: ?", size=30, color=MUTED).move_to(ax_i.c2p(20, 0.55))
        self.play(FadeIn(i_title), run_time=0.4)
        with self.voiceover(
            'RWKV-Instant asks a narrower question: <bookmark mark="n"/>if you reviewed '
            "this card right now, would you recall it?",
            hold="step",
        ):
            self.play(Create(ax_i), run_time=0.6)
            self.at("n", FadeIn(now, scale=0.5), FadeIn(now_l))
        with self.voiceover(
            'In the RWKV4Anki add-on, <bookmark mark="p"/>the same idea is called RWKV-P.',
            hold="step",
        ):
            self.at("p", FadeIn(i_sub))
        with self.voiceover(
            'It answers using everything up to this moment, <bookmark mark="q"/>but there is no curve to read '
            "a due date from.",
            hold="reveal",
        ):
            self.at("q", FadeIn(later))
        odd = VGroup(*(Dot(ax_i.c2p(x, y), radius=0.07, color=NEGATIVE)
                       for x, y in ((8, 0.62), (14, 0.68), (20, 0.74), (26, 0.79))))  # fmt: skip
        odd_l = label("never 100 %  ·  can rise with time", size=24, color=NEGATIVE).next_to(
            ax_i, DOWN, buff=0.55
        )
        with self.voiceover(
            "Nothing forces its answers into a curve's shape, so it can say odd things: "
            '<bookmark mark="o"/>never quite a hundred percent, or a recall that <bookmark mark="r"/>rises as '
            "more time passes.",
            hold="reveal",
        ):
            self.play(FadeOut(later), run_time=0.4)
            self.at("o", FadeIn(odd_l), run_time=0.4)
            self.at(
                "r", LaggedStart(*(FadeIn(d, scale=0.5) for d in odd), lag_ratio=0.3), run_time=1.2
            )
        self.clear_stage()

        names = ("RWKV-Instant", "RWKV-Curve", "FSRS-7")
        scores = (0.2773, 0.3193, 0.3401)
        colors = (SPECIAL, PRIMARY, MUTED)
        bars = VGroup()
        for name, s, col in zip(names, scores, colors, strict=True):
            bar = Rectangle(width=s * 22, height=0.5, stroke_width=0).set_fill(col, 0.85)
            n = label(name, size=26, color=col).next_to(bar, LEFT, buff=0.3)
            v = label(f"{s:.4f}", size=26).next_to(bar, RIGHT, buff=0.25)
            bars.add(VGroup(n, bar, v))
        bars.arrange(DOWN, buff=0.35)
        for b in bars:
            b[1].align_to(bars[0][1], LEFT)
            b[0].next_to(b[1], LEFT, buff=0.3)
            b[2].next_to(b[1], RIGHT, buff=0.25)
        bars.move_to(DOWN * 0.2)
        cap = label("log loss, lower is better (Video 1.2)", size=24, color=MUTED).next_to(
            bars, UP, buff=0.5
        )
        with self.voiceover(
            "On the leaderboard from Video 1.2, the narrow question wins by far: "
            '<bookmark mark="a"/>Instant first, <bookmark mark="b"/>Curve second, '
            '<bookmark mark="c"/>FSRS-7 behind both.',
            hold="insight",
        ):
            self.play(FadeIn(cap), run_time=0.5)
            self.at("a", FadeIn(bars[0]), run_time=0.5)
            self.at("b", FadeIn(bars[1]), run_time=0.5)
            self.at("c", FadeIn(bars[2]), run_time=0.5)
        self.checkpoint(
            "Your friend's collection is loaded into RWKV,\nand into FSRS with Optimize.\n"
            "What changes inside each model?",
            "RWKV: only its state (their history replayed); the weights stay fixed. FSRS: its parameters are refitted.",
        )


class S5Outro(LessonScene):
    def construct(self) -> None:
        self.chapter("5", "Best score, no due date")
        lead = VGroup(
            label("Is the lead fair?", size=32, color=ACCENT),
            label("Where does it come from?", size=32, color=ACCENT),
            label("How do you schedule with “right now”?", size=32, color=ACCENT),
        ).arrange(DOWN, buff=0.35)
        with self.voiceover(
            "So the model that can't tell Anki when a card is due has the best score. "
            '<bookmark mark="f"/>Is that lead fair?',
            hold="step",
        ):
            self.at("f", FadeIn(lead[0], shift=UP * 0.1), run_time=0.4)
        self.play(FadeIn(lead[1], shift=UP * 0.1), run_time=0.4)
        with self.voiceover(
            'Where does it come from, <bookmark mark="s"/>and how do you schedule with a '
            "model that only knows right now? That's Video 1.4.",
            hold="chapter",
        ):
            self.at("s", FadeIn(lead[2], shift=UP * 0.1))
        self.clear_stage()
        self.recall(
            [
                "Which can move RWKV's prediction for card A but not FSRS's:\na lapse on A, a slow answer on A's sibling, reviewing on a Sunday?",
                "You want a channel to still feel last month's reviews.\nShould its decay factor be near 0 or near 1?",
                "Anki needs a due date for a card. Which RWKV variant\ncan give one, and what does it read it from?",
            ]
        )
