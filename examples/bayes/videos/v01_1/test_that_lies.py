"""Video 1.1 – The test that lies: why a positive result can mean only 9 %.  (original example)"""

# Beats
#   S0  hook: 1-in-1000 disease, 99 % accurate test, positive – guess how likely you are sick
#   S1  count a thousand people: 1 sick and positive, about 10 healthy and positive → 1 in 11
#   S2  why rarity wins: the false alarms come from the size of the healthy crowd; 1 in 100
#       flips the picture to about one half; check (about S1) with new numbers
#   S3  ending: cliffhanger into odds; recall
# Opening: a question most people answer wrong. Building: concrete before abstract (count first).

from manim import DOWN, RIGHT, UP, Create, FadeIn, GrowFromEdge, Rectangle, Square, Transform, VGroup

from lvp.props import question
from lvp.style import ACCENT, FG, MUTED, NEGATIVE, POSITIVE, LessonScene, label

SERIES = "Bayes in Practice · Video 1.1"


def crowd(n_cols: int = 40, n_rows: int = 25, side: float = 0.17) -> VGroup:
    """A thousand people as small squares."""
    people = VGroup(*(Square(side, stroke_width=1, color=MUTED).set_fill(MUTED, 0.25)
                      for _ in range(n_cols * n_rows)))  # fmt: skip
    return people.arrange_in_grid(rows=n_rows, cols=n_cols, buff=0.05)


