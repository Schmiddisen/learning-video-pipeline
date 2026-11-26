"""Video 1.3 – The prosecutor's mistake: one in a million is not one in a million.  (original example)"""

# Beats
#   S0  hook: a DNA trace matches the suspect; random match 1 in a million – guilty? pretest
#   S1  count the city: 5 million people → about 5 innocent matches + the real culprit → 1 in 6
#   S2  the swap: P(match | innocent) is not P(innocent | match); other evidence = prior odds;
#       check (about S1) with new numbers
#   S3  ending: where the same swap hides (screening, spam filters, alarms); recall
# Opening: a real-world trap. Building: callback to counting (video 1.1) and odds (video 1.2).

from manim import DOWN, LEFT, RIGHT, UP, FadeIn, VGroup

from lvp.props import question
from lvp.style import ACCENT, FG, MUTED, NEGATIVE, POSITIVE, PRIMARY, LessonScene, label

SERIES = "Bayes in Practice · Video 1.3"


class S0Hook(LessonScene):
    def construct(self) -> None:
        q = question("A DNA trace matches the suspect.\nOnly 1 in a million people would match by chance.")
        q.move_to(UP * 1.5)
        self.opening(SERIES, q)
        claim = label("“So the chance he is innocent is one in a million.”", size=30, color=NEGATIVE)
        claim.move_to(DOWN * 0.6)
        with self.voiceover(
            'In court, the prosecutor puts it like this: <bookmark mark="c"/>the chance that he '
            "is innocent is one in a million.",
            hold="step",
        ):
            self.at("c", FadeIn(claim, shift=UP * 0.1), run_time=0.5)
        with self.voiceover("Is that right? Decide before we count.", hold="question"):
            pass
        self.title_card("The prosecutor's mistake", say="We count a city, the way we counted patients.")
        self.pretest(["What do you need to know besides\nthe one-in-a-million match rate?"])


class S1City(LessonScene):
    def construct(self) -> None:
        self.chapter("1", "Counting a city")
        city = label("city: 5 000 000 people", size=36).move_to(UP * 1.8)
        with self.voiceover(
            '<bookmark mark="c"/>Say the crime happened in a city of five million, and nothing '
            "else points to anyone yet.",
            hold="step",
        ):
            self.at("c", FadeIn(city, shift=UP * 0.1), run_time=0.4)
        rows = VGroup(
            label("innocent people who match by chance:  about 5", size=30, color=ACCENT),
            label("the real culprit, who matches:  1", size=30, color=NEGATIVE),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to(UP * 0.2)
        with self.voiceover(
            "One in a million of five million: "
            '<bookmark mark="i"/>about five innocent people match by chance. '
            '<bookmark mark="g"/>Plus the one who did it.',
            hold="reveal",
        ):
            self.at("i", FadeIn(rows[0], shift=RIGHT * 0.1), run_time=0.5)
            self.at("g", FadeIn(rows[1], shift=RIGHT * 0.1), run_time=0.5)
        res = label("a match alone: about 1 in 6 that he did it", size=34, color=PRIMARY)
        res.to_edge(DOWN, buff=1.0)
        with self.voiceover(
            "Six people match. "
            '<bookmark mark="r"/>A match alone makes our suspect guilty with about one chance in '
            "six – not nine hundred ninety-nine thousand in a million.",
            hold="insight",
        ):
            self.at("r", FadeIn(res, shift=UP * 0.1), run_time=0.5)


class S2Swap(LessonScene):
    def construct(self) -> None:
        self.chapter("2", "The swap")
        a = label("P(match | innocent) = 1 in a million", size=32, color=ACCENT).move_to(UP * 1.6)
        b = label("P(innocent | match) = about 5 in 6", size=32, color=NEGATIVE).move_to(UP * 0.6)
        with self.voiceover(
            '<bookmark mark="a"/>One in a million is the chance that an innocent person matches. '
            '<bookmark mark="b"/>The court needs the reverse: the chance that someone who '
            "matches is innocent.",
            hold="reveal",
        ):
            self.at("a", FadeIn(a, shift=UP * 0.1), run_time=0.5)
            self.at("b", FadeIn(b, shift=UP * 0.1), run_time=0.5)
        with self.voiceover(
            "Swapping the two is the whole mistake – the same one as reading a ninety-nine "
            "percent test as a ninety-nine percent diagnosis.",
            hold="insight",
        ):
            self.play(a.animate.set_opacity(0.5), run_time=0.4)
        more = label("other evidence  →  better starting odds", size=30, color=POSITIVE)
        more.move_to(DOWN * 0.9)
        with self.voiceover(
            "The match is still strong evidence. "
            '<bookmark mark="m"/>Combined with anything else – a motive, a witness, being near '
            "the scene – it multiplies much better starting odds.",
            hold="insight",
        ):
            self.at("m", FadeIn(more, shift=UP * 0.1), run_time=0.5)
        note = label("same evidence, different starting point", size=26, color=MUTED)
        note.next_to(more, DOWN, buff=0.3)
        with self.voiceover(
            "Exactly as with the second test: the evidence stays the same, the starting "
            'point <bookmark mark="n"/>decides what it means.',
            hold="step",
        ):
            self.at("n", FadeIn(note), run_time=0.4)
        self.checkpoint(
            "Same trace, but the town has only 200 000 people.\n"
            "Roughly how likely is a matching suspect to be the culprit?",
            "About 0.2 innocent matches + 1 culprit: about 5 in 6",
        )


class S3Outro(LessonScene):
    def construct(self) -> None:
        self.chapter("3", "Where the swap hides")
        places = VGroup(
            label("cancer screening", size=30, color=FG),
            label("spam filters", size=30, color=FG),
            label("fraud alarms", size=30, color=FG),
        ).arrange(DOWN, buff=0.35).move_to(UP * 0.3)
        with self.voiceover(
            "You will meet this swap wherever a rare thing is searched for in a large crowd: "
            '<bookmark mark="s"/>screening, <bookmark mark="f"/>spam filters, '
            '<bookmark mark="a"/>fraud alarms.',
            hold="reveal",
        ):
            self.at("s", FadeIn(places[0]), run_time=0.4)
            self.at("f", FadeIn(places[1]), run_time=0.4)
            self.at("a", FadeIn(places[2]), run_time=0.4)
        with self.voiceover(
            "The question is always the same: how many false alarms does the crowd produce, "
            "next to the one true hit?",
            hold="insight",
        ):
            self.play(places.animate.set_color(ACCENT), run_time=0.5)
        self.clear_stage()
        self.recall([
            "A spam filter flags 1 % of good mail; 1 in 500 mails is spam.\nIs a flagged mail probably spam?",
            "Why is 'one in a million' not the chance\nthat a matching suspect is innocent?",
            "What does other evidence change in the calculation\n– the match rate or the starting odds?",
        ])
