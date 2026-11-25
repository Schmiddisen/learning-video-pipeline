/* lvp player – core: video, transcript, questions, tutor, notes, progress.
   review.js (flashcards) and labs.js (hands-on labs) plug in through window.LVP. */
"use strict";

const STR = {
  en: {
    kicker: "Course", tabs: { ask: "Ask", map: "Video", review: "Review", lab: "Lab", course: "Today" },
    mark: "Mark", drawBadge: "Draw on the picture, then ask", send: "Ask", stop: "Stop", frame: "send the picture",
    stopAtQ: "Pause at questions", practice: "New question", note: "Note", makeCard: "Card",
    pretest: "Guess first", check: "Quick check", recall: "Recall", practiceKind: "Practice", followup: "One more try",
    explain: "Explain it back", noteKind: "Note at", cardKind: "New flashcard",
    submitGuess: "Lock in my guess", submit: "Check my answer", skip: "Skip", cont: "Continue the video",
    fromVideo: "From the video", yourAnswer: "Your answer: ", noAnswer: "(no answer)",
    guessSaved: "Your guess is saved – the video answers it.", rewatch: "Rewatch", tryFollowup: "Try a follow-up",
    right: "Right", partly: "Partly", wrong: "Not quite", grading: "Checking your answer…", generating: "Writing a question…",
    placeholder: "Ask about this moment – or anything in the course…", quizPlaceholder: "Type your answer – a sentence is enough",
    explainPrompt: "Explain the core idea of this video in your own words, as if to a friend who missed it. Claude points out what is solid and what is missing.",
    explainPlaceholder: "In my own words: …", explainSubmit: "Get feedback", solid: "Solid", missing: "Missing", wrongs: "Not right",
    nextStep: "Next", explainBtn: "Explain this video back", save: "Save", cancel: "Cancel", saved: "Saved",
    notePlaceholder: "Your note for this moment", front: "Front (question)", back: "Back (answer)", drafting: "Drafting a card…",
    addCard: "Add to my cards", cardAdded: "Added to your cards – it shows up in Review.",
    chips: ["Explain this differently", "Give me a concrete example", "Why does this matter?", "What did I just miss?"],
    socratic: "Guide me, don't tell me",
    emptyTitle: "Pause anywhere and ask.",
    emptyBody: "Claude sees the picture, what was just said, the whole video and how you are doing. Press Mark to circle something first.",
    thinking: "Thinking…", claude: "Claude", at: "at", marked: "your marking", picture: "picture", saveNote: "Save as note", toCard: "Make a card",
    resumed: "Resumed at", startOver: "Start over",
    unavailable: "Asking Claude is not available in this view – open the artifact on claude.ai or in the Claude app.",
    errors: {
      not_granted: "Claude isn't allowed for this page. You can allow it in the page's Permissions menu.",
      sampling_disabled: "Claude isn't available for this account.",
      rate_limited: "Too many questions at once or a usage limit reached – try again in a moment.",
      session_expired: "Please sign in again.", refused: "Claude declined this one – try rephrasing it.",
      image_rejected: "The picture couldn't be sent – try again without it.",
      images_unavailable: "Pictures can't be sent from this view.",
      prompt_too_large: "That was too much at once – ask about a shorter part.",
      invalid_json: "Claude's answer came back garbled – try again.",
      other: "Something went wrong on the way to Claude – try again."
    },
    watched: "watched", answered: "answered", loadError: "course.json could not be loaded.",
    notes: "Your notes", chapters: "Chapters and questions", none: "Nothing yet.",
    todayTitle: "Today", continueAt: "Continue", dueCards: "cards due for review", weak: "Moments to revisit",
    explainTodo: "Explain back what you watched", allVideos: "All videos", labTodo: "Try the lab for",
    noTodo: "All caught up. Pick the next video or ask Claude for a challenge."
  },
  de: {
    kicker: "Kurs", tabs: { ask: "Fragen", map: "Video", review: "Wiederholen", lab: "Labor", course: "Heute" },
    mark: "Markieren", drawBadge: "Ins Bild zeichnen, dann fragen", send: "Fragen", stop: "Stopp", frame: "Bild mitschicken",
    stopAtQ: "Bei Fragen anhalten", practice: "Neue Frage", note: "Notiz", makeCard: "Karte",
    pretest: "Erst raten", check: "Kurz prüfen", recall: "Zum Abrufen", practiceKind: "Übung", followup: "Noch ein Versuch",
    explain: "Erklär es zurück", noteKind: "Notiz bei", cardKind: "Neue Karteikarte",
    submitGuess: "Tipp festhalten", submit: "Antwort prüfen", skip: "Überspringen", cont: "Video fortsetzen",
    fromVideo: "Aus dem Video", yourAnswer: "Deine Antwort: ", noAnswer: "(keine Antwort)",
    guessSaved: "Dein Tipp ist gespeichert – das Video löst ihn auf.", rewatch: "Nochmal ansehen", tryFollowup: "Folgefrage versuchen",
    right: "Richtig", partly: "Teilweise", wrong: "Noch nicht", grading: "Prüfe deine Antwort …", generating: "Schreibe eine Frage …",
    placeholder: "Frag zu dieser Stelle – oder zu allem im Kurs …", quizPlaceholder: "Antwort eintippen – ein Satz genügt",
    explainPrompt: "Erklär die Kernidee dieses Videos in eigenen Worten, als würdest du sie jemandem erzählen, der es verpasst hat. Claude sagt dir, was sitzt und was fehlt.",
    explainPlaceholder: "In eigenen Worten: …", explainSubmit: "Feedback holen", solid: "Sitzt", missing: "Fehlt", wrongs: "Stimmt nicht",
    nextStep: "Als Nächstes", explainBtn: "Dieses Video zurückerklären", save: "Speichern", cancel: "Abbrechen", saved: "Gespeichert",
    notePlaceholder: "Deine Notiz zu dieser Stelle", front: "Vorderseite (Frage)", back: "Rückseite (Antwort)", drafting: "Entwerfe eine Karte …",
    addCard: "Zu meinen Karten", cardAdded: "Hinzugefügt – die Karte erscheint unter Wiederholen.",
    chips: ["Erklär das anders", "Gib mir ein konkretes Beispiel", "Wozu brauche ich das?", "Was habe ich gerade verpasst?"],
    socratic: "Führ mich hin, verrat nichts",
    emptyTitle: "Halte irgendwo an und frag.",
    emptyBody: "Claude sieht das Bild, was gerade gesagt wurde, das ganze Video und wie es bei dir läuft. Mit Markieren kannst du vorher etwas einkreisen.",
    thinking: "Denkt nach …", claude: "Claude", at: "bei", marked: "deine Markierung", picture: "Bild", saveNote: "Als Notiz", toCard: "Karte daraus",
    resumed: "Fortgesetzt bei", startOver: "Von vorn",
    unavailable: "Claude fragen geht in dieser Ansicht nicht – öffne das Artefakt auf claude.ai oder in der Claude-App.",
    errors: {
      not_granted: "Claude ist für diese Seite nicht erlaubt. Das lässt sich im Berechtigungsmenü der Seite ändern.",
      sampling_disabled: "Claude ist für dieses Konto nicht verfügbar.",
      rate_limited: "Zu viele Fragen auf einmal oder Nutzungslimit erreicht – gleich noch einmal versuchen.",
      session_expired: "Bitte neu anmelden.", refused: "Claude hat das abgelehnt – anders formulieren.",
      image_rejected: "Das Bild ließ sich nicht senden – ohne Bild noch einmal versuchen.",
      images_unavailable: "Bilder gehen in dieser Ansicht nicht.",
      prompt_too_large: "Das war zu viel auf einmal – frag nach einem kürzeren Teil.",
      invalid_json: "Claudes Antwort kam unlesbar zurück – noch einmal versuchen.",
      other: "Auf dem Weg zu Claude ist etwas schiefgegangen – noch einmal versuchen."
    },
    watched: "gesehen", answered: "beantwortet", loadError: "course.json konnte nicht geladen werden.",
    notes: "Deine Notizen", chapters: "Kapitel und Fragen", none: "Noch nichts.",
    todayTitle: "Heute", continueAt: "Weiter mit", dueCards: "Karten fällig", weak: "Stellen zum Nachholen",
    explainTodo: "Erklär zurück, was du gesehen hast", allVideos: "Alle Videos", labTodo: "Probier das Labor zu",
    noTodo: "Alles erledigt. Nimm dir das nächste Video vor oder lass dir von Claude eine Herausforderung geben."
  }
};

