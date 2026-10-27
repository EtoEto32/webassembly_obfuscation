'use strict';
// Reuses saved test inputs. Independent word expression oracle; no attack metadata.
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
function evaluate(t, x) {
  if (t[0] === 'var') return x[t[1]] >>> 0;
  if (t[0] === 'const') return t[1] >>> 0;
  const a = evaluate(t[1], x), b = evaluate(t[2], x);
  if (t[0] === 'and') return (a & b) >>> 0;
  if (t[0] === 'or') return (a | b) >>> 0;
  if (t[0] === 'xor') return (a ^ b) >>> 0;
  throw new Error('Unsupported fixture');
}
async function main(prior, directory) {
  const report = JSON.parse(fs.readFileSync(path.join(directory, 'analysis.json')));
  const fixtures = JSON.parse(fs.readFileSync(path.join(prior, 'fixtures.json')));
  const inputs = JSON.parse(fs.readFileSync(path.join(prior, 'inputs.json')));
  const rows = [];
  let calls = 0;
  for (const row of report.recovered_binaries) {
    const binary = fs.readFileSync(path.join(directory, row.path));
    if (crypto.createHash('sha256').update(binary).digest('hex') !== row.sha256) throw new Error('Wrong binary');
    if (!WebAssembly.validate(binary)) throw new Error('Invalid output');
    const instance = (await WebAssembly.instantiate(binary)).instance;
    let count = 0;
    for (const x of inputs[row.kernel].concat(inputs[row.kernel].slice(0, 7).reverse())) {
      const expected = evaluate(fixtures[row.kernel].tree, x);
      if ((instance.exports.run(...x) >>> 0) !== expected) throw new Error(JSON.stringify({row, x, expected}));
      count++; calls++;
    }
    rows.push({file:row.file, strategy:row.strategy, status:'passed', calls:count});
  }
  const result = {node:process.version, v8:process.versions.v8, conditions:rows.length, calls, mismatches:0, rows,
    note:'Reused finite inputs, not new independent coverage or a whole-compiler proof.'};
  fs.writeFileSync(path.join(directory, 'correctness.json'), JSON.stringify(result,null,2), {flag:'wx'});
  console.log(JSON.stringify({conditions:rows.length, calls, mismatches:0}));
}
main(process.argv[2], process.argv[3]).catch(e=>{console.error(e);process.exitCode=1;});
