/* lvp player – hands-on labs: Claude designs a small lab for the section being watched
   (or the course ships authored ones), the learner codes in the browser, checks run
   locally, hints come in steps, and the lab tutor can run the learner's code itself. */
"use strict";
(() => {
  const LVP = window.LVP, { $, el, fmt } = LVP;
  const S = {
    en: {
      intro: "Practise the idea of the part you are watching with a small hands-on task. Claude designs it for this part; checks run right here.",
      make: "Make a lab for this part", another: "Another lab", making: "Designing a lab…", run: "Run", check: "Check",
      hint: "Hint", help: "Ask the lab tutor", solution: "Show solution", reset: "Reset code", wide: "Wide",
      passed: "All checks passed.", failed: "Not yet – read the output above.", loadingPy: "Starting Python (first time takes a few seconds)…",
      stopped: "Stopped after 20 s – an endless loop?", noRuntime: "This lab's runtime could not start here.",
      helpPrompt: "I'm stuck on this lab. Look at my code and the last output; give me the smallest nudge that gets me unstuck – no full solution.",
      solConfirm: "Show the solution? Try a hint first – struggling a bit is where the learning happens.", yes: "Show it", no: "Not yet",
      part: "Part", done: "done", authored: "from the course", lang: { python: "Python", javascript: "JavaScript" },
      noClaude: "Labs are designed by Claude – open the player on claude.ai or in the Claude app.",
      step: "Step", example: "worked example", opening: "Opening", stepsType: "Worked problem", notYet: "Not yet.", showStep: "Show this step"
    },
    de: {
      intro: "Übe die Idee des Abschnitts, den du gerade siehst, mit einer kleinen praktischen Aufgabe. Claude entwirft sie für diesen Abschnitt; die Prüfungen laufen direkt hier.",
      make: "Labor zu diesem Abschnitt", another: "Anderes Labor", making: "Entwerfe ein Labor …", run: "Ausführen", check: "Prüfen",
      hint: "Hinweis", help: "Labor-Tutor fragen", solution: "Lösung zeigen", reset: "Code zurücksetzen", wide: "Breit",
      passed: "Alle Prüfungen bestanden.", failed: "Noch nicht – lies die Ausgabe oben.", loadingPy: "Starte Python (beim ersten Mal dauert es ein paar Sekunden) …",
      stopped: "Nach 20 s gestoppt – eine Endlosschleife?", noRuntime: "Die Laufzeitumgebung für dieses Labor startet hier nicht.",
      helpPrompt: "Ich komme bei diesem Labor nicht weiter. Sieh dir meinen Code und die letzte Ausgabe an; gib mir den kleinsten Schubs, der mich weiterbringt – keine komplette Lösung.",
      solConfirm: "Lösung zeigen? Probier erst einen Hinweis – ein bisschen Ringen ist der Teil, bei dem man lernt.", yes: "Zeigen", no: "Noch nicht",
      part: "Abschnitt", done: "geschafft", authored: "aus dem Kurs", lang: { python: "Python", javascript: "JavaScript" },
      noClaude: "Labore entwirft Claude – öffne den Player auf claude.ai oder in der Claude-App.",
      step: "Schritt", example: "Beispiel", opening: "Einstieg", stepsType: "Aufgabe in Schritten", notYet: "Noch nicht.", showStep: "Schritt zeigen"
    }
  };
  let T = S.en, course = null, worker = null, seq = 0;
  const waiting = new Map();
  const key = (v, sec) => "lab-" + v + "-" + sec;

  function spawn() {
    try {
      worker = new Worker("lab-worker.js");
      worker.onmessage = (e) => { const w = waiting.get(e.data.id); if (w) { waiting.delete(e.data.id); clearTimeout(w.timer); w.resolve(e.data); } };
      worker.onerror = () => { for (const w of waiting.values()) w.resolve({ out: T.noRuntime, ok: false, fatal: true }); waiting.clear(); };
    } catch { worker = null; }
  }
  function exec(lang, code, limit = 20000, warm = false) {
    if (!worker) spawn();
    if (!worker) return Promise.resolve({ out: T.noRuntime, ok: false, fatal: true });
    return new Promise((resolve) => {
      const id = ++seq;
      const timer = setTimeout(() => { worker.terminate(); worker = null; waiting.delete(id); resolve({ out: T.stopped, ok: false }); }, limit);
      waiting.set(id, { resolve, timer });
      worker.postMessage({ id, lang, code, warm });
    });
  }
  LVP.runCode = exec;

  async function design(cur, sec, avoid) {
    const sample = LVP.sample();
    const prompt = [
      `Design ONE hands-on lab for a learner of the course "${course.title}" who is watching "${cur.title}", part "${sec.title}".`,
      "What this part teaches:", LVP.transcriptText(sec.t, sec.end, 9000),
      course.learner ? "About the learner:\n" + course.learner.slice(0, 800) : "",
      avoid ? "Do something different from this earlier lab: " + avoid : "",
      "",
      "First decide which skill this part should train, then pick the lab type that trains it:",
      '- "code": the learner builds, breaks, measures or simulates the mechanism in a little code (best when the idea is a procedure, an algorithm, an attack, a simulation, or the learner programs).',
      '- "steps": a worked problem solved step by step – computations, derivations, applying a rule to a case, reading a result (best for formulas, quantities, proofs and judgement; no programming needed).',
      "10–30 minutes of work. Everything learner-facing in the language of the narration.",
      "",
      'For "code":',
      course.python === false
        ? "- lang: javascript (plain functions, console.log; no DOM, no network)."
        : "- lang: python (preferred; standard library only – no numpy, no network, no files, no input()) or javascript (plain functions, console.log; no DOM, no network).",
      "- starter: runnable code with clear TODOs and all helpers they shouldn't have to write, small and readable.",
      "- check: code appended after the learner's code that tests it with assert statements (python) or assert(cond, message) calls (javascript; assert is provided). Every failing check says what is wrong, not the answer. The last line prints exactly ALL CHECKS PASSED.",
      "- hints: 3 graded hints – 1. direction, 2. method, 3. nearly the code. solution: the starter completed so that it passes the checks.",
      "",
      'For "steps": 3–6 steps that build on each other; the first may be fully worked (example: true) so the learner sees the method, later ones fade to the learner.',
      '- each step: {"prompt": "...", "kind": "number" | "text", "answer": the correct answer, "calc": for numbers a Python expression that computes it (e.g. "99 / (99 + 999)"), "tol": relative tolerance for numbers (e.g. 0.02), "hint": "...", "explain": "why, 1-2 sentences", "example": true|false}',
      "- numbers: ask for one value with its unit or format stated (e.g. 'as a percentage, one decimal'); text: a short answer Claude will judge.",
      "",
      'Reply with only JSON. Code: {"type": "code", "title": "...", "goal": "what to do and why it matters, 2-4 sentences", "lang": "python" | "javascript", "starter": "...", "check": "...", "hints": ["...", "...", "..."], "solution": "..."}',
      'Steps: {"type": "steps", "title": "...", "goal": "...", "steps": [ ... ]}',
    ].filter(Boolean).join("\n");
    let lab = await sample.json(prompt, { cache: false });
    for (let attempt = 0; attempt < 2; attempt++) {
      const problem = await verify(lab);
      if (!problem) { lab.verified = true; return lab; }
      if (attempt === 1) break;
      // one repair round: show Claude exactly what failed
      lab = await sample.json(prompt + "\n\nYour previous lab failed verification:\n" + problem + "\nPrevious lab:\n" + JSON.stringify(lab).slice(0, 12000) + "\nReturn the corrected lab, same JSON format.", { cache: false });
    }
    throw { code: "invalid_json" };
  }
  LVP.designLab = design;

  // Returns null when the lab is sound, else a description of what failed.
  async function verify(lab) {
    if (!lab || typeof lab !== "object") return "not a JSON object";
    if (lab.type === "steps") {
      if (!Array.isArray(lab.steps) || !lab.steps.length) return "no steps";
      for (const [i, st] of lab.steps.entries()) {
        if (!st.prompt) return `step ${i + 1} has no prompt`;
        if (st.kind === "number") {
          const want = toNumber(st.answer);
          if (want == null) return `step ${i + 1}: answer is not a number`;
          if (st.calc && course.python !== false) {
            const r = await exec("python", `print(repr(float(${st.calc})))`, 30000);
            const got = r.ok ? Number(r.out.trim()) : NaN;
            if (!Number.isFinite(got)) return `step ${i + 1}: calc "${st.calc}" does not evaluate: ${r.out.slice(0, 200)}`;
            if (!close(got, want, Math.max(Number(st.tol) || 0.01, 0.005))) return `step ${i + 1}: answer ${st.answer} but calc gives ${got}`;
            // the computed value is the truth: small slips inside the tolerance must not reach the learner
            if (got !== want) st.answer = String(Number(got.toPrecision(4)));
          }
        }
      }
      return null;
    }
    lab.type = "code";
    if (!lab.starter || !lab.check || !lab.solution) return "starter, check and solution are required";
    lab.lang = lab.lang === "javascript" ? "javascript" : "python";
    const r = await exec(lab.lang, lab.solution + "\n\n" + lab.check, 30000);
    if (!(r.ok && /ALL CHECKS PASSED/.test(r.out))) return "the solution does not pass the checks. Output:\n" + String(r.out).slice(-1500);
    const s = await exec(lab.lang, lab.starter + "\n\n" + lab.check, 30000);
    if (s.ok && /ALL CHECKS PASSED/.test(s.out)) return "the unfinished starter already passes the checks – the checks test nothing";
    return null;
  }
  LVP.verifyLab = verify;

  // "9,1 %", "1/11", "0.0909", "≈ 91%" → number (percent stays as written: 9.1)
  function toNumber(v) {
    if (typeof v === "number") return v;
    let s = String(v ?? "").replace(/[≈~\s]/g, "").replace(/%$/, "").replace(/(\d),(\d)/g, "$1.$2");
    const f = /^(-?[\d.]+)\/(-?[\d.]+)$/.exec(s);
    if (f) return Number(f[1]) / Number(f[2]);
    s = s.replace(/[^\d.eE+-]/g, "");
    const n = parseFloat(s);
    return Number.isFinite(n) ? n : null;
  }
  const close = (a, b, tol) => Math.abs(a - b) <= Math.max(Math.abs(b) * tol, 1e-9);

  function renderSteps(box, st) {
    const lab = st.lab; st.steps ||= {};
    lab.steps.forEach((step, i) => {
      const done = st.steps[i]?.ok || step.example;
      const prevDone = i === 0 || lab.steps.slice(0, i).every((x, k) => x.example || st.steps[k]?.ok || st.steps[k]?.shown);
      if (!prevDone) return;   // steps unlock one after another
      const v = el("div", "verdict " + (done ? "right" : ""));
      v.append(el("b", null, `${T.step} ${i + 1}${step.example ? " · " + T.example : ""}`));
      const pr = el("div"); LVP.renderRich(pr, step.prompt); v.append(pr);
      if (step.example || st.steps[i]?.ok || st.steps[i]?.shown) {
        v.append(el("div", "mine", "→ " + String(step.answer)));
        if (step.explain) { const e = el("div"); LVP.renderRich(e, step.explain); v.append(e); }
        box.append(v); return;
      }
      const inp = el("input", "field"); inp.style.minHeight = "0"; inp.id = `step-${i}`; inp.value = st.steps[i]?.text || "";
      const fb = el("div", "hint");
      const check = el("button", "btn small primary", T.check);
      check.onclick = async () => {
        const rec = (st.steps[i] ||= { tries: 0 }); rec.text = inp.value.trim(); rec.tries++;
        let ok = false;
        if (step.kind === "number") {
          const got = toNumber(rec.text), want = toNumber(step.answer);
          ok = got != null && want != null && (close(got, want, Number(step.tol) || 0.02) || close(got * 100, want, Number(step.tol) || 0.02) || close(got, want * 100, Number(step.tol) || 0.02));
          fb.textContent = ok ? T.passed : (rec.tries >= 2 && step.hint ? `${T.notYet} ${T.hint}: ${step.hint}` : T.notYet);
        } else if (LVP.sample()) {
          check.disabled = true; fb.textContent = LVP.L.grading;
          try {
            const r = await LVP.sample().json([
              "Judge a learner's short answer to one step of a worked problem. Accept answers that are right in substance.",
              `Step: ${step.prompt}`, `Correct answer: ${step.answer}`, `Learner: ${rec.text}`,
              'Reply with only JSON in the language of the step: {"ok": true|false, "feedback": "one sentence"}',
            ].join("\n"), { modelTier: "quick", cache: false });
            ok = !!r.ok; fb.textContent = String(r.feedback || "");
          } catch (e) { fb.textContent = LVP.errText(e); }
          check.disabled = false;
        }
        rec.ok = ok;
        if (ok && lab.steps.every((x, k) => x.example || st.steps[k]?.ok || st.steps[k]?.shown) && !st.passed) { st.passed = true; st.passedAt = Date.now(); }
        LVP.store.set(st._key, st);
        if (ok) render();
      };
      const show = el("button", "btn small", T.showStep);
      show.onclick = () => { (st.steps[i] ||= { tries: 0 }).shown = true; LVP.store.set(st._key, st); render(); };
      inp.addEventListener("keydown", (e) => { if (e.key === "Enter") check.click(); });
      const row = el("div", "row"); row.append(check); if ((st.steps[i]?.tries || 0) >= 2) row.append(show);
      v.append(inp, row, fb); box.append(v);
    });
  }

  function render() {
    const box = $("lab"); if (!box) return; box.textContent = "";
    const cur = LVP.cur(); if (!cur) return;
    const sec = labSection(cur);
    const head = el("div", "row"); head.style.justifyContent = "space-between";
    head.append(el("span", "hint", `${T.part}: ${sec.title}`));
    const wide = el("button", "btn small", T.wide); wide.setAttribute("aria-pressed", String(document.body.classList.contains("wide")));
    wide.onclick = () => { document.body.classList.toggle("wide"); render(); };
    head.append(wide); box.append(head);
    const state = LVP.store.get(key(cur.id, sec.name));
    const authored = (course.labs || []).find((l) => l.video === cur.id && (!l.section || l.section === sec.name));
    if (!state && !authored) {
      box.append(el("p", "hint", T.intro));
      if (!LVP.sample()) { box.append(el("p", "hint", T.noClaude)); return; }
      const b = el("button", "btn primary", T.make); b.onclick = () => create(cur, sec, null, b); box.append(b);
      return;
    }
    const st = state || { _key: key(cur.id, sec.name), lab: { type: authored.steps ? "steps" : "code", ...authored, authored: true }, code: authored.starter, hints: 0, checks: 0 };
    if (!state) LVP.store.set(st._key, st);
    const lab = st.lab;
    const t = el("h2", "h", lab.title || ""); box.append(t);
    box.append(el("span", "hint", `${lab.type === "steps" ? T.stepsType : (T.lang[lab.lang] || lab.lang)}${lab.authored ? " · " + T.authored : ""}${st.passed ? " · ✓ " + T.done : ""}`));
    const goal = el("div", "lab-goal"); LVP.renderRich(goal, lab.goal || ""); box.append(goal);
    if (lab.type === "steps") {
      renderSteps(box, st);
      if (LVP.sample()) { const again = el("button", "btn small", T.another); again.onclick = () => create(cur, sec, lab.title, again); box.append(rowOf(again)); }
      return;
    }
    const code = el("textarea", "code"); code.value = st.code ?? lab.starter; code.spellcheck = false; code.id = "lab-code";
    code.addEventListener("keydown", (e) => {
      if (e.key === "Tab") { e.preventDefault(); const s = code.selectionStart; code.setRangeText("    ", s, code.selectionEnd, "end"); }
    });
    code.addEventListener("input", () => { st.code = code.value; LVP.store.set(st._key, st); });
    box.append(code);
    const out = el("pre", "out"); out.textContent = st.out || ""; box.append(out);
    const row = el("div", "row");
    const btn = (label, f, cls = "btn small") => { const b = el("button", cls, label); b.onclick = f; row.append(b); return b; };
    const show = (r, cls) => { out.textContent = r.out || "(no output)"; out.className = "out " + (cls || ""); st.out = out.textContent; LVP.store.set(st._key, st); };
    const runIt = async (withCheck, b) => {
      b.disabled = true;
      if (lab.lang === "python") out.textContent = T.loadingPy;
      const r = await exec(lab.lang, code.value + (withCheck ? "\n\n" + lab.check : ""));
      b.disabled = false;
      if (!withCheck) return show(r, r.ok ? "" : "fail");
      st.checks = (st.checks || 0) + 1;
      const pass = r.ok && /ALL CHECKS PASSED/.test(r.out);
      if (pass && !st.passed) { st.passed = true; st.passedAt = Date.now(); }
      show({ out: (r.out || "") + "\n" + (pass ? T.passed : T.failed) }, pass ? "pass" : "fail");
      if (pass) render();
    };
    const runB = btn(T.run, () => runIt(false, runB));
    const chkB = btn(T.check, () => runIt(true, chkB), "btn small primary");
    if ((lab.hints || []).length) btn(`${T.hint} ${Math.min((st.hints || 0) + 1, lab.hints.length)}/${lab.hints.length}`, () => { st.hints = Math.min((st.hints || 0) + 1, lab.hints.length); LVP.store.set(st._key, st); render(); });
    if (LVP.sample()) btn(T.help, () => tutor(cur, sec, st, code.value));
    if (lab.solution) btn(T.solution, () => {
      if (st.checks >= 2 || st.passed) { code.value = lab.solution; st.code = lab.solution; LVP.store.set(st._key, st); return; }
      const c = el("div", "notice"); c.append(document.createTextNode(T.solConfirm + " "));
      const y = el("button", "btn small", T.yes), n = el("button", "btn small", T.no);
      y.onclick = () => { code.value = lab.solution; st.code = lab.solution; st.checks = 99; LVP.store.set(st._key, st); c.remove(); };
      n.onclick = () => c.remove(); c.append(y, n); box.insertBefore(c, row.nextSibling);
    });
    btn(T.reset, () => { code.value = lab.starter; st.code = lab.starter; LVP.store.set(st._key, st); });
    box.append(row);
    for (let i = 0; i < (st.hints || 0); i++) { const h = el("div", "verdict partly"); h.append(el("b", null, `${T.hint} ${i + 1}`)); const s = el("span"); LVP.renderRich(s, lab.hints[i]); h.append(s); box.append(h); }
    if (st.tutor) { const m = el("div", "msg claude"); m.append(el("span", "who", "Claude")); const s = el("span"); LVP.renderRich(s, st.tutor); m.append(s); box.append(m); }
    if (LVP.sample()) { const again = el("button", "btn small", T.another); again.onclick = () => create(cur, sec, lab.title, again); box.append(rowOf(again)); }
  }
  const rowOf = (...xs) => { const r = el("div", "row"); r.append(...xs); return r; };
  function labSection(cur) {
    const t = LVP.video.currentTime, s = LVP.sectionAt(t);
    const ch = cur.chapters.filter((c) => c.t >= s.t - 0.1 && c.t < s.end)[0];
    return { name: s.name, t: s.t, end: s.end, title: ch?.title || (/^S0/.test(s.name) ? T.opening : s.name.replace(/^S\d+/, "")) };
  }
  async function create(cur, sec, avoid, b) {
    b.disabled = true; b.textContent = T.making;
    try {
      const lab = await design(cur, sec, avoid);
      LVP.store.set(key(cur.id, sec.name), { lab, code: lab.starter, hints: 0, checks: 0 }, true);
    } catch (e) { b.disabled = false; b.textContent = T.make; $("lab").append(el("p", "err", LVP.errText(e))); return; }
    render();
  }
  async function tutor(cur, sec, st, code) {
    const sample = LVP.sample(); if (!sample) return;
    st.tutor = LVP.L.thinking; render();
    const lab = st.lab;
    const prompt = [
      `You are the lab tutor for "${lab.title}" in the course "${course.title}" (video "${cur.title}", part "${sec.title}").`,
      "Lab goal:", lab.goal, "", `Language: ${lab.lang}`, "Checks that must pass:", lab.check, "",
      "Learner's current code:", code, "", "Last output:", st.out || "(not run yet)", "",
      T.helpPrompt,
      "You may run code with the run tool (their code, or a small experiment) to see what actually happens before answering. Reply in the language of the lab, 2-5 sentences, refer to their own lines.",
    ].join("\n");
    const lim = await sample.limits().catch(() => null);
    const tools = lim?.tools ? [{
      name: "run", description: "Run code in the learner's lab sandbox and return its output (stdout + errors). Use it to test their code or a small experiment.",
      inputSchema: { type: "object", properties: { code: { type: "string" } }, required: ["code"] },
      execute: async (input) => { const r = await exec(lab.lang, String(input.code || ""), 15000); return (r.out || "").slice(0, 4000) + (r.ok ? "" : "\n(exited with an error)"); },
    }] : undefined;
    try {
      const opts = { onText: ({ text }) => { st.tutor = text; } };
      if (tools) opts.tools = tools; else opts.cache = false;
      const r = await sample(prompt, opts);
      st.tutor = r.text;
    } catch (e) { st.tutor = e.text || LVP.errText(e); }
    LVP.store.set(st._key, st); render();
  }

  LVP.panels.lab = render;
  LVP.hooks.ready.push((c) => {
    course = c; T = S[(c.language || "en").slice(0, 2)] || S.en;
    const style = document.createElement("style");
    style.textContent = "body.wide main { grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); }";
    document.head.append(style);
  });
  // follow the video: a different part means a different lab
  let lastSec = null;
  LVP.hooks.tick.push((t) => {
    const cur = LVP.cur(); if (!cur || $("panel-lab").hidden) return;
    const s = LVP.sectionAt(t)?.name;
    if (s !== lastSec) { lastSec = s; render(); }
  });
})();
