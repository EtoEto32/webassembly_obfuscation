'use strict';
const fs = require('node:fs'), assert = require('node:assert/strict');
const task = JSON.parse(fs.readFileSync(process.argv[2]));
const bytes = fs.readFileSync(task.file);
assert(WebAssembly.validate(bytes));
const api = new WebAssembly.Instance(new WebAssembly.Module(bytes)).exports;
const keys = task.items.map(([k]) => k), expected = new Map(task.items);
assert(keys.length > 0);
let epoch = 0;
function batch(count) {
  let sum = 0;
  const start = process.hrtime.bigint();
  for (let i = 0; i < count; i++) {
    sum += api.set(keys[i % keys.length], (i+epoch) >>> 0);
  }
  const ns = Number(process.hrtime.bigint()-start);
  assert.equal(sum, count);
  for (let i = 0; i < count; i++) expected.set(keys[i % keys.length], (i+epoch) >>> 0);
  epoch = (epoch+count+1) >>> 0;
  for (const [k,v] of expected) assert.equal(api.lookup(k) >>> 0, v);
  return ns;
}
batch(8192);
let count = 128;
while (batch(count) < 5e6 && count < 131072) count *= 2;
const nsPerUpdate = [], batchMs = [];
for (let b = 0; b < 9; b++) {
  const ns = batch(count); nsPerUpdate.push(ns/count); batchMs.push(ns/1e6);
}
const sorted = [...nsPerUpdate].sort((a,b) => a-b);
console.log(JSON.stringify({id:task.id, count, warmupCalls:8192, batches:9, nsPerUpdate,
  batchMs, medianNs:sorted[4], peakRssKiB:process.resourceUsage().maxRSS,
  linearMemoryBytes:65536, node:process.version, v8:process.versions.v8,
  includes:'JS loop, key selection, JS-to-Wasm call, set status sum; final-state verification outside timed region'}));