const $ = (id) => document.getElementById(id);
const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; };
const fmt = (s) => { s = Math.max(0, Math.floor(s)); const h = Math.floor(s / 3600), m = Math.floor(s / 60) % 60, x = String(s % 60).padStart(2, "0"); return h ? `${h}:${String(m).padStart(2, "0")}:${x}` : `${m}:${x}`; };
const safeId = (id) => String(id).replace(/[^A-Za-z0-9-]/g, "-");
const parseTs = (s) => { const m = /^(\d{1,2}):(\d{2})$/.exec(String(s || "").trim()); return m ? Number(m[1]) * 60 + Number(m[2]) : null; };

const LVP = (window.LVP = { STR, L: STR.en, $, el, fmt, safeId, parseTs, panels: {}, hooks: { open: [], tick: [], ready: [] } });
const video = $("video"), ink = $("ink"), stage = $("stage");
let course = null, cur = null, curIndex = 0;
let sample = null, sampleChecked = false, imagesOk = false;
const chats = {};
let strokes = [], drawing = false, lastT = 0, activeLine = -1, cardBusy = null, askCtl = null, socratic = false;

/* ---------- storage: the learner's account when available, else this browser ---------- */
const Store = (LVP.store = {
  db: null, uid: null, data: {}, timers: {}, chain: Promise.resolve(),
  get(key, fallback) { return this.data[key] ?? fallback; },
  set(key, value, now = false) {
    value.updated = Date.now(); value._key = key; this.data[key] = value;
    try { localStorage.setItem("lvp:" + key, JSON.stringify(value)); } catch { /* private mode */ }
    clearTimeout(this.timers[key]);
    this.timers[key] = setTimeout(() => this.push(key), now ? 0 : 3000);
  },
  push(key) {
    if (!this.db || !this.uid) return;
    const value = this.data[key];
    this.chain = this.chain.then(() => this.db.collection("data/users/" + this.uid).doc(safeId(key)).set(JSON.parse(JSON.stringify(value)))).catch(() => {});
  },
  loadLocal() {
    try {
      for (let i = 0; i < localStorage.length; i++) {
        const k = localStorage.key(i);
        if (k && k.startsWith("lvp:")) this.data[k.slice(4)] = JSON.parse(localStorage.getItem(k));
      }
    } catch { /* no storage */ }
  },
  async loadAccount(db, uid) {
    this.db = db; this.uid = uid;
    try {
      const snap = await Promise.race([db.collection("data/users/" + uid).get(), new Promise((_, r) => setTimeout(() => r(new Error("timeout")), 10000))]);
      for (const d of snap.docs) {
        const v = d.data() || {}; const key = v._key || d.id;
        const mine = this.data[key];
        if (!mine || (v.updated || 0) > (mine.updated || 0)) { this.data[key] = v; try { localStorage.setItem("lvp:" + key, JSON.stringify(v)); } catch { /* */ } }
        else if ((mine.updated || 0) > (v.updated || 0)) this.push(key);
      }
      for (const key of Object.keys(this.data)) if (!snap.docs.some((d) => (d.data()?._key || d.id) === key)) this.push(key);
      return true;
    } catch { return false; }
  },
});
const prog = (id = cur?.id) => {
  const key = "p-" + id;
  if (!Store.data[key]) Store.data[key] = { _key: key, pos: 0, furthest: 0, answers: {}, notes: [] };
  const p = Store.data[key]; p._key = key; p.answers ||= {}; p.notes ||= []; return p;
};
const saveProg = (id = cur?.id, now = false) => Store.set("p-" + id, prog(id), now);
LVP.prog = prog; LVP.saveProg = saveProg;

/* ---------- course + video ---------- */
const videoLabel = (v) => v.title.split(/\s{2,}|\.\s{2}/)[0].replace(/\.$/, "");
const quizKey = (q) => q.quiz + ":" + q.q.slice(0, 80);
const chapterAt = (t) => { let c = null; for (const x of cur.chapters) if (x.t <= t + 0.05) c = x; return c; };
const lineAt = (t) => { let i = -1; cur.lines.forEach((l, k) => { if (l.t <= t) i = k; }); return i; };
const screenAt = (t) => { let s = null; for (const x of cur.screens || []) if (x.t <= t + 0.05) s = x; return s ? s.texts : null; };
const sectionAt = (t) => cur.sections.find((s) => s.t <= t && t < s.end) || cur.sections[cur.sections.length - 1];
Object.assign(LVP, { videoLabel, chapterAt, sectionAt, lineAt });
LVP.cur = () => cur; LVP.course = () => course; LVP.video = video;

function transcriptText(from, to, limit, v = cur) {
  let s = "";
  for (const l of v.lines) if (l.t >= from && l.t <= to) s += `[${fmt(l.t)}] ${l.text}\n`;
  return s.length > limit ? s.slice(0, limit) + "\n[…]" : s;
}
LVP.transcriptText = transcriptText;

