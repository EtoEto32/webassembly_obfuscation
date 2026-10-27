import fs from 'node:fs';
import crypto from 'node:crypto';
const [input] = process.argv.slice(2);
const spec = JSON.parse(fs.readFileSync(input, 'utf8'));
const hash = data => crypto.createHash('sha256').update(data).digest('hex');
const rows = [];
for (const pair of spec.accepted) {
  const runs = [];
  for (const side of ['original', 'snapshot']) {
    const { instance } = await WebAssembly.instantiate(fs.readFileSync(pair[side]), {});
    if (side === 'original') instance.exports['wizer-initialize']();
    const observations = [];
    for (const name of pair.actions) {
      let result;
      try { result = { type: 'return', value: instance.exports[name]() ?? null }; }
      catch (error) { if (!(error instanceof WebAssembly.RuntimeError)) throw error; result = { type: 'trap' }; }
      observations.push({ name, result, memorySha256: hash(new Uint8Array(instance.exports.memory.buffer)) });
    }
    runs.push(observations);
  }
  rows.push({ name: pair.name, same: JSON.stringify(runs[0]) === JSON.stringify(runs[1]), runs });
}
console.log(JSON.stringify({ node: process.version, rows, mismatches: rows.filter(x => !x.same).length }));
