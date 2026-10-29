'use strict';
const fs = require('fs');
const path = require('path');
const dir = process.argv[2];
const cases = JSON.parse(fs.readFileSync(path.join(dir, 'wasm-cases.json')));
let calls = 0;
const details = [];
for (const c of cases) {
  const bytes = fs.readFileSync(path.join(dir, c.file));
  if (!WebAssembly.validate(bytes)) throw new Error('validation failed: ' + c.file);
  const e = new WebAssembly.Instance(new WebAssembly.Module(bytes)).exports;
  const roots = [];
  for (let s = 0; s < c.expected.length; ++s) {
    const got = e.step(s) >>> 0;
    ++calls;
    if (got !== c.expected[s]) throw new Error('step mismatch: ' + c.file + ':' + s);
    if (got === s) roots.push(s);
  }
  const count = e.count() >>> 0;
  ++calls;
  if (JSON.stringify(roots) !== JSON.stringify(c.roots) || count !== roots.length) {
    throw new Error('fixed-point mismatch: ' + c.file);
  }
  details.push({file: c.file, states: c.expected.length, roots, count});
}
console.log(JSON.stringify({modules: cases.length, calls, mismatches: 0, details}));