function buildPicker() {
  const sel = $("video-select"); sel.textContent = "";
  for (const v of course.videos) { const o = el("option", null, videoLabel(v)); o.value = v.id; sel.append(o); }
  sel.onchange = () => openVideo(sel.value);
  $("prev").onclick = () => curIndex > 0 && openVideo(course.videos[curIndex - 1].id);
  $("next").onclick = () => curIndex < course.videos.length - 1 && openVideo(course.videos[curIndex + 1].id);
}

function openVideo(id, at = null) {
  const i = course.videos.findIndex((v) => v.id === id);
  if (i < 0) return;
  if (cur && cur.id !== id) { prog().pos = video.currentTime; saveProg(cur.id, true); }
  const same = cur && cur.id === id;
  curIndex = i; cur = course.videos[i];
  $("video-select").value = id;
  try { history.replaceState(null, "", "#" + safeId(id)); } catch { /* */ }
  Store.set("last", { _key: "last", video: id });
  if (same) { if (at != null) seekTo(at); return; }
  closeCard(); clearInk();
  video.src = cur.file;
  const p = prog();
  video.addEventListener("loadedmetadata", function once() {
    video.removeEventListener("loadedmetadata", once);
    if (at != null) seekTo(at);
    else if (p.pos > 5 && p.pos < cur.duration - 10) { video.currentTime = p.pos; showResume(p.pos); }
    lastT = video.currentTime; $("seek").max = String(cur.duration); tick();
  });
  video.playbackRate = Number($("speed").value);
  buildMarks(); buildTranscript(); renderChat(); updateWhere(0);
  $("prev").disabled = i === 0; $("next").disabled = i === course.videos.length - 1;
  for (const f of LVP.hooks.open) f(cur);
  refreshPanels();
}
LVP.openVideo = openVideo;
function seekTo(t) { video.currentTime = Math.max(0, Math.min(t, (cur?.duration || 1e9) - 0.1)); lastT = video.currentTime - 0.01; tick(); }
LVP.seek = (videoId, t) => { if (!cur || videoId !== cur.id) openVideo(videoId, t); else seekTo(t); stage.scrollIntoView({ block: "nearest", behavior: "smooth" }); };
function showResume(pos) {
  const n = el("div", "notice");
  n.append(document.createTextNode(`${LVP.L.resumed} ${fmt(pos)} · `));
  const b = el("button", "ts", LVP.L.startOver); b.onclick = () => { seekTo(0); n.remove(); };
  n.append(b); $("chat").prepend(n);
}

/* ---------- transport ---------- */
function setPlayIcon() { $("play").innerHTML = video.paused ? "&#9654;" : "&#10074;&#10074;"; $("bigplay").hidden = !video.paused || !!cardBusy; }
function togglePlay() { if (cardBusy?.blocking) return; video.paused ? video.play().catch(() => {}) : video.pause(); }
$("play").onclick = togglePlay; $("bigplay").onclick = togglePlay; video.addEventListener("click", togglePlay);
video.addEventListener("play", () => { if (strokes.length) clearInk(); setDrawMode(false); if (cardBusy && !cardBusy.blocking) closeCard(); setPlayIcon(); loop(); });
video.addEventListener("pause", () => { setPlayIcon(); if (cur) { prog().pos = video.currentTime; saveProg(cur.id, true); } updateCtxLine(); });
video.addEventListener("ended", () => { setPlayIcon(); if (!cur) return; prog().furthest = cur.duration; saveProg(cur.id, true); refreshPanels(); if (!prog().explain) openExplain(); });
$("back").onclick = () => seekTo(video.currentTime - 10);
$("speed").onchange = (e) => { video.playbackRate = Number(e.target.value); };
const seekBar = $("seek");
seekBar.addEventListener("input", () => { video.currentTime = Number(seekBar.value); lastT = video.currentTime; tick(); });
$("full").onclick = () => { (document.fullscreenElement ? document.exitFullscreen() : stage.requestFullscreen()).catch(() => {}); };
document.addEventListener("keydown", (e) => {
  if (e.target.matches("textarea, input, select")) return;
  if (e.key === " " || e.key === "k") { e.preventDefault(); togglePlay(); }
  else if (e.key === "ArrowLeft") seekTo(video.currentTime - 5);
  else if (e.key === "ArrowRight") seekTo(video.currentTime + 5);
  else if (e.key === "d") $("draw").click();
  else if (e.key === "a") { e.preventDefault(); selectTab("ask"); $("ask-input").focus(); }
});
let looping = false;
function loop() { if (looping) return; looping = true; const step = () => { tick(); if (!video.paused) requestAnimationFrame(step); else looping = false; }; step(); }
function tick() {
  if (!cur) return;
  const t = video.currentTime;
  if (document.activeElement !== seekBar) seekBar.value = String(t);
  $("time").textContent = `${fmt(t)} / ${fmt(cur.duration)}`;
  const p = prog();
  if (t > (p.furthest || 0) + 1) { p.furthest = t; p.pos = t; saveProg(); }
  if (!video.paused && $("stop-at-q").checked && !cardBusy && t > lastT && t - lastT < 1.5) {
    const q = cur.quizzes.find((x) => lastT < x.t + 0.4 && x.t + 0.4 <= t);
    if (q) { video.pause(); openQuiz(q); }
  }
  lastT = t;
  highlight(t); updateWhere(t);
  for (const f of LVP.hooks.tick) f(t);
}

function buildMarks() {
  const m = $("marks"); m.textContent = "";
  const add = (t, cls, title) => { const x = el("i", "mk " + cls); x.style.left = (100 * t / cur.duration) + "%"; if (title) x.title = title; m.append(x); };
  for (const c of cur.chapters) add(c.t, "", c.title);
  for (const q of cur.quizzes) add(q.t, "q");
  for (const n of prog().notes) add(n.t, "n");
}

