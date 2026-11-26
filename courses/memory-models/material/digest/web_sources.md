# Digest: web sources (paraphrased, numbers copied exactly; fetched 2026-11-26)

Sources:
- S1 open-spaced-repetition/srs-benchmark README (+ rwkv/ folder README)
- S2 zaguk/RWKV4Anki README (Anki add-on)
- S3 JSchoreels/anki README + RWKV_FAQ.md (experimental Anki fork: FSRS-7, RWKV, Dynamic Desired Retention)
- S4 Reddit post by the fork author (pasted by the user)
- S5 BlinkDL/RWKV-LM README (architecture background)

## S1 srs-benchmark
- Data: anki-revlogs-10k, 10k Anki collections, ~727M reviews. Evaluated: 9,999 collections /
  349,923,850 reviews (no same-day) and 10,000 / 519,296,315 (with same-day). (README also has a
  stale paragraph mentioning 20k users / 1.7B reviews – ignore.)
- Split: TimeSeriesSplit per user (train on older, test on newer, 5 splits, first dropped).
  RWKV is the exception: one shared model trained on 5,000 users, tested on the other 5,000,
  swapped (twice) for coverage. FSRS: parameters per user. GRU/LSTM: pretrained on 100 users
  (Reptile), fine-tuned per user.
- Metrics: Log loss (binary cross-entropy of predicted recall vs 0/1 outcome, lower better);
  RMSE(bins) (reviews binned by interval length, review count, lapses; squared gap between mean
  prediction and mean outcome per bin, weighted by bin size; lower better); AUC (ranking:
  probability a random recalled review gets a higher prediction than a random forgotten one;
  0.5 = chance). LL and RMSE(bins) = calibration; AUC = discrimination.
  RMSE-BINS-EXPLOIT baseline: RMSE(bins) 0.01350 (best of all!) with log loss 4.608 – shows the
  metric can be gamed.
- RWKV-Curve: modified RWKV architecture (RNN with transformer-like training), reads the whole
  collection's review history (all cards), with extra features: review duration, new cards and
  reviews done today, sibling cards, deck/preset hierarchy, day of week/month/year ("not
  limited to"). Outputs a forgetting curve.
- RWKV-Instant: predicts recall at the moment just before the review; no forgetting curve;
  can give unintuitive outputs (never 100 %, recall rising with time).
- Params: RWKV 2,762,884; GRU 503; LSTM 8,869; FSRS-7 34; FSRS-6 21; HLR 3.
- Results (no same-day, LL / RMSE(bins) / AUC):
  RWKV-Instant 0.2773 / 0.02502 / 0.8329; RWKV-Curve 0.3193 / 0.0540 / 0.7683;
  GRU 0.3328 / 0.0549 / 0.7324; LSTM 0.3332 / 0.05378 / 0.7329;
  FSRS-7 recency 100ep 0.3363 / 0.05764 / 0.7243; MOVING-AVG 0.3369 / 0.05915 / 0.7001;
  FSRS-7 0.3401 / 0.0634 / 0.7167; FSRS-6 0.3460 / 0.0653 / 0.7034;
  FSRS-5 0.3561 / 0.0742 / 0.7010; DASH 0.3682 / 0.0838 / 0.6311; AVG 0.3945 / 0.1034 / 0.4997;
  ACT-R 0.4033 / 0.1074 / 0.5225; HLR 0.4694 / 0.1275 / 0.6369; Ebisu v2 0.4989 / 0.1627 / 0.6051;
  RMSE-BINS-EXPLOIT 4.608 / 0.01350 / 0.6548.
- With same-day: RWKV-Instant 0.2660 / 0.03212 / 0.8450; RWKV-Curve 0.2974 / 0.05438 / 0.7964;
  FSRS-7 0.3206 / 0.06148 / 0.7475; FSRS-6 0.3842 / 0.0985 / 0.6830.
- rwkv/ training: CUDA, ~400 GB preprocessing storage, WSD learning-rate schedule.

## S2 RWKV4Anki (add-on)
- Inference only, Rust/PyO3 backend (RWKV-SRS), no Torch; CPU or GPU; compact recurrent state
  over the review history; partial state loading (only relevant card/note/deck/preset state);
  local checkpoints so the history needn't be replayed at every start.
- "RWKV-P" = estimate right before a review (= the benchmark's Instant); "Forgetting Curve" =
  recall vs elapsed time (predict-ahead, scheduling experiments).
- Live Session: refreshes predictions between reviews, picks cards below desired retention.
- Filtered decks from predictions; evaluation tools (LL, RMSE(bins), AUC, calibration graph).
- Desktop only (Anki ≥ 26.05); mobile can't update predictions. Pre-1.0, AI-written (Codex),
  generated mirror, no licence granted.

## S3 JSchoreels fork + FAQ
- Review scheduler per preset: FSRS-6, FSRS-7, RWKV-Curve, RWKV-Instant.
- Curve → day intervals (load balancer and fuzz up to 90 days); can schedule < 1 day with
  same-day reviews enabled.
- Instant → orders cards from current predicted recall; its interval isn't authoritative; a
  fallback due-date calculator (FSRS or Curve) writes due dates for sync/mobile/statistics;
  same-day spacing default: 5 other answers and 30 s; "minimum reviews per day" is a floor.
- Weights trained beforehand; loading replays your review history into the state – no
  per-user gradient training. Sizes: Small 331,511 params (default), Tiny 185,057 each.
- Deleted-card leak: in the public data deleted cards lack card/note/deck rows; a naive
  pipeline marks them "missing", which tells a model the card will be deleted later (i.e.
  abandoned, often forgotten). Fork models zero those inputs and skip deleted cards.
- FSRS7-"Instant" experiment (cited PR #360, users 1–300): parameters updated up to review
  time 0.3269 vs 0.3519 LL; parameters from just after the previous review: +0.4 %, CI
  includes 0 → most of Instant's edge is information that arrives after the last review.
- Changing desired retention doesn't retrain RWKV. No guarantee of fewer reviews than FSRS.
- Dynamic Desired Retention: reviewer hook lets an add-on set desired retention per card from
  ordered search rules (e.g. Frequency<1000).

## S4 Reddit post (author's framing)
- Six months of work; goal is to test scheduler ideas in daily use, not a "better Anki".
- Benchmark wins ≠ daily usefulness: learning steps, stats, undo, sync, filtered decks,
  mobile, large collections.
- Mobile falls back to FSRS-6 for next intervals.
- AI coding agents heavily used; author reviews, tests and is responsible.

## S5 RWKV architecture
- Linear-time, constant-memory RNN that trains in parallel like a transformer; no KV cache.
- Time mixing: receptance r, key k, value v from the input; WKV = exponentially decaying
  weighted average of past values, weights e^{k}, per-channel learned decay w; output gated
  by sigmoid(r). Channel mixing: gated feed-forward. RWKV-5/6: matrix-valued states,
  data-dependent decay; RWKV-7: state "test-time-trained" on the context.
- Which RWKV version the SRS model uses is not stated – don't claim one.
