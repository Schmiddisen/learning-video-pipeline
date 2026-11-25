"""Video 1.2 – Odds and updates: Bayes' theorem in one multiplication.  (original example)"""

# Beats
#   S0  hook: two independent positive tests – 18 % or much more? pretest
#   S1  odds: 1 : 999 before, × 99 for a positive, 99 : 999 ≈ 1 : 10 (the 9 % from video 1.1)
#   S2  a second test: start from 1 : 10, × 99 again → 99 : 10 ≈ 91 %; check about S1
#   S3  the usual formula read as counting; check about S2; recall
# Opening: a misconception (tests add up). Building: let the viewer invent the shortcut.

from manim import DOWN, LEFT, RIGHT, UP, FadeIn, VGroup

from lvp.props import DefBox, question
from lvp.style import ACCENT, FG, MUTED, NEGATIVE, POSITIVE, PRIMARY, LessonScene, label

SERIES = "Bayes in Practice · Video 1.2"


class S0Hook(LessonScene):
    def construct(self) -> None:
        q = question("Two independent tests are both positive.\nHow likely are you sick now?")
        q.move_to(UP * 1.4)
        self.opening(SERIES, q)
        guess = label("9 %  →  18 % ?", size=40, color=MUTED).move_to(DOWN * 0.8)
        with self.voiceover(
            "One positive test moved you from one in a thousand to about nine percent. "
            '<bookmark mark="g"/>A second, independent test is positive too.',
            hold="step",
        ):
            self.at("g", FadeIn(guess, shift=UP * 0.1))
        with self.voiceover(
            "Does that double the nine percent? Or does it do something else entirely?",
            hold="question",
        ):
            pass
        self.title_card(
            "Odds and updates",
            say="We need one shortcut for the counting – then the second test is easy.",
        )
        self.pretest(["Why might a second positive test move you\nmuch further than the first one did?"])


class S1Odds(LessonScene):
    def construct(self) -> None:
        self.chapter("1", "Odds instead of percentages")
        before = label("sick : healthy  =  1 : 999", size=40).move_to(UP * 1.6)
        with self.voiceover(
            'Before any test, compare the two groups directly: <bookmark mark="b"/>one sick '
            "person for every nine hundred ninety-nine healthy ones. Those are odds.",
            hold="reveal",
        ):
            self.at("b", FadeIn(before, shift=UP * 0.1))
        lr = VGroup(
            label("sick → positive: 99 %", size=30, color=NEGATIVE),
            label("healthy → positive: 1 %", size=30, color=ACCENT),
            label("ratio: 99", size=34, color=PRIMARY),
        ).arrange(DOWN, buff=0.25).move_to(DOWN * 0.3)
        with self.voiceover(
            '<bookmark mark="l"/>A positive result is ninety-nine times more likely '
            "for a sick person than for a healthy one.",
            hold="reveal",
        ):
            self.at("l", FadeIn(lr, shift=UP * 0.1), run_time=0.4)
        after = label("1 : 999  × 99  =  99 : 999  ≈  1 : 10", size=36, color=FG)
        after.to_edge(DOWN, buff=0.8)
        with self.voiceover(
            'So multiply the odds by ninety-nine: <bookmark mark="m"/>ninety-nine to nine '
            "hundred ninety-nine – about one to ten. One sick person among eleven: the nine "
            "percent from last time, without drawing anyone.",
            hold="insight",
        ):
            self.at("m", FadeIn(after, shift=UP * 0.1))
        rule = DefBox(
            "Bayes' theorem, odds form",
            "odds after the evidence = odds before × how much more likely the evidence is "
            "if it is true",
            color=PRIMARY,
            width=11.0,
        )
        self.clear_stage()
        with self.voiceover(
            "That is the whole of Bayes' theorem: odds before, times how much more likely the "
            "evidence is if it is true.",
            hold="insight",
        ):
            self.play(FadeIn(rule, shift=UP * 0.1))


class S2Second(LessonScene):
    def construct(self) -> None:
        self.chapter("2", "A second test")
        start = label("after test 1:  1 : 10", size=38).move_to(UP * 1.5)
        self.play(FadeIn(start, shift=UP * 0.1), run_time=0.4)
        with self.voiceover(
            "After the first positive, one to ten is your new starting point.", hold="step"
        ):
            pass
        step = label("1 : 10  × 99  =  99 : 10", size=38, color=FG).move_to(UP * 0.2)
        res = label("≈ 91 % sick", size=44, color=NEGATIVE, weight="BOLD").move_to(DOWN * 1.1)
        with self.voiceover(
            'An independent second positive multiplies by ninety-nine again: '
            '<bookmark mark="m"/>ninety-nine to ten. <bookmark mark="r"/>About ninety-one '
            "percent.",
            hold="insight",
        ):
            self.at("m", FadeIn(step, shift=UP * 0.1))
            self.at("r", FadeIn(res, shift=UP * 0.1))
        why = label("same evidence, different starting odds", size=30, color=POSITIVE)
        why.to_edge(DOWN, buff=0.7)
        with self.voiceover(
            "The second test is exactly as good as the first. "
            '<bookmark mark="w"/>What changed is where it started – no longer one in a '
            "thousand, but one in eleven.",
            hold="insight",
        ):
            self.at("w", FadeIn(why, shift=UP * 0.1))
        self.checkpoint(
            "Odds before: 1 : 499. The evidence is 50 times more likely\n"
            "if it is true. What are the odds after?",
            "50 : 499 ≈ 1 : 10 – about 9 %",
        )


class S3Formula(LessonScene):
    def construct(self) -> None:
        self.chapter("3", "The textbook formula")
        f = label("P(sick | +)  =  P(+ | sick) · P(sick)  /  P(+)", size=36).move_to(UP * 1.6)
        with self.voiceover(
            'Textbooks write it <bookmark mark="f"/>as probabilities instead of odds.',
            hold="reveal",
        ):
            self.at("f", FadeIn(f, shift=UP * 0.1))
        parts = VGroup(
            label("P(+ | sick) · P(sick):  the sick who test positive – 1 in 1000", size=28,
                  color=NEGATIVE),
            label("P(+):  everyone who tests positive – 11 in 1000", size=28, color=ACCENT),
            label("ratio:  1 / 11  ≈  9 %", size=32, weight="BOLD"),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to(DOWN * 0.6)  # fmt: skip
        with self.voiceover(
            '<bookmark mark="t"/>The top counts the sick people who test positive. '
            '<bookmark mark="b"/>The bottom counts everyone who tests positive. '
            '<bookmark mark="r"/>Their ratio is the count from the first video.',
            hold="insight",
        ):
            self.at("t", FadeIn(parts[0], shift=RIGHT * 0.1), run_time=0.6)
            self.at("b", FadeIn(parts[1], shift=RIGHT * 0.1), run_time=0.6)
            self.at("r", FadeIn(parts[2], shift=RIGHT * 0.1), run_time=0.6)
        self.checkpoint(
            "After two positives you are at 99 : 10.\nA third independent positive?",
            "99 : 10 × 99 = 9801 : 10 – over 99.8 %",
        )
        self.recall([
            "A disease affects 1 in 1000; the evidence ratio is 20.\nOdds after one positive?",
            "Why does a second test move the probability\nfurther than the first one did?",
            "In P(+ | sick) · P(sick) / P(+), what does the top count,\nwhat does the bottom count?",
        ])