class S0Hook(LessonScene):
    def construct(self) -> None:
        q = question("A 99 % accurate test says you are sick.\nHow worried should you be?")
        q.move_to(UP * 1.6)
        self.opening(SERIES, q)
        facts = VGroup(
            label("disease: 1 in 1000 people", size=30),
            label("test: right 99 % of the time", size=30),
            label("your result: positive", size=30, color=NEGATIVE),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to(DOWN * 1.2)
        with self.voiceover(
            'A disease affects <bookmark mark="d"/>one person in a thousand.', hold="step"
        ):
            self.at("d", FadeIn(facts[0], shift=UP * 0.1))
        with self.voiceover(
            'You take <bookmark mark="t"/>a test that is right ninety-nine percent of the time, '
            '<bookmark mark="r"/>and it comes back positive.',
            hold="step",
        ):
            self.at("t", FadeIn(facts[1], shift=UP * 0.1))
            self.at("r", FadeIn(facts[2], shift=UP * 0.1))
        with self.voiceover(
            "Before we go on: how likely is it that you really have the disease? Pick a number.",
            hold="question",
        ):
            pass
        self.title_card(
            "The test that lies", say="No formula yet. We will simply count people."
        )
        self.pretest(["Why should it matter how rare the disease is,\nif the test is 99 % accurate?"])


class S1Count(LessonScene):
    def construct(self) -> None:
        self.chapter("1", "A thousand people")
        people = crowd().move_to(UP * 0.35)
        with self.voiceover('Line up <bookmark mark="g"/>a thousand people.', hold="step"):
            self.at("g", Create(people, lag_ratio=0.002), run_time=2.0)
        sick = people[537]
        with self.voiceover(
            '<bookmark mark="s"/>One of them has the disease, and the test catches them.',
            hold="step",
        ):
            self.at("s", sick.animate.set_fill(NEGATIVE, 1).set_stroke(NEGATIVE, 2).scale(1.6))
        false_alarms = VGroup(*(people[i] for i in (12, 88, 160, 233, 301, 420, 615, 702, 811, 955)))
        with self.voiceover(
            "But the test is wrong one time in a hundred, also for healthy people. "
            '<bookmark mark="f"/>One percent of the nine hundred ninety-nine healthy ones is '
            "about ten.",
            hold="reveal",
        ):
            self.at("f", *(p.animate.set_fill(ACCENT, 1).set_stroke(ACCENT, 2).scale(1.6)
                           for p in false_alarms))  # fmt: skip
        tally = VGroup(
            label("positive: 1 sick + 10 healthy = 11", size=30),
            label("sick among them: 1 in 11 ≈ 9 %", size=34, color=NEGATIVE),
        ).arrange(DOWN, buff=0.25).to_edge(DOWN, buff=0.35)
        self.play(people.animate.scale(0.8).shift(UP * 0.45), run_time=0.8)
        with self.voiceover(
            '<bookmark mark="p"/>Eleven people get a positive result. '
            '<bookmark mark="o"/>Only one of them is sick.',
            hold="insight",
        ):
            self.at("p", FadeIn(tally[0], shift=UP * 0.1))
            self.at("o", FadeIn(tally[1], shift=UP * 0.1))
        with self.voiceover(
            "So a positive result means about a nine percent chance – not ninety-nine.",
            hold="insight",
        ):
            self.play(tally[1].animate.scale(1.08), run_time=0.6)


class S2Rare(LessonScene):
    def construct(self) -> None:
        self.chapter("2", "Why rarity wins")
        base = DOWN * 1.6

        def bar(value: float, color: str, x: float):
            return Rectangle(width=1.2, height=max(0.04, value), stroke_width=0).set_fill(
                color, 1
            ).move_to(base + RIGHT * x, aligned_edge=DOWN)

        b1, b2 = bar(0.3, NEGATIVE, -2.8), bar(3.0, ACCENT, 2.8)
        l1 = label("sick and positive", size=24, color=NEGATIVE).next_to(b1, DOWN, buff=0.2)
        l2 = label("healthy and positive", size=24, color=ACCENT).next_to(b2, DOWN, buff=0.2)
        n1 = label("1", size=30).next_to(b1, UP, buff=0.15)
        n2 = label("10", size=30).next_to(b2, UP, buff=0.15)
        with self.voiceover(
            "The false alarms don't come from a bad test. "
            '<bookmark mark="b"/>They come from how many healthy people there are to be wrong '
            "about.",
            hold="reveal",
        ):
            self.at("b", GrowFromEdge(b1, DOWN), GrowFromEdge(b2, DOWN), FadeIn(l1, l2, n1, n2))
        with self.voiceover(
            "Nine hundred ninety-nine chances for a one-percent mistake "
            "outweigh a single sick person.",
            hold="insight",
        ):
            self.play(b2.animate.set_fill(ACCENT, 0.7), run_time=0.5)
        title = label("disease: 1 in 100", size=30, color=FG).to_edge(UP, buff=0.9)
        tall = b1.copy().stretch_to_fit_height(3.0, about_edge=DOWN)
        n1b = label("10", size=30).next_to(tall, UP, buff=0.15)
        with self.voiceover(
            'Make <bookmark mark="c"/>the disease ten times more common – one in a hundred – '
            '<bookmark mark="n"/>and ten sick people test positive, next to about ten false '
            "alarms.",
            hold="reveal",
        ):
            self.at("c", FadeIn(title), run_time=0.4)
            self.at("n", b1.animate.stretch_to_fit_height(3.0, about_edge=DOWN), Transform(n1, n1b))
        half = label("positive → about 50 % sick", size=32, color=POSITIVE, weight="BOLD")
        half.next_to(title, DOWN, buff=0.35)
        with self.voiceover(
            'Now <bookmark mark="h"/>a positive result means about one half. Same test – only '
            "the rarity changed.",
            hold="insight",
        ):
            self.at("h", FadeIn(half, shift=UP * 0.1), run_time=0.4)
        self.checkpoint(
            "A test is right 98 % of the time; the disease is 1 in 1000.\n"
            "Among 1000 people, how many positives – and how many sick?",
            "About 20 false alarms + 1 sick = 21 positives: under 5 % are sick",
        )


class S3Outro(LessonScene):
    def construct(self) -> None:
        self.chapter("3", "Where this goes")
        lead = label("counting  →  one line of algebra", size=36, color=ACCENT)
        with self.voiceover(
            '<bookmark mark="l"/>Counting people works every time, but it is slow. '
            "Next time, the same count becomes one line – and it shows "
            "why a second test is so powerful.",
            hold="chapter",
        ):
            self.at("l", FadeIn(lead, shift=UP * 0.1))
        self.clear_stage()
        self.recall([
            "Why can a 99 % accurate test be wrong\nmost of the times it says positive?",
            "The disease affects half of all people.\nWhat does a positive result from the 99 % test mean?",
            "Besides the accuracy, which number must you know\nto judge a positive result?",
        ])