/* ---------- transcript ---------- */
function buildTranscript() {
  const box = $("transcript"); box.textContent = "";
  const items = [
    ...cur.chapters.map((c) => ({ t: c.t, kind: "chapter", c })),
    ...cur.lines.map((l, i) => ({ t: l.t, kind: "line", l, i })),
    ...cur.quizzes.map((q) => ({ t: q.t, kind: "quiz", q })),
  ].sort((a, b) => a.t - b.t || (a.kind === "chapter" ? -1 : 1));
  for (const it of items) {
    if (it.kind === "chapter") { box.append(el("h3", null, it.c.title)); continue; }
    if (it.kind === "quiz") { const r = el("div", "qline"); r.append(el("span", "mono", fmt(it.t)), el("span", null, `${LVP.L[it.q.quiz]}: ${it.q.q.replace(/\n/g, " ")}`)); box.append(r); continue; }
    const b = el("button", "line"); b.dataset.i = it.i;
    b.append(el("span", "mono", fmt(it.l.t)), el("span", "txt", it.l.text));
    b.onclick = () => seekTo(it.l.t);
    box.append(b);
  }
  activeLine = -1;
}
function highlight(t) {
  const i = lineAt(t), box = $("transcript");
  if (i !== activeLine) {
    box.querySelector(".line.now")?.classList.remove("now");
    const prev = box.querySelector(`.line[data-i="${activeLine}"] .txt`);
    if (prev && activeLine >= 0) prev.textContent = cur.lines[activeLine].text;
    activeLine = i;
    const b = box.querySelector(`.line[data-i="${i}"]`);
    if (b) {
      b.classList.add("now");
      const l = cur.lines[i], words = l.words || [], shown = l.text.split(/\s+/).filter(Boolean);
      if (words.length && words.length === shown.length) {
        const span = b.querySelector(".txt"); span.textContent = "";
        shown.forEach((w, k) => { const s = el("span", "w", w); s.dataset.t = words[k][0]; span.append(s, document.createTextNode(" ")); });
      }
      if (!box.matches(":hover")) box.scrollTo({ top: b.offsetTop - box.offsetTop - box.clientHeight / 3, behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
    }
  }
  if (i >= 0) box.querySelectorAll(`.line[data-i="${i}"] .w`).forEach((s) => s.classList.toggle("said", Number(s.dataset.t) <= t + 0.05));
}
function updateWhere(t) {
  const w = $("where"); w.textContent = "";
  const c = chapterAt(t);
  w.append(el("strong", null, videoLabel(cur)));
  if (c) w.append(el("span", null, c.title));
  const done = cur.quizzes.filter((q) => prog().answers[quizKey(q)]).length;
  if (cur.quizzes.length) w.append(el("span", null, `${done}/${cur.quizzes.length} ${LVP.L.answered}`));
}

/* ---------- drawing on the picture ---------- */
function sizeInk() { const r = stage.getBoundingClientRect(), dpr = window.devicePixelRatio || 1; ink.width = Math.round(r.width * dpr); ink.height = Math.round(r.height * dpr); redraw(); }
new ResizeObserver(sizeInk).observe(stage);
function redraw() {
  const g = ink.getContext("2d"); g.clearRect(0, 0, ink.width, ink.height);
  g.lineCap = "round"; g.lineJoin = "round"; g.strokeStyle = getComputedStyle(document.documentElement).getPropertyValue("--pen").trim() || "#e0185f"; g.lineWidth = Math.max(3, ink.width / 220);
  for (const s of strokes) { g.beginPath(); s.forEach(([x, y], k) => (k ? g.lineTo(x * ink.width, y * ink.height) : g.moveTo(x * ink.width, y * ink.height))); g.stroke(); }
}
function setDrawMode(on) { stage.classList.toggle("drawing", on); $("draw").setAttribute("aria-pressed", String(on)); $("draw-badge").hidden = !on; if (on && !video.paused) video.pause(); }
function clearInk() { strokes = []; redraw(); $("clear-ink").hidden = true; updateCtxLine(); }
$("draw").onclick = () => setDrawMode(!stage.classList.contains("drawing"));
$("clear-ink").onclick = clearInk;
const pt = (e) => { const r = ink.getBoundingClientRect(); return [(e.clientX - r.left) / r.width, (e.clientY - r.top) / r.height]; };
ink.addEventListener("pointerdown", (e) => { drawing = true; ink.setPointerCapture(e.pointerId); strokes.push([pt(e)]); $("draw-badge").hidden = true; });
ink.addEventListener("pointermove", (e) => { if (drawing) { strokes[strokes.length - 1].push(pt(e)); redraw(); } });
ink.addEventListener("pointerup", () => { drawing = false; $("clear-ink").hidden = !strokes.length; updateCtxLine(); });
function frameBlob() {
  return new Promise((resolve) => {
    try {
      const w = video.videoWidth || 854, h = video.videoHeight || 480, c = document.createElement("canvas");
      c.width = w; c.height = h; const g = c.getContext("2d"); g.drawImage(video, 0, 0, w, h);
      if (strokes.length) g.drawImage(ink, 0, 0, w, h);
      c.toBlob((b) => resolve(b), "image/jpeg", 0.88);
    } catch { resolve(null); }
  });
}

/* ---------- Claude ---------- */
const errText = (e) => LVP.L.errors[e?.code] || LVP.L.errors.other;
LVP.errText = errText;
LVP.sample = () => sample;
function learnerContext() {
  const lines = [];
  if (course.learner) lines.push("About the learner (their own profile):\n" + course.learner.slice(0, 1500));
  const misses = [];
  for (const v of course.videos) {
    const p = Store.get("p-" + v.id); if (!p) continue;
    for (const [k, a] of Object.entries(p.answers || {})) if (a.verdict && a.verdict !== "right") misses.push(`${videoLabel(v)}: "${k.split(":").slice(1).join(":")}" (${a.verdict})`);
  }
  if (misses.length) lines.push("Questions they recently got wrong or partly wrong:\n- " + misses.slice(-8).join("\n- "));
  const lapses = LVP.review?.struggles?.() || [];
  if (lapses.length) lines.push("Flashcards they keep forgetting:\n- " + lapses.slice(0, 6).join("\n- "));
  const notes = prog().notes.slice(-6).map((n) => `[${fmt(n.t)}] ${n.text}`);
  if (notes.length) lines.push("Their notes on this video:\n" + notes.join("\n"));
  return lines.join("\n\n");
}
function rules() {
  return [
    `You are the tutor built into a video player for the course "${course.title}". The learner is watching "${cur.title}". You get the video's full narration with timestamps, the exact moment they paused, the text on screen and usually the current frame as an image (their red marks on it show what they mean).`,
    "How to answer:",
    "- Answer exactly what they asked, concisely. Build on what the video showed; use its notation and examples; don't retell the video.",
    "- For a different explanation, use a genuinely different angle (an analogy from what they know, small concrete numbers, a picture in words).",
    "- Never be condescending; assume a sharp learner who missed one step. Use what you know about their difficulties, without lecturing them about it.",
    "- Refer to moments in this video as [m:ss] (they become clickable). If another video of the course covers it, name that video.",
    "- Reply in the language the learner writes in. Plain text, short paragraphs, formulas in Unicode; no Markdown headings or tables.",
    "- If the video contains a mistake, say so plainly and give the correct version.",
    socratic ? "- SOCRATIC MODE: do not give the answer. Ask one short guiding question that gets them one step closer, building on what they said. Only confirm when they have it." : "",
    "", "Videos in this course:", course.videos.map((v) => "- " + videoLabel(v)).join("\n"),
    "", learnerContext(), "", `Full narration of "${videoLabel(cur)}":`, transcriptText(0, cur.duration, 60000),
  ].filter((x) => x !== "").join("\n");
}
function moment(t) {
  const c = chapterAt(t), i = lineAt(t), screen = screenAt(t);
  const recent = cur.lines.slice(Math.max(0, i - 2), i + 1).map((l) => `[${fmt(l.t)}] ${l.text}`).join("\n");
  const q = cur.quizzes.find((x) => x.t - 0.5 <= t && t <= (x.answer_t || x.t + x.think) + 4);
  return [
    `Paused at ${fmt(t)}${c ? ` in chapter "${c.title}"` : ""}.`,
    recent ? "Just said:\n" + recent : "Nothing said yet at this point.",
    screen ? "Text on screen: " + screen.join(" | ") : "",
    q ? `On screen is a question: "${q.q}"${q.a ? ` (answer shown in the video: "${q.a}")` : ""}.` : "",
  ].filter(Boolean).join("\n");
}
function renderRich(node, text, videoId = cur?.id) {
  node.textContent = "";
  const re = /\[(\d{1,2}):(\d{2})\]/g; let last = 0, m;
  while ((m = re.exec(text))) {
    node.append(document.createTextNode(text.slice(last, m.index)));
    const s = Number(m[1]) * 60 + Number(m[2]);
    const b = el("button", "ts", `${m[1]}:${m[2]}`); b.onclick = () => LVP.seek(videoId, s);
    node.append(b); last = re.lastIndex;
  }
  node.append(document.createTextNode(text.slice(last)));
}
LVP.renderRich = renderRich;
function updateCtxLine() {
  const c = $("ctxline"); c.textContent = "";
  if (!cur) return;
  const t = video.currentTime, ch = chapterAt(t);
  c.append(el("span", null, `${LVP.L.at} ${fmt(t)}` + (ch ? ` · ${ch.title}` : "")));
  if ($("with-frame").checked && imagesOk) c.append(el("span", strokes.length ? "pen" : null, "+ " + LVP.L.picture + (strokes.length ? " + " + LVP.L.marked : "")));
}
$("with-frame").onchange = updateCtxLine;
function renderChat() {
  const box = $("chat"); box.textContent = "";
  const turns = chats[cur?.id] || [];
  if (!turns.length) { const e = el("div", "empty"); e.append(el("b", null, LVP.L.emptyTitle), el("span", null, sampleChecked && !sample ? LVP.L.unavailable : LVP.L.emptyBody)); box.append(e); }
  for (const m of turns) box.append(m.node);
  box.scrollTop = box.scrollHeight;
}
async function ask(question) {
  question = question.trim(); if (!question || !cur) return;
  if (!sample) { renderChat(); return; }
  selectTab("ask");
  if (!video.paused) video.pause();
  const t = video.currentTime, turns = (chats[cur.id] ||= []);
  const withFrame = $("with-frame").checked && imagesOk;
  const blob = withFrame ? await frameBlob() : null;
  const you = el("div", "msg you"); you.append(el("span", "ctx", fmt(t) + (strokes.length && withFrame ? " · " + LVP.L.marked : "")), document.createTextNode(question));
  if (blob) { const img = el("img"); img.alt = ""; img.src = URL.createObjectURL(blob); you.append(img); }
  const content = moment(t) + (blob ? (strokes.length ? "\nThe attached image is this frame with the learner's red marks." : "\nThe attached image is this frame.") : "") + "\n\nQuestion: " + question;
  turns.push({ role: "user", content, node: you });
  const ans = el("div", "msg claude"); ans.append(el("span", "who", LVP.L.claude)); const body = el("span", null, LVP.L.thinking); ans.append(body);
  const entry = { role: "assistant", content: "", node: ans }; turns.push(entry); renderChat();
  $("ask-input").value = ""; $("ask-send").disabled = true; $("ask-stop").hidden = false;
  askCtl = new AbortController();
  const history = turns.slice(0, -1).filter((x) => x.content).slice(-9).map((x) => ({ role: x.role, content: x.content }));
  try {
    const r = await sample([{ role: "user", content: rules() }, ...history], { cache: false, signal: askCtl.signal, images: blob ? [blob] : undefined, onText: ({ text }) => { renderRich(body, text); $("chat").scrollTop = $("chat").scrollHeight; } });
    entry.content = r.text; renderRich(body, r.text);
    const acts = el("div", "acts");
    const n = el("button", "btn small", LVP.L.saveNote); n.onclick = () => { addNote(t, r.text.slice(0, 600)); n.disabled = true; n.textContent = LVP.L.saved; };
    const c = el("button", "btn small", LVP.L.toCard); c.onclick = () => openCardDraft(t, question + "\n\n" + r.text);
    acts.append(n, c); ans.append(acts);
    if (blob) clearInk();
  } catch (e) {
    entry.content = e.text || "";
    if (e.code !== "cancelled") { if (e.text) renderRich(body, e.text); else body.textContent = ""; ans.append(el("div", "err", errText(e))); }
    if (e.code === "not_granted" || e.code === "sampling_disabled") sample = null;
    if (e.code === "images_unavailable") { imagesOk = false; updateCtxLine(); }
  } finally { $("ask-send").disabled = false; $("ask-stop").hidden = true; askCtl = null; }
}
LVP.ask = ask;
$("ask-send").onclick = () => ask($("ask-input").value);
$("ask-stop").onclick = () => askCtl?.abort();
$("ask-input").addEventListener("keydown", (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); ask($("ask-input").value); } });
function buildChips() {
  const c = $("chips"); c.textContent = "";
  for (const s of LVP.L.chips) { const b = el("button", "chip", s); b.onclick = () => ask(s); c.append(b); }
  const so = el("button", "chip", LVP.L.socratic); so.setAttribute("aria-pressed", String(socratic));
  so.onclick = () => { socratic = !socratic; so.setAttribute("aria-pressed", String(socratic)); };
  c.append(so);
}

