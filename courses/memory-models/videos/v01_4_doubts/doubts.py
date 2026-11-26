"""Video 1.4 – Benchmark gold, everyday doubts: what RWKV's lead means in daily Anki use."""

# Beats
#   S0  hook: Instant 0.277 vs FSRS-7 0.340 – how much of the gap would FSRS-7 close if it
#       could update right before each review? (guess) · roadmap · pretest
#   S1  the information window: Instant predicts at review time, a scheduler commits at the
#       last review; FSRS-7 experiment (fork's FAQ, PR #360): 0.3519 → 0.3269, frozen ≈ 0
#   S2  fairness: user-level vs per-user time split, extra inputs, the deleted-card leak;
#       steelman (Curve 0.3193 < FSRS-7 0.3401; unseen users are a hard test) · check on S1
#   S3  into Anki: per-preset scheduler, Curve → days, Instant → order + fallback dates,
#       phones → FSRS-6, RWKV4Anki (Rust, checkpoints, Live Session, filtered decks),
#       per-card desired retention without retraining, what real use needs · check on S2
#   S4  what would convince you: log loss ≠ workload; three numbers to track; try the
#       player's RWKV mode · check on S3 · new angle: a scheduler picks its own test data
# Opening: predict-before-reveal on real numbers. Building: a timeline that the viewer reads,
# then steelman. Ending: open question for the learner's own collection.

from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    Arrow,
    CurvedArrow,
    FadeIn,
    GrowArrow,
    GrowFromEdge,
    Line,
    Rectangle,
    VGroup,
)

from lvp.props import Badge, DefBox, cross, question, tick
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

SERIES = "Memory Models · Video 1.4"

K = 15.0  # bar length per unit of log loss


class Lesson(LessonScene):
    """Short entrances by default, so a word's object is on screen while it is spoken."""

    def at(self, mark: str, *animations, **kw) -> None:
        kw.setdefault("run_time", 0.5)
        super().at(mark, *animations, **kw)


def bar_row(name: str, value: float, color: str, shown: str | None = None, x0: float = -2.4):
    """Horizontal log-loss bar: name on the left, bar from x0, value at the end."""
    bar = Rectangle(width=value * K, height=0.42, stroke_width=0).set_fill(color, 1)
    bar.move_to([x0, 0, 0], aligned_edge=LEFT)
    name_t = label(name, size=26, color=color).next_to(bar, LEFT, buff=0.3)
    val = label(shown or f"{value:.4f}", size=26).next_to(bar, RIGHT, buff=0.2)
    return VGroup(name_t, bar, val)


class S0Hook(Lesson):
    def construct(self) -> None:
        q = question("Where does RWKV-Instant's lead come from?").move_to(UP * 2.6)
        self.opening(SERIES, q)
        inst = bar_row("RWKV-Instant", 0.2773, ACCENT).shift(UP * 0.9)
        fsrs = bar_row("FSRS-7", 0.3401, PRIMARY).shift(UP * 0.1)
        axis = label("log loss – lower is better", size=22, color=MUTED).move_to(DOWN * 0.6)
        with self.voiceover(
            'On the board from Video 1.2, <bookmark mark="i"/>RWKV-Instant sits at '
            "zero point two seven seven.",
            hold="step",
        ):
            self.at("i", GrowFromEdge(inst[1], LEFT), FadeIn(inst[0], inst[2], axis))
        with self.voiceover(
            'The best hand-built model, <bookmark mark="f"/>FSRS-7, sits at zero point three four.',
            hold="step",
        ):
            self.at("f", GrowFromEdge(fsrs[1], LEFT), FadeIn(fsrs[0], fsrs[2]))
        gap = Badge("−18 %", color=ACCENT).next_to(inst, RIGHT, buff=0.4)
        with self.voiceover(
            'That is <bookmark mark="g"/>about eighteen percent less log loss – '
            "a huge gap on this benchmark.",
            hold="reveal",
        ):
            self.at("g", FadeIn(gap, shift=LEFT * 0.1))
        mystery = (
            VGroup(
                label("FSRS-7, updated at review time", size=26, color=TEAL),
                label("?", size=40, color=TEAL, weight="BOLD"),
            )
            .arrange(RIGHT, buff=0.4)
            .move_to(DOWN * 1.5)
        )
        with self.voiceover(
            'Now let FSRS-7 <bookmark mark="u"/>refresh its parameters right before each '
            "review, using everything that happened since the last one.",
            hold="step",
        ):
            self.at("u", FadeIn(mystery, shift=UP * 0.1))
        opts = (
            VGroup(label("none", size=30), label("some", size=30), label("all", size=30))
            .arrange(RIGHT, buff=1.4)
            .move_to(DOWN * 2.6)
        )
        with self.voiceover(
            'How much of the gap does it close: <bookmark mark="n"/>none, '
            '<bookmark mark="s"/>some, <bookmark mark="a"/>or all of it?',
            hold="question",
        ):
            self.at("n", FadeIn(opts[0]), run_time=0.3)
            self.at("s", FadeIn(opts[1]), run_time=0.3)
            self.at("a", FadeIn(opts[2]), run_time=0.3)
        self.title_card(
            "Benchmark gold, everyday doubts",
            say="First where that edge comes from, then how fair the race is, then what it "
            "takes to run inside Anki – and what would actually convince you.",
        )
        self.pretest([
            "A model is tested on users it has never seen.\n"
            "Easier or harder than testing on\nthe same users' future reviews?",
            "If a model predicts your recall better,\nmust it save you reviews?",
        ])  # fmt: skip


