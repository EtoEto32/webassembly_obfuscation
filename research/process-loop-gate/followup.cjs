'use strict';
const fs = require('fs');
const path = require('path');
const out = process.argv[2];
const p = JSON.parse(fs.readFileSync(path.join(out, 'cases.json')));
function instance(name) {
  const bytes = fs.readFileSync(path.join(out, name));
  if (!WebAssembly.validate(bytes)) throw new Error('invalid module ' + name);
  return new WebAssembly.Instance(new WebAssembly.Module(bytes)).exports;
}
function compare(actual, expected, name) {
  actual = actual.map(x => x >>> 0);
  if (JSON.stringify(actual) !== JSON.stringify(expected)) {
    throw new Error('mismatch ' + name + ': ' + JSON.stringify({actual, expected}));
  }
}
let solverCalls = 0, pairCalls = 0;
for (const file of p.solver_files) {
  const e = instance(file);
  for (const c of p.solver_cases) {
    compare(e.solve(...c.input), c.expected, file);
    ++solverCalls;
  }
}
for (const group of p.pair_cases) {
  for (const file of group.files) {
    const e = instance(file);
    for (const c of group.checks) {
      compare(e.step(...c.input), c.expected, file);
      ++pairCalls;
    }
    for (const x of group.example_word_roots) compare(e.step(...x), x, file);
  }
}
console.log(JSON.stringify({solver_modules: p.solver_files.length,
  solver_calls: solverCalls, pair_modules: p.pair_cases.flatMap(g => g.files).length,
  pair_calls: pairCalls, extra_fixed_point_checks: p.pair_cases.reduce((s,g)=>s+g.example_word_roots.length*g.files.length,0),
  mismatches: 0, word_root_counts: p.pair_cases.map(g => ({label:g.label,count:g.word_root_count_by_cartesian_product}))}));
