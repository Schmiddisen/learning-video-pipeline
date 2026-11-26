/* lvp player – flashcards: FSRS review inside the player, linked to the video moments,
   plus a direct AnkiConnect bridge when the player runs as an installed desktop app. */
"use strict";
(() => {
  const LVP = window.LVP, { $, el, fmt } = LVP;
  const S = {
    en: {
      title: "Review", due: "due", newToday: "new today", locked: "unlock as you watch", total: "cards",
      show: "Show answer", again: "Again", hard: "Hard", good: "Good", easy: "Easy", watch: "Watch the moment",
      why: "Why? Ask Claude", done: "Done for now.", doneBody: "New cards unlock when you reach the moment in the video that teaches them.",
      nextIn: "Next card due", mine: "yours", ankiTitle: "Anki", ankiOff: "To review in Anki itself, install this player as an app from the Claude desktop app (artifact menu → Install as app), with Anki and the AnkiConnect add-on running.",
      ankiConnect: "Connect to Anki", ankiChecking: "Looking for Anki…", ankiOn: "Connected to Anki", ankiNo: "Anki isn't answering. Start Anki with the AnkiConnect add-on (code 2055492159).",
      ankiMode: "Study Anki's decks (every answer goes to Anki)", rwkvHint: "RWKV is a small neural network trained on the review histories of 10,000 Anki users. It reads your whole history – every card, the time of day, how long you took – and shows the cards you are about to forget first. With Anki's decks on, it reads Anki's review log.", sched: "Scheduler", schedFsrs: "FSRS", schedRwkv: "RWKV – neural memory model", retention: "Target recall", rwkvLoading: "RWKV is reading your review history", rwkvReady: (n) => `RWKV has read ${n} reviews`, rwkvFail: "RWKV unavailable", queueMode: "Due cards", queueLive: "Live – as RWKV-Instant in the RWKV Anki fork", queueDay: "Fixed per day – the count drops by one per answer", liveHint: "Live: after every answer RWKV re-estimates all cards, so the count is a snapshot – it can drop faster than one per answer, or rise. A card returns after at least 5 other answers and 30 seconds.", waiting: (n) => `${n} waiting (5 other answers and 30 s between repeats)`, curveTip: "Estimate from RWKV-Curve; with the live queue, RWKV decides from the current prediction when the card returns", ankiSync: "Sync AnkiWeb", ankiPush: "Add missing cards to Anki", ankiPushed: "added",
      ankiMapped: "cards matched in Anki", ankiPending: "reviews waiting to go to Anki", ankiSent: "sent", install: "Install as app",
      explainMiss: "I forgot this flashcard. Explain the idea behind it so it sticks – briefly, with a different angle than the card.",
      edit: "Edit with Claude", editTitle: "How should the card change?", editHow: "e.g. shorter, add an example, ask about the reason instead", editGo: "Rewrite", save: "Save", cancel: "Cancel", del: "Delete", delSure: "Really delete?",
      fromAnki: "Decks and counts straight from Anki.",
      deck: "Deck", colNew: "New", colLearn: "Learn", colDue: "Due", decks: "Decks", settings: "Anki and settings",
      dailyNew: "New cards per day", notify: "cards are due", videoQuestions: "Video questions",
      link: "Link my Anki cards to the videos", linkAgain: "Link new Anki cards", linked: "linked", linking: "Claude is linking", linkedNew: "cards linked to videos", linkReport: (d, all, n) => `${d} decks checked: ${all} cards are linked to their video moment (${n} new this time).`,
      linkHint: "Claude finds the decks that belong to this course and links each card to the moment that teaches it. New cards are linked automatically from then on."
    },
    de: {
      title: "Wiederholen", due: "fällig", newToday: "neu heute", locked: "werden beim Schauen freigeschaltet", total: "Karten",
      show: "Antwort zeigen", again: "Nochmal", hard: "Schwer", good: "Gut", easy: "Leicht", watch: "Stelle im Video",
      why: "Warum? Claude fragen", done: "Für jetzt erledigt.", doneBody: "Neue Karten werden frei, sobald du die Stelle im Video erreichst, die sie erklärt.",
      nextIn: "Nächste Karte fällig", mine: "eigene", ankiTitle: "Anki", ankiOff: "Um direkt in Anki zu wiederholen: den Player in der Claude-Desktop-App als App installieren (Artefakt-Menü → Als App installieren), Anki mit dem Add-on AnkiConnect geöffnet.",
      ankiConnect: "Mit Anki verbinden", ankiChecking: "Suche Anki …", ankiOn: "Mit Anki verbunden", ankiNo: "Anki antwortet nicht. Starte Anki mit dem Add-on AnkiConnect (Code 2055492159).",
      ankiMode: "Ankis Stapel lernen (jede Antwort geht an Anki)", rwkvHint: "RWKV ist ein kleines neuronales Netz, trainiert auf den Lernverläufen von 10.000 Anki-Nutzern. Es liest deinen ganzen Verlauf – jede Karte, die Tageszeit, wie lange du gebraucht hast – und zeigt zuerst die Karten, die du gleich vergisst. Mit Ankis Stapeln liest es Ankis Lernverlauf.", sched: "Planung", schedFsrs: "FSRS", schedRwkv: "RWKV – neuronales Gedächtnismodell", retention: "Ziel-Erinnerung", rwkvLoading: "RWKV liest deinen Lernverlauf", rwkvReady: (n) => `RWKV hat ${n} Wiederholungen gelesen`, rwkvFail: "RWKV nicht verfügbar", queueMode: "Fällige Karten", queueLive: "Live – wie RWKV-Instant im RWKV-Anki-Fork", queueDay: "Fest pro Tag – die Zahl sinkt um eins pro Antwort", liveHint: "Live: Nach jeder Antwort schätzt RWKV alle Karten neu – die Zahl ist eine Momentaufnahme und kann schneller als um eins sinken oder auch steigen. Eine Karte kommt frühestens nach 5 anderen Antworten und 30 Sekunden wieder.", waiting: (n) => `${n} warten (5 andere Antworten und 30 s zwischen Wiederholungen)`, curveTip: "Schätzung aus RWKV-Curve; in der Live-Warteschlange entscheidet RWKV anhand der aktuellen Vorhersage, wann die Karte wiederkommt", ankiSync: "AnkiWeb synchronisieren", ankiPush: "Fehlende Karten zu Anki hinzufügen", ankiPushed: "hinzugefügt",
      ankiMapped: "Karten in Anki gefunden", ankiPending: "Wiederholungen warten auf Anki", ankiSent: "übertragen", install: "Als App installieren",
      explainMiss: "Ich habe diese Karteikarte vergessen. Erklär die Idee dahinter so, dass sie hängen bleibt – kurz und aus einem anderen Blickwinkel als die Karte.",
      edit: "Mit Claude bearbeiten", editTitle: "Wie soll sich die Karte ändern?", editHow: "z. B. kürzer, mit Beispiel, nach dem Grund fragen", editGo: "Umschreiben", save: "Speichern", cancel: "Abbrechen", del: "Löschen", delSure: "Wirklich löschen?",
      fromAnki: "Stapel und Zahlen direkt aus Anki.",
      deck: "Stapel", colNew: "Neu", colLearn: "Lernen", colDue: "Fällig", decks: "Stapel", settings: "Anki und Einstellungen",
      dailyNew: "Neue Karten pro Tag", notify: "Karten sind fällig", videoQuestions: "Fragen aus den Videos",
      link: "Meine Anki-Karten mit den Videos verknüpfen", linkAgain: "Neue Anki-Karten verknüpfen", linked: "verknüpft", linking: "Claude verknüpft", linkedNew: "Karten mit Videos verknüpft", linkReport: (d, all, n) => `${d} Stapel geprüft: ${all} Karten sind mit ihrer Stelle im Video verknüpft (${n} davon neu).`,
      linkHint: "Claude sucht die Stapel, die zu diesem Kurs gehören, und verknüpft jede Karte mit der Stelle, die sie erklärt. Neue Karten werden danach automatisch verknüpft."
    }
  };
  let T = S.en, course = null, fsrs = null, current = null, revealed = false, focusIds = null, shown = { id: null, at: 0 };
  const F = window.FSRS;
  const store = LVP.store;
  const srs = () => { const s = store.ensure("srs", () => ({ cards: {}, log: [], newDays: {} })); s.cards ||= {}; s.log ||= []; s.newDays ||= {}; return s; };
  const mine = () => { const m = store.ensure("mine", () => ({ cards: [] })); m.cards ||= []; return m; };
  const settings = () => store.get("review-settings") || { _key: "review-settings", newPerDay: 20, ankiMode: false };
  const today = () => new Date().toISOString().slice(0, 10);
  // the video's own check questions come back as spaced cards (lag-1 in the video, days later here)
  let quizCards = [];
  const buildQuizCards = () => {
    quizCards = [];
    for (const v of course.videos) v.quizzes.forEach((q, i) => {
      if (q.quiz === "check" && q.a) quizCards.push({ id: `q-${v.id}-${i}`, deck: `${course.title}::${T.videoQuestions}`, front: q.q, back: q.a, video: v.id, t: Math.max(0, q.t - 1), tags: ["video-question"] });
    });
  };
  // the learner's own Anki notes that Claude linked to a video moment
  const links = () => { const l = store.ensure("anki-links", () => ({ notes: {}, checked: [] })); l.notes ||= {}; l.checked ||= []; return l; };
  const linkedCards = () => Object.entries(links().notes).map(([nid, n]) => ({ id: "a-" + nid, deck: n.deck, front: n.front, back: n.back, cloze: n.cloze, extra: n.extra, video: n.video, t: n.t, tags: n.tags || [], anki: true }));
  const changes = () => { const c = store.ensure("card-changes", () => ({ edited: {}, deleted: [] })); c.edited ||= {}; c.deleted ||= []; return c; };
  const allCards = () => {
    const ch = changes(), gone = new Set(ch.deleted);
    return [...(course?.cards || []), ...quizCards, ...mine().cards, ...linkedCards()]
      .filter((c) => !gone.has(c.id)).map((c) => (ch.edited[c.id] ? { ...c, ...ch.edited[c.id] } : c));
  };
  async function ankiNote(c) {   // the Anki note behind a card, when Anki is connected
    const cards = anki.ok && (c.cardId ? [c.cardId] : anki.map[c.id]); if (!cards?.length) return null;
    const [nid] = await anki.call("cardsToNotes", { cards: [cards[0]] }).catch(() => []);
    return nid || null;
  }
  async function deleteCard(c) {
    const ch = changes(); ch.deleted.push(c.id); store.set("card-changes", ch, true);
    const nid = await ankiNote(c);
    if (nid) await anki.call("deleteNotes", { notes: [nid] }).catch(() => {});
    delete anki.map[c.id]; current = null; revealed = false; render(); LVP.updateDue();
  }
  async function saveEdit(c, fields) {
    const ch = changes(); ch.edited[c.id] = fields; store.set("card-changes", ch, true);
    const nid = await ankiNote(c);
    if (nid) {
      const [info] = await anki.call("notesInfo", { notes: [nid] }).catch(() => []);
      const names = Object.entries(info?.fields || {}).sort((a, b) => a[1].order - b[1].order).map(([k]) => k);
      const vals = fields.cloze != null ? [fields.cloze, fields.extra] : [fields.front, fields.back, fields.extra];
      const upd = {}; names.forEach((k, i) => { if (vals[i] != null) upd[k] = String(vals[i]); });
      if (Object.keys(upd).length) await anki.call("updateNoteFields", { note: { id: nid, fields: upd } }).catch(() => {});
    }
    render();
  }
  function editBox(c, f) {
    const box = el("div", "verdict"); box.append(el("b", null, T.editTitle));
    const how = el("textarea", "field"); how.placeholder = T.editHow; how.style.minHeight = "54px";
    const go = el("button", "btn small primary", T.editGo), out = el("div");
    go.onclick = async () => {
      if (!how.value.trim()) return;
      go.disabled = true; out.textContent = LVP.L.thinking;
      const now = c.cloze ? { cloze: c.cloze, extra: c.extra || "" } : { front: c.front, back: c.back, extra: c.extra || "" };
      try {
        const r = await LVP.sample().json([
          "Rewrite this flashcard as the learner asks. Keep it one idea, in its language; keep cloze markers {{c1::…}} if it has them.",
          "Card: " + JSON.stringify(now), "Learner's request: " + how.value.trim(),
          "Reply with only JSON with the same keys as the card.",
        ].join("\n"), LVP.m("cards", { cache: false }));
        out.textContent = "";
        const prev = el("div", "flash"); prev.append(face({ ...c, ...r }, false), face({ ...c, ...r }, true)); out.append(prev);
        const save = el("button", "btn small primary", T.save), no = el("button", "btn small", T.cancel);
        save.onclick = () => saveEdit(c, Object.fromEntries(Object.keys(now).map((k) => [k, String(r[k] ?? now[k])])));
        no.onclick = () => box.remove();
        const row = el("div", "row"); row.append(save, no); out.append(row);
      } catch (e) { out.textContent = LVP.errText(e); }
      go.disabled = false;
    };
    box.append(how, go, out); return box;
  }
  const plain = (s) => String(s || "").replace(/<[^>]+>/g, " ").replace(/&nbsp;/g, " ").replace(/\s+/g, " ").trim();
  const norm = (s) => plain(s).toLowerCase().replace(/\{\{c\d+::([^}]*?)(::[^}]*)?\}\}/g, "$1").replace(/[^\p{L}\p{N}]+/gu, "").slice(0, 60);

  const unlocked = (c) => {
    if (!c.video) return true;
    const v = course.videos.find((x) => x.id === c.video); if (!v) return true;
    const reached = LVP.store.get("p-" + c.video)?.furthest || 0;
    return reached >= (c.t != null ? c.t + 5 : v.duration * 0.9);
  };
  const inDeck = (c, deck) => !deck || c.deck === deck || (c.deck || "").startsWith(deck + "::");
  function queue(deck = null) {
    const st = srs().cards, now = Date.now(), due = [], fresh = [];
    let locked = 0, learning = 0, ahead = new Set();
    const rwOn = !!snapFor("player"), live = liveFor("player");
    let waiting = 0, reviews = null;
    const learnAhead = now + 20 * 60000, steps = [];   // like Anki: learning cards due within 20 min count
    for (const c of allCards()) {
      if (!inDeck(c, deck)) continue;
      const s = st[c.id];
      if (live && s && s.state !== 0) {   // learning cards keep their steps; reviews follow RWKV now
        if (s.state === 1 || s.state === 3) { if (new Date(s.due).getTime() <= now) { if (spacingOk(c.id)) { due.push(c); learning++; } else waiting++; } }
        else { const k = liveState(c.id); if (k === "due") due.push(c); else if (k === "wait") waiting++; }
        continue;
      }
      if (rwOn) {
        const l = rw.snap.learn[c.id];
        if (l != null) { if (l <= learnAhead) steps.push(c); }
        else if (rw.snap.set.has(c.id)) due.push(c);
        else if (!(s && s.state !== 0)) { if (unlocked(c)) fresh.push(c); else locked++; }
        continue;
      }
      if (s && s.state !== 0) { if (new Date(s.due).getTime() <= now) { due.push(c); if (s.state !== 2) learning++; } }
      else if (unlocked(c)) fresh.push(c); else locked++;
    }
    if (rwOn) {   // learning steps first (by time), then the day's reviews, most at risk first
      due.sort((a, b) => snapP(a.id) - snapP(b.id));
      steps.sort((a, b) => rw.snap.learn[a.id] - rw.snap.learn[b.id]);
      const ready = steps.filter((c) => rw.snap.learn[c.id] <= now);
      due.unshift(...ready); const later = steps.filter((c) => rw.snap.learn[c.id] > now && aheadOk(c.id)); due.push(...later); ahead = new Set(later); learning = steps.length; reviews = due.length - ready.length - later.length;
    } else if (live) due.sort((a, b) => (st[b.id].state !== 2) - (st[a.id].state !== 2) || (rw.p[a.id] ?? 0) - (rw.p[b.id] ?? 0));
    else due.sort((a, b) => new Date(st[a.id].due) - new Date(st[b.id].due));
    if (focusIds) {  // practising one concept: its cards first, due or not (once each)
      const extra = allCards().filter((c) => focusIds.has(c.id) && !due.includes(c) && st[c.id] && st[c.id].state !== 0);
      due.unshift(...extra.filter((c) => !(st[c.id].focusDone)));
    }
    const left = Math.max(0, settings().newPerDay - (srs().newDays[today()] || 0));
    return { due, fresh: fresh.slice(0, left), locked, learning, freshAll: fresh.length, ahead, waiting, reviews: reviews ?? due.length - learning };
  }
  LVP.review = {
    // Anki's decks on: Anki's own counts (RWKV's fixed queue for the reviews), else the player's
    dueCount: () => { if (!course || !F) return 0; if (ankiLive()) return ankiTotal.n ?? 0; const q = queue(); return q.due.length + q.fresh.length; },
    struggles: () => allCards().filter((c) => (srs().cards[c.id]?.lapses || 0) > 0).sort((a, b) => srs().cards[b.id].lapses - srs().cards[a.id].lapses).map((c) => plain(c.front || c.cloze).slice(0, 120)),
    // memory per concept tag: mean FSRS retrievability now (unseen cards count as 0)
    mastery: () => {
      if (!F || !fsrs) return [];
      const st = srs().cards, now = new Date(), tags = {};
      for (const c of allCards()) for (const t of c.tags || []) {
        if (/^v\d+\.\d+$/.test(t) || ["video-question", "mine", "definition"].includes(t)) continue;
        const s = st[c.id];
        const r = !(s && s.state !== 0) ? 0 : rw.ready && rw.key === "player" && rw.p[c.id] != null ? rw.p[c.id] : fsrs.get_retrievability(reviveCard(s), now, false);
        (tags[t] ||= { tag: t, cards: [], seen: 0, sum: 0 }).cards.push(c.id);
        tags[t].sum += r; if (s && s.state !== 0) tags[t].seen++;
      }
      // only concepts the learner has started; r = recall of the cards learned so far
      return Object.values(tags).filter((t) => t.cards.length >= 2 && t.seen > 0).map((t) => ({ tag: t.tag, n: t.cards.length, seen: t.seen, r: t.sum / t.seen, cards: t.cards }));
    },
    // scheduler state for tests and the coach (no learner content)
    rwkvState: () => ({ ready: rw.ready, key: rw.key, live: liveMode(), seq: rw.seq || 0, lastSeq: { ...(rw.lastSeq || {}) }, learn: { ...(rw.snap?.learn || {}) }, left: rw.snap ? [...rw.snap.set] : [], now: Date.now() }),
    focus: (ids) => { focusIds = new Set(ids); current = null; LVP.selectTab("review"); },
    addCard: (c) => { const id = "m-" + Date.now().toString(36); mine().cards.push({ id, deck: (course.title || "Course") + "::Mine", tags: ["mine"], ...c }); store.set("mine", mine(), true); LVP.updateDue(); },
  };
  const ankiTotal = { n: null, at: 0, busy: false };
  async function refreshAnkiTotal() {
    if (ankiTotal.busy) return; ankiTotal.busy = true;
    try {
      const tops = (await anki.call("deckNames")).filter((d) => d !== "Default" && !d.includes("::"));
      const by = await deckStats(tops);
      const snap = snapFor("anki"), live = liveFor("anki");
      ankiTotal.n = tops.reduce((n, d) => n + (by[d]?.new_count || 0) + (by[d]?.learn_count || 0) + (snap || live ? 0 : by[d]?.review_count || 0), 0)
        + (live ? Object.values(rw.meta).filter((m) => m.type === 2 && liveState(m.card) === "due").length : snap ? snap.set.size : 0);
      ankiTotal.at = Date.now();
    } catch { /* Anki closed */ }
    ankiTotal.busy = false; paintDue();
  }
  function paintDue() {
    const n = LVP.review.dueCount(), pill = $("due-pill");
    pill.textContent = LVP.L.reviewNav + (n ? ` · ${n} ${T.due}` : ""); pill.onclick = () => LVP.selectTab("review");
  }
  LVP.updateDue = () => { paintDue(); if (ankiLive() && Date.now() - ankiTotal.at > 3000) refreshAnkiTotal(); };

  /* --- RWKV: a neural memory model (rwkv.js, in a worker) reads the whole review history and
     orders the reviews by the chance of forgetting; FSRS keeps the bookkeeping underneath --- */
  const rw = { previews: {}, snap: null, worker: null, key: null, ready: false, loading: false, failed: null, progress: 0, error: "", n: 0, p: {}, meta: {}, last: {}, presets: {}, msgId: 0, wait: {} };
  const useRwkv = () => !!course?.rwkv && settings().scheduler === "rwkv";
  const target = () => settings().retention || 0.9;
  const rwKey = () => (ankiLive() ? "anki" : "player");
  function rwCall(msg, onProgress) {
    if (!rw.worker) {
      rw.worker = new Worker("rwkv-worker.js");
      rw.worker.onmessage = ({ data }) => {
        const w = rw.wait[data.id]; if (!w) return;
        if (data.progress != null) { w.onProgress?.(data.progress); return; }
        delete rw.wait[data.id]; if (data.error) w.rej(new Error(data.error)); else w.res(data.result);
      };
      rw.worker.onerror = (e) => { for (const w of Object.values(rw.wait)) w.rej(new Error(e.message || "worker")); rw.wait = {}; };
    }
    return new Promise((res, rej) => { const id = ++rw.msgId; rw.wait[id] = { res, rej, onProgress }; rw.worker.postMessage({ ...msg, id }); });
  }
  const pMeta = (c) => ({ card: c.id, note: c.note || c.id, deck: c.deck || "-", preset: "player" });
  function playerHistory() {
    const meta = {}; for (const c of allCards()) meta[c.id] = pMeta(c);
    const events = srs().log.filter((e) => meta[e.id] && e.g >= 1).map((e) => ({ ...meta[e.id], ts: Date.parse(e.at), rating: e.g, duration: e.ms, state: e.st }));
    return { meta, events: events.sort((a, b) => a.ts - b.ts) };
  }
  const chunks = (xs, n) => Array.from({ length: Math.ceil(xs.length / n) }, (_, i) => xs.slice(i * n, i * n + n));
  async function ankiHistory() {
    const ids = await anki.call("findCards", { query: "-is:new -is:suspended" }), meta = {}, events = [];
    for (const part of chunks(ids, 500)) {
      for (const ci of await anki.call("cardsInfo", { cards: part })) meta["k" + ci.cardId] = { card: "k" + ci.cardId, note: "n" + ci.note, deck: ci.deckName, preset: "-", cardId: ci.cardId, type: ci.type };
    }
    for (const d of new Set(Object.values(meta).map((m) => m.deck))) {
      const conf = await anki.call("getDeckConfig", { deck: d }).catch(() => null);
      rw.presets[d] = conf?.id != null ? "c" + conf.id : "-";
    }
    for (const m of Object.values(meta)) m.preset = rw.presets[m.deck];
    for (const part of chunks(ids, 500)) {
      const revs = await anki.call("getReviewsOfCards", { cards: part.map(String) });
      for (const [cid, list] of Object.entries(revs || {})) {
        const m = meta["k" + cid]; if (!m) continue;
        // as the RWKV Anki fork replays history: graded entries of types 0–5 (learn, review, relearn,
        // filtered, manual, rescheduled) except cram reviews that did not reschedule (type 3, factor 0),
        // and only since the card's last fresh start (a reset card starts over)
        const ok = list.filter((r) => r.ease >= 1 && r.ease <= 4 && r.type >= 0 && r.type <= 5 && !(r.type === 3 && r.factor === 0)).sort((a, b) => a.id - b.id);
        let start = 0;
        ok.forEach((r, i) => { if (r.type === 0 && (i === 0 || ok[i - 1].type !== 0)) start = i; });
        for (const r of ok.slice(start)) {   // the dataset's states: 1 learning, 2 review, 3 relearning (first = 0 new)
          events.push({ card: m.card, note: m.note, deck: m.deck, preset: m.preset, ts: r.id, rating: r.ease, duration: r.time, state: [1, 2, 3, 2, 2, 2][r.type] });
        }
      }
    }
    return { meta, events: events.sort((a, b) => a.ts - b.ts) };
  }
  function rwState() {
    if (rw.error) return `${T.rwkvFail}: ${rw.error}`;
    if (rw.loading) return `${T.rwkvLoading} … ${Math.round(rw.progress * 100)} %`;
    return rw.ready ? T.rwkvReady(rw.n) : "";
  }
  async function rwLoad() {
    const key = rwKey();
    if (rw.loading || (rw.ready && rw.key === key) || rw.failed === key) return;
    rw.loading = true; rw.ready = false; rw.error = ""; rw.progress = 0;
    if (rw.snap?.key !== key) { rw.snap = null; rwRestore(key); }
    try {
      const h = key === "anki" ? await ankiHistory() : playerHistory();
      const r = await rwCall({ type: "load", events: h.events, max: 20000 }, (p) => { rw.progress = p; const s = $("rwkv-state"); if (s) s.textContent = rwState(); });
      rw.meta = h.meta; rw.n = r.n; rw.key = key; rw.last = {};
      for (const e of h.events) rw.last[e.card] = e.ts;
      await rwPredict(); rwSnapshot(); rw.ready = true;
    } catch (e) { rw.error = String(e?.message || e); rw.failed = key; }
    rw.loading = false; ankiTotal.at = 0; render(); LVP.updateDue();
  }
  async function rwPredict() {
    rw.p = await rwCall({ type: "predict", cards: Object.values(rw.meta).filter((m) => rw.last[m.card]).map(({ card, note, deck, preset }) => ({ card, note, deck, preset })), now: Date.now() });
  }
  /* The day's queue is fixed when it is built, as in Anki: the cards whose chance of recall is
     below the target then. Answers only take cards out (live predictions would move other cards
     across the line after every answer, as each review updates the deck and global state).
     Short repeats (player mode) are learning steps with the interval RWKV gives for the rating. */
  const ankiDay = (t = Date.now()) => Math.floor((t / 1000 - new Date(t).getTimezoneOffset() * 60 - 4 * 3600) / 86400);
  const rwDue = (card) => !!rw.snap?.set.has(card);
  const liveMode = () => useRwkv() && (settings().rwkvQueue || "live") === "live";
  const snapFor = (key) => (useRwkv() && !liveMode() && rw.snap?.key === key ? rw.snap : null);   // today's fixed queue
  const liveFor = (key) => liveMode() && rw.ready && rw.key === key;
  /* Live queue, as RWKV-Instant in the RWKV Anki fork (JSchoreels/anki, rslib/src/scheduler/rwkv.rs):
     a review card is eligible while its predicted recall now is at or below the target, ordered by
     recall ÷ target (lowest first); a card returns only after 5 other answers and 30 seconds. */
  const SPACING = { answers: 5, secs: 30 };
  function rwNoteAnswer(card) { rw.seq = (rw.seq || 0) + 1; (rw.lastSeq ||= {})[card] = rw.seq; rw.last[card] = Date.now(); }
  const spacingOk = (card) => {
    const since = (Date.now() - (rw.last[card] || 0)) / 1000, others = rw.lastSeq?.[card] == null ? Infinity : rw.seq - rw.lastSeq[card];
    return since >= SPACING.secs && others >= SPACING.answers;
  };
  // a learning card shown before its step is due (learn ahead): not straight after its own answer
  const aheadOk = (card) => (Date.now() - (rw.last[card] || 0)) / 1000 >= SPACING.secs || (rw.lastSeq?.[card] == null ? true : rw.seq - rw.lastSeq[card] >= SPACING.answers);
  const liveState = (card) => { const p = rw.p[card]; if (p == null || !(p <= target())) return "no"; return spacingOk(card) ? "due" : "wait"; };
  const snapP = (card) => rw.p[card] ?? rw.snap?.info[card]?.p ?? 0;
  /** the stored queue of today, usable at once after a reload (before the model has re-read the history) */
  function rwRestore(key) {
    const saved = store.get("rwkv-snap-" + key);
    if (!(saved && saved.key === key && saved.day === ankiDay() && saved.target === target() && saved.info)) return false;
    rw.snap = { learn: {}, answered: {}, steps: {}, ...saved, set: new Set(saved.cards) };
    return true;
  }
  function rwSnapshot(force = false) {
    const t = target();
    if (!force && (rw.snap?.key === rw.key || rwRestore(rw.key))) {
      // reviews made elsewhere (Anki desktop, another device) since it was built leave it
      for (const c of [...rw.snap.set]) if (!rw.meta[c] || ((rw.last[c] || 0) > rw.snap.at && !(c in rw.snap.answered))) rw.snap.set.delete(c);
    } else {
      const ms = Object.values(rw.meta).filter((m) => (rw.key === "anki" ? m.type === 2 : true) && rw.p[m.card] != null && rw.p[m.card] < t);
      const info = Object.fromEntries(ms.map((m) => [m.card, { deck: m.deck, cardId: m.cardId, p: Math.round(rw.p[m.card] * 1e4) / 1e4 }]));
      rw.snap = { key: rw.key, day: ankiDay(), target: t, at: Date.now(), info, learn: {}, answered: {}, steps: {}, set: new Set(ms.map((m) => m.card)) };
    }
    rwSaveSnap();
  }
  const rwSaveSnap = () => {
    const { set, ...plain } = rw.snap; plain.cards = [...set];
    plain.info = Object.fromEntries(plain.cards.map((c) => [c, rw.snap.info[c]]));   // only what is left
    store.set("rwkv-snap-" + plain.key, plain);
  };
  /** an answer: out of today's queue; a short interval (player mode) becomes a learning step */
  function rwAnswered(card, grade, state) {
    if (!rw.snap || !useRwkv()) return;
    if (card in rw.snap.learn) state = 1;
    rw.snap.set.delete(card); rw.snap.answered[card] = Date.now(); delete rw.snap.learn[card];
    // same-day repeats as in Anki: after Again/Hard, or while a card is new or still in learning;
    // at most 4 per card and day; Good/Easy on a review card finishes it for today
    const steps = (rw.snap.steps ||= {}), learningCard = state === 0 || state === 1 || state === 3;
    if (rw.snap.key === "player" && (grade <= 2 || learningCard) && (steps[card] || 0) < 4) {
      const iv = rw.previews[card]?.[grade - 1] ?? (grade === 1 ? 600000 : null);
      if (iv != null && iv < 864e5) { rw.snap.learn[card] = Date.now() + Math.max(60000, iv); steps[card] = (steps[card] || 0) + 1; }
    }
    rwSaveSnap();
  }
  const rwMeta = (c) => {
    if (!rw.ready) return null;
    if (rw.key === "player" && !c.cardId) return pMeta(c);
    if (rw.key === "anki" && c.cardId) return rw.meta["k" + c.cardId] || { card: "k" + c.cardId, note: "n" + c.noteId, deck: c.deck, preset: rw.presets[c.deck] || "-", cardId: c.cardId, type: c.ankiType };
    return null;
  };
  async function rwFeed(meta, grade, ms, state) {
    rw.meta[meta.card] ||= meta;
    const { card, note, deck, preset } = meta;
    await rwCall({ type: "feed", event: { card, note, deck, preset, ts: Date.now(), rating: grade, duration: ms, state } });
    await rwPredict(); ankiTotal.at = 0; LVP.updateDue(); if (deckView === null || liveMode()) render();
  }
  setInterval(() => {   // a new day builds a new queue; otherwise only the order follows the predictions
    if (rw.ready && !rw.loading) rwPredict().then(() => { if (rw.snap && rw.snap.day !== ankiDay()) { rwSnapshot(true); render(); } LVP.updateDue(); }).catch(() => {});
  }, 300000);
  function schedRow() {
    const wrap = el("div", "anki"); if (!course?.rwkv) return wrap;
    const row = el("div", "row"), sel = el("select"); sel.id = "scheduler";
    for (const [v, t] of [["fsrs", T.schedFsrs], ["rwkv", T.schedRwkv]]) { const o = el("option", null, t); o.value = v; sel.append(o); }
    sel.value = useRwkv() ? "rwkv" : "fsrs";
    sel.onchange = () => { const s = settings(); s.scheduler = sel.value; rw.failed = null; store.set("review-settings", s, true); render(); LVP.updateDue(); };
    row.append(el("b", null, T.sched), sel);
    if (useRwkv()) {
      const ret = el("input"); ret.type = "number"; ret.min = "0.7"; ret.max = "0.97"; ret.step = "0.01"; ret.value = String(target()); ret.style.width = "70px"; ret.id = "retention";
      ret.onchange = () => { const s = settings(); s.retention = Math.min(0.97, Math.max(0.7, Number(ret.value) || 0.9)); store.set("review-settings", s, true); if (rw.ready) rwSnapshot(true); else rw.snap = null; render(); LVP.updateDue(); };
      row.append(el("span", null, T.retention), ret);
    }
    wrap.append(row, el("span", "hint", T.rwkvHint));
    if (useRwkv()) {
      const qrow = el("div", "row"), qs = el("select"); qs.id = "rwkv-queue";
      for (const [v, t] of [["live", T.queueLive], ["day", T.queueDay]]) { const o = el("option", null, t); o.value = v; qs.append(o); }
      qs.value = settings().rwkvQueue || "live";
      qs.onchange = () => { const s = settings(); s.rwkvQueue = qs.value; store.set("review-settings", s, true); if (qs.value === "day" && rw.ready) rwSnapshot(); render(); LVP.updateDue(); };
      qrow.append(el("span", null, T.queueMode), qs); wrap.append(qrow);
      if (liveMode()) wrap.append(el("span", "hint", T.liveHint));
    }
    if (useRwkv()) { const st = el("span", "state", rwState()); st.id = "rwkv-state"; wrap.append(st); }
    return wrap;
  }

  /* --- rendering a card --- */
  function face(c, back) {
    const box = el("div");
    if (c.cloze) {
      const parts = c.cloze.split(/(\{\{c\d+::[^}]*?(?:::[^}]*)?\}\})/g);
      for (const p of parts) {
        const m = /^\{\{c\d+::([^}]*?)(?:::([^}]*))?\}\}$/.exec(p);
        if (!m) box.append(document.createTextNode(p));
        else box.append(el("span", "cloze-gap", back ? m[1] : (m[2] ? `[${m[2]}]` : "[…]")));
      }
    } else box.textContent = back ? c.back : c.front;
    return box;
  }
  let deckView = null;   // null: the deck list (like Anki's main screen); a deck name: studying it
  function deckList(box) {
    const names = [...new Set(allCards().map((c) => c.deck).filter(Boolean))];
    const all = new Set();
    for (const n of names) { const parts = n.split("::"); for (let i = 1; i <= parts.length; i++) all.add(parts.slice(0, i).join("::")); }
    const table = el("div", "decks");
    const head = el("div", "deckrow head"); head.append(el("span", null, T.deck), el("span", "n new", T.colNew), el("span", "n learn", T.colLearn), el("span", "n due", T.colDue)); table.append(head);
    for (const d of [...all].sort()) {
      const q = queue(d), depth = d.split("::").length - 1;
      const row = el("button", "deckrow");
      const name = el("span", "dname", d.split("::").pop()); name.style.paddingLeft = depth * 20 + "px";
      const n = (v, cls) => el("span", "n " + cls + (v ? "" : " zero"), String(v));
      row.append(name, n(q.fresh.length, "new"), n(q.learning, "learn"), n(q.reviews, "due"));
      row.onclick = () => { deckView = d; current = null; render(); };
      table.append(row);
    }
    box.append(table);
  }
  /* ---- Anki as the source of truth (connected + "follow Anki's schedule"): Anki's decks,
     counts and queue; every rating goes to Anki, which schedules it ---- */
  const ankiLive = () => anki.ok && settings().ankiMode;
  let aq = null;   // Anki queue for the open deck: [{cardId, kind}]
  const q_ = (d) => `"deck:${d.replace(/"/g, "")}"`;
  const byCardId = () => { const m = {}; for (const [id, cards] of Object.entries(anki.map)) for (const c of cards) m[c] = id; return m; };
  async function deckStats(names) {
    const ids = await anki.call("deckNamesAndIds");
    const stats = await anki.call("getDeckStats", { decks: names }).catch(() => ({}));
    return Object.fromEntries(names.map((n) => [n, stats[String(ids[n])] || {}]));
  }
  async function ankiDeckList(box) {
    const names = (await anki.call("deckNames")).filter((d) => d !== "Default").sort();
    const by = await deckStats(names);
    const table = el("div", "decks");
    const head = el("div", "deckrow head"); head.append(el("span", null, T.deck), el("span", "n new", T.colNew), el("span", "n learn", T.colLearn), el("span", "n due", T.colDue)); table.append(head);
    const snap = snapFor("anki"), live = liveFor("anki"), waiting = useRwkv() && !snap && !live;   // RWKV still reading: no review count yet
    for (const d of names) {
      const x = { ...(by[d] || {}) }, depth = d.split("::").length - 1;
      if (live) x.review_count = Object.values(rw.meta).filter((m) => m.type === 2 && inDeck(m, d) && liveState(m.card) === "due").length;
      else if (snap) x.review_count = [...snap.set].filter((c) => inDeck(snap.info[c] || {}, d)).length;
      else if (waiting) x.review_count = "…";
      const row = el("button", "deckrow");
      const name = el("span", "dname", d.split("::").pop()); name.style.paddingLeft = depth * 20 + "px";
      const n = (v, cls) => el("span", "n " + cls + (v ? "" : " zero"), String(v || 0));
      row.append(name, n(x.new_count, "new"), n(x.learn_count, "learn"), n(x.review_count, "due"));
      row.onclick = () => { deckView = d; aq = null; current = null; revealed = false; render(); };
      table.append(row);
    }
    box.textContent = ""; box.append(el("p", "hint", T.fromAnki), table);
    const more = el("details", "anki-more"); more.append(el("summary", null, T.settings)); more.append(ankiPanel(), schedRow(), dailyRow()); box.append(more);
  }
  async function ankiNext(deck) {
    // Anki's order: learning cards that are due, then reviews, then new cards (within Anki's daily limit)
    const st = (await deckStats([deck]))[deck];
    let learn = await anki.call("findCards", { query: `${q_(deck)} is:learn is:due` });
    let due = await anki.call("findCards", { query: `${q_(deck)} is:review is:due -is:learn` });
    const snap = snapFor("anki");
    if (liveFor("anki")) {   // live, as RWKV-Instant: eligible now, lowest recall ÷ target first
      learn = learn.filter((id) => spacingOk("k" + id));
      const ms = Object.values(rw.meta).filter((m) => m.type === 2 && inDeck(m, deck) && !learn.includes(m.cardId));
      due = ms.filter((m) => liveState(m.card) === "due").sort((a, b) => rw.p[a.card] - rw.p[b.card]).map((m) => m.cardId);
      if (st) { st.review_count = due.length; st.learn_count = learn.length; st.waiting = ms.filter((m) => liveState(m.card) === "wait").length; }
    } else if (snap) {   // RWKV's queue of today, most at risk first
      due = [...snap.set].filter((c) => inDeck(snap.info[c] || {}, deck)).sort((a, b) => snapP(a) - snapP(b)).map((c) => snap.info[c].cardId).filter((id) => id && !learn.includes(id));
      if (st) st.review_count = due.length;
    } else if (useRwkv()) { due = []; if (st) st.review_count = "…"; }   // RWKV still reading the history
    const fresh = (st?.new_count || 0) ? await anki.call("findCards", { query: `${q_(deck)} is:new -is:suspended -is:buried` }) : [];
    const ids = [...learn, ...due, ...fresh.slice(0, st?.new_count || 0)];
    return { ids, counts: st || {} };
  }
  async function ankiStudy(box) {
    const { ids, counts } = await ankiNext(deckView);
    box.textContent = "";
    const top = el("div", "row"); top.style.justifyContent = "space-between";
    const back = el("button", "btn small", T.decks); back.onclick = () => { deckView = null; current = null; render(); };
    const c3 = el("span", "counts"); c3.append(el("span", "n new", String(counts.new_count || 0)), el("span", "n learn", String(counts.learn_count || 0)), el("span", "n due", String(counts.review_count || 0)));
    top.append(back, el("b", null, deckView.split("::").pop()), c3); box.append(top);
    if (!ids.length) { const d = el("div", "empty"); d.append(el("b", null, T.done)); if (counts.waiting) d.append(el("span", null, T.waiting(counts.waiting))); const b2 = el("button", "btn", T.decks); b2.onclick = back.onclick; d.append(b2); box.append(d); current = null; return; }
    if (!current?.cardId || (!ids.includes(current.cardId) && !liveMode())) {
      const [info] = await anki.call("cardsInfo", { cards: [ids[0]] });
      const ours = allCards().find((c) => c.id === byCardId()[ids[0]]);
      const f = Object.values(info.fields || {}).sort((a, b) => a.order - b.order).map((x) => x.value);
      const isCloze = /\{\{c\d+::/.test(f[0] || "");
      current = { ...(ours || {}), id: ours?.id || "anki-" + ids[0], cardId: ids[0], deck: info.deckName, noteId: info.note, ankiType: info.type,
        front: ours?.front ?? (isCloze ? null : plain(f[0])), back: ours?.back ?? (isCloze ? null : plain(f[1])),
        cloze: ours?.cloze ?? (isCloze ? plain(f[0]) : null), extra: ours?.extra ?? plain(isCloze ? f[1] : f[2]) };
      revealed = false;
    }
    studyCard(box, current, null);
  }
  async function rateAnki(c, grade) {
    const ms = Math.min(60000, Date.now() - shown.at), meta = rwMeta(c);
    if (snapFor("anki")) rwAnswered("k" + c.cardId, grade, c.ankiType ?? 2);
    if (c.cardId) rwNoteAnswer("k" + c.cardId);
    await anki.call("answerCards", { answers: [{ cardId: c.cardId, ease: grade }] }).catch(() => {});
    if (meta) {
      rwFeed(meta, grade, ms, c.ankiType ?? 2).catch(() => {});
      anki.call("cardsInfo", { cards: [c.cardId] }).then(([ci]) => { if (ci) meta.type = ci.type; }).catch(() => {});
    }
    // keep the player's own record in step, so the concept map and the coach see the review
    if (c.id && !c.id.startsWith("anki-")) srs().log.push({ id: c.id, g: grade, at: new Date().toISOString(), sent: true, ms, st: c.ankiType ?? 2 });
    current = null; revealed = false; ankiTotal.at = 0; render(); LVP.updateDue();
  }

  function render() {
    const box = $("review"); if (!box) return;
    if (useRwkv()) rwLoad();
    if (ankiLive()) { (deckView === null ? ankiDeckList(box) : ankiStudy(box)).catch((e) => { box.textContent = ""; box.append(el("p", "err", String(e?.message || e))); }); return; }
    box.textContent = "";
    if (!F) { box.append(el("p", "err", "FSRS library failed to load.")); return; }
    if (deckView === null) {
      deckList(box);
      const more = el("details", "anki-more"); more.append(el("summary", null, T.settings));
      more.append(ankiPanel(), schedRow(), dailyRow()); box.append(more);
      return;
    }
    const q = queue(deckView), st = srs();
    const top = el("div", "row"); top.style.justifyContent = "space-between";
    const back = el("button", "btn small", T.decks); back.onclick = () => { deckView = null; render(); };
    const counts = el("span", "counts");
    counts.append(el("span", "n new", String(q.fresh.length)), el("span", "n learn", String(q.learning)), el("span", "n due", String(q.reviews)));
    top.append(back, el("b", null, deckView.split("::").pop()), counts); box.append(top);
    // same card, maybe edited; live: a card being answered stays even if a fresh prediction moved it
    const same = current && ([...q.due, ...q.fresh].find((x) => x.id === current.id) || (liveMode() ? allCards().find((x) => x.id === current.id) : null));
    if (same) current = same; else { current = q.due.find((c) => !q.ahead.has(c)) || q.fresh[0] || q.due[0] || null; revealed = false; }
    if (!current) {
      const d = el("div", "empty"); d.append(el("b", null, T.done), el("span", null, T.doneBody));
      if (q.waiting) d.append(el("span", null, T.waiting(q.waiting)));
      const pending = snapFor("player") ? Object.values(rw.snap.learn) : Object.values(st.cards).map((x) => new Date(x.due).getTime());
      const next = pending.filter((t) => t > Date.now()).sort((a, b) => a - b)[0];
      clearTimeout(rw.wake);   // come back by itself when the next card is due (or a waiting card may return)
      if (next || q.waiting) rw.wake = setTimeout(() => { if (document.body.classList.contains("review-mode")) render(); }, Math.min(60000, Math.max(5000, (next || Date.now() + 30000) - Date.now() + 500)));
      if (next) d.append(el("span", null, `${T.nextIn}: ${new Date(next).toLocaleString()}`));
      if (LVP.session) { const go = el("button", "btn primary", LVP.L.sessionNext); go.onclick = () => LVP.continueSession(); d.append(go); }
      const toDecks = el("button", "btn", T.decks); toDecks.onclick = () => { deckView = null; render(); }; d.append(toDecks);
      box.append(d);
    } else studyCard(box, current, st);
  }
  // one card on screen; st = the player's own schedule (null when Anki schedules)
  function studyCard(box, c, st) {
    if (shown.id !== c.id) shown = { id: c.id, at: Date.now() };
    {
      const f = el("div", "flash");
      f.dataset.card = c.id;
      const head = el("div", "hint"); head.textContent = (c.deck || "") + (c.id.startsWith("m-") ? ` · ${T.mine}` : ""); f.append(head);
      const front = face(c, false); front.className = "front"; f.append(front);
      if (!revealed) {
        const b = el("button", "btn primary", T.show + "  (Space)"); b.onclick = () => { revealed = true; render(); }; f.append(b);
        setTimeout(() => b.focus({ preventScroll: true }), 30);
      } else {
        if (!c.cloze) { const back = face(c, true); back.className = "back"; f.append(back); } else { front.replaceWith(Object.assign(face(c, true), { className: "front" })); }
        if (c.extra) f.append(el("div", "extra", plain(c.extra)));
        const acts = el("div", "row");
        if (c.video != null && c.t != null) { const w = el("button", "btn small", `${T.watch} ${fmt(c.t)}`); w.onclick = () => LVP.seek(c.video, Math.max(0, c.t - 3)); acts.append(w); }
        if (LVP.sample()) { const y = el("button", "btn small", T.why); y.onclick = () => whyCard(c); acts.append(y); }
        if (LVP.sample()) { const e2 = el("button", "btn small", T.edit); e2.onclick = () => { if (!f.querySelector(".verdict")) f.insertBefore(editBox(c, f), acts.nextSibling); }; acts.append(e2); }
        const del = el("button", "btn small", T.del);
        del.onclick = () => { if (del.dataset.sure) deleteCard(c); else { del.dataset.sure = "1"; del.textContent = T.delSure; } };
        acts.append(del);
        f.append(acts);
        const rates = el("div", "rates");
        const now = new Date(), card0 = st && (st.cards[c.id] ? reviveCard(st.cards[c.id]) : F.createEmptyCard(now));
        const meta = useRwkv() && rwMeta(c), prev = st && !meta ? fsrs.repeat(card0, now) : null, smalls = [];
        [["again", 1], ["hard", 2], ["good", 3], ["easy", 4]].forEach(([k, g]) => {
          const sm = el("small", null, prev ? span(prev[g].card.due - now) : ""); smalls.push(sm); if (meta) sm.title = T.curveTip;
          const b = el("button", k); b.append(el("span", null, `${g} · ${T[k]}`), sm);
          b.onclick = () => rate(c, g); rates.append(b);
        });
        if (meta) {
          const { card, note, deck, preset } = meta, state = c.cardId ? (c.ankiType ?? 2) : (st?.cards[c.id]?.state ?? 0);
          rwCall({ type: "preview", card: { card, note, deck, preset, state }, now: Date.now(), target: target() })
            .then((ms) => { rw.previews[card] = ms; smalls.forEach((x, i) => { x.textContent = span(Math.max(60000, ms[i])); }); }).catch(() => {});
        }
        f.append(rates);
      }
      box.append(f);
    }
  }
  function dailyRow() {
    const set = settings(), row = el("label", "switch");
    const inp = el("input"); inp.type = "number"; inp.min = "0"; inp.max = "200"; inp.value = String(set.newPerDay); inp.style.width = "64px"; inp.id = "new-per-day";
    inp.onchange = () => { set.newPerDay = Math.max(0, Number(inp.value) || 0); store.set("review-settings", set, true); render(); LVP.updateDue(); };
    row.append(document.createTextNode(T.dailyNew + " "), inp); return row;
  }
  // Anki's keys: Space/Enter shows the answer, then Space/Enter = Good; 1–4 rate
  document.addEventListener("keydown", (e) => {
    if (!document.body.classList.contains("review-mode") || deckView === null || !current) return;
    if (e.target.matches("textarea, input, select") || e.ctrlKey || e.metaKey || e.altKey) return;
    if (e.key === " " || e.key === "Enter") { e.preventDefault(); e.stopImmediatePropagation(); if (!revealed) { revealed = true; render(); } else rate(current, 3); }
    else if (revealed && ["1", "2", "3", "4"].includes(e.key)) { e.preventDefault(); e.stopImmediatePropagation(); rate(current, Number(e.key)); }
  }, true);
  const span = (ms) => { if (!Number.isFinite(ms)) return "–"; const m = ms / 60000; if (m < 60) return `${Math.max(1, Math.round(m))} min`; const h = m / 60; if (h < 24) return `${Math.round(h)} h`; const d = h / 24; return d < 30 ? `${Math.round(d)} d` : `${(d / 30).toFixed(1)} mo`; };
  // a stored state the scheduler can work with (repairs states without stability, e.g. old imports)
  const reviveCard = (s) => {
    const c = { ...s, due: new Date(s.due), last_review: s.last_review ? new Date(s.last_review) : undefined };
    if (c.state !== 0 && !(c.stability > 0)) c.stability = Math.max(1, c.scheduled_days || 1);
    if (c.state !== 0 && !(c.difficulty >= 1)) c.difficulty = 5;
    if (c.state !== 0 && !c.last_review) c.last_review = new Date(c.due.getTime() - c.stability * 864e5);
    return c;
  };
  // Anki's view of a card → an FSRS state: interval ≈ stability (at 90 % retention), ease → difficulty
  function fromAnki(ci, isDue) {
    const now = Date.now(), ivl = Math.max(1, ci.interval || 1);
    const ease = (ci.factor || 2500) / 1000;
    const learning = ci.type === 1 || ci.type === 3;
    const stability = learning ? 1 : ivl;
    const due = isDue ? now : now + Math.max(1, ivl / 2) * 864e5;
    return {
      state: ci.type === 3 ? 3 : learning ? 1 : 2, stability,
      difficulty: Math.min(10, Math.max(1, 11 - (ease - 1.3) * 5)),
      reps: ci.reps || 1, lapses: ci.lapses || 0, learning_steps: 0,
      elapsed_days: 0, scheduled_days: learning ? 0 : ivl,
      due: new Date(due).toISOString(), last_review: new Date(due - stability * 864e5).toISOString(),
    };
  }
  function rate(c, grade) {
    if (ankiLive() && c.cardId) return rateAnki(c, grade);
    const st = srs(), now = new Date();
    const wasNew = !st.cards[c.id] || st.cards[c.id].state === 0, before = st.cards[c.id]?.state ?? 0;
    const ms = Math.min(60000, Date.now() - shown.at), meta = useRwkv() && rwMeta(c);
    const res = fsrs.next(st.cards[c.id] ? reviveCard(st.cards[c.id]) : F.createEmptyCard(now), now, grade);
    st.cards[c.id] = { ...res.card, due: res.card.due.toISOString(), last_review: res.card.last_review ? new Date(res.card.last_review).toISOString() : now.toISOString() };
    if (wasNew) st.newDays[today()] = (st.newDays[today()] || 0) + 1;
    st.log.push({ id: c.id, g: grade, at: now.toISOString(), sent: false, ms, st: before });
    if (snapFor("player")) rwAnswered(c.id, grade, before);
    rwNoteAnswer(c.id);
    if (meta) rwFeed(meta, grade, ms, before).catch(() => {});
    if (focusIds?.has(c.id)) { focusIds.delete(c.id); if (!focusIds.size) focusIds = null; }
    if (st.log.length > 3000) st.log = st.log.slice(-3000);
    store.set("srs", st);
    current = null; revealed = false;
    render(); LVP.updateDue();
    if (anki.ok) anki.flush().then(render);   // connected: every review goes to Anki right away
  }
  async function whyCard(c) {
    LVP.selectTab("ask");
    if (c.video && LVP.cur()?.id !== c.video) LVP.openVideo(c.video, c.t ?? 0);
    else if (c.t != null) LVP.seek(c.video, c.t);
    const text = c.cloze ? plain(c.cloze).replace(/\{\{c\d+::([^}]*?)(::[^}]*)?\}\}/g, "$1") : `${plain(c.front)} → ${plain(c.back)}`;
    setTimeout(() => LVP.ask(`${T.explainMiss}\n\n${text}`), 400);
  }

  /* --- Anki through AnkiConnect (desktop app only) --- */
  const anki = {
    desktop: null, ok: false, status: "", map: {}, mapped: 0,
    mode: () => anki.ok && settings().ankiMode,
    async call(action, params = {}) {
      const cp = anki.desktop?.childProcess; if (!cp) throw new Error("no desktop");
      const body = JSON.stringify({ action, version: 6, params });
      const r = await cp.exec("curl -s -m 20 -X POST http://127.0.0.1:8765 --data-binary @-", { input: body, timeout: 25000 });
      if (r.code !== 0 || !r.stdout) throw new Error("anki not reachable");
      const j = JSON.parse(r.stdout);
      if (j.error) throw new Error(j.error);
      return j.result;
    },
    async connect() {
      anki.status = T.ankiChecking; render();
      try {
        await anki.call("version"); anki.ok = true; anki.status = T.ankiOn;
        if (!settings().ankiWanted) { const s = settings(); s.ankiWanted = true; store.set("review-settings", s, true); }
        await anki.match(); await anki.flush();
        if (settings().ankiMode) await anki.pull().catch(() => {});
        if (links().done) anki.link(null, true).then((n) => { if (n) { anki.status = `${T.ankiOn} · ${n} ${T.linkedNew}`; render(); LVP.updateDue(); } }).catch(() => {});
      } catch { anki.ok = false; anki.status = T.ankiNo; }
      render();
    },
    async match() {
      const decks = [...new Set(allCards().map((c) => c.deck).filter(Boolean))];
      const byText = {};
      for (const c of allCards()) byText[norm(c.front || c.cloze)] = c.id;
      anki.map = {};
      for (const d of decks) {
        const ids = await anki.call("findNotes", { query: `"deck:${d.replace(/"/g, "")}"` }).catch(() => []);
        for (let i = 0; i < ids.length; i += 200) {
          const info = await anki.call("notesInfo", { notes: ids.slice(i, i + 200) });
          for (const n of info) {
            const first = Object.values(n.fields || {}).sort((a, b) => a.order - b.order)[0]?.value;
            const id = byText[norm(first)];
            if (id && n.cards?.length) anki.map[id] = n.cards;
          }
        }
      }
      for (const [nid, n] of Object.entries(links().notes)) if (n.cards?.length) anki.map["a-" + nid] = n.cards;
      anki.mapped = Object.keys(anki.map).length;
    },
    async flush() {
      if (!anki.ok) return;
      const st = srs(), latest = {};
      for (const e of st.log) if (!e.sent && anki.map[e.id]) latest[e.id] = e;
      const answers = Object.values(latest).map((e) => ({ cardId: anki.map[e.id][0], ease: e.g }));
      if (!answers.length) return;
      try {
        await anki.call("answerCards", { answers });
        for (const e of st.log) if (anki.map[e.id]) e.sent = true;
        store.set("srs", st, true);
      } catch { /* keep them for the next try */ }
    },
    async pull() {
      // Anki is the schedule: copy due dates of matched cards into the player
      const st = srs(); const ids = Object.values(anki.map).map((x) => x[0]);
      for (let i = 0; i < ids.length; i += 200) {
        const info = await anki.call("cardsInfo", { cards: ids.slice(i, i + 200) });
        const due = await anki.call("areDue", { cards: ids.slice(i, i + 200) });
        info.forEach((ci, k) => {
          const id = Object.keys(anki.map).find((x) => anki.map[x][0] === ci.cardId); if (!id) return;
          if (ci.type === 0) return; // new in Anki: the player's own unlocking decides
          st.cards[id] = fromAnki(ci, !!due[k]);
        });
      }
      store.set("srs", st, true);
    },
    async push() {
      const models = await anki.call("modelNames");
      const pick = (want) => models.find((m) => want.some((w) => m.toLowerCase().includes(w)));
      const basic = pick(["lvp basic", "kk basic", "basic", "einfach"]) || models[0];
      const cloze = pick(["lvp cloze", "kk cloze", "cloze", "lückentext"]);
      let added = 0;
      for (const [deck, cards] of Object.entries(groupBy(allCards().filter((c) => !anki.map[c.id]), (c) => c.deck))) {
        await anki.call("createDeck", { deck }).catch(() => {});
        for (const kind of ["basic", "cloze"]) {
          const model = kind === "cloze" ? cloze : basic; if (!model) continue;
          const fields = await anki.call("modelFieldNames", { modelName: model });
          const notes = cards.filter((c) => (kind === "cloze") === !!c.cloze).map((c) => ({
            deckName: deck, modelName: model, tags: (c.tags || []).map((t) => String(t).replace(/\s+/g, "_")),
            fields: kind === "cloze" ? { [fields[0]]: c.cloze, ...(fields[1] && c.extra ? { [fields[1]]: c.extra } : {}) }
              : { [fields[0]]: c.front, [fields[1]]: c.back, ...(fields[2] && c.extra ? { [fields[2]]: c.extra } : {}) },
            options: { allowDuplicate: false },
          }));
          if (!notes.length) continue;
          const res = await anki.call("addNotes", { notes }).catch(() => []);
          added += (res || []).filter(Boolean).length;
        }
      }
      await anki.match();
      return added;
    },
  };
  const groupBy = (xs, f) => xs.reduce((m, x) => ((m[f(x)] ||= []).push(x), m), {});

  /* Claude links the learner's existing Anki notes to the videos: it picks the decks that belong
     to the course, then assigns each note a video and chapter; the exact moment comes from the
     narration of that chapter. Already checked notes are skipped, so later runs only see new ones. */
  const words = (t) => new Set((String(t).toLowerCase().match(/[\p{L}\p{N}]{4,}/gu) || []));
  function bestMoment(video, chapterT, text) {
    const v = course.videos.find((x) => x.id === video); if (!v) return null;
    const ch = v.chapters.filter((c) => c.t <= (chapterT ?? -1) + 0.5).pop();
    const next = ch ? v.chapters.find((c) => c.t > ch.t) : null;
    const lines = v.lines.filter((l) => !ch || (l.t >= ch.t && (!next || l.t < next.t)));
    const want = words(text);
    let best = null, score = 0;
    for (const l of lines) { let n = 0; for (const w of words(l.text)) if (want.has(w)) n++; if (n > score) { score = n; best = l; } }
    return best ? best.t : (ch ? ch.t : 0);
  }
  anki.link = async (onProgress, quiet = false) => {
    const sample = LVP.sample(); if (!sample || !anki.ok) return 0;
    const L = links(), checked = new Set(L.checked);
    const index = course.videos.map((v) => `${v.id}: ${LVP.videoLabel(v)}\n` + v.chapters.map((c) => `  ${fmt(c.t)} ${c.title}`).join("\n")).join("\n");
    let decks = await anki.call("deckNames");
    if (!L.decks || (L.allDecks || []).join("|") !== decks.join("|")) {   // ask again when decks change
      const r = await sample.json([
        `Which of these Anki decks contain flashcards about the topics of the course "${course.title}"? Videos of the course:`,
        index, "", "Decks:", decks.map((d) => "- " + d).join("\n"),
        'Reply with only JSON: {"decks": ["exact deck name", ...]} – include a parent deck only if its own cards belong; [] if none.',
      ].join("\n"), LVP.m("link", { cache: false }));
      L.decks = (r.decks || []).filter((d) => decks.includes(d)); L.allDecks = decks;
      store.set("anki-links", L, true);
    }
    const inCourse = new Set(Object.values(anki.map).flat());
    const notes = [];
    let viaCourse = 0;
    for (const d of L.decks) {
      const ids = await anki.call("findNotes", { query: `"deck:${d.replace(/"/g, "")}" -"deck:${d.replace(/"/g, "")}::*"` }).catch(() => []);
      const todo = ids.filter((id) => !checked.has(id));
      for (let i = 0; i < todo.length; i += 200) {
        for (const n of await anki.call("notesInfo", { notes: todo.slice(i, i + 200) })) {
          if ((n.cards || []).some((c) => inCourse.has(c))) { checked.add(n.noteId); viaCourse++; continue; }   // a course card: linked already
          const f = Object.values(n.fields || {}).sort((a, b) => a.order - b.order).map((x) => x.value);
          const isCloze = /\{\{c\d+::/.test(f[0] || "");
          notes.push({ id: n.noteId, deck: d, cards: n.cards, tags: n.tags || [], front: isCloze ? null : plain(f[0]), back: isCloze ? null : plain(f[1]), cloze: isCloze ? plain(f[0]) : null, extra: isCloze ? plain(f[1]) : plain(f[2]) });
        }
      }
    }
    let linked = 0;
    for (let i = 0; i < notes.length; i += 30) {
      const batch = notes.slice(i, i + 30);
      onProgress?.(i, notes.length);
      try {
        const r = await sample.json([
          `Link flashcards to the video of the course "${course.title}" that teaches them. Videos and their chapters (m:ss title):`,
          index, "",
          "Cards:", batch.map((n, k) => `${k}. ${(n.cloze || (n.front + " → " + n.back)).slice(0, 300)}`).join("\n"), "",
          'Reply with only JSON: {"links": [{"n": card number, "video": "video id" | null, "chapter": "m:ss" | null}]} – null when no video teaches it.',
        ].join("\n"), LVP.m("link", { cache: false }));
        for (const x of r.links || []) {
          const n = batch[Number(x.n)]; if (!n) continue;
          const v = course.videos.find((y) => y.id === x.video);
          if (v) {
            L.notes[n.id] = { video: v.id, t: bestMoment(v.id, LVP.parseTs(x.chapter), n.cloze || n.front + " " + n.back), deck: n.deck, cards: n.cards, tags: n.tags, front: n.front, back: n.back, cloze: n.cloze, extra: n.extra };
            anki.map["a-" + n.id] = n.cards; linked++;
          }
        }
        for (const n of batch) checked.add(n.id);
      } catch (e) { if (!quiet) throw e; break; }
      L.checked = [...checked]; L.done = true; store.set("anki-links", L, true);
    }
    L.checked = [...checked]; L.done = true; store.set("anki-links", L, true);
    anki.mapped = Object.keys(anki.map).length;
    if (settings().ankiMode) await anki.pull().catch(() => {});
    anki.linkReport = { decks: L.decks.length, viaCourse: viaCourse + Object.values(anki.map).filter(() => false).length, linked, total: Object.keys(L.notes).length };
    return linked;
  };
  function ankiPanel() {
    const box = el("div", "anki"); box.append(el("b", null, T.ankiTitle));
    if (!anki.desktop?.childProcess) {
      box.append(el("span", "hint", T.ankiOff));
      anki.desktop?.install?.state?.().then((s) => { if (s === "available") { const b = el("button", "btn small", T.install); b.onclick = () => anki.desktop.install.request().catch(() => {}); box.append(b); } }).catch(() => {});
      return box;
    }
    if (anki.status) box.append(el("span", "state", anki.status));
    if (!anki.ok) { const b = el("button", "btn small", T.ankiConnect); b.onclick = () => anki.connect(); box.append(b); return box; }
    const pending = srs().log.filter((e) => !e.sent && anki.map[e.id]).length;
    box.append(el("span", "hint", `${anki.mapped}/${allCards().length} ${T.ankiMapped}` + (pending ? ` · ${pending} ${T.ankiPending}` : "")));
    const lab = el("label", "switch"); const cb = el("input"); cb.type = "checkbox"; cb.checked = !!settings().ankiMode; cb.id = "anki-mode";
    cb.onchange = async () => { const s = settings(); s.ankiMode = cb.checked; store.set("review-settings", s, true); if (cb.checked) { await anki.pull().catch(() => {}); } render(); LVP.updateDue(); };
    lab.append(cb, document.createTextNode(" " + T.ankiMode)); box.append(lab);
    const r = el("div", "row");
    const sync = el("button", "btn small", T.ankiSync); sync.onclick = async () => { sync.disabled = true; await anki.flush(); await anki.call("sync").catch(() => {}); if (settings().ankiMode) await anki.pull().catch(() => {}); sync.disabled = false; render(); LVP.updateDue(); };
    const push = el("button", "btn small", T.ankiPush); push.onclick = async () => { push.disabled = true; const n = await anki.push().catch(() => 0); anki.status = `${T.ankiOn} · ${n} ${T.ankiPushed}`; render(); };
    r.append(sync, push); box.append(r);
    if (LVP.sample()) {
      const n = Object.keys(links().notes).length;
      const lk = el("button", "btn small", n ? `${T.linkAgain} (${n} ${T.linked})` : T.link);
      lk.onclick = async () => {
        lk.disabled = true;
        try {
          const got = await anki.link((i, total) => { lk.textContent = `${T.linking} ${i}/${total}`; });
          const r = anki.linkReport || {};
          anki.status = T.linkReport(r.decks || 0, anki.mapped, got);
        } catch (e) { anki.status = LVP.errText(e); }
        render(); LVP.updateDue();
      };
      box.append(lk, el("span", "hint", T.linkHint));
    }
    return box;
  }

  LVP.panels.review = render;
  LVP.hooks.ready.push(async (c, fromAccount) => {
    course = c; T = S[(c.language || "en").slice(0, 2)] || S.en;
    buildQuizCards();
    let repaired = 0;
    for (const [id, s] of Object.entries(srs().cards)) {
      if (s.state !== 0 && !(s.stability > 0 && s.difficulty >= 1)) {
        const r = reviveCard(s);
        srs().cards[id] = { ...s, stability: r.stability, difficulty: r.difficulty, last_review: r.last_review.toISOString() };
        repaired++;
      }
    }
    if (repaired) store.set("srs", srs(), true);
    if (F && !fsrs) fsrs = F.fsrs(F.generatorParameters({ request_retention: 0.9, enable_fuzz: true }));
    LVP.updateDue();
    if (fromAccount) { if (anki.desktop?.childProcess && !anki.ok && settings().ankiWanted) anki.connect(); LVP.updateDue(); return; }
    if (anki.desktop !== null) return;
    anki.desktop = (await LVP.use("desktop")) || false;
    if (anki.desktop?.childProcess) {
      const st = await anki.desktop.permissions?.state?.("full-access").catch(() => null);
      // connected once: reconnect on every load (the app may ask for the permission again after an update)
      if (st === "granted" || settings().ankiWanted) anki.connect();
      const n = LVP.review.dueCount();
      const nst = await anki.desktop.permissions?.state?.("notifications").catch(() => null);
      if (n && nst === "granted") anki.desktop.notification?.show?.({ body: `${c.title}: ${n} ${T.notify}` }).catch(() => {});
    }
  });
  LVP.hooks.tick.push(() => { /* cheap: unlocking happens via progress; refresh the pill now and then */ });
  setInterval(() => LVP.updateDue?.(), 30000);
})();