class S1Window(Lesson):
    def construct(self) -> None:
        self.chapter("1", "The information window")
        y = 0.6
        line = Line(LEFT * 5.6 + UP * y, RIGHT * 5.6 + UP * y, color=FG, stroke_width=3)
        t_last = Line(UP * (y + 0.25), UP * (y - 0.25), color=FG, stroke_width=5).shift(LEFT * 4.6)
        t_next = Line(UP * (y + 0.25), UP * (y - 0.25), color=FG, stroke_width=5).shift(RIGHT * 4.6)
        l_last = label("last review", size=22, color=MUTED).next_to(t_last, DOWN, buff=0.2)
        l_next = label("next review", size=22, color=MUTED).next_to(t_next, DOWN, buff=0.2)
        with self.voiceover(
            'Take one card. <bookmark mark="l"/>You reviewed it last week, '
            '<bookmark mark="n"/>and it comes up again today.',
            hold="step",
        ):
            self.at("l", FadeIn(line), FadeIn(t_last, l_last))
            self.at("n", FadeIn(t_next, l_next))
        inst = Card("Instant predicts", color=ACCENT).scale(0.8).next_to(t_next, UP, buff=0.35)
        inst.shift(LEFT * 0.4)
        with self.voiceover(
            '<bookmark mark="p"/>Instant makes its guess at the last possible moment, '
            "just before you answer.",
            hold="step",
        ):
            self.at("p", FadeIn(inst, shift=DOWN * 0.1))
        region = Rectangle(width=8.4, height=2.0, stroke_width=0).set_fill(ACCENT, 0.15)
        region.move_to(DOWN * 1.45)
        events = (
            VGroup(
                label("today's other cards", size=24),
                label("a sibling failed at noon", size=24),
                label("slow answers", size=24),
                label("tired, 200 reviews in", size=24),
            )
            .arrange_in_grid(rows=2, cols=2, buff=(0.6, 0.45))
            .move_to(region)
        )
        with self.voiceover(
            'By then its state has absorbed <bookmark mark="e"/>everything since the last '
            'review: <bookmark mark="o"/>how today\'s other cards went, '
            '<bookmark mark="s"/>a sibling you failed at noon.',
            hold="none",
        ):
            self.at("e", FadeIn(region))
            self.at("o", FadeIn(events[0]), run_time=0.4)
            self.at("s", FadeIn(events[1]), run_time=0.4)
        with self.voiceover(
            'It even sees <bookmark mark="w"/>how slowly you answer, '
            '<bookmark mark="t"/>and how many reviews you have already done today.',
            hold="step",
        ):
            self.at("w", FadeIn(events[2]), run_time=0.4)
            self.at("t", FadeIn(events[3]), run_time=0.4)
        sched = Card("due date set", color=PRIMARY).scale(0.8).next_to(t_last, UP, buff=0.35)
        sched.shift(RIGHT * 0.4)
        with self.voiceover(
            "A scheduler has to commit much earlier: "
            '<bookmark mark="d"/>it sets the due date right after the last review.',
            hold="step",
        ):
            self.at("d", FadeIn(sched, shift=DOWN * 0.1))
        blind = cross(size=0.4).next_to(sched, RIGHT, buff=0.3)
        with self.voiceover(
            'Everything in this window <bookmark mark="x"/>is invisible to it.',
            hold="insight",
        ):
            self.at("x", FadeIn(blind), events.animate.set_color(MUTED))

        self.clear_stage()
        src = label(
            "experiment reported in the Anki fork's FAQ (srs-benchmark PR #360)"
            " – not verified by us",
            size=20,
            color=MUTED,
        ).to_edge(DOWN, buff=0.45)
        head = label("FSRS-7, users 1–300", size=30, weight="BOLD").to_edge(UP, buff=1.0)
        with self.voiceover(
            "How much of Instant's lead is that window? "
            '<bookmark mark="h"/>Someone tested it with FSRS-7 itself, on the first three '
            "hundred users.",
            hold="step",
        ):
            self.at("h", FadeIn(head), FadeIn(src))
        x0 = -1.2
        normal = bar_row("normal", 0.3519, PRIMARY, x0=x0).shift(UP * 1.1)
        live = bar_row("updated up to review", 0.3269, TEAL, x0=x0).shift(UP * 0.1)
        frozen = bar_row("frozen after last review", 0.3519, MUTED, "≈ normal", x0=x0)
        frozen.shift(DOWN * 0.9)
        with self.voiceover(
            "This is an experiment reported in an Anki fork's FAQ – "
            "we could not check it ourselves.",
            hold="none",
        ):
            pass
        with self.voiceover(
            'There, <bookmark mark="a"/>normal FSRS-7 scored zero point three five two.',
            hold="step",
        ):
            self.at("a", GrowFromEdge(normal[1], LEFT), FadeIn(normal[0], normal[2]))
        minus = Badge("−7.1 %", color=TEAL).next_to(live, RIGHT, buff=0.3)
        with self.voiceover(
            "Allowed to update its parameters "
            '<bookmark mark="b"/>right up to each review, it dropped to zero point three '
            'two seven – <bookmark mark="p"/>about seven percent lower.',
            hold="reveal",
        ):
            self.at("b", GrowFromEdge(live[1], LEFT), FadeIn(live[0], live[2]))
            self.at("p", FadeIn(minus))
        ci = label("0.4 %, CI includes 0", size=22, color=MUTED).next_to(frozen, DOWN, buff=0.2)
        ci.align_to(frozen[1], LEFT)
        with self.voiceover(
            'The control: <bookmark mark="c"/>parameters frozen just after the previous '
            "review, so the window stays closed.",
            hold="step",
        ):
            self.at("c", GrowFromEdge(frozen[1], LEFT), FadeIn(frozen[0], frozen[2]))
        with self.voiceover(
            'The gain <bookmark mark="z"/>shrinks to about zero point four percent, '
            "and the confidence interval includes zero.",
            hold="reveal",
        ):
            self.at("z", FadeIn(ci))
        with self.voiceover(
            "So your guess from the start: some – a sizeable part, "
            "from a model whose formula never changed.",
            hold="step",
        ):
            self.play(minus.animate.scale(1.15), run_time=0.5)
        with self.voiceover(
            "Different users, so it can't be subtracted from the eighteen percent, "
            "but much of Instant's edge looks like timing, not architecture.",
            hold="insight",
        ):
            pass
        self.clear_stage()
        box = DefBox(
            "Two different questions",
            "At review time: will you recall this card now? "
            "At scheduling time: when should you see it next?",
            color=ACCENT,
            width=10.0,
        )
        with self.voiceover(
            'Predicting recall at review time <bookmark mark="k"/>is a different task '
            "from predicting it when the date is set.",
            hold="insight",
        ):
            self.at("k", FadeIn(box, shift=UP * 0.1))


