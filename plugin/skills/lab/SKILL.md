---
name: lab
description: Design hands-on labs for any subject – decide per concept which skill must be practised and which lab type trains it (code the learner builds or breaks, or a worked problem solved step by step), write it, verify it mechanically, and ship it with the study player. Use when a part of the course is done, when the user wants practice that goes beyond questions, or when the coach finds a concept that answers alone don't fix.
---

# Labs: practice by doing

The study player can already design a lab on demand for the section being watched. Authored
labs are for the concepts that matter most: they are reviewed, verified and fit the course.
Read `learner.md` and the part's coverage map first.

## 1. Pick the skill, then the lab type
For each core concept, write one sentence: *after the lab the learner can …* (compute,
build, break, decide, predict, explain). Then choose:

| The skill is … | Lab type | Example |
|---|---|---|
| a procedure, algorithm, mechanism, attack, simulation | `code` (Python by default; JavaScript when the course is about the web) | break a reused key; simulate a population; implement a scheduler |
| a computation, derivation, applying a rule to a case | `steps` (no programming) | posterior after two tests; a proof in four steps; a tax calculation |
| a judgement between options | `steps` with text answers | which mode of operation fits; which experiment design is valid |

Prefer *build it, break it, measure it* over reproducing a formula. One idea per lab, 10–30
minutes. If the learner does not program (`learner.md`), use `steps` everywhere.

## 2. Write it – `labs/NN_part.yaml`
```yaml
labs:
  - video: v2.2            # or a video id; optional section: S3Name
    title: …
    goal: what to do and why it matters (2–4 sentences, the course language)
    # code lab
    lang: python
    starter: |            # runnable, clear TODOs, all helpers given
    check: |              # asserts with messages that say what is wrong, not the answer;
                          # last line: print("ALL CHECKS PASSED")
    hints: [direction, method, nearly the code]
    solution: |
  - video: v2.3
    title: …
    goal: …
    steps:                 # worked problem: first step may be a worked example
      - {prompt: "…", kind: number, answer: "9.1", calc: "100 * 99 / 1098", tol: 0.02, example: true, explain: "…"}
      - {prompt: "…", kind: number, answer: "…", calc: "…", tol: 0.02, hint: "…", explain: "…"}
      - {prompt: "…", kind: text, answer: "…", hint: "…"}
```
Number answers accept `9,1 %`, `1/11` and `0.091` style input; `tol` is relative. Text
answers are judged by Claude against `answer`.

## 3. Verify – no lab ships unverified
- code: the solution plus the checks prints `ALL CHECKS PASSED`; the unchanged starter plus
  the checks fails with a helpful message (otherwise the checks test nothing).
- steps: every `calc` evaluates (Python) to `answer` within `tol`.

```bash
uv run python - <<'PY'
import yaml, io, contextlib
for lab in yaml.safe_load(open("labs/NN_part.yaml"))["labs"]:
    if "steps" in lab:
        for s in lab["steps"]:
            if s.get("calc"):
                assert abs(eval(s["calc"]) - float(str(s["answer"]).replace(",", ".").rstrip(" %"))) <= abs(float(str(s["answer"]).replace(",", ".").rstrip(" %"))) * s.get("tol", 0.02), s
    else:
        out = io.StringIO()
        with contextlib.redirect_stdout(out): exec(lab["solution"] + "\n" + lab["check"], {})
        assert "ALL CHECKS PASSED" in out.getvalue(), lab["title"]
        try:
            with contextlib.redirect_stdout(io.StringIO()): exec(lab["starter"] + "\n" + lab["check"], {})
            raise SystemExit(f"starter passes: {lab['title']}")
        except AssertionError:
            pass
    print("ok", lab["title"])
PY
```
The player applies the same rules to the labs Claude designs live (with one repair round);
a lab that still fails is not shown.

## 4. Ship
`uv run lvp-player --only-data` and republish the player (`player` skill). The lab appears
in the Lab tab of its video and section; the learner's progress (`lab-…` documents) is
visible to the `coach` skill.
