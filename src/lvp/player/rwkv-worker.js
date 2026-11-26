/* lvp player – runs the RWKV memory model (rwkv.js) off the main thread.
   Messages: load {events, max}, feed {event}, predict {cards, now}, preview {card, now, target}. */
"use strict";
importScripts("rwkv.js");
let model = null, mem = null;
async function getModel() {
  if (model) return model;
  const [man, buf] = await Promise.all([
    fetch("rwkv_weights.json").then((r) => { if (!r.ok) throw new Error("rwkv_weights.json " + r.status); return r.json(); }),
    fetch("rwkv_weights.wasm").then((r) => { if (!r.ok) throw new Error("rwkv_weights.wasm " + r.status); return r.arrayBuffer(); }),
  ]);
  return (model = new self.LVP_RWKV.Model(man, buf));
}
self.onmessage = async ({ data: m }) => {
  const reply = (result) => self.postMessage({ id: m.id, result });
  try {
    if (m.type === "load") {
      mem = new self.LVP_RWKV.Memory(await getModel());
      const ev = m.events, cut = Math.max(0, ev.length - (m.max || 20000));
      for (let i = 0; i < ev.length; i++) {
        mem.feed(ev[i], i >= cut);
        if (i % 100 === 0) self.postMessage({ id: m.id, progress: i / ev.length });
      }
      reply({ n: ev.length, replayed: ev.length - cut });
    } else if (m.type === "feed") { mem.feed(m.event); reply(true); }
    else if (m.type === "predict") {
      const out = {};
      for (const c of m.cards) { const p = mem.predict(c, m.now); if (p != null) out[c.card] = p; }
      reply(out);
    } else if (m.type === "preview") reply(mem.preview(m.card, m.now, m.target));
  } catch (e) { self.postMessage({ id: m.id, error: String(e?.message || e) }); }
};
