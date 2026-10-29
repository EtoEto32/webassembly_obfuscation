'use strict';
// Falsification experiment for the 42 pure arithmetic modules in this repository.
// Reads only Wasm files: no source, manifest, encodings, or mapping.json is used.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const root = path.resolve(process.argv[2] || path.join(__dirname, '..', 'artifacts'));
const output = path.resolve(process.argv[3] || path.join(root, 'affine-recovery.json'));
const sha = value => crypto.createHash('sha256').update(value).digest('hex');
const u32 = value => value >>> 0;
const schema = /^(coordinate_step|pair_recurrence|integer_filter)-(baseline|global|per_region)-(0|101|202|303)(-O2)?\.wasm$/;
const files = fs.readdirSync(root).filter(name => schema.test(name)).sort();
assert.equal(files.length, 42, 'This audit is scoped to the existing 42 artifacts');

function recover(oracle) {
  const offset = oracle(0, 0).map(u32);
  const ex = oracle(1, 0).map(u32);
  const ey = oracle(0, 1).map(u32);
  return {matrix: offset.map((b, i) => [u32(ex[i] - b), u32(ey[i] - b)]), offset};
}
function predict(model, x, y) {
  return model.matrix.map((row, i) => u32(Math.imul(row[0], x) + Math.imul(row[1], y) + model.offset[i]));
}
function same(a, b) { return a.length === b.length && a.every((v, i) => v === b[i]); }

// These controls must reject a non-affine function, rather than pass tautologically.
const negativeControls = [
  {name: 'cross_product', oracle: (x, y) => [u32(Math.imul(x, y)), u32(y)]},
  {name: 'square', oracle: (x, y) => [u32(Math.imul(x, x)), u32(y)]},
].map(({name, oracle}) => {
  const model = recover(oracle);
  const expected = oracle(2, 3), predicted = predict(model, 2, 3);
  assert(!same(expected, predicted), `${name} should fail affine holdout validation`);
  return {name, input: [2, 3], predicted, actual: expected, rejected: true};
});

const trainingPoints = new Set(['0,0', '1,0', '0,1']);
const holdout = [];
const edges = [0, 1, 2, 0x7fffffff, 0x80000000, 0xfffffffe, 0xffffffff];
for (const x of edges) for (const y of edges)
  if (!trainingPoints.has(`${x},${y}`)) holdout.push([x, y]);
assert.equal(holdout.length, 46);
let randomState = 0xa10d17;
function random32() {
  randomState ^= randomState << 13;
  randomState ^= randomState >>> 17;
  randomState ^= randomState << 5;
  return randomState >>> 0;
}
for (let i = 0; i < 1024;) {
  const point = [random32(), random32()];
  if (trainingPoints.has(point.join(','))) continue;
  holdout.push(point); i++;
}

const results = [];
for (const file of files) {
  const binary = fs.readFileSync(path.join(root, file));
  assert(WebAssembly.validate(binary), file);
  const module = new WebAssembly.Module(binary);
  assert.deepEqual(WebAssembly.Module.imports(module), [], file);
  assert.deepEqual(WebAssembly.Module.exports(module), [{name: 'run', kind: 'function'}], file);
  const run = new WebAssembly.Instance(module, {}).exports.run;
  const slices = [];
  for (let flag = 0; flag < 2; flag++) for (let n = 0; n < 16; n++) {
    let oracleCalls = 0;
    const oracle = (x, y) => { oracleCalls++; return run(x, y, flag, n).map(u32); };
    const model = recover(oracle);
    assert.equal(oracleCalls, 3);
    for (const [x, y] of holdout)
      assert.deepEqual(predict(model, x, y), oracle(x, y), `${file}, flag=${flag}, n=${n}, x=${x}, y=${y}`);
    assert.equal(oracleCalls, 3 + holdout.length);
    slices.push({flag, n, model, fit_queries: 3, holdout_pairs: holdout.length, mismatches: 0});
  }
  const [, program, mode, seed, optimization] = schema.exec(file);
  results.push({file, sha256: sha(binary), bytes: binary.length, program, mode,
    seed: Number(seed), optimization: optimization ? 'O2' : 'none', slices});
}

// Only AFTER independent inference, compare inferred behavior across variants.
let equivalentVariantSlices = 0;
for (const result of results) {
  const baseline = results.find(r => r.program === result.program && r.mode === 'baseline' && r.optimization === 'none');
  for (let i = 0; i < result.slices.length; i++) {
    assert.deepEqual(result.slices[i].model, baseline.slices[i].model);
    equivalentVariantSlices++;
  }
}
const totalSlices = results.reduce((n, r) => n + r.slices.length, 0);
const report = {
  status: 'passed', node: process.version, v8: process.versions.v8,
  script_sha256: sha(fs.readFileSync(__filename)),
  method: 'Three-query affine input/output reconstruction modulo 2^32 at fixed flag and n',
  read_inputs: 'Only the 42 filename-selected Wasm binaries; no manifest, source, or encoding mappings',
  control_domain: {flag: [0, 1], n: Array.from({length: 16}, (_, i) => i)},
  fit_points: [[0, 0], [1, 0], [0, 1]], random_seed: '0x00a10d17',
  holdout_per_slice: {boundary_pairs: 46, pseudorandom_pairs: 1024},
  artifacts: results.length, slices: totalSlices, fit_queries: totalSlices * 3,
  holdout_pairs: totalSlices * holdout.length, equivalent_variant_slices: equivalentVariantSlices,
  mismatches: 0, negative_controls: negativeControls,
  limitations: [
    'Assumes a two-input affine function per fixed control slice; not generic deobfuscation.',
    'Fits observable behavior, not original source, CFG, internal values, or secret encoding coefficients.',
    'Finite holdouts are not a universal equivalence proof.',
    'Shows equal fitting-query counts, not equal runtime or resistance to every analysis.',
    'The entire programs are affine within control slices; no conclusion for nonlinear workloads.',
    'No claim that this established algebraic fitting method is a novel research contribution.'
  ], results
};
fs.writeFileSync(output, JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify({status: report.status, artifacts: report.artifacts, slices: report.slices,
  fit_queries: report.fit_queries, holdout_pairs: report.holdout_pairs, mismatches: report.mismatches,
  negative_controls_rejected: negativeControls.length}));