/* ---------- the card under the picture ---------- */
const card = $("card");
function closeCard() { cardBusy = null; card.hidden = true; card.textContent = ""; setPlayIcon(); }
function openCardShell(kind, blocking) {
  cardBusy = { kind, blocking }; card.hidden = false; card.textContent = ""; setPlayIcon();
  card.append(el("p", "kicker", kind));
  setTimeout(() => card.scrollIntoView({ block: "nearest", behavior: "smooth" }), 30);
  return card;
}
function verdictBox(res) {
  const v = ["right", "partly", "wrong"].includes(res.verdict) ? res.verdict : "partly";
  const box = el("div", "verdict " + v); box.append(el("b", null, LVP.L[v]));
  const fb = el("span"); renderRich(fb, String(res.feedback || "")); box.append(fb);
  return box;
}
async function grade(q, answer) {
  const sec = sectionAt(q.t);
  const prompt = [
    `You grade a learner's answer to a question in the video "${cur.title}" of the course "${course.title}".`,
    `Question: ${q.q}`,
    q.a ? `Reference answer: ${q.a}` : "There is no reference answer; judge from the narration.",
    `Learner's answer: ${answer || "(empty)"}`,
    "", "Narration of the video (with timestamps):", transcriptText(Math.max(0, sec.t - 240), sec.end + 30, 14000),
    "", "Reply with only a JSON object:",
    '{"verdict": "right" | "partly" | "wrong", "feedback": "1-3 sentences in the language of the question: what exactly is right, what is missing or wrong. Address the learner as you.", "rewatch": "m:ss of the moment in the narration that explains what they missed, or null", "followup": {"q": "a different, short question on the same idea that they can answer now", "a": "its answer"} or null}',
    "Be fair: accept answers that are correct in substance even if worded differently. Give a followup only when the verdict is not right.",
  ].join("\n");
  return sample.json(prompt, { cache: false });
}
function openQuiz(q, opts = {}) {
  const L = LVP.L;
  const kind = { pretest: L.pretest, check: L.check, recall: L.recall, practice: L.practiceKind, followup: L.followup }[q.quiz] || q.quiz;
  openCardShell(kind, !opts.free);
  card.append(el("p", "q", q.q));
  const ta = el("textarea"); ta.placeholder = L.quizPlaceholder; ta.setAttribute("aria-label", L.quizPlaceholder);
  const prev = q.quiz !== "practice" && q.quiz !== "followup" ? prog().answers[quizKey(q)] : null;
  ta.value = prev?.text || "";
  const row = el("div", "row");
  const ok = el("button", "btn primary", q.quiz === "pretest" ? L.submitGuess : L.submit);
  const skip = el("button", "btn", L.skip);
  row.append(ok, skip); card.append(ta, row);
  setTimeout(() => ta.focus({ preventScroll: true }), 60);
  const finish = () => { closeCard(); if (q.answer_t && !opts.free) video.currentTime = q.answer_t; lastT = video.currentTime; if (!opts.free) video.play().catch(() => {}); };
  skip.onclick = finish;
  ok.onclick = async () => {
    const text = ta.value.trim();
    ta.disabled = true; row.remove();
    const record = q.quiz === "practice" || q.quiz === "followup" ? null : (prog().answers[quizKey(q)] = { text, at: Date.now() });
    if (record) { saveProg(cur.id, true); updateWhere(video.currentTime); }
    const out = el("div"); out.style.display = "grid"; out.style.gap = "10px"; card.append(out);
    const cont = el("button", "btn primary", opts.free ? "OK" : L.cont); cont.onclick = finish;
    if (q.quiz === "pretest") { out.append(el("p", "mine", L.guessSaved)); out.append(rowOf(cont)); return; }
    if (q.a) { const ref = el("div", "ref"); ref.append(el("b", null, L.fromVideo), el("span", null, q.a)); out.append(ref); }
    if (!sample || !text) { out.append(rowOf(cont)); return; }
    const wait = el("p", "hint", L.grading); out.append(wait);
    try {
      const res = await grade(q, text);
      wait.remove(); out.append(verdictBox(res));
      if (record) { record.verdict = res.verdict; record.feedback = res.feedback; record.rewatch = parseTs(res.rewatch); saveProg(cur.id, true); }
      const r = el("div", "row");
      const rt = parseTs(res.rewatch);
      if (rt != null && res.verdict !== "right") { const b = el("button", "btn", `${L.rewatch} ${fmt(rt)}`); b.onclick = () => { closeCard(); seekTo(rt); video.play().catch(() => {}); }; r.append(b); }
      if (res.followup?.q && res.verdict !== "right" && q.quiz !== "followup") {
        const f = el("button", "btn", L.tryFollowup);
        f.onclick = () => openQuiz({ quiz: "followup", q: String(res.followup.q), a: String(res.followup.a || ""), t: q.t, answer_t: q.answer_t }, opts);
        r.append(f);
      }
      r.append(cont); out.append(r);
      LVP.refreshPanels?.();
    } catch (e) { wait.textContent = errText(e); out.append(rowOf(cont)); }
  };
}
const rowOf = (...xs) => { const r = el("div", "row"); r.append(...xs); return r; };
LVP.openQuiz = openQuiz;

