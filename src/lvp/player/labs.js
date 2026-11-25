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
      noClaude: "Labs are designed by Claude – open the player on claude.ai or in the Claude app."
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
      noClaude: "Labore entwirft Claude – öffne den Player auf claude.ai oder in der Claude-App."
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
      "Rules:",
      "- The learner writes a little code that makes the idea tangible: implement the mechanism in miniature, break it, measure it, or simulate it. 10–30 minutes of work.",
      course.python === false
        ? "- Language: javascript (plain functions, console.log; no DOM, no network)."
        : "- Language: python (preferred; standard library only – no numpy, no network, no files, no input()) or javascript (plain functions, console.log; no DOM, no network).",
      "- starter: runnable code with clear TODOs, all helpers they shouldn't have to write, small and readable.",
      "- check: code appended after the learner's code that tests it with assert statements (python) or assert(cond, message) calls (javascript; assert is provided). Every failing check prints a helpful message that says what is wrong, not the answer. The last line prints exactly ALL CHECKS PASSED.",
      "- hints: 3 graded hints – 1. direction, 2. method, 3. nearly the code.",
      "- solution: a complete starter with the TODOs filled in that passes the checks.",
      "- Everything learner-facing in the language of the narration.",
      'Reply with only JSON: {"title": "...", "goal": "what to do and why it matters, 2-4 sentences", "lang": "python" | "javascript", "starter": "...", "check": "...", "hints": ["...", "...", "..."], "solution": "..."}',
    ].filter(Boolean).join("\n");
    const lab = await sample.json(prompt, { cache: false });
    if (!lab || !lab.starter || !lab.check) throw { code: "invalid_json" };
    lab.lang = lab.lang === "javascript" ? "javascript" : "python";
    // a lab whose own solution fails its checks is not handed to the learner
    const verify = await exec(lab.lang, lab.solution + "\n\n" + lab.check, 30000);
    lab.verified = verify.ok && /ALL CHECKS PASSED/.test(verify.out);
    return lab;
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
    const st = state || { _key: key(cur.id, sec.name), lab: { ...authored, authored: true }, code: authored.starter, hints: 0, checks: 0 };
    if (!state) LVP.store.set(st._key, st);
    const lab = st.lab;
    const t = el("h2", "h", lab.title || ""); box.append(t);
    box.append(el("span", "hint", `${T.lang[lab.lang] || lab.lang}${lab.authored ? " · " + T.authored : ""}${st.passed ? " · ✓ " + T.done : ""}`));
    const goal = el("div", "lab-goal"); LVP.renderRich(goal, lab.goal || ""); box.append(goal);
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
    return { name: s.name, t: s.t, end: s.end, title: ch?.title || s.name };
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
