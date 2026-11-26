/* RWKV memory model in the player: a JavaScript port of the RNN form of the RWKV-7 spaced
   repetition model from open-spaced-repetition/srs-benchmark (rwkv/run_as_rnn.py,
   rwkv/model/srs_model_rnn.py, rwkv/model/rwkv_rnn_model.py). It reads the whole review history
   (every card, deck, note, the time of day, the daily load, answer times) and predicts the chance
   of recalling a card right now. Weights: pretrain/RWKV_trained_on_101_4999.pth of that project,
   loaded at run time from rwkv_weights.wasm – raw float32, named .wasm only so artifact hosting
   serves it (not part of this repository).
   Verified against the PyTorch original (tests: max difference ~1e-5). */
"use strict";
(function (root) {
  const C = 128, H = 4, K = 32;
  const MODULES = [   // order of rwkv_modules: [name, layers, channel mixer factor]
    ["card_id", 3, 1.5], ["deck_id", 4, 2.0], ["note_id", 2, 1.5], ["preset_id", 3, 2.0], ["user_id", 4, 2.0],
  ];
  const ID_DIMS = { card_id: 12, note_id: 12, deck_id: 8, preset_id: 8 };
  const ID_ORDER = ["card_id", "note_id", "deck_id", "preset_id"];
  const PERIODS = [3, 7, 30, 100, 365, 3650, 36500];
  const STAT = {
    ed: [1.51, 1.62], edc: [2.14, 2.25], es: [9.96, 5.21], esc: [10.86, 5.8], dur: [8.9, 1.07],
    dnc: [2.945, 2.011], dr: [4.64, 2.59], cnt: [2.55, 1.41], crt: [4.59, 1.30],
  };
  const DAY = 86400;
  const pmod = (a, n) => ((a % n) + n) % n;   // Python's % for negative numbers

  // ---- tensor helpers (Float32Array) ----
  const sigmoid = (x) => 1 / (1 + Math.exp(-x));
  const softplus = (x) => (x > 20 ? x : Math.log1p(Math.exp(x)));
  function linear(W, b, x, out, inn) {
    const y = new Float32Array(out);
    for (let o = 0; o < out; o++) { let s = b ? b[o] : 0; const r = o * inn; for (let i = 0; i < inn; i++) s += W[r + i] * x[i]; y[o] = s; }
    return y;
  }
  function layerNorm(x, w, b, eps = 1e-5) {
    const n = x.length; let m = 0; for (let i = 0; i < n; i++) m += x[i]; m /= n;
    let v = 0; for (let i = 0; i < n; i++) v += (x[i] - m) ** 2; v /= n;
    const d = 1 / Math.sqrt(v + eps), y = new Float32Array(n);
    for (let i = 0; i < n; i++) y[i] = (x[i] - m) * d * w[i] + b[i];
    return y;
  }
  function groupNorm(x, groups, w, b, eps) {
    const n = x.length, g = n / groups, y = new Float32Array(n);
    for (let h = 0; h < groups; h++) {
      let m = 0; for (let i = 0; i < g; i++) m += x[h * g + i]; m /= g;
      let v = 0; for (let i = 0; i < g; i++) v += (x[h * g + i] - m) ** 2; v /= g;
      const d = 1 / Math.sqrt(v + eps);
      for (let i = 0; i < g; i++) { const j = h * g + i; y[j] = (x[j] - m) * d * w[j] + b[j]; }
    }
    return y;
  }
  const map = (x, f) => { const y = new Float32Array(x.length); for (let i = 0; i < x.length; i++) y[i] = f(x[i], i); return y; };
  const lerp = (a, b, w) => map(a, (v, i) => v + w[i] * (b[i] - v));

  class Model {
    constructor(manifest, buffer) {
      const all = new Float32Array(buffer);
      this.w = {};
      for (const t of manifest) { const n = t.shape.reduce((a, b) => a * b, 1); this.w[t.name] = all.subarray(t.offset, t.offset + n); }
      const raw = (sp, n) => Array.from({ length: n }, (_, i) => Math.exp(i * sp / (n - 1)));
      this.sSpace = raw(18.5, 128).map((r) => 0.1 + (r - 1) * Math.E ** (22 - 18.5));
      this.pSpace = raw(18.5, 128).map((r) => 0.5 + (r - 1) * Math.E ** (21 - 18.5));
    }
    p(name) { const v = this.w[name]; if (!v) throw new Error("missing weight " + name); return v; }

    timeMixer(pre, layer, inp, v0, state) {
      const P = (n) => this.p(pre + n);
      const x = layerNorm(inp, P("layer_norm.weight"), P("layer_norm.bias"));
      const xs = state ? state.x : x, S0 = state ? state.S : new Float32Array(H * K * K);
      const L = P("rkvdag_lerp");   // [8, 1, 1, C]
      const m = [0, 1, 2, 3, 4, 5, 6, 7].map((j) => lerp(x, xs, L.subarray(j * C, (j + 1) * C)));
      const r = linear(P("W_r.weight"), null, m[0], C, C);
      const k0 = linear(P("W_k.weight"), null, m[1], C, C);
      const ks = map(linear(P("k_scale_linear.weight"), P("k_scale_linear.bias"), m[6], H, C), sigmoid);
      const vs = map(linear(P("v_scale_linear.weight"), P("v_scale_linear.bias"), m[7], H, C), sigmoid);
      let v;
      if (layer === 0) { v = linear(P("W_v.weight"), null, m[2], C, C); v0 = v; }
      else {
        const vl = map(linear(P("v_lora_simple.B_and_lamb.weight"), P("v_lora_simple.B_and_lamb.bias"), linear(P("v_lora_simple.A.weight"), null, m[2], 8, C), C, 8), sigmoid);
        v = lerp(linear(P("W_v.weight"), null, m[2], C, C), v0, vl);
      }
      const a = map(linear(P("a_lora_simple.B_and_lamb.weight"), P("a_lora_simple.B_and_lamb.bias"), linear(P("a_lora_simple.A.weight"), null, m[4], 16, C), C, 16), sigmoid);
      const g = linear(P("lora_B_g.weight"), null, map(linear(P("lora_A_g.weight"), null, m[5], 16, C), sigmoid), C, 16);
      const dl = linear(P("d_lora_mlp.B_and_lamb.weight"), P("d_lora_mlp.B_and_lamb.bias"), map(linear(P("d_lora_mlp.A.weight"), null, m[3], 16, C), Math.tanh), C, 16);
      const w = map(dl, (z) => Math.exp(-Math.exp(-0.5 - softplus(-z))));
      const kk = new Float32Array(C), kd = new Float32Array(C), vv = new Float32Array(C);
      for (let h = 0; h < H; h++) {
        let nk = 0, nv = 0;
        for (let i = 0; i < K; i++) { nk += k0[h * K + i] ** 2; nv += v[h * K + i] ** 2; }
        nk = Math.max(Math.sqrt(nk), 1e-12); nv = Math.max(Math.sqrt(nv), 1e-12);
        for (let i = 0; i < K; i++) {
          const j = h * K + i;
          kd[j] = ks[h] * k0[j] / nk; vv[j] = vs[h] * v[j] / nv; kk[j] = kd[j] * a[j];
        }
      }
      // single_timestep: S' = S·diag(w) − (S·kd)(a∘kd)ᵀ + v kᵀ ; out = S'·r
      const S = new Float32Array(H * K * K), out = new Float32Array(C);
      for (let h = 0; h < H; h++) {
        const o = h * K * K, hk = h * K;
        for (let i = 0; i < K; i++) {
          let sk = 0; for (let l = 0; l < K; l++) sk += S0[o + i * K + l] * kd[hk + l];
          let acc = 0;
          for (let jj = 0; jj < K; jj++) {
            const s = S0[o + i * K + jj] * w[hk + jj] - sk * (a[hk + jj] * kd[hk + jj]) + vv[hk + i] * kk[hk + jj];
            S[o + i * K + jj] = s; acc += s * r[hk + jj];
          }
          out[hk + i] = acc;
        }
      }
      const gn = groupNorm(out, H, P("out_group_norm.weight"), P("out_group_norm.bias"), 64e-5);
      const bonus = P("bonus"), mix = new Float32Array(C);
      for (let h = 0; h < H; h++) {
        let s = 0; for (let i = 0; i < K; i++) s += r[h * K + i] * bonus[h * K + i] * kk[h * K + i];
        for (let i = 0; i < K; i++) { const j = h * K + i; mix[j] = g[j] * (gn[j] + s * vv[j]); }
      }
      const o2 = linear(P("W_o.weight"), null, mix, C, C);
      return { y: map(inp, (q, i) => q + o2[i]), v0, state: { x, S } };
    }
    channelMixer(pre, inp, state, factor) {
      const P = (n) => this.p(pre + n);
      const x = layerNorm(inp, P("layer_norm.weight"), P("layer_norm.bias"));
      const xs = state || x, kd = Math.round(factor * C);
      const k = linear(P("W_k.weight"), null, lerp(x, xs, P("lerp_k")), kd, C);
      const o = linear(P("W_v.weight"), null, map(k, (z) => (z > 0 ? z * z : 0)), C, kd);
      return { y: map(inp, (q, i) => q + o[i]), state: x };
    }
    module(mi, inp, state) {
      const [, layers, factor] = MODULES[mi], next = [];
      let x = inp, v0 = null;
      for (let l = 0; l < layers; l++) {
        const pre = `rwkv_modules.${mi}.blocks.${l}.`, st = state ? state[l] : null;
        const t = this.timeMixer(pre + "time_mixer.", l, x, v0, st && st.t);
        v0 = t.v0;
        const c = this.channelMixer(pre + "channel_mixer.", t.y, st && st.c, factor);
        x = c.y; next.push({ t: t.state, c: c.state });
      }
      return { y: x, state: next };
    }
    review(features, states) {
      let x = linear(this.p("features2card.0.weight"), this.p("features2card.0.bias"), features, 512, 92);
      x = map(x, (z) => z * sigmoid(z));
      x = layerNorm(x, this.p("features2card.2.weight"), this.p("features2card.2.bias"));
      x = map(linear(this.p("features2card.3.weight"), this.p("features2card.3.bias"), x, C, 512), (z) => z * sigmoid(z));
      const next = [];
      for (let mi = 0; mi < 5; mi++) { const r = this.module(mi, x, states[mi]); x = r.y; next.push(r.state); }
      const z = layerNorm(x, this.p("prehead_norm.weight"), this.p("prehead_norm.bias"));
      let hw = map(linear(this.p("head_w.0.weight"), this.p("head_w.0.bias"), z, C, C), (q) => Math.max(0, q));
      hw = layerNorm(hw, this.p("head_w.2.weight"), this.p("head_w.2.bias"));
      hw = linear(this.p("head_w.4.weight"), this.p("head_w.4.bias"), hw, 512, C);
      const wl = linear(this.p("w_linear.weight"), this.p("w_linear.bias"), hw, 128, 512);
      const mx = Math.max(...wl); let sum = 0; const ow = map(wl, (q) => { const e = Math.exp(q - mx); sum += e; return e; });
      for (let i = 0; i < ow.length; i++) ow[i] /= sum;
      const ah = linear(this.p("ahead_linear.weight"), this.p("ahead_linear.bias"), map(linear(this.p("head_ahead_logits.0.weight"), this.p("head_ahead_logits.0.bias"), z, 512, C), (q) => Math.max(0, q)), 128, 512);
      const pl = linear(this.p("p_linear.weight"), this.p("p_linear.bias"), map(linear(this.p("head_p.0.weight"), this.p("head_p.0.bias"), z, 512, C), (q) => Math.max(0, q)), 4, 512);
      return { ahead: ah, w: ow, p: pl, next };
    }
    curveP(curve, elapsedSeconds) {   // predict_func: forgetting curve + learned residual
      const les = Math.max(1, elapsedSeconds);
      let s = 0; for (let i = 0; i < 128; i++) s += curve.w[i] * 0.9 ** (les / this.sSpace[i]);
      const cp = 1e-5 + (1 - 2e-5) * s;
      let ri = this.pSpace.findIndex((x) => x >= les); if (ri < 0) ri = 127;
      const li = Math.max(0, ri - 1), xl = this.pSpace[li], xr = this.pSpace[ri], yl = curve.ahead[li], yr = curve.ahead[ri];
      const res = 1e-5 + (1 - 2e-5) * (yl + (yr - yl) * (les - xl) / (xr - xl));
      return sigmoid(Math.log(cp / (1 - cp)) + res);
    }
  }

  // ---- the RNNProcess of run_as_rnn.py: features from the review history, states per id ----
  class Process {
    constructor(model, codeFor) {
      this.m = model; this.codeFor = codeFor;
      this.card = {}; this.note = {}; this.deck = {}; this.preset = {}; this.global = null;
      this.first = null; this.prev = null; this.cardSet = new Set(); this.lastNew = {}; this.i = 0; this.lastI = {};
      this.today = -1; this.todayReviews = 0; this.todayNew = 0; this.cardFirst = {}; this.edc = {}; this.esc = {};
      this.codes = { card_id: {}, note_id: {}, deck_id: {}, preset_id: {} };
    }
    code(sub, id) { return (this.codes[sub][id] ||= this.codeFor(sub, id, ID_DIMS[sub])); }
    same(r) {
      const row = { ...r }, c = row.card_id;
      const sc = (x, [m, s]) => ((x === -1 ? 0 : Math.log(1 + 1e-5 + x)) - m) / s;
      row.edc = (this.edc[c] || 0) + row.elapsed_days;
      row.esc = (this.esc[c] || 0) + row.elapsed_seconds;
      const ang = (x) => pmod(x, DAY) * 2 * Math.PI / DAY;
      row.f_es_sin = Math.sin(ang(row.elapsed_seconds)); row.f_es_cos = Math.cos(ang(row.elapsed_seconds));
      row.f_esc_sin = Math.sin(ang(row.esc)); row.f_esc_cos = Math.cos(ang(row.esc));
      row.day_offset = this.first === null ? 0 : row.day_offset - this.first;
      row.day_offset_first = c in this.cardFirst ? this.cardFirst[c] : row.day_offset;
      row.day_of_week = (pmod(row.day_offset, 7) - 3) / 3;
      row.f_dod = Math.log(Math.log(Math.E + (row.day_offset - (this.prev ? this.prev.day_offset : 0))));
      const dnc = c in this.lastNew ? this.cardSet.size - this.lastNew[c] : 0;
      const dr = c in this.lastI ? Math.max(0, this.i - this.lastI[c] - 1) : 0;
      let tr = this.todayReviews, tn = this.todayNew;
      if (row.day_offset !== this.today) { tn = 0; tr = -1; }
      tr += 1; if (!this.cardSet.has(c)) tn += 1;
      const lg = (x, [m, s]) => (Math.log(3 + x) - m) / s;
      row.f = [sc(row.elapsed_days, STAT.ed), sc(row.edc, STAT.edc), sc(row.elapsed_seconds, STAT.es), row.f_es_sin, row.f_es_cos,
        sc(row.esc, STAT.esc), row.f_esc_sin, row.f_esc_cos];
      row.tail = [0, 0, 0, row.f_dod, row.day_of_week, lg(dnc, STAT.dnc), lg(dr, STAT.dr), lg(tn, STAT.cnt), lg(tr, STAT.crt)];
      return row;
    }
    features(row, dur, ratings, state, query) {
      // CARD_FEATURE_COLUMNS, then the id codes, then the day encodings
      const f = [...row.f, dur, ...ratings, ...row.tail, state, query];
      for (const sub of ID_ORDER) f.push(...this.code(sub, row[sub]));
      for (const P of PERIODS) {
        const k = 2 * Math.PI / P;
        f.push(Math.sin(k * pmod(row.day_offset, P)), Math.cos(k * pmod(row.day_offset, P)));
        f.push(Math.sin(k * pmod(row.day_offset_first, P)), Math.cos(k * pmod(row.day_offset_first, P)));
      }
      return Float32Array.from(f);
    }
    run(row, x, skip) {
      const st = [this.card[row.card_id], this.deck[row.deck_id], this.note[row.note_id], this.preset[row.preset_id], this.global];
      const out = this.m.review(x, st);
      if (!skip) { [this.card[row.card_id], this.deck[row.deck_id], this.note[row.note_id], this.preset[row.preset_id], this.global] = out.next; }
      const mx = Math.max(...out.p); const e = Array.from(out.p, (q) => Math.exp(q - mx)); const s = e.reduce((a, b) => a + b, 0);
      return { curve: { ahead: out.ahead, w: out.w }, pNow: 1 - e[0] / s };
    }
    /** Chance of recall if the card were shown now (RWKV-P); does not change the state. */
    immediate(r) { const row = this.same(r); return this.run(row, this.features(row, 0, [0, 0, 0, 0], 0, 1), true).pNow; }
    /** Feed one review (rating 1–4, duration ms, state 0 new / 1 learning / 2 review / 3 relearning).
        mode "run" updates the model, "peek" only returns the curve after such a review,
        "book" only keeps the counters (old history beyond the replay limit). */
    review(r, mode = "run") {
      const row = this.same(r), c = row.card_id;
      let curve = null;
      if (mode !== "book") {
        const ratings = [1, 2, 3, 4].map((g) => (r.rating === g ? 1 : 0));
        const x = this.features(row, (Math.log(10 + r.duration) - STAT.dur[0]) / STAT.dur[1], ratings, r.state - 2, 0);
        curve = this.run(row, x, mode === "peek").curve;
        if (mode === "peek") return curve;
      }
      this.edc[c] = (this.edc[c] || 0) + r.elapsed_days; this.esc[c] = (this.esc[c] || 0) + r.elapsed_seconds;
      if (this.first === null) this.first = row.day_offset;
      if (row.day_offset !== this.today) { this.today = row.day_offset; this.todayNew = 0; this.todayReviews = -1; }
      this.todayReviews += 1;
      if (!this.cardSet.has(c)) { this.todayNew += 1; this.cardSet.add(c); this.cardFirst[c] = row.day_offset - this.first; }
      this.prev = row; this.lastI[c] = this.i; this.lastNew[c] = this.cardSet.size; this.i += 1;
      return curve;
    }
  }

  /* Review events with real timestamps → the model's rows. An event:
     {card, note, deck, preset, ts (ms), rating 1–4, duration (ms), state (before the review)}.
     Days roll over at 4 am local time, as in Anki. */
  class Memory {
    constructor(model, rollHour = 4) { this.m = model; this.p = new Process(model, hashCode); this.last = {}; this.roll = rollHour * 3600; }
    day(ts) { return Math.floor((ts / 1000 - new Date(ts).getTimezoneOffset() * 60 - this.roll) / DAY); }
    row(ev, ts) {
      const l = this.last[ev.card], d = Math.max(this.day(ts), l ? l.day : -Infinity, this.p.prev ? this.p.prev.day_offset + (this.p.first || 0) : -Infinity);
      return { card_id: ev.card, note_id: ev.note ?? ev.card, deck_id: ev.deck ?? "-", preset_id: ev.preset ?? "-", day_offset: d,
        elapsed_days: l ? d - l.day : -1, elapsed_seconds: l ? Math.max(0, Math.round((ts - l.ts) / 1000)) : -1 };
    }
    state(ev) { return !this.last[ev.card] ? 0 : (ev.state == null || ev.state === 0 ? 2 : ev.state); }
    /** Add a review to the history; run = false only keeps the bookkeeping (cheap). */
    feed(ev, run = true) {
      const r = { ...this.row(ev, ev.ts), rating: ev.rating, duration: Math.min(Math.max(ev.duration || 8000, 0), 600000), state: this.state(ev) };
      this.p.review(r, run ? "run" : "book");
      this.last[ev.card] = { ts: ev.ts, day: r.day_offset };
    }
    has(card) { return !!this.last[card]; }
    /** Chance of recalling the card at time now (ms); null for a card without reviews. */
    predict(meta, now) { return this.has(meta.card) ? this.p.immediate(this.row(meta, now)) : null; }
    /** For each rating 1–4 (reviewed now): how long until recall drops to target (ms). */
    preview(meta, now, target, durationMs = 8000) {
      const base = { ...this.row(meta, now), duration: durationMs, state: this.state(meta) };
      return [1, 2, 3, 4].map((g) => {
        const curve = this.p.review({ ...base, rating: g }, "peek");
        let lo = 1, hi = 3.6e9;   // seconds; bisection on a log scale
        if (this.m.curveP(curve, hi) >= target) return hi * 1000;
        if (this.m.curveP(curve, lo) < target) return lo * 1000;
        for (let i = 0; i < 40; i++) { const mid = Math.sqrt(lo * hi); if (this.m.curveP(curve, mid) >= target) lo = mid; else hi = mid; }
        return lo * 1000;
      });
    }
  }

  // stable pseudo-random id codes in {−1.5, −0.5, 0.5, 1.5}, as the model was trained with
  function hashCode(sub, id, dims) {
    let h = 2166136261; const s = sub + ":" + id;
    for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); }
    const out = [];
    for (let i = 0; i < dims; i++) { h ^= h << 13; h ^= h >>> 17; h ^= h << 5; out.push(((h >>> 0) % 4) - 1.5); }
    return out;
  }

  const api = { Model, Process, Memory, hashCode };
  if (typeof module !== "undefined") module.exports = api; else root.LVP_RWKV = api;
})(typeof self !== "undefined" ? self : this);