async function practice() {
  if (!sample) { selectTab("ask"); renderChat(); return; }
  if (!video.paused) video.pause();
  const t = video.currentTime, sec = sectionAt(t);
  openCardShell(LVP.L.practiceKind, false); const wait = el("p", "hint", LVP.L.generating); card.append(wait);
  const own = cur.quizzes.map((q) => "- " + q.q.replace(/\n/g, " ")).join("\n");
  const prompt = [
    `Write ONE practice question for a learner of "${course.title}" who just watched this part of "${cur.title}".`,
    "Narration of the part:", transcriptText(sec.t, Math.min(t + 5, sec.end), 9000),
    "", "Questions the video already asks (do not repeat them):", own,
    "", learnerContext(),
    "", "The question must make them apply the idea to a concrete new case, a small computation or a 'what breaks if' – never a definition recall. Answerable in one or two sentences from what was taught. Same language as the narration.",
    'Reply with only JSON: {"q": "...", "a": "the correct answer, 1-2 sentences"}',
  ].join("\n");
  try {
    const r = await sample.json(prompt, { cache: false });
    closeCard(); openQuiz({ quiz: "practice", q: String(r.q), a: String(r.a || ""), t }, { free: true });
  } catch (e) { wait.textContent = errText(e); card.append(rowOf(Object.assign(el("button", "btn", "OK"), { onclick: closeCard }))); }
}
$("practice-btn").onclick = practice;