class S2Fairness(Lesson):
    def construct(self) -> None:
        self.chapter("2", "How fair is the race?")

        def user_rows(n: int, split: float | None, x: float) -> VGroup:
            rows = VGroup()
            for i in range(n):
                if split is None:
                    color = PRIMARY if i < n // 2 else ACCENT
                    r = Rectangle(width=4.2, height=0.22, stroke_width=0).set_fill(color, 1)
                    rows.add(r)
                else:
                    a = Rectangle(width=4.2 * split, height=0.22, stroke_width=0)
                    b = Rectangle(width=4.2 * (1 - split), height=0.22, stroke_width=0)
                    a.set_fill(PRIMARY, 1)
                    b.set_fill(ACCENT, 1)
                    rows.add(VGroup(a, b).arrange(RIGHT, buff=0.04))
            return rows.arrange(DOWN, buff=0.12).move_to(RIGHT * x + UP * 0.3)

        left = user_rows(8, 0.65, -4.0)
        right = user_rows(8, None, 2.0)
        lt = label("FSRS: each user's past → future", size=24).next_to(left, UP, buff=0.35)
        rt = label("RWKV: new users", size=24).next_to(right, UP, buff=0.35)
        legend = (
            VGroup(label("train", size=22, color=PRIMARY), label("test", size=22, color=ACCENT))
            .arrange(RIGHT, buff=0.8)
            .to_edge(DOWN, buff=0.6)
        )
        with self.voiceover(
            '<bookmark mark="t"/>FSRS is graded on each user\'s own future – '
            "the time split from Video 1.2.",
            hold="step",
        ):
            self.at("t", FadeIn(left, lt, legend))
        n_tr = label("5,000 users", size=22, color=PRIMARY).next_to(right[:4], RIGHT, buff=0.2)
        n_te = label("5,000 others", size=22, color=ACCENT).next_to(right[4:], RIGHT, buff=0.2)
        with self.voiceover(
            'RWKV gets a different exam: <bookmark mark="r"/>one shared model trained on '
            'five thousand users, <bookmark mark="s"/>tested on five thousand others.',
            hold="reveal",
        ):
            self.at("r", FadeIn(right[:4], rt))
            self.at("s", FadeIn(right[4:]))
        self.play(FadeIn(n_tr, n_te), run_time=0.4)
        with self.voiceover(
            "Two scores from two different exams are not a clean comparison.",
            hold="step",
        ):
            pass

        self.clear_stage()
        inputs = VGroup(
            label("siblings", size=26), label("decks", size=26),
            label("today's load", size=26), label("answer time", size=26),
        ).arrange(RIGHT, buff=0.6).move_to(UP * 2.3)  # fmt: skip
        extra = label("only RWKV sees:", size=24, color=MUTED).next_to(inputs, UP, buff=0.25)
        with self.voiceover(
            'Second, <bookmark mark="x"/>RWKV reads inputs FSRS never gets, '
            "the ones you met in Video 1.3.",
            hold="step",
        ):
            self.at("x", FadeIn(extra), FadeIn(inputs, lag_ratio=0.2))
        row = (
            VGroup(
                Card(label("card 4711", size=26), color=FG, pad=0.18),
                Card(label("note: —", size=26, color=MUTED), color=MUTED, pad=0.18),
                Card(label("deck: —", size=26, color=MUTED), color=MUTED, pad=0.18),
            )
            .arrange(RIGHT, buff=0.25)
            .move_to(UP * 0.4)
        )
        with self.voiceover(
            'Third, a subtler problem. In the public data, <bookmark mark="d"/>deleted cards '
            "have no card, note or deck rows.",
            hold="step",
        ):
            self.at("d", FadeIn(row, shift=UP * 0.1))
        miss = label('input: "missing"', size=26, color=NEGATIVE).next_to(row, DOWN, buff=0.4)
        with self.voiceover(
            'A naive pipeline fills those gaps with <bookmark mark="m"/>"missing".',
            hold="step",
        ):
            self.at("m", FadeIn(miss))
        arrow = Arrow(UP * 0.3, DOWN * 0.3, color=NEGATIVE).next_to(miss, DOWN, buff=0.1)
        means = label("deleted later → often a card you kept forgetting", size=26)
        means.next_to(arrow, DOWN, buff=0.1)
        with self.voiceover(
            'But "missing" really says: <bookmark mark="f"/>this card will be deleted later – '
            "often one you gave up on because you kept forgetting it.",
            hold="step",
        ):
            self.at("f", GrowArrow(arrow), FadeIn(means))
        leak = label("a hint from the future", size=32, color=NEGATIVE, weight="BOLD")
        leak.next_to(means, DOWN, buff=0.35)
        with self.voiceover('That is <bookmark mark="h"/>a hint from the future.', hold="insight"):
            self.at("h", FadeIn(leak, scale=1.1))
        status = VGroup(
            VGroup(label("fork's models: inputs zeroed", size=24), tick(size=0.3)).arrange(RIGHT),
            VGroup(label("benchmark model:", size=24), label("?", size=32, color=ACCENT)).arrange(
                RIGHT
            ),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.25)
        with self.voiceover(
            "The fork's own models zero those inputs; "
            '<bookmark mark="q"/>whether the benchmark model had the leak is an open question.',
            hold="reveal",
        ):
            self.play(
                VGroup(row, miss, arrow, means, leak).animate.scale(0.75).to_edge(LEFT, buff=0.6)
            )
            status.next_to(VGroup(row, miss, arrow, means, leak), RIGHT, buff=0.6)
            self.at("q", FadeIn(status, shift=LEFT * 0.1))

        self.clear_stage()
        steel = label("The strongest case for RWKV", size=32, weight="BOLD").to_edge(UP, buff=1.0)
        curve = bar_row("RWKV-Curve", 0.3193, SPECIAL).shift(UP * 0.7)
        f7 = bar_row("FSRS-7", 0.3401, PRIMARY).shift(DOWN * 0.1)
        with self.voiceover('<bookmark mark="s"/>Now the strongest case for RWKV.', hold="none"):
            self.at("s", FadeIn(steel))
        with self.voiceover(
            'Even <bookmark mark="c"/>RWKV-Curve, the version you can schedule with, '
            'still beats <bookmark mark="v"/>FSRS-7: zero point three one nine against '
            "zero point three four.",
            hold="reveal",
        ):
            self.at("c", GrowFromEdge(curve[1], LEFT), FadeIn(curve[0], curve[2]))
            self.at("v", GrowFromEdge(f7[1], LEFT), FadeIn(f7[0], f7[2]))
        harder = label("unseen users: arguably the harder exam", size=28, color=POSITIVE)
        harder.move_to(DOWN * 1.4)
        with self.voiceover(
            'And predicting people the model has <bookmark mark="u"/>never seen '
            "is arguably harder than predicting your own future.",
            hold="reveal",
        ):
            self.at("u", FadeIn(harder, shift=UP * 0.1))
        real = label("real edge – smaller than the headline", size=30, color=ACCENT)
        real.next_to(harder, DOWN, buff=0.4)
        with self.voiceover(
            'So the edge is <bookmark mark="e"/>real – just smaller than the headline number.',
            hold="insight",
        ):
            self.at("e", FadeIn(real))
        self.checkpoint(
            "Your phone synced a card's due date this morning.\n"
            "At noon you fail three of its siblings.\n"
            "Which can react: the due date, or a model\nthat orders cards when you open the deck?",
            "Only the ordering model – the date was fixed before the lapses happened",
        )


