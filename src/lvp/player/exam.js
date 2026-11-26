/* lvp player – exam mode: interleaved, exam-style questions across everything watched so
   far, answered without help, then graded in one report that links back to the moments. */
"use strict";
(() => {
  const LVP = window.LVP, { $, el, fmt } = LVP;
  const S = {
    en: {
      title: "Exam practice", intro: "Mixed questions across the videos you have watched – the way an exam asks them. No hints while you answer; one report at the end.",
      start: "Start exam practice", count: "Questions", making: "Writing your exam…", q: "Question", of: "of",
      next: "Next", finish: "Hand in", grading: "Grading…", score: "Score", again: "New exam", close: "Close",
      need: "Watch at least one video to the end first.", history: "Earlier exams", placeholder: "Your answer",
      rewatch: "Rewatch", timeLeft: "left"
    },
    de: {
      title: "Klausurtraining", intro: "Gemischte Fragen über alle Videos, die du gesehen hast – so, wie eine Klausur fragt. Keine Hinweise beim Antworten; am Ende ein Bericht.",
      start: "Klausurtraining starten", count: "Fragen", making: "Schreibe deine Klausur …", q: "Frage", of: "von",
      next: "Weiter", finish: "Abgeben", grading: "Bewerte …", score: "Punkte", again: "Neue Klausur", close: "Schließen",
      need: "Schau zuerst mindestens ein Video bis zum Ende.", history: "Frühere Klausuren", placeholder: "Deine Antwort",
      rewatch: "Nochmal ansehen", timeLeft: "übrig"
    }
  };
  let T = S.en, course = null;
  const watched = () => course.videos.filter((v) => (LVP.store.get("p-" + v.id)?.furthest || 0) >= v.duration * 0.9);
  const exams = () => { const e = LVP.store.ensure("exams", () => ({ list: [] })); e.list ||= []; return e; };

  function pickVideos(n) {
    // weight: weak answers and long-ago watching first, then the rest – interleaving across parts
    const vs = watched().map((v) => {
      const p = LVP.store.get("p-" + v.id) || {};
      const misses = Object.values(p.answers || {}).filter((a) => a.verdict && a.verdict !== "right").length;
      return { v, w: misses * 3 + (Date.now() - (p.updated || 0)) / 864e5 + Math.random() * 2 };
    }).sort((a, b) => b.w - a.w);
    return vs.slice(0, n).map((x) => x.v);
  }

  async function build(n) {
    const sample = LVP.sample();
    const vids = pickVideos(Math.min(6, Math.max(2, Math.ceil(n / 2))));
    const per = Math.floor(40000 / Math.max(1, vids.length));
    const material = vids.map((v) => `### ${v.id} – ${LVP.videoLabel(v)}\n` + LVP.transcriptText(0, v.duration, per, v)).join("\n\n");
    const prompt = [
      `Write an exam practice set of ${n} questions for the course "${course.title}", from the narration of these videos.`,
      material, "",
      "Rules: interleave the videos (never two from the same video in a row); mix types – small computations, 'what happens if', classify an example, compare two ideas, explain why; each answerable in 1–4 sentences from what was taught; no definition recall; exam difficulty, not trick questions. Language of the narration.",
      'Reply with only JSON: {"questions": [{"q": "...", "a": "model answer", "video": "<video id from the ### headings>", "t": "m:ss where the narration teaches it", "points": 1-3}]}',
    ].join("\n");
    const r = await sample.json(prompt, LVP.m("exam", { cache: false }));
    const qs = (r.questions || []).filter((x) => x && x.q).slice(0, n);
    if (!qs.length) throw { code: "invalid_json" };
    return qs.map((x) => ({ q: String(x.q), a: String(x.a || ""), video: String(x.video || ""), t: LVP.parseTs(x.t), points: Math.max(1, Math.min(3, Number(x.points) || 1)) }));
  }

  async function grade(exam) {
    const prompt = [
      `Grade an exam practice set of the course "${course.title}". For each question compare the learner's answer with the model answer; be fair to correct answers worded differently.`,
      JSON.stringify(exam.questions.map((x, i) => ({ i, q: x.q, model: x.a, points: x.points, answer: exam.answers[i] || "" }))),
      "", "Reply with only JSON in the language of the questions, addressing the learner as you:",
      '{"results": [{"i": 0, "got": points earned (may be half points), "feedback": "1-2 sentences: what was right, what was missing"}], "summary": "2-3 sentences: the pattern in what went well and what to work on next"}',
    ].join("\n");
    return LVP.sample().json(prompt, LVP.m("exam", { cache: false }));
  }

  function render(box, state) {
    box.textContent = "";
    box.append(el("h2", "h", T.title));
    if (!state) {
      box.append(el("p", "hint", T.intro));
      if (!watched().length) { box.append(el("p", "hint", T.need)); return; }
      const row = el("div", "row");
      const sel = el("select"); sel.id = "exam-count";
      for (const n of [6, 10, 15]) { const o = el("option", null, `${n} ${T.count}`); o.value = String(n); sel.append(o); }
      const go = el("button", "btn primary", T.start);
      go.onclick = async () => {
        go.disabled = true; go.textContent = T.making;
        try { const questions = await build(Number(sel.value)); render(box, { questions, answers: [], i: 0, started: Date.now() }); }
        catch (e) { go.disabled = false; go.textContent = T.start; box.append(el("p", "err", LVP.errText(e))); }
      };
      row.append(sel, go); box.append(row);
      const list = exams().list.slice(-5).reverse();
      if (list.length) {
        box.append(el("p", "section-title", T.history));
        for (const x of list) box.append(el("p", "hint", `${new Date(x.at).toLocaleDateString()} · ${x.got}/${x.max} · ${x.summary || ""}`));
      }
      return;
    }
    if (state.result) return report(box, state);
    const x = state.questions[state.i];
    box.append(el("p", "kicker", `${T.q} ${state.i + 1} ${T.of} ${state.questions.length} · ${x.points} P`));
    box.append(el("p", "q", x.q));
    const ta = el("textarea", "field"); ta.placeholder = T.placeholder; ta.value = state.answers[state.i] || ""; ta.id = "exam-answer"; ta.style.minHeight = "120px";
    ta.oninput = () => { state.answers[state.i] = ta.value; };
    box.append(ta);
    const last = state.i === state.questions.length - 1;
    const b = el("button", "btn primary", last ? T.finish : T.next);
    b.onclick = async () => {
      state.answers[state.i] = ta.value;
      if (!last) { state.i++; render(box, state); return; }
      b.disabled = true; b.textContent = T.grading;
      try { state.result = await grade(state); }
      catch (e) { b.disabled = false; b.textContent = T.finish; box.append(el("p", "err", LVP.errText(e))); return; }
      const got = (state.result.results || []).reduce((s, r) => s + (Number(r.got) || 0), 0);
      const max = state.questions.reduce((s, q) => s + q.points, 0);
      const e = exams(); e.list.push({ at: Date.now(), got, max, summary: String(state.result.summary || "").slice(0, 300), misses: state.questions.filter((q, i) => (Number(state.result.results?.find((r) => r.i === i)?.got) || 0) < q.points).map((q) => ({ q: q.q.slice(0, 160), video: q.video, t: q.t })) });
      if (e.list.length > 30) e.list = e.list.slice(-30);
      LVP.store.set("exams", e, true);
      render(box, state);
    };
    const nav = el("div", "row"); nav.append(b); box.append(nav);
    setTimeout(() => ta.focus({ preventScroll: true }), 30);
  }
  function report(box, state) {
    const res = state.result, max = state.questions.reduce((s, q) => s + q.points, 0);
    const got = (res.results || []).reduce((s, r) => s + (Number(r.got) || 0), 0);
    box.append(el("p", "q", `${T.score}: ${got} / ${max}`));
    const bar = el("span", "bar"); const fill = el("i"); fill.style.width = (100 * got / (max || 1)) + "%"; bar.append(fill); box.append(bar);
    if (res.summary) { const s = el("div", "verdict"); LVP.renderRich(s, String(res.summary)); box.append(s); }
    state.questions.forEach((q, i) => {
      const r = (res.results || []).find((x) => x.i === i) || {};
      const cls = (Number(r.got) || 0) >= q.points ? "right" : (Number(r.got) || 0) > 0 ? "partly" : "wrong";
      const v = el("div", "verdict " + cls);
      v.append(el("b", null, `${i + 1}. ${Number(r.got) || 0}/${q.points}`), el("div", null, q.q), el("div", "mine", (LVP.L.yourAnswer || "") + (state.answers[i] || "–")));
      const fb = el("div"); LVP.renderRich(fb, String(r.feedback || ""), q.video); v.append(fb);
      const ref = el("div", "mine", "→ " + q.a); v.append(ref);
      if (cls !== "right" && q.video && q.t != null && course.videos.some((x) => x.id === q.video)) {
        const b = el("button", "btn small", `${T.rewatch} ${fmt(q.t)}`); b.onclick = () => LVP.seek(q.video, q.t); v.append(b);
      }
      box.append(v);
    });
    const again = el("button", "btn", T.again); again.onclick = () => render(box, null);
    const end = el("div", "row"); end.append(again); box.append(end);
  }

  LVP.exam = { open: () => { LVP.selectTab("course"); const box = $("course"); render(box, null); } };
  LVP.examMisses = () => exams().list.slice(-3).flatMap((x) => x.misses || []).slice(-8);
  LVP.hooks.ready.push((c) => { course = c; T = S[(c.language || "en").slice(0, 2)] || S.en; });
})();
