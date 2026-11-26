# Part 01 – The science behind RWKV scheduling

## Concepts (source → id)
C1 Retrievability R: probability of recall now; a scheduler = predictor of R + a rule (review when R hits desired retention) [S1, S3]
C2 Forgetting curve, stability; FSRS as a hand-designed model, few params fit per user (21/34) [S1]
C3 Desired retention as the lever; dynamic per-card DR (frequency rules) [S3, S4]
C4 Benchmark data: 10k collections, ~350M eval reviews, same-day vs not [S1]
C5 Time-series split per user vs RWKV's user-level 5k/5k split [S1]
C6 Log loss [S1]; C7 calibration, RMSE(bins) [S1]; C8 AUC / discrimination [S1]
C9 RMSE-BINS-EXPLOIT: best RMSE, LL 4.6 → never trust one metric [S1]
C10 Results: RWKV-Instant 0.2773 / RWKV-Curve 0.3193 / GRU 0.3328 / FSRS-7 0.3401 / FSRS-6 0.3460 / AVG 0.3945 [S1]
C11 Recurrent state: replay a history into a fixed-size memory [S2, S5]
C12 RWKV mechanics: r/k/v, WKV decaying weighted average, learned per-channel decay, linear time, constant state, parallel training [S5]
C13 What RWKV sees: whole collection, siblings, deck/preset, daily load, answer time, calendar [S1]
C14 One shared 2.76M-param model, trained once, state not weights per user; fork Small 331,511 [S1, S3]
C15 Curve vs Instant: curve can produce intervals; Instant only "now" → orders cards, needs fallback due dates [S1, S2, S3]
C16 Why Instant scores so much better: it sees what happened since the last review (same-day performance, today's load); FSRS-7-Instant experiment 0.3519 → 0.3269 [S3]
C17 Caveats: different split, extra features, deleted-card leak, unintuitive outputs [S1, S3]
C18 Benchmark ≠ daily use: learning steps, undo, sync, mobile fallback to FSRS-6, no guarantee of fewer reviews [S3, S4]
C19 Live session / filtered decks in RWKV4Anki; desktop only [S2]

## Prerequisites
C1 → C2 → C3; C1 → C6–C9 → C10; C11 → C12 → C13/C14 → C15 → C16 → C17 → C18.
Earlier parts: none (new course). The Krypto course's "indistinguishability game" idea is a
possible callback for AUC (ranking pairs) – optional.

## Video plan (8–12 min each)
**1.1 What a scheduler actually predicts** – Every scheduler is a guess about one number: the
chance you'd remember this card right now.
- S0 hook: two cards, both "due today" – which one would you rather review? (pretest)
- S1 retrievability and the forgetting curve, stability
- S2 the rule: desired retention turns a curve into an interval; per-card DR
- S3 FSRS as a hand-built curve: few parameters, fit to *your* history – and what it cannot see
- Out: cliffhanger – how would you know whose guess is better?
- Leaves out: FSRS's formulas in detail.

**1.2 How to grade a fortune teller** – Log loss, calibration and AUC on 350 million reviews,
and the baseline that wins a metric by cheating.
- S0 hook: a forecaster that says "70 %" every day – good or bad? (misconception first)
- S1 log loss: the price of confident mistakes
- S2 calibration and RMSE(bins); the exploit that tops the table with log loss 4.6
- S3 AUC: ranking, not probability
- S4 the benchmark: 10k collections, train-on-past/test-on-future; the leaderboard
- Leaves out: superiority plots, every row of the table.

**1.3 A memory that reads your whole collection** – How RWKV turns a review log into a
fixed-size state, and what it gets to see that FSRS doesn't.
- S0 hook: replay 100,000 reviews on a laptop – why a transformer would choke (predict-before-reveal)
- S1 recurrence: a running state, updated per review
- S2 RWKV's trick: decaying weighted average (WKV), learned decay per channel, linear time & parallel training
- S3 the inputs: siblings, decks, today's load, answer time; one shared model, 2.76M params, no per-user training
- S4 Curve vs Instant: a curve you can schedule with vs a "right now" snapshot
- Leaves out: RWKV version internals (5/6/7 matrix states) – one sentence.

**1.4 Benchmark gold, everyday doubts** – Why RWKV-Instant's lead is real but not what it
seems, and what it takes to put it in Anki.
- S0 hook: Instant's log loss 0.277 vs FSRS-7's 0.340 – guess how much of the gap FSRS closes when it may update right before a review (pretest)
- S1 the information advantage: FSRS-7-Instant experiment; prediction vs scheduling
- S2 fairness: user-level vs time split, extra features, the deleted-card leak
- S3 into Anki: Curve schedules, Instant orders + fallback due dates; live sessions; mobile falls back to FSRS-6; dynamic desired retention
- S4 what would convince you: retention and workload in daily use, not log loss
- Ways out: open question for the learner's own collection (try it in the player's RWKV mode).

## Source errors / caveats
- srs-benchmark README has a stale "20k users / 1.7B reviews" paragraph; we use the 10k set.
- "RWKV-P" (add-on) and "RWKV-Instant" (benchmark) described identically; we treat them as the
  same idea and say so.
- The SRS model's RWKV version isn't published – we teach the shared mechanism only.
- FSRS-7-Instant numbers come from the fork's FAQ citing a benchmark PR – marked as such.

## Additions (not in sources)
- Weather-forecast analogy for calibration; coin-flip baseline intuition for log loss
  (ln 2 ≈ 0.693). AVG = always predict the average; its 0.3945 averages over users with
  different recall rates, so it can't be reduced to one global mean (corrected after review).
