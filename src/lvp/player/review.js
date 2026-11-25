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
      ankiMode: "Review with Anki's schedule", ankiSync: "Sync AnkiWeb", ankiPush: "Add missing cards to Anki", ankiPushed: "added",
      ankiMapped: "cards matched in Anki", ankiPending: "reviews waiting to go to Anki", ankiSent: "sent", install: "Install as app",
      explainMiss: "I forgot this flashcard. Explain the idea behind it so it sticks – briefly, with a different angle than the card.",
      dailyNew: "New cards per day", notify: "cards are due"
    },
    de: {
      title: "Wiederholen", due: "fällig", newToday: "neu heute", locked: "werden beim Schauen freigeschaltet", total: "Karten",
      show: "Antwort zeigen", again: "Nochmal", hard: "Schwer", good: "Gut", easy: "Leicht", watch: "Stelle im Video",
      why: "Warum? Claude fragen", done: "Für jetzt erledigt.", doneBody: "Neue Karten werden frei, sobald du die Stelle im Video erreichst, die sie erklärt.",
      nextIn: "Nächste Karte fällig", mine: "eigene", ankiTitle: "Anki", ankiOff: "Um direkt in Anki zu wiederholen: den Player in der Claude-Desktop-App als App installieren (Artefakt-Menü → Als App installieren), Anki mit dem Add-on AnkiConnect geöffnet.",
      ankiConnect: "Mit Anki verbinden", ankiChecking: "Suche Anki …", ankiOn: "Mit Anki verbunden", ankiNo: "Anki antwortet nicht. Starte Anki mit dem Add-on AnkiConnect (Code 2055492159).",
      ankiMode: "Mit Ankis Zeitplan wiederholen", ankiSync: "AnkiWeb synchronisieren", ankiPush: "Fehlende Karten zu Anki hinzufügen", ankiPushed: "hinzugefügt",
      ankiMapped: "Karten in Anki gefunden", ankiPending: "Wiederholungen warten auf Anki", ankiSent: "übertragen", install: "Als App installieren",
      explainMiss: "Ich habe diese Karteikarte vergessen. Erklär die Idee dahinter so, dass sie hängen bleibt – kurz und aus einem anderen Blickwinkel als die Karte.",
      dailyNew: "Neue Karten pro Tag", notify: "Karten sind fällig"
    }
  };
  let T = S.en, course = null, fsrs = null, current = null, revealed = false;
  const F = window.FSRS;
  const store = LVP.store;
  const srs = () => { const s = store.get("srs"); if (s) { s.cards ||= {}; s.log ||= []; s.newDays ||= {}; return s; } store.data.srs = { _key: "srs", cards: {}, log: [], newDays: {} }; return store.data.srs; };
  const mine = () => { const m = store.get("mine"); if (m) { m.cards ||= []; return m; } store.data.mine = { _key: "mine", cards: [] }; return store.data.mine; };
  const settings = () => store.get("review-settings") || { _key: "review-settings", newPerDay: 20, ankiMode: false };
  const today = () => new Date().toISOString().slice(0, 10);
  const allCards = () => [...(course?.cards || []), ...mine().cards];
  const plain = (s) => String(s || "").replace(/<[^>]+>/g, " ").replace(/&nbsp;/g, " ").replace(/\s+/g, " ").trim();
  const norm = (s) => plain(s).toLowerCase().replace(/\{\{c\d+::([^}]*?)(::[^}]*)?\}\}/g, "$1").replace(/[^\p{L}\p{N}]+/gu, "").slice(0, 60);

  const unlocked = (c) => {
    if (!c.video) return true;
    const v = course.videos.find((x) => x.id === c.video); if (!v) return true;
    const reached = LVP.store.get("p-" + c.video)?.furthest || 0;
    return reached >= (c.t != null ? c.t + 5 : v.duration * 0.9);
  };
  function queue() {
    const st = srs().cards, now = Date.now(), due = [], fresh = [];
    let locked = 0;
    for (const c of allCards()) {
      const s = st[c.id];
      if (s && s.state !== 0) { if (new Date(s.due).getTime() <= now) due.push(c); }
      else if (unlocked(c)) fresh.push(c); else locked++;
    }
    due.sort((a, b) => new Date(st[a.id].due) - new Date(st[b.id].due));
    const left = Math.max(0, settings().newPerDay - (srs().newDays[today()] || 0));
    return { due, fresh: fresh.slice(0, left), locked, freshAll: fresh.length };
  }
  LVP.review = {
    dueCount: () => { if (!course || !F) return 0; const q = queue(); return q.due.length + q.fresh.length; },
    struggles: () => allCards().filter((c) => (srs().cards[c.id]?.lapses || 0) > 0).sort((a, b) => srs().cards[b.id].lapses - srs().cards[a.id].lapses).map((c) => plain(c.front || c.cloze).slice(0, 120)),
    addCard: (c) => { const id = "m-" + Date.now().toString(36); mine().cards.push({ id, deck: (course.title || "Course") + "::Mine", tags: ["mine"], ...c }); store.set("mine", mine(), true); LVP.updateDue(); },
  };
  LVP.updateDue = () => {
    const n = LVP.review.dueCount(), pill = $("due-pill");
    pill.hidden = !n; pill.textContent = `${n} ${T.due}`; pill.onclick = () => LVP.selectTab("review");
    const tab = $("tabs").querySelector('[data-panel="review"]');
    if (tab) { tab.textContent = LVP.L.tabs.review; if (n) tab.append(el("span", "count", String(n))); }
  };

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
  function render() {
    const box = $("review"); if (!box) return; box.textContent = "";
    if (!F) { box.append(el("p", "err", "FSRS library failed to load.")); return; }
    const q = queue(), st = srs();
    const stats = el("div", "stats");
    const s = (n, label) => { const x = el("span"); x.append(el("b", null, String(n)), document.createTextNode(" " + label)); stats.append(x); };
    s(q.due.length, T.due); s(q.fresh.length, T.newToday); s(q.locked, T.locked); s(allCards().length, T.total);
    box.append(stats);
    if (!current || !(q.due.includes(current) || q.fresh.includes(current))) { current = q.due[0] || q.fresh[0] || null; revealed = false; }
    if (!current) {
      const d = el("div", "empty"); d.append(el("b", null, T.done), el("span", null, T.doneBody));
      const next = Object.values(st.cards).map((x) => new Date(x.due).getTime()).filter((t) => t > Date.now()).sort((a, b) => a - b)[0];
      if (next) d.append(el("span", null, `${T.nextIn}: ${new Date(next).toLocaleString()}`));
      box.append(d);
    } else {
      const c = current, f = el("div", "flash");
      const head = el("div", "hint"); head.textContent = (c.deck || "") + (c.id.startsWith("m-") ? ` · ${T.mine}` : ""); f.append(head);
      const front = face(c, false); front.className = "front"; f.append(front);
      if (!revealed) {
        const b = el("button", "btn primary", T.show); b.onclick = () => { revealed = true; render(); }; f.append(b);
        setTimeout(() => b.focus({ preventScroll: true }), 30);
      } else {
        if (!c.cloze) { const back = face(c, true); back.className = "back"; f.append(back); } else { front.replaceWith(Object.assign(face(c, true), { className: "front" })); }
        if (c.extra) f.append(el("div", "extra", plain(c.extra)));
        const acts = el("div", "row");
        if (c.video != null && c.t != null) { const w = el("button", "btn small", `▶ ${T.watch} ${fmt(c.t)}`); w.onclick = () => LVP.seek(c.video, Math.max(0, c.t - 3)); acts.append(w); }
        if (LVP.sample()) { const y = el("button", "btn small", T.why); y.onclick = () => whyCard(c); acts.append(y); }
        f.append(acts);
        const rates = el("div", "rates");
        const now = new Date(), card0 = st.cards[c.id] ? reviveCard(st.cards[c.id]) : F.createEmptyCard(now);
        const prev = fsrs.repeat(card0, now);
        [["again", 1], ["hard", 2], ["good", 3], ["easy", 4]].forEach(([k, g]) => {
          const b = el("button", k); b.append(el("span", null, T[k]), el("small", null, span(prev[g].card.due - now)));
          b.onclick = () => rate(c, g); rates.append(b);
        });
        f.append(rates);
      }
      box.append(f);
    }
    box.append(ankiPanel());
    const set = settings(), row = el("label", "switch");
    const inp = el("input"); inp.type = "number"; inp.min = "0"; inp.max = "200"; inp.value = String(set.newPerDay); inp.style.width = "64px"; inp.id = "new-per-day";
    inp.onchange = () => { set.newPerDay = Math.max(0, Number(inp.value) || 0); store.set("review-settings", set, true); render(); LVP.updateDue(); };
    row.append(document.createTextNode(T.dailyNew + " "), inp); box.append(row);
  }
  const span = (ms) => { const m = ms / 60000; if (m < 60) return `${Math.max(1, Math.round(m))} min`; const h = m / 60; if (h < 24) return `${Math.round(h)} h`; const d = h / 24; return d < 30 ? `${Math.round(d)} d` : `${(d / 30).toFixed(1)} mo`; };
  const reviveCard = (s) => ({ ...s, due: new Date(s.due), last_review: s.last_review ? new Date(s.last_review) : undefined });
  function rate(c, grade) {
    const st = srs(), now = new Date();
    const wasNew = !st.cards[c.id] || st.cards[c.id].state === 0;
    const res = fsrs.next(st.cards[c.id] ? reviveCard(st.cards[c.id]) : F.createEmptyCard(now), now, grade);
    st.cards[c.id] = { ...res.card, due: res.card.due.toISOString(), last_review: res.card.last_review ? new Date(res.card.last_review).toISOString() : now.toISOString() };
    if (wasNew) st.newDays[today()] = (st.newDays[today()] || 0) + 1;
    st.log.push({ id: c.id, g: grade, at: now.toISOString(), sent: false });
    if (st.log.length > 3000) st.log = st.log.slice(-3000);
    store.set("srs", st);
    current = null; revealed = false;
    render(); LVP.updateDue();
    if (anki.mode()) anki.flush().then(render);
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
        await anki.match(); await anki.flush();
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
          const s = st.cards[id] || { ...F.createEmptyCard(new Date()), due: new Date().toISOString() };
          if (ci.type === 0) return; // new in Anki: the player's own unlocking decides
          s.state = s.state || 2;
          s.due = due[k] ? new Date().toISOString() : new Date(Date.now() + Math.max(1, ci.interval || 1) * 864e5 / 2).toISOString();
          st.cards[id] = s;
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
    return box;
  }

  LVP.panels.review = render;
  LVP.hooks.ready.push(async (c, fromAccount) => {
    course = c; T = S[(c.language || "en").slice(0, 2)] || S.en;
    if (F && !fsrs) fsrs = F.fsrs(F.generatorParameters({ request_retention: 0.9, enable_fuzz: true }));
    LVP.updateDue();
    if (fromAccount || anki.desktop !== null) return;
    anki.desktop = (await LVP.use("desktop")) || false;
    if (anki.desktop?.childProcess) {
      const st = await anki.desktop.permissions?.state?.("full-access").catch(() => null);
      if (st === "granted") anki.connect();
      const n = LVP.review.dueCount();
      const nst = await anki.desktop.permissions?.state?.("notifications").catch(() => null);
      if (n && nst === "granted") anki.desktop.notification.show({ body: `${c.title}: ${n} ${T.notify}` }).catch(() => {});
    }
  });
  LVP.hooks.tick.push(() => { /* cheap: unlocking happens via progress; refresh the pill now and then */ });
  setInterval(() => LVP.updateDue?.(), 30000);
})();