function openExplain() {
  const L = LVP.L;
  openCardShell(L.explain, false);
  card.append(el("p", "q", L.explainPrompt));
  const ta = el("textarea"); ta.placeholder = L.explainPlaceholder; ta.style.minHeight = "120px";
  const prev = prog().explain; if (prev) ta.value = prev.text;
  const go = el("button", "btn primary", L.explainSubmit), no = el("button", "btn", L.cancel);
  no.onclick = closeCard;
  const row = rowOf(go, no); card.append(ta, row);
  if (prev?.result) card.append(renderExplain(prev.result));
  go.onclick = async () => {
    const text = ta.value.trim(); if (!text || !sample) return;
    go.disabled = true; const wait = el("p", "hint", L.grading); card.append(wait);
    const prompt = [
      `A learner explains the video "${cur.title}" (course "${course.title}") back in their own words – the Feynman technique. Judge it against the narration.`,
      "Narration:", transcriptText(0, cur.duration, 30000), "", "Learner's explanation:", text, "",
      "Reply with only JSON, all text in the language of the narration, addressing the learner as you:",
      '{"score": 0-100, "solid": ["what they explained correctly, short"], "missing": [{"point": "an important idea they left out", "t": "m:ss where the video explains it"}], "wrong": ["any misconception, with the correction"], "next": "one sentence: the single most useful thing to do now"}',
      "At most 4 items per list. Missing means important for understanding, not every detail.",
    ].join("\n");
    try {
      const res = await sample.json(prompt, { cache: false });
      wait.remove(); card.querySelector(".explain-result")?.remove(); card.append(renderExplain(res));
      prog().explain = { text, result: res, at: Date.now() }; saveProg(cur.id, true); LVP.refreshPanels?.();
    } catch (e) { wait.textContent = errText(e); }
    go.disabled = false;
  };
}
function renderExplain(res) {
  const L = LVP.L, box = el("div", "explain-result"); box.style.display = "grid"; box.style.gap = "8px";
  const score = Math.max(0, Math.min(100, Number(res.score) || 0));
  const bar = el("span", "bar"); const fill = el("i"); fill.style.width = score + "%"; bar.append(fill); box.append(bar);
  const list = (title, items, cls, f) => { if (!items?.length) return; const v = el("div", "verdict " + cls); v.append(el("b", null, title)); const ul = el("ul", "list-plain"); for (const it of items) { const li = el("li"); f(li, it); ul.append(li); } v.append(ul); box.append(v); };
  list(L.solid, res.solid, "right", (li, it) => { li.textContent = String(it); });
  list(L.missing, res.missing, "partly", (li, it) => { li.append(document.createTextNode(String(it.point || it) + " ")); const t = parseTs(it.t); if (t != null) { const b = el("button", "ts", fmt(t)); b.onclick = () => seekTo(t); li.append(b); } });
  list(L.wrongs, res.wrong, "wrong", (li, it) => { li.textContent = String(it); });
  if (res.next) { const p = el("p", "mine"); p.textContent = `${L.nextStep}: ${res.next}`; box.append(p); }
  return box;
}
LVP.openExplain = openExplain;

/* ---------- notes ---------- */
function addNote(t, text) { prog().notes.push({ t, text, at: Date.now() }); prog().notes.sort((a, b) => a.t - b.t); saveProg(cur.id, true); buildMarks(); LVP.refreshPanels?.(); }
$("note-btn").onclick = () => {
  if (!video.paused) video.pause();
  const t = video.currentTime;
  openCardShell(`${LVP.L.noteKind} ${fmt(t)}`, false);
  const ta = el("textarea"); ta.placeholder = LVP.L.notePlaceholder;
  const s = el("button", "btn primary", LVP.L.save), c = el("button", "btn", LVP.L.cancel);
  s.onclick = () => { if (ta.value.trim()) addNote(t, ta.value.trim()); closeCard(); };
  c.onclick = closeCard; card.append(ta, rowOf(s, c)); setTimeout(() => ta.focus(), 50);
};

/* ---------- flashcard from a moment or an answer ---------- */
async function openCardDraft(t, source) {
  const L = LVP.L;
  if (!video.paused) video.pause();
  openCardShell(L.cardKind, false);
  const f = el("textarea", "field"), b = el("textarea", "field");
  f.placeholder = L.front; b.placeholder = L.back; f.style.minHeight = "54px";
  const add = el("button", "btn primary", L.addCard), no = el("button", "btn", L.cancel);
  no.onclick = closeCard;
  card.append(el("label", "hint", L.front), f, el("label", "hint", L.back), b, rowOf(add, no));
  add.onclick = () => {
    if (!f.value.trim() || !b.value.trim()) return;
    LVP.review?.addCard({ front: f.value.trim(), back: b.value.trim(), video: cur.id, t });
    card.append(el("p", "hint", L.cardAdded)); add.disabled = true; setTimeout(closeCard, 1600);
  };
  if (!sample) return;
  f.value = L.drafting;
  const i = lineAt(t);
  const ctx = source || cur.lines.slice(Math.max(0, i - 3), i + 1).map((l) => l.text).join("\n");
  try {
    const r = await sample.json([
      "Draft ONE flashcard (spaced repetition) from this material, in its language. Prefer a 'why / what happens if' question over a definition; one idea only; answer in at most two short sentences.",
      `Course: ${course.title}; video: ${cur.title}.`, "Material:", ctx.slice(0, 6000),
      'Reply with only JSON: {"front": "...", "back": "..."}',
    ].join("\n"), { modelTier: "quick", cache: false });
    f.value = String(r.front || ""); b.value = String(r.back || "");
  } catch { f.value = ""; }
}
$("card-btn").onclick = () => openCardDraft(video.currentTime, null);
LVP.openCardDraft = openCardDraft;

/* ---------- side panels ---------- */
function selectTab(name) {
  for (const b of $("tabs").querySelectorAll("button")) { const on = b.dataset.panel === name; b.setAttribute("aria-selected", String(on)); $("panel-" + b.dataset.panel).hidden = !on; }
  LVP.panels[name]?.();
}
LVP.selectTab = selectTab;
for (const b of $("tabs").querySelectorAll("button")) b.onclick = () => selectTab(b.dataset.panel);
function refreshPanels() {
  const open = [...$("tabs").querySelectorAll("button")].find((b) => b.getAttribute("aria-selected") === "true")?.dataset.panel;
  if (open && open !== "ask") LVP.panels[open]?.();
  LVP.updateDue?.();
}
LVP.refreshPanels = refreshPanels;

LVP.panels.map = () => {
  const box = $("map"), L = LVP.L; box.textContent = "";
  const eb = el("button", "btn", L.explainBtn); eb.onclick = openExplain; box.append(rowOf(eb));
  if (prog().explain?.result) box.append(renderExplain(prog().explain.result));
  box.append(el("p", "section-title", L.chapters));
  const items = [...cur.chapters.map((c) => ({ t: c.t, c })), ...cur.quizzes.map((q) => ({ t: q.t, q }))].sort((a, b) => a.t - b.t);
  for (const it of items) {
    const b = el("button", "item"); b.append(el("span", "mono", fmt(it.t)));
    const body = el("span");
    if (it.c) body.append(el("strong", null, it.c.title));
    else {
      body.append(el("span", null, `${L[it.q.quiz]}: ${it.q.q.replace(/\n/g, " ")}`));
      const a = prog().answers[quizKey(it.q)];
      if (a) body.append(el("span", "sub " + (a.verdict === "right" ? "ok" : a.verdict === "wrong" ? "no" : ""), L.yourAnswer + (a.text || L.noAnswer) + (a.feedback ? "\n" + a.feedback : "")));
    }
    b.append(body); b.onclick = () => { seekTo(Math.max(0, it.t - (it.q ? 0.5 : 0))); };
    box.append(b);
  }
  box.append(el("p", "section-title", L.notes));
  if (!prog().notes.length) box.append(el("p", "hint", L.none));
  for (const n of prog().notes) {
    const b = el("button", "item"); b.append(el("span", "mono", fmt(n.t)), el("span", null, n.text)); b.onclick = () => seekTo(n.t); box.append(b);
  }
};

