# Teaching style guide

The bar: **3Blue1Brown**, with ideas borrowed from Veritasium, Vsauce and Philosophy Tube. The
viewer thinks along, feels smart and is never talked down to. The reasons behind several rules
are in `pitfalls.md`, the evidence in the repository's `docs/research/learning_science.md`.

This is a **toolbox, not a formula**. A coherent style is good; a template every video follows
beat for beat is not. The learner profile (`learner.md`) adjusts depth, tone and analogies.

## Always

- **Respect the viewer.** No "simply", "just", "don't worry", no hand-holding. Assume a sharp
  listener.
- **Explain once.** Every idea is explained in exactly one place in the whole course. Later
  videos use a one-sentence callback ("you know the base rate from Video 2.2") and add only
  what is new. A short deliberate refresher right before an idea is *extended* is fine;
  re-deriving it is not. (The most common viewer complaint: the same derivation again.)
- **No recaps** inside a video ("as we have seen …"). The picture may reinforce; the narration
  doesn't restate.
- **Concise.** Cut filler. Hold a shot only while it shows something.
- **Motivated, not dropped.** A definition comes with its reason: why this, what else could it
  have been, what breaks without it.
- **The picture carries the load.** Never read on-screen text aloud, never describe what is
  obvious on screen.
- **Correct.** Real numbers that compute; claims that match the source material. Where the
  source is wrong, teach it right and note the correction in the coverage map.
- **The videos replace the source.** Never point at material the viewer doesn't have ("the
  slide says", "according to the lecture"). Cross-references go to our own videos; exercises
  may be named.
- **Never narrate over an empty screen.** The engine keeps the last picture until the next one
  appears; don't defeat it with `clear_stage(now=True)` before narration.

## The learning loop (evidence-based, built into every video)

| Element | Where | Rule |
|---|---|---|
| `self.pretest([...])` | end of the hook (S0) | 1–2 guess-first questions on the *core* concepts. Never the question the hook just answered. (Pretesting: g ≈ 0.5 for the asked content.) |
| `self.checkpoint(q, a)` | end of every section from S2 on | asks about the **previous** section (lag 1) – retrieval only trains memory after some forgetting; a question answered one sentence ago is an echo. **Application or transfer**, not a repeated sentence. 5 s think, 3.5 s answer. (Interpolated testing with feedback: g ≈ 0.5, d = 1.38 in lecture videos.) |
| `self.recall([...])` | end of the video | 3 questions; the last section's material goes here. Different from every check in the video and from earlier videos. |

**What makes a good question:** a concrete scenario the video didn't show ("the same test,
but the disease is ten times rarer – what changes?"), a "what breaks if", a computation with new numbers, a
classification of mixed examples. **Bad:** answered in the line before, a definition recall
("what is X?"), the same question asked in another video, an answer that needs content not yet
taught, ambiguous wording, anything whose answer could be disputed.

## Toolbox

Over a few videos, each tool should show up sometimes and none every time.

**Ways in:** a puzzle or impossible-seeming task · a real incident and how it happened · a
question most people answer wrong (viewer commits, then reveal) · a naive design that almost
works and the moment it fails · straight in, when the topic is its own hook.

**Ways through:**
- *Let them invent it:* build from the problem so the solution feels like the viewer's own
  idea; name it afterwards.
- *Misconception first:* state the tempting wrong idea, then take it apart.
- *Steelman:* the strongest attack / counter-position, not a strawman.
- *Concrete before abstract:* small numbers first, then the general form.
- *Curiosity chain:* surprising facts that loop back to the starting question.
- *Historical arc:* how people actually got there, wrong turns included.
- *Worked example → faded:* one full calculation, then the viewer does the next step.

**Thinking moments:** predict-before-reveal (on-screen question + `hold="question"`), "how
would you break this?", a deliberately wrong step to catch.

**Ways out:** a new angle (not a recap) · a cliffhanger into the next video · an open question
the next video answers.

## Lessons from real 3Blue1Brown scripts

Re-read one official transcript (github.com/3b1b/captions) before writing a new script; a
zero-shot draft drifts.

- Make the viewer the designer: each step fixes a problem, then a loophole motivates the next.
- One-sentence bridges between topics: close the last idea, open the next.
- Voice the skeptic ("at first this seems impossible").
- Hand the viewer a puzzle.
- Be honest about limits ("there's no rigorous proof that …").
- Every definition has a motivating example *before* it.
- Wonder first, then a roadmap: show the surprising thing, then say in one or two sentences
  where the video goes (`title_card(..., say=roadmap)` keeps the title on screen meanwhile).
- Admit temporary confusion ("it might not yet be clear why this matters, but …").
- Make huge numbers tangible – **once per course**; later videos refer back.

## Variety check (before each script)

Look at the previous two videos and vary the opening type, the main building technique and
the ending. Recurring elements (characters, colours, voice) give coherence; the shape of each
video should still surprise.

## Language

- Narration in the course language (`lvp.toml`). Second person, active voice, short spoken
  sentences. Numbers the voice reads are written as words where it matters ("two to the power
  of one hundred twenty-eight").
- Standard technical terms stay in their usual form, explained once.
- No stock phrases: "In this video …", "Let's dive in", "As we have seen", hype words.
- Pronunciation problems go into `[pronunciation]` in `lvp.toml`, never into the visible text.

## Coverage

Every topic in the source and every exam hint must land somewhere: a video, a card or a
question. `plan/coverage.md` lists source item → where it is covered. Gaps are flagged to the
user, never silently dropped.

## Companion material

- **Cards:** atomic; prefer "why / what happens if" over definitions; cloze for formulas.
  Size the deck to the learner's review budget (20 new/day ≈ 200 reviews/day at FSRS 0.90):
  typically 30–45 cards per 90-minute source.
- **Exercise companions:** graded hints (Hint 1 = direction, Hint 2 = method, then the worked
  solution), so the learner gets stuck productively instead of reading the answer.
- **Mixed practice:** interleave problem types across parts of the course (not vocabulary).
