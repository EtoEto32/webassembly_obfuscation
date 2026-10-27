'use strict';
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const os = require('os');
const {recover} = require('./attack.cjs');
const dir = path.resolve(process.argv[2]);
const output = path.join(dir, 'checks.json');
if (fs.existsSync(output)) throw Error('Refuse overwrite');
const manifest = JSON.parse(fs.readFileSync(path.join(dir, 'manifest.json')));
let seed = 0x4d613f91;
function rand() {seed ^= seed << 13; seed ^= seed >>> 17; seed ^= seed << 5; return seed >>> 0;}
const hash = p => crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
function reference(t, start, limit) {
  start >>>= 0; limit = (limit >>> 0) & 255;
  if (start >= t.nodes) return {trap: 'unreachable'};
  let p = t.addresses[start], acc = 0;
  for (let i = 0; i < limit && p !== 0; i++) {
    const node = (p - 256) / 16;
    acc = (((acc << 5) | (acc >>> 27)) ^ t.values[node]) | 0;
    p = t.next[node];
  }
  return {value: acc};
}
function call(f, a, b) {
  try { return {value: f(a, b)}; }
  catch (e) {
    if (!(e instanceof WebAssembly.RuntimeError)) throw e;
    return {trap: e.message};
  }
}
function same(a, b) {return JSON.stringify(a) === JSON.stringify(b);}
const rows = [];
let total = 0, mismatches = 0;
for (const r of manifest.rows) {
  const t = manifest.truth[r.family];
  const inputPath = path.join(dir, r.wasm), tracePath = path.join(dir, r.traced);
  if (hash(inputPath) !== r.sha256 || hash(tracePath) !== r.traced_sha256) throw Error('Binary hash mismatch');
  const ordinary = new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(inputPath))).exports.run;
  let events = [], collect = false;
  const audit = {
    before(site, base, offset) {
      if (collect) events.push({kind: 'before', site, address: (base >>> 0) + (offset >>> 0)});
      return base;
    },
    after(site, base, offset, value) {
      if (collect) events.push({kind: 'after', site, address: (base >>> 0) + (offset >>> 0), value: value >>> 0});
      return value;
    }
  };
  const traced = new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(tracePath)), {audit}).exports.run;
  const cases = [];
  for (const a of [0, 1, t.nodes - 1, t.nodes, 0x7fffffff, 0xffffffff])
    for (const b of [0, 1, 2, 127, 255, 256, 0x7fffffff, 0xffffffff]) cases.push([a, b]);
  for (let i = 0; i < 256; i++) cases.push([rand() % t.nodes, rand()]);
  for (let i = 0; i < 32; i++) cases.push([rand(), rand()]);
  let bad = 0, traps = 0;
  for (const [a, b] of cases) {
    const want = reference(t, a, b), got = call(ordinary, a, b), instrumented = call(traced, a, b);
    if (want.trap) traps++;
    if (!same(want, got) || !same(want, instrumented)) bad++;
  }
  collect = true;
  const traceOutcome = call(traced, t.head_index, 255);
  collect = false;
  if (traceOutcome.trap) throw Error('Unexpected trace trap');
  const begin = process.hrtime.bigint();
  const recovered = recover(events, 16);
  const attack_ns = Number(process.hrtime.bigint() - begin);
  // Ground truth is used only AFTER attack output has been obtained.
  const expected = new Set(t.next.flatMap((v, i) => v ? [`${t.addresses[i]}:${v}`] : []));
  function score(xs) {
    const actual = new Set(xs);
    let tp = 0; for (const x of actual) if (expected.has(x)) tp++;
    return {true_positive: tp, false_positive: actual.size - tp, false_negative: expected.size - tp,
      precision: actual.size ? tp / actual.size : null, recall: tp / expected.size};
  }
  const traceFile = r.traced.replace('.wasm', '.events.json');
  fs.writeFileSync(path.join(dir, traceFile), JSON.stringify({events, recovered, traceOutcome}));
  total += cases.length * 2; mismatches += bad;
  rows.push({...r, input_conditions: cases.length, executions: cases.length * 2,
    mismatches: bad, trap_conditions: traps, graph_edges: expected.size,
    trace_score: score(recovered.edges), value_score: score(recovered.valueEdges),
    trace_file: traceFile, attack_ns, events: events.length, cases});
}
// Required negative controls: the algorithm does not see unseen edges, and
// aligned addresses alone cannot distinguish repeated accesses from self-edges.
const negativeControls = {
  no_events: recover([], 16).edges.length === 0,
  one_node_only: recover([{kind:'after', address:256, value:272}],16).edges.length === 0,
  immediate_self_edge_not_claimed: recover([{kind:'after',address:256,value:256},
    {kind:'after',address:260,value:9},{kind:'after',address:256,value:256}],16).edges.length === 0,
};
const result = {node: process.version, v8: process.versions.v8, platform: process.platform,
  arch: process.arch, cpu: os.cpus()[0].model, total_executions: total,
  mismatched_input_conditions: mismatches, negative_controls: negativeControls,
  manifest_sha256: hash(path.join(dir,'manifest.json')),
  checker_sha256: hash(__filename), attack_sha256: hash(path.join(__dirname,'attack.cjs')), rows,
  scope: 'Read-only synthetic linked-record controls; binary-only load observation; no NotDec/DSI execution.',
  attack_cost_scope: 'Single recovery from already captured trace, excluding Wasm execution and instrumentation; no performance superiority claim.'};
fs.writeFileSync(output, JSON.stringify(result,null,2));
console.log(JSON.stringify({conditions:rows.length,total_executions:total,mismatched_input_conditions:mismatches,
  exact_trace_graphs:rows.filter(r=>r.trace_score.false_positive===0&&r.trace_score.false_negative===0).length,
  negative_controls:negativeControls}));
if (mismatches || Object.values(negativeControls).some(v=>!v)) process.exitCode = 1;