class S3IntoAnki(Lesson):
    def construct(self) -> None:
        self.chapter("3", "Into Anki")
        head = label("Review scheduler (per preset)", size=26, color=MUTED)
        opts = VGroup(
            label("FSRS-6", size=28), label("FSRS-7", size=28),
            label("RWKV-Curve", size=28, color=SPECIAL),
            label("RWKV-Instant", size=28, color=ACCENT),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.3)  # fmt: skip
        panel = VGroup(head, opts).arrange(DOWN, aligned_edge=LEFT, buff=0.35)
        frame = Rectangle(
            width=panel.width + 0.6, height=panel.height + 0.5, color=MUTED, stroke_width=2
        )
        menu = VGroup(frame, panel)
        panel.move_to(frame)
        menu.move_to(LEFT * 3.9 + UP * 0.6)
        who = label("experimental Anki fork (JSchoreels/anki)", size=20, color=MUTED)
        who.next_to(menu, DOWN, buff=0.3)
        with self.voiceover(
            'An <bookmark mark="m"/>experimental Anki fork puts these models into a real '
            "scheduler: per preset you choose FSRS-6, FSRS-7, RWKV-Curve or "
            "RWKV-Instant.",
            hold="step",
        ):
            self.at("m", FadeIn(menu), FadeIn(who))
        cal = (
            VGroup(
                label("Curve → intervals in days", size=26, color=SPECIAL),
                label("load balancer · fuzz (up to 90 days)", size=22, color=MUTED),
            )
            .arrange(DOWN, aligned_edge=LEFT, buff=0.15)
            .move_to(RIGHT * 2.2 + UP * 2.2)
        )
        with self.voiceover(
            '<bookmark mark="c"/>Curve behaves like any scheduler: '
            "its curve becomes an interval in days, with Anki's load balancer and fuzz on top.",
            hold="step",
        ):
            self.at("c", FadeIn(cal, shift=LEFT * 0.1), opts[2].animate.scale(1.08))
        inst = VGroup(
            label("Instant → order by recall right now", size=26, color=ACCENT),
            label("+ fallback due dates (FSRS or Curve)", size=22, color=MUTED),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        inst.next_to(cal, DOWN, buff=0.5).align_to(cal, LEFT)
        with self.voiceover(
            '<bookmark mark="i"/>Instant cannot name a date; '
            "it sorts your cards by how likely you are to recall them right now.",
            hold="step",
        ):
            self.at("i", FadeIn(inst[0], shift=LEFT * 0.1), opts[3].animate.scale(1.08))
        with self.voiceover(
            "But sync, statistics and phones need due dates, "
            '<bookmark mark="f"/>so a fallback calculator – FSRS or Curve – writes them.',
            hold="step",
        ):
            self.at("f", FadeIn(inst[1]))
        phone = VGroup(label("phone", size=26, color=PRIMARY), label("→ FSRS-6", size=26)).arrange(
            RIGHT, buff=0.25
        )
        phone.next_to(inst, DOWN, buff=0.5).align_to(cal, LEFT)
        with self.voiceover(
            '<bookmark mark="p"/>On a phone, the fork falls back to FSRS-6 for the next intervals.',
            hold="step",
        ):
            self.at("p", FadeIn(phone))
        replay = label("fixed weights · history replayed into the state", size=22, color=MUTED)
        replay.next_to(phone, DOWN, buff=0.5).align_to(cal, LEFT)
        with self.voiceover(
            'The weights never change: <bookmark mark="w"/>loading your collection replays '
            "your history into the state, as in Video 1.3.",
            hold="step",
        ):
            self.at("w", FadeIn(replay))

        self.clear_stage()
        addon = label("RWKV4Anki (add-on)", size=32, weight="BOLD").to_edge(UP, buff=1.0)
        feats = (
            VGroup(
                label("Rust backend, no PyTorch", size=26),
                label("checkpoints: no full replay at start", size=26),
                label("Live Session: refresh between reviews,", size=26),
                label("serve cards below desired retention", size=26),
                label("filtered decks from predictions", size=26),
                label("desktop only", size=26, color=NEGATIVE),
            )
            .arrange(DOWN, aligned_edge=LEFT, buff=0.22)
            .next_to(addon, DOWN, buff=0.45)
        )
        feats[3].shift(RIGHT * 0.4)
        with self.voiceover(
            'A separate add-on, <bookmark mark="a"/>RWKV4Anki, '
            '<bookmark mark="r"/>runs the same kind of model in Rust, without PyTorch.',
            hold="step",
        ):
            self.at("a", FadeIn(addon))
            self.at("r", FadeIn(feats[0]))
        with self.voiceover(
            '<bookmark mark="k"/>It saves checkpoints, so your history isn\'t replayed '
            "at every start.",
            hold="step",
        ):
            self.at("k", FadeIn(feats[1]))
        with self.voiceover(
            'Its <bookmark mark="l"/>Live Session refreshes predictions between reviews '
            '<bookmark mark="b"/>and serves whatever has dropped below your desired retention.',
            hold="reveal",
        ):
            self.at("l", FadeIn(feats[2]))
            self.at("b", FadeIn(feats[3]))
        with self.voiceover(
            '<bookmark mark="d"/>It can build filtered decks from the predictions – '
            '<bookmark mark="o"/>on the desktop only.',
            hold="step",
        ):
            self.at("d", FadeIn(feats[4]))
            self.at("o", FadeIn(feats[5]))

        self.clear_stage()
        rules = (
            VGroup(
                label("Frequency<1000  →  0.95", size=28, color=ACCENT),
                label("everything else  →  0.85", size=28),
            )
            .arrange(DOWN, aligned_edge=LEFT, buff=0.3)
            .move_to(UP * 1.4)
        )
        cap = label("desired retention per card (example rules)", size=22, color=MUTED)
        cap.next_to(rules, UP, buff=0.35)
        with self.voiceover(
            "Desired retention, the lever from Video 1.1, can differ per card here: "
            '<bookmark mark="s"/>search rules might ask ninety-five percent for '
            "your thousand most frequent words.",
            hold="step",
        ):
            self.at("s", FadeIn(cap), FadeIn(rules, lag_ratio=0.3))
        split = (
            VGroup(
                Card(label("model: predicts recall", size=26, color=PRIMARY), color=PRIMARY),
                Card(label("rule: decides when to act", size=26, color=ACCENT), color=ACCENT),
            )
            .arrange(RIGHT, buff=0.6)
            .move_to(DOWN * 0.4)
        )
        with self.voiceover(
            'Changing it <bookmark mark="n"/>retrains nothing: '
            "the model predicts, the rule decides.",
            hold="insight",
        ):
            self.at("n", FadeIn(split, shift=UP * 0.1))
        needs = VGroup(*(Badge(t, color=FG) for t in (
            "learning steps", "undo", "sync", "filtered decks", "phones", "huge collections",
        ))).arrange(RIGHT, buff=0.2)  # fmt: skip
        if needs.width > 12.4:
            needs.scale_to_fit_width(12.4)
        needs.move_to(DOWN * 2.3)
        with self.voiceover(
            "And the fork's author is blunt about the rest: real use needs "
            '<bookmark mark="r"/>learning steps, undo, sync, filtered decks, phones and huge '
            "collections to keep working – none of which a benchmark scores.",
            hold="insight",
        ):
            self.at("r", FadeIn(needs, lag_ratio=0.15))
        self.checkpoint(
            "A new model scores best on exactly the cards\n"
            'whose deck input reads "missing". What do you suspect?',
            "A leak: missing rows mark cards deleted later – a hint from the future",
        )


class S4Convince(Lesson):
    def construct(self) -> None:
        self.chapter("4", "What would convince you?")
        ll = Card("lower log loss", color=PRIMARY).move_to(LEFT * 4.0 + UP * 1.2)
        goals = (
            VGroup(Card("fewer reviews", color=POSITIVE), Card("higher retention", color=POSITIVE))
            .arrange(DOWN, buff=0.4)
            .move_to(RIGHT * 3.6 + UP * 1.2)
        )
        arr = Arrow(ll.get_right(), goals.get_left(), color=MUTED, buff=0.3)
        qm = label("?", size=44, color=ACCENT, weight="BOLD").next_to(arr, UP, buff=0.1)
        with self.voiceover(
            'Start with the catch: <bookmark mark="l"/>a lower log loss is a promise '
            "about predictions, "
            '<bookmark mark="w"/>not about your workload.',
            hold="step",
        ):
            self.at("l", FadeIn(ll))
            self.at("w", GrowArrow(arr), FadeIn(goals), FadeIn(qm))
        faq = label("“no guarantee of fewer reviews than FSRS”", size=26, slant="ITALIC")
        faq.move_to(DOWN * 0.8)
        with self.voiceover(
            "Even the fork's own FAQ says it plainly: "
            '<bookmark mark="g"/>no guarantee of fewer reviews than FSRS.',
            hold="reveal",
        ):
            self.at("g", FadeIn(faq))
        with self.voiceover(
            "A sharper ranking of today's cards changes which card comes first, "
            "not how many come due.",
            hold="insight",
        ):
            self.play(qm.animate.scale(1.2), run_time=0.5)

        self.clear_stage()
        dash = VGroup(
            Card(VGroup(label("true retention", size=26),
                        label("at your desired retention", size=20, color=MUTED)).arrange(DOWN),
                 color=POSITIVE),
            Card(label("reviews per day", size=26), color=PRIMARY),
            Card(label("minutes per day", size=26), color=SPECIAL),
        ).arrange(RIGHT, buff=0.5).move_to(UP * 1.8)  # fmt: skip
        with self.voiceover(
            "So measure what you care about, three numbers: "
            '<bookmark mark="r"/>true retention at your desired retention, '
            '<bookmark mark="n"/>reviews per day, <bookmark mark="t"/>and minutes per day.',
            hold="reveal",
        ):
            self.at("r", FadeIn(dash[0]))
            self.at("n", FadeIn(dash[1]))
            self.at("t", FadeIn(dash[2]))
        path = label("study player: Review → settings → RWKV mode", size=26, color=ACCENT)
        path.move_to(UP * 0.1)
        with self.voiceover(
            'Your own study player has an RWKV mode, <bookmark mark="p"/>under Review, '
            "in the settings.",
            hold="step",
        ):
            self.at("p", FadeIn(path, shift=UP * 0.1))
        cols = (
            VGroup(
                label("FSRS weeks", size=26, color=PRIMARY),
                label("vs", size=24, color=MUTED),
                label("RWKV weeks", size=26, color=ACCENT),
            )
            .arrange(RIGHT, buff=0.6)
            .move_to(DOWN * 1.2)
        )
        with self.voiceover(
            'Run it for a few weeks, <bookmark mark="c"/>then compare those three numbers '
            "with your FSRS weeks.",
            hold="step",
        ):
            self.at("c", FadeIn(cols, lag_ratio=0.2))
        fair = label("same decks · same desired retention · similar new cards", size=22,
                     color=MUTED).next_to(cols, DOWN, buff=0.45)  # fmt: skip
        with self.voiceover(
            "Keep it fair the way the benchmark couldn't: "
            '<bookmark mark="f"/>same decks, same desired retention, a similar load of '
            "new cards.",
            hold="reveal",
        ):
            self.at("f", FadeIn(fair))
        self.checkpoint(
            "Your preset uses RWKV-Instant, and you review\n"
            "on your phone during a train ride.\nWhat decides which cards are due there?",
            "Fallback due dates – the phone schedules with FSRS-6, no live ordering",
        )

        model = Card("model", color=PRIMARY).move_to(LEFT * 3.2 + UP * 0.6)
        log = Card("your review log", color=ACCENT).move_to(RIGHT * 3.2 + UP * 0.6)
        top = CurvedArrow(model.get_top() + UP * 0.1, log.get_top() + UP * 0.1, angle=-1.0,
                          color=FG)  # fmt: skip
        bot = CurvedArrow(log.get_bottom() + DOWN * 0.1, model.get_bottom() + DOWN * 0.1,
                          angle=-1.0, color=FG)  # fmt: skip
        picks = label("picks which reviews happen", size=22).next_to(top, UP, buff=0.1)
        grades = label("is later graded on them", size=22).next_to(bot, DOWN, buff=0.1)
        with self.voiceover(
            '<bookmark mark="p"/>One last twist: once a model chooses which cards you see, '
            'it also chooses the reviews <bookmark mark="g"/>it will '
            "later be graded on.",
            hold="reveal",
        ):
            self.at("p", FadeIn(model, log), FadeIn(top), FadeIn(picks))
            self.at("g", FadeIn(bot), FadeIn(grades))
        with self.voiceover(
            "A benchmark of old logs can't show that loop. "
            "Whether the edge survives it, only your own collection can tell you.",
            hold="chapter",
        ):
            self.play(log.animate.scale(1.1), run_time=0.6)
        self.clear_stage()
        self.recall([
            "Model A predicts at review time, model B when the\n"
            "due date is set. A has lower log loss.\nWhich one schedules better?",
            "Name two reasons RWKV's benchmark score may be\n"
            "flattered – and one reason its test is harder.",
            "After a month of RWKV mode: same true retention,\n"
            "10 % more reviews per day. Did it win?",
        ])  # fmt: skip