LVP.panels.course = () => {
  const box = $("course"), L = LVP.L; box.textContent = "";
  box.append(el("h2", "h", L.todayTitle));
  const todo = el("div", "today"); let n = 0;
  const add = (text, f) => { const b = el("button", "todo"); b.append(el("span", "n", String(++n)), el("span", null, text)); b.onclick = f; todo.append(b); };
  const due = LVP.review?.dueCount?.() || 0;
  if (due) add(`${due} ${L.dueCards}`, () => selectTab("review"));
  const lastId = Store.get("last")?.video;
  const next = course.videos.find((v) => (Store.get("p-" + v.id)?.furthest || 0) < v.duration * 0.9);
  const resume = lastId && (Store.get("p-" + lastId)?.furthest || 0) < (course.videos.find((v) => v.id === lastId)?.duration || 0) * 0.9 ? lastId : next?.id;
  if (resume) { const v = course.videos.find((x) => x.id === resume); add(`${L.continueAt}: ${videoLabel(v)}`, () => { openVideo(v.id); selectTab("ask"); }); }
  for (const v of course.videos) {
    const p = Store.get("p-" + v.id);
    if (p && p.furthest >= v.duration * 0.9 && !p.explain) { add(`${L.explainTodo}: ${videoLabel(v)}`, () => { openVideo(v.id); setTimeout(openExplain, 300); }); break; }
  }
  const weak = [];
  for (const v of course.videos) for (const [k, a] of Object.entries(Store.get("p-" + v.id)?.answers || {})) if (a.verdict && a.verdict !== "right" && a.rewatch != null) weak.push({ v, k, a });
  if (n === 0 && !weak.length) todo.append(el("p", "hint", L.noTodo));
  box.append(todo);
  if (weak.length) {
    box.append(el("p", "section-title", L.weak));
    for (const w of weak.slice(-6).reverse()) {
      const b = el("button", "item"); b.append(el("span", "mono", fmt(w.a.rewatch)));
      const body = el("span"); body.append(el("strong", null, videoLabel(w.v)), el("span", "sub", w.k.split(":").slice(1).join(":")));
      b.append(body); b.onclick = () => LVP.seek(w.v.id, w.a.rewatch); box.append(b);
    }
  }
  box.append(el("p", "section-title", L.allVideos));
  let total = 0, seen = 0;
  for (const v of course.videos) {
    const p = Store.get("p-" + v.id) || {}; const frac = Math.min(1, (p.furthest || 0) / v.duration);
    total += v.duration; seen += frac * v.duration;
    const b = el("button", "item vid" + (v.id === cur?.id ? " now" : ""));
    const left = el("span"); left.append(el("strong", null, videoLabel(v)));
    const done = v.quizzes.filter((q) => p.answers?.[quizKey(q)]).length;
    left.append(el("span", "sub", `${fmt(v.duration)} · ${Math.round(frac * 100)} % ${L.watched}` + (v.quizzes.length ? ` · ${done}/${v.quizzes.length} ${L.answered}` : "")));
    const bar = el("span", "bar"); const fill = el("i"); fill.style.width = frac * 100 + "%"; bar.append(fill);
    b.append(left, bar); b.onclick = () => openVideo(v.id); box.append(b);
  }
  box.append(el("p", "hint", `${Math.round(100 * seen / (total || 1))} % ${L.watched}`));
};

/* ---------- dictation ---------- */
function setupDictation(d) {
  if (!d) return;
  const mic = $("mic"); mic.hidden = false; let base = "";
  d.onPartial(({ text }) => { $("ask-input").value = base + text; });
  d.onFinal(({ text }) => { base = base + text + " "; $("ask-input").value = base; });
  d.onState(({ state, reason }) => { mic.setAttribute("aria-pressed", String(state === "listening" || state === "starting")); if (state === "idle" && (reason === "not_granted" || reason === "unavailable")) mic.hidden = true; });
  mic.onclick = () => {
    if (mic.getAttribute("aria-pressed") === "true") { d.stop().catch(() => {}); return; }
    base = $("ask-input").value ? $("ask-input").value + " " : "";
    if (!video.paused) video.pause();
    d.start().catch(() => {});
  };
}

/* ---------- start ---------- */
function applyStrings() {
  const L = LVP.L;
  $("s-kicker").textContent = L.kicker;
  for (const b of $("tabs").querySelectorAll("button")) b.textContent = L.tabs[b.dataset.panel];
  $("s-draw").textContent = L.mark; $("draw-badge").textContent = L.drawBadge; $("ask-send").textContent = L.send; $("ask-stop").textContent = L.stop;
  $("s-frame").textContent = L.frame; $("s-stop").textContent = L.stopAtQ; $("ask-input").placeholder = L.placeholder;
  $("practice-btn").textContent = L.practice; $("note-btn").textContent = L.note; $("card-btn").textContent = L.makeCard;
  buildChips();
}
const use = (n) => (window.claude?.use ? window.claude.use(n).catch(() => null) : Promise.resolve(null));
LVP.use = use;
async function boot() {
  try { const r = await fetch("course.json"); if (!r.ok) throw new Error(String(r.status)); course = await r.json(); }
  catch { $("chat").append(el("div", "err", STR.en.loadError)); return; }
  LVP.L = STR[(course.language || "en").slice(0, 2)] || STR.en;
  document.documentElement.lang = course.language || "en";
  $("course-title").textContent = course.title;
  applyStrings(); buildPicker(); Store.loadLocal();
  for (const f of LVP.hooks.ready) f(course);
  const fromHash = course.videos.find((v) => safeId(v.id) === location.hash.slice(1))?.id;
  openVideo(fromHash || Store.get("last")?.video || course.videos[0].id);
  window.addEventListener("hashchange", () => { const v = course.videos.find((x) => safeId(x.id) === location.hash.slice(1)); if (v && v.id !== cur?.id) openVideo(v.id); });
  window.addEventListener("pagehide", () => { if (cur) { prog().pos = video.currentTime; Store.push("p-" + cur.id); } });
  use("sample").then(async (s) => {
    sample = s; sampleChecked = true;
    if (s) { const lim = await s.limits().catch(() => null); imagesOk = !!lim?.images; }
    $("with-frame").parentElement.hidden = !imagesOk;
    for (const id of ["practice-btn"]) $(id).hidden = !s;
    updateCtxLine(); renderChat();
  });
  use("dictation").then(setupDictation);
  Promise.all([use("db"), use("user")]).then(async ([d, u]) => {
    if (!d || !u) return;
    const uid = await u.id().catch(() => null); if (!uid) return;
    if (await Store.loadAccount(d, uid)) { buildMarks(); refreshPanels(); for (const f of LVP.hooks.ready) f(course, true); }
  });
}
window.addEventListener("DOMContentLoaded", boot);
