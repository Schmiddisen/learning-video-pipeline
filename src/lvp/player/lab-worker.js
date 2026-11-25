/* lvp player – lab sandbox: runs Python (Pyodide, served with the player) or JavaScript
   off the page's thread, so an endless loop can be stopped by ending the worker. */
"use strict";
let py = null;

async function python() {
  if (py) return py;
  importScripts("pyodide/pyodide.js");
  const base = new URL("pyodide/", self.location.href).href;
  // the standard library ships as .wasm: artifact hosting serves no .zip files (bytes are the same)
  py = await self.loadPyodide({ indexURL: base, stdLibURL: base + "python_stdlib.wasm" });
  return py;
}

function runJs(code) {
  const out = [];
  const fmt = (a) => (typeof a === "string" ? a : (() => { try { return JSON.stringify(a); } catch { return String(a); } })());
  const con = { log: (...a) => out.push(a.map(fmt).join(" ")), error: (...a) => out.push(a.map(fmt).join(" ")) };
  con.info = con.warn = con.log;
  const assert = (cond, msg) => { if (!cond) throw new Error("Check failed: " + (msg || "assertion")); };
  try {
    // eslint-disable-next-line no-new-func
    new Function("console", "assert", '"use strict";\n' + code)(con, assert);
    return { out: out.join("\n"), ok: true };
  } catch (e) {
    out.push(String(e && e.message ? e.message : e));
    return { out: out.join("\n"), ok: false };
  }
}

self.onmessage = async (e) => {
  const { id, lang, code, warm } = e.data;
  try {
    if (lang === "python") {
      const p = await python();
      if (warm) { self.postMessage({ id, out: "", ok: true }); return; }
      let out = "";
      p.setStdout({ batched: (s) => { out += s + "\n"; } });
      p.setStderr({ batched: (s) => { out += s + "\n"; } });
      const scope = p.toPy({});
      try {
        await p.runPythonAsync(code, { globals: scope });
        self.postMessage({ id, out, ok: true });
      } catch (err) {
        const msg = String(err && err.message ? err.message : err);
        // keep the learner-relevant tail of the traceback
        const lines = msg.split("\n").filter((l) => !/File "\/lib\/python|_pyodide|pyodide\/|^\s*$/.test(l));
        self.postMessage({ id, out: out + lines.slice(-8).join("\n"), ok: false });
      } finally { scope.destroy(); }
    } else {
      self.postMessage({ id, ...runJs(code) });
    }
  } catch (err) {
    self.postMessage({ id, out: "Runtime could not start: " + String(err && err.message ? err.message : err), ok: false, fatal: true });
  }
};
