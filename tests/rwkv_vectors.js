// node tests/rwkv_vectors.js <JSchoreels/anki checkout> [sm118] – prints the max abs error
"use strict";
const fs = require("fs"), zlib = require("zlib"), path = require("path");
const R = require("../src/lvp/player/rwkv.js");
const [fork, pkg = "sm118"] = process.argv.slice(2);
const dir = path.join(fork, "qt/aqt/rwkv_inference", pkg);
const b = fs.readFileSync(path.join(dir, "weights.f32.bin")), dv = new DataView(b.buffer, b.byteOffset, b.length);
if (b.subarray(0, 13).toString() !== "ARWKVWEIGHTS1") throw new Error("not an f32 export");
let o = 13; const n = dv.getUint32(o, true); o += 4; const tensors = [], parts = []; let off = 0;
for (let i = 0; i < n; i++) {
  const L = dv.getUint16(o, true); o += 2; const name = b.subarray(o, o + L).toString(); o += L;
  const r = dv.getUint8(o); o += 1; const shape = []; let len = 1;
  for (let k = 0; k < r; k++) { const d = dv.getUint32(o, true); o += 4; shape.push(d); len *= d; }
  const v = new Float32Array(len); for (let k = 0; k < len; k++) { v[k] = dv.getFloat32(o, true); o += 4; }
  tensors.push({ name, shape, offset: off }); parts.push(v); off += len;
}
const all = new Float32Array(off); off = 0; for (const p of parts) { all.set(p, off); off += p.length; }
const arch = JSON.parse(fs.readFileSync(path.join(dir, "architecture.json")));
const m = new R.Model({ tensors, steps: arch.layer_steps, zero_features: arch.zero_features }, all.buffer);
const vec = JSON.parse(zlib.gunzipSync(fs.readFileSync(path.join(fork, `rslib/src/rwkv/testdata/${pkg}-vectors.json.gz`))));
let max = 0;
for (const u of vec) {
  const st = { card: {}, deck: {}, note: {}, preset: {} }; let glob = null;
  for (const row of u.rows) {
    const [c, d, nn, p] = row.ids;
    const out = m.review(row.features, [st.card[c], st.deck[d], st.note[nn], st.preset[p], glob]);
    const act = [Math.min(1 - 1e-5, Math.max(1e-5, 1 - out.probs[0])), ...out.probs, m.curveP(out.curve, row.elapsed), ...u.sweep.map((e) => m.curveP(out.curve, e))];
    act.forEach((a, i) => { max = Math.max(max, Math.abs(a - row.fp32[i])); });
    if (!row.skip) [st.card[c], st.deck[d], st.note[nn], st.preset[p], glob] = out.next;
  }
}
console.log(pkg, "max abs error", max);
