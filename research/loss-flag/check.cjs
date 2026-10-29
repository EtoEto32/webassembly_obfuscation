const fs = require('node:fs'), path = require('node:path');
const dir = process.argv[2], manifest = JSON.parse(fs.readFileSync(path.join(dir, 'manifest.json')));
let rng = 0x6221001;
function next() { rng ^= rng << 13; rng ^= rng >>> 17; rng ^= rng << 5; return rng >>> 0; }
function positions(rows) { return rows.map(row => { let v = BigInt(row), out = []; for (let i = 0; v; i++, v >>= 1n) if (v & 1n) out.push(i); return out; }); }
function apply(rows, x) { return Uint8Array.from(rows, row => row.reduce((a, i) => a ^ x[i], 0)); }
function hash(x) { let h = 2166136261; for (const v of x) h = Math.imul(h ^ v, 16777619) >>> 0; return h; }
function model(x, ops, fail) { for (let j = 0; j < ops.length && (fail >>> 0) !== j; j++) { const [d, s, l] = ops[j]; x.copyWithin(d, s, s + l); } }
const rows = [], negative = [], benchChecks = [];
for (const t of manifest.targets) {
  const bytes = fs.readFileSync(path.join(dir, t.probe));
  if (!WebAssembly.validate(bytes)) throw Error('invalid outer module');
  const e = new WebAssembly.Instance(new WebAssembly.Module(bytes)).exports;
  const n = t.meta.n, b = positions(t.meta.matrix), ops = t.meta.ops;
  const initial = [0, 1, 127, 128, 254, 255].map(v => new Uint8Array(n).fill(v));
  for (let i = 0; i < n; i++) { const v = new Uint8Array(n); v[i] = 255; initial.push(v); }
  for (let j = 0; j < 64; j++) initial.push(Uint8Array.from({length: n}, () => next() & 255));
  const actions = [...ops.map((_, j) => j), ops.length, 0x80000000, 0xffffffff];
  const memory = Buffer.from(e.memory.buffer), expected = Buffer.alloc(65536);
  let calls = 0, traps = 0, mismatches = 0, first = null;
  function reset(x) { memory.fill(0); memory.set(apply(b, x)); }
  function step(x, fail, caseIndex, sequence) {
    model(x, ops, fail); let trap = false;
    try { e.run(fail); } catch (err) { if (!(err instanceof WebAssembly.RuntimeError)) throw err; trap = true; }
    expected.fill(0); expected.set(apply(b, x));
    const observed = e.digest() >>> 0;
    const mismatch = !memory.equals(expected) || observed !== hash(x) || trap !== ((fail >>> 0) < ops.length);
    calls++; traps += Number(trap);
    if (mismatch) { mismatches++; if (!first) first = {caseIndex, sequence, fail, observed, expected: hash(x), trap}; }
    if (t.mode !== 'bad' && mismatch) throw Error(JSON.stringify({file: t.file, first}));
  }
  for (let index = 0; index < initial.length; index++) {
    for (const fail of actions) { const x = initial[index].slice(); reset(x); step(x, fail, index, false); }
    const x = initial[index].slice(); reset(x);
    for (const fail of [...actions, 0xffffffff, 1, 0xffffffff]) step(x, fail, index, true);
  }
  const result = {file: t.file, states: initial.length, calls, traps, mismatches, first};
  if (t.mode === 'bad') { if (!mismatches) throw Error('bad condition had no counterexample'); negative.push(result); }
  else rows.push(result);
  if (t.bench) {
    for (const count of [0, 1, 7, 1024]) {
      const be = new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(dir, t.bench)))).exports;
      const logical = Uint8Array.from(manifest.fixtures[t.name].data);
      for (let i = 0; i < count; i++) model(logical, ops, 0xffffffff);
      const got = be.bench(count) >>> 0;
      if (got !== hash(logical)) throw Error('benchmark result differs');
      benchChecks.push({file: t.bench, count, result: got});
    }
  }
}
const out = {node: process.version, v8: process.versions.v8, rows, negative, benchChecks,
  calls: rows.reduce((a, r) => a + r.calls, 0), traps: rows.reduce((a, r) => a + r.traps, 0),
  note: 'Each call checks digest, trap class and entire 64KiB physical memory. Instrumented memory exports initialize arbitrary logical states; production ABI remains private.'};
fs.writeFileSync(path.join(dir, 'checks.json'), JSON.stringify(out, null, 2));
console.log(JSON.stringify({positive: rows.length, calls: out.calls, traps: out.traps, negative: negative.length, benchChecks: benchChecks.length}));
