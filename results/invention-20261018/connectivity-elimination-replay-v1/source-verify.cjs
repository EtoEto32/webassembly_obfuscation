// Independent word evaluator, finite input tests and warmed timing worker.
// No network, package dependencies, or access to transform correspondence maps.
'use strict';
const fs = require('fs');
const path = require('path');
const os = require('os');
const {performance} = require('perf_hooks');
const crypto = require('crypto');

function evaluate(t, x) {
  if (t[0] === 'var') return x[t[1]] >>> 0;
  if (t[0] === 'const') return t[1] >>> 0;
  const a = evaluate(t[1], x), b = evaluate(t[2], x);
  if (t[0] === 'and') return (a & b) >>> 0;
  if (t[0] === 'or') return (a | b) >>> 0;
  if (t[0] === 'xor') return (a ^ b) >>> 0;
  throw new Error('Invalid fixture');
}

function inputs(n) {
  let state = (0x434f4e4e ^ n) >>> 0;
  const next = () => {
    state ^= state << 13; state ^= state >>> 17; state ^= state << 5;
    return state >>> 0;
  };
  const rows = [];
  for (const x of [0, 1, 0x7fffffff, 0x80000000, 0xffffffff, 0xaaaaaaaa, 0x55555555]) rows.push(Array(n).fill(x));
  for (let i = 0; i < n; i++) for (let bit = 0; bit < 32; bit++) {
    const row = Array(n).fill(0); row[i] = (2 ** bit) >>> 0; rows.push(row);
  }
  for (let k = 0; k < 512; k++) rows.push(Array.from({length:n}, next));
  // Each lane is one Boolean assignment. This is exhaustive only for n<=12.
  if (n <= 12) for (let base = 0; base < 2**n; base += 32) {
    const row = Array(n).fill(0);
    for (let lane = 0; lane < 32; lane++) for (let i = 0; i < n; i++) {
      if (((base + lane) & (2**n-1)) & (1 << i)) row[i] = (row[i] | (1 << lane)) >>> 0;
    }
    rows.push(row);
  }
  return rows;
}

async function run(directory) {
  const report = JSON.parse(fs.readFileSync(path.join(directory, 'build.json')));
  if (report.status !== 'built') throw new Error('Build incomplete');
  const fixtures = JSON.parse(fs.readFileSync(path.join(directory, 'fixtures.json')));
  const savedInputs = Object.fromEntries(Object.entries(fixtures).map(([k, f]) => [k, inputs(f.n)]));
  fs.writeFileSync(path.join(directory, 'inputs.json'), JSON.stringify(savedInputs), {flag:'wx'});
  const rows = [];
  let comparisons = 0;
  for (const condition of report.conditions) {
    for (const kind of ['original', 'recovered']) {
      const file = path.join(directory, kind === 'original' ? '' : 'recovered-v2', condition.file);
      if (!fs.existsSync(file)) { rows.push({file:condition.file, kind, status:'missing'}); continue; }
      const binary = fs.readFileSync(file);
      const valid = WebAssembly.validate(binary);
      if (!valid) throw new Error('Invalid binary: ' + file);
      const instance = (await WebAssembly.instantiate(binary)).instance;
      if (Object.keys(instance.exports).join(',') !== 'run') throw new Error('Unexpected public ABI');
      let count = 0;
      for (const x of savedInputs[condition.kernel]) {
        const expected = evaluate(fixtures[condition.kernel].tree, x);
        const actual = instance.exports.run(...x) >>> 0;
        if (actual !== expected) throw new Error(JSON.stringify({file, x, actual, expected}));
        count++; comparisons++;
      }
      // Reuse the same instance with a different sequence to detect stale scratch.
      for (const x of savedInputs[condition.kernel].slice(0, 7).reverse()) {
        if ((instance.exports.run(...x) >>> 0) !== evaluate(fixtures[condition.kernel].tree, x)) throw new Error('Repeated-call mismatch');
        count++; comparisons++;
      }
      rows.push({file:condition.file, kind, status:'passed', cases:count, valid,
                 sha256:crypto.createHash('sha256').update(binary).digest('hex')});
    }
  }
  const mutation = (await WebAssembly.instantiate(fs.readFileSync(path.join(directory, 'mutation-control.wasm')))).instance;
  let detected = 0;
  for (const x of savedInputs.mixed12) if ((mutation.exports.run(...x) >>> 0) !== evaluate(fixtures.mixed12.tree, x)) detected++;
  if (!detected) throw new Error('Incorrect graph control was not detected');
  const result = {node:process.version, v8:process.versions.v8, cpu:os.cpus()[0].model,
                  rows, comparisons, mismatches:0, mutation_mismatches:detected,
                  note:'Finite tests. n<=12 additionally covers all Boolean assignments per lane. No arbitrary-Wasm equivalence proof.'};
  fs.writeFileSync(path.join(directory, 'correctness.json'), JSON.stringify(result,null,2), {flag:'wx'});
  fs.copyFileSync(__filename, path.join(directory,'source-verify.cjs'), fs.constants.COPYFILE_EXCL);
  console.log(JSON.stringify({conditions:rows.length, comparisons, mutation_mismatches:detected, mismatches:0}));
}

async function timing(file, n) {
  const instance = (await WebAssembly.instantiate(fs.readFileSync(file))).instance;
  const x = Array.from({length:n}, (_, i) => Math.imul(0x9e3779b1, i+1) | 0);
  let checksum = 0;
  for (let i=0; i<128; i++) { x[0] = (x[0]+1)|0; checksum ^= instance.exports.run(...x); }
  const observations = [];
  const calls = 128;
  for (let trial=0; trial<9; trial++) {
    const begin = performance.now();
    for (let i=0; i<calls; i++) { x[0] = (x[0]+1)|0; checksum ^= instance.exports.run(...x); }
    observations.push((performance.now()-begin)*1e6/calls);
  }
  console.log(JSON.stringify({file:path.basename(file), samples_ns:observations, warmup:128, calls_per_trial:calls,
    checksum, max_rss_kib:process.resourceUsage().maxRSS, memory:process.memoryUsage(), node:process.version,
    v8:process.versions.v8, cpu:os.cpus()[0].model, host_call_and_argument_passing_included:true}));
}

if (process.argv[2] === '--timing') timing(process.argv[3], Number(process.argv[4])).catch(e => {console.error(e);process.exitCode=1;});
else run(process.argv[2]).catch(e => {console.error(e);process.exitCode=1;});
