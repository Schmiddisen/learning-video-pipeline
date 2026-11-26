/* lvp player – things only the installed desktop app can do: render the final videos on this
   PC (finds the project folder, pulls the latest version, runs the render menu without
   questions, shows its progress). */
"use strict";
(() => {
  const LVP = window.LVP, { $, el } = LVP;
  const S = {
    en: {
      title: "Render on this PC", intro: "Renders the final videos on this computer from the recorded narration (never pays). Videos that are already rendered and unchanged are skipped.", redo: "render all again",
      quality: { "4k30": "4K, 30 fps", "4k60": "4K, 60 fps", "1080p": "1080p" }, start: "Render", stop: "Stop", open: "Show the videos",
      finding: "Looking for the project folder…", notFound: "Project folder not found. Paste its path:", use: "Use this folder",
      pulling: "Getting the latest version…", pullFailed: "Could not update automatically – rendering the version on this PC.",
      running: "Rendering – this can take a while; you can keep studying.", done: "Done.", failed: "Stopped with an error – see the log.",
      fromPc: "from this PC", folder: "Project folder:", noGit: "git not found – using the version on this PC.", outdated: "This PC has an old version of the project. In GitHub Desktop: Fetch origin, then Pull origin – then press Render again.",
      install: "Install as app", needApp: "Rendering on your PC works in the installed app (Claude desktop app → artifact menu → Install as app)."
    },
    de: {
      title: "Auf diesem PC rendern", intro: "Rendert die finalen Videos auf diesem Rechner aus der aufgenommenen Sprache (kostet nichts). Schon gerenderte, unveränderte werden übersprungen.", redo: "alle neu rendern",
      quality: { "4k30": "4K, 30 fps", "4k60": "4K, 60 fps", "1080p": "1080p" }, start: "Rendern", stop: "Abbrechen", open: "Videos zeigen",
      finding: "Suche den Projektordner …", notFound: "Projektordner nicht gefunden. Pfad einfügen:", use: "Diesen Ordner nehmen",
      pulling: "Hole die neueste Version …", pullFailed: "Automatisches Aktualisieren ging nicht – rendere die Version auf diesem PC.",
      running: "Rendert – das kann dauern; du kannst weiterlernen.", done: "Fertig.", failed: "Mit Fehler beendet – siehe Protokoll.",
      fromPc: "vom PC", folder: "Projektordner:", noGit: "git nicht gefunden – nehme die Version auf diesem PC.", outdated: "Auf diesem PC liegt eine alte Version des Projekts. In GitHub Desktop: Fetch origin, dann Pull origin – danach noch einmal Rendern.",
      install: "Als App installieren", needApp: "Rendern auf dem PC geht in der installierten App (Claude-Desktop-App → Artefakt-Menü → Als App installieren)."
    }
  };
  let T = S.en, course = null, desk = null, sep = "/", proc = null, log = [], status = "";

  const join = (...p) => p.join(sep);
  async function findRepo() {
    const saved = LVP.store.get("local")?.repo;
    if (saved && await desk.fs.exists(saved).catch(() => false)) return saved;
    const home = await desk.os.homedir();
    const name = course.repo || "";
    for (const base of [["Documents", "GitHub"], ["GitHub"], ["source", "repos"], ["Documents"], ["Desktop"], []]) {
      const dir = join(home, ...base, name);
      if (await desk.fs.exists(join(dir, "pyproject.toml")).catch(() => false)) return dir;
    }
    return null;
  }
  async function gitCommand() {
    // GitHub Desktop ships its own git; use the one on PATH first
    const r = await desk.childProcess.exec("git --version", { timeout: 8000 }).catch(() => null);
    if (r && r.code === 0) return "git";
    if (sep !== "\\") return null;
    const base = join(await desk.os.homedir(), "AppData", "Local", "GitHubDesktop");
    const apps = (await desk.fs.readdir(base).catch(() => [])).filter((e) => /^app-/.test(e.name)).map((e) => e.name).sort();
    if (!apps.length) return null;
    const g = join(base, apps[apps.length - 1], "resources", "app", "git", "cmd", "git.exe");
    return (await desk.fs.exists(g).catch(() => false)) ? `"${g}"` : null;
  }
  function say(text, box) { status = text; render(box); }
  const clean = (t) => String(t || "").split(/\r?\n/).map((l) => l.trim()).filter(Boolean);
  async function start(box, quality, dir, redo) {
    log = [T.folder + " " + dir]; say(T.pulling, box);
    const git = await gitCommand();
    if (!git) log.push(T.noGit);
    else {
      const pull = await desk.childProcess.exec(`${git} pull --ff-only`, { cwd: dir, timeout: 120000 }).catch((e) => ({ code: -1, stderr: String(e && e.message || e) }));
      log.push(...clean(pull.stdout).slice(-3), ...clean(pull.stderr).slice(-3));
      if (pull.code !== 0) log.push(T.pullFailed);
    }
    // the menu must know the options the player passes – an old checkout does not
    const base = course.render || "uv run lvp";
    const help = await desk.childProcess.exec(`${base} --help`, { cwd: dir, timeout: 300000 }).catch((e) => ({ code: -1, stdout: "", stderr: String(e && e.message || e) }));
    if (!/--quality/.test((help.stdout || "") + (help.stderr || ""))) {
      log.push(...clean(help.stderr).slice(-4), T.outdated); proc = null; say(T.failed, box); return;
    }
    say(T.running, box);
    const args = `--quality ${quality}${redo ? " --redo" : ""}`;
    // the normal environment of this PC (PATH etc.), plus unbuffered UTF-8 output
    const cmd = sep === "\\" ? `set PYTHONUNBUFFERED=1&& set PYTHONIOENCODING=utf-8&& ${base} ${args}` : `PYTHONUNBUFFERED=1 PYTHONIOENCODING=utf-8 ${base} ${args}`;
    log.push("> " + base + " " + args);
    proc = desk.childProcess.spawn(cmd, [], { cwd: dir, shell: true });
    const add = (chunk) => { log.push(...clean(chunk)); if (log.length > 400) log = log.slice(-400); render(box); };
    proc.stdout.on("data", add); proc.stderr.on("data", add);
    proc.on("error", (e) => { log.push(String(e && e.message || e)); proc = null; say(T.failed, box); });
    proc.on("exit", (code) => { proc = null; log.push(`exit ${code}`); say(code === 0 ? T.done : T.failed, box); });
  }

  function render(box = $("local-box")) {
    if (!box) return;
    box.textContent = "";
    box.append(el("p", "section-title", T.title));
    if (!desk?.childProcess) {
      box.append(el("p", "hint", T.needApp));
      desk?.install?.state?.().then((s) => { if (s === "available") { const b = el("button", "btn small", T.install); b.onclick = () => desk.install.request().catch(() => {}); box.append(b); } }).catch(() => {});
      return;
    }
    box.append(el("p", "hint", T.intro));
    const row = el("div", "row");
    const sel = el("select"); sel.id = "render-quality";
    for (const [k, v] of Object.entries(T.quality)) { const o = el("option", null, v); o.value = k; sel.append(o); }
    sel.value = LVP.store.get("local")?.quality || "4k30";
    const go = el("button", "btn primary", T.start); go.disabled = !!proc;
    go.onclick = async () => {
      const local = { ...(LVP.store.get("local") || {}), quality: sel.value };
      say(T.finding, box);
      const dir = local.repo && await desk.fs.exists(local.repo).catch(() => false) ? local.repo : await findRepo();
      if (!dir) { askPath(box); return; }
      LVP.store.set("local", { ...local, repo: dir }, true);
      start(box, sel.value, dir, rb.checked);
    };
    const redo = el("label", "switch"); const rb = el("input"); rb.type = "checkbox"; rb.id = "render-redo"; redo.append(rb, document.createTextNode(" " + T.redo));
    row.append(sel, go, redo);
    if (proc) { const k = el("button", "btn", T.stop); k.onclick = () => proc?.kill().catch(() => {}); row.append(k); }
    const repo = LVP.store.get("local")?.repo;
    if (repo) { const o = el("button", "btn", T.open); o.onclick = () => desk.shell.openPath(join(repo, "build", "videos")).catch(() => {}); row.append(o); }
    box.append(row);
    if (status) box.append(el("p", "hint", status));
    if (log.length) { const pre = el("pre", "out", log.slice(-14).join("\n")); box.append(pre); }
  }
  function askPath(box) {
    status = T.notFound; render(box);
    const inp = el("input", "field"); inp.style.minHeight = "0"; inp.placeholder = sep === "\\" ? "C:\\Users\\…\\Documents\\GitHub\\" + (course.repo || "") : "/home/…/" + (course.repo || "");
    const ok = el("button", "btn small", T.use);
    ok.onclick = async () => {
      const dir = inp.value.trim().replace(/[\\/]+$/, "");
      if (dir && await desk.fs.exists(join(dir, "pyproject.toml")).catch(() => false)) {
        LVP.store.set("local", { ...(LVP.store.get("local") || {}), repo: dir }, true); status = ""; render(box);
      }
    };
    const r = el("div", "row"); r.append(inp, ok); box.append(r);
  }

  /* Play the best render on this PC (4K, then 1080p) instead of the 480p copy that ships with the
     player. Same timeline, so questions and moments stay in sync. Falls back on any problem. */
  let objectUrl = null, quality = null;
  async function localSource(v) {
    if (!desk?.fs) return;
    const repo = LVP.store.get("local")?.repo || await findRepo();
    if (!repo) return;
    for (const [q, label] of [["k", "4K"], ["h", "1080p"]]) {
      const f = join(repo, "build", "videos", `${v.id}_${q}.mp4`);
      const st = await desk.fs.stat(f).catch(() => null);
      if (!st || st.size > 3e9) continue;
      const bytes = await desk.fs.readFile(f).catch(() => null);
      if (!bytes || LVP.cur()?.id !== v.id) return;
      const video = LVP.video, t = video.currentTime, wasPlaying = !video.paused, loaded = video.readyState > 0;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
      objectUrl = URL.createObjectURL(new Blob([bytes], { type: "video/mp4" }));
      const fallback = () => { video.removeEventListener("error", fallback); quality = null; showQuality(); video.src = v.file; video.currentTime = t; };
      video.addEventListener("error", fallback, { once: true });
      video.src = objectUrl;
      video.addEventListener("loadedmetadata", () => { if (loaded) video.currentTime = t; if (wasPlaying) video.play().catch(() => {}); video.removeEventListener("error", fallback); }, { once: true });
      quality = label; showQuality();
      return;
    }
  }
  function showQuality() {
    let b = $("quality-badge");
    if (!b) { b = el("span", "hint"); b.id = "quality-badge"; $("time")?.after(b); }
    b.textContent = quality ? `${quality} ${T.fromPc}` : "";
  }

  LVP.local = { render };
  LVP.hooks.open.push((v) => { quality = null; showQuality(); localSource(v).catch(() => {}); });
  LVP.hooks.ready.push(async (c, fromAccount) => {
    if (fromAccount) return;
    course = c; T = S[(c.language || "en").slice(0, 2)] || S.en;
    desk = await LVP.use("desktop");
    if (desk?.os) sep = (await desk.os.platform().catch(() => "")) === "win32" ? "\\" : "/";
    render();
    if (LVP.cur()) localSource(LVP.cur()).catch(() => {});
  });
})();
