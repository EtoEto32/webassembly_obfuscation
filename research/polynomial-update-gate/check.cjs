'use strict';
const fs = require('node:fs'), path = require('node:path'), assert = require('node:assert/strict');
const tasks = JSON.parse(fs.readFileSync(process.argv[2]));
const out = process.argv[3], P = 4294967291;
const rows = [], snapshots = [];
let calls = 0;
function save(name, data) { fs.writeFileSync(path.join(out, name), data, {flag: 'wx'}); }
for (const task of tasks) {
  const bytes = fs.readFileSync(task.file);
  assert(WebAssembly.validate(bytes));
  const api = new WebAssembly.Instance(new WebAssembly.Module(bytes)).exports;
  assert.deepEqual(Object.keys(api).sort(), task.audit ? ['audit_memory','lookup','set'] : ['lookup','set']);
  const oracle = new Map(task.items), start = calls;
  const n = task.items.filter(([k]) => k < P).length, len = 4*(8+3*n);
  const snap = () => Buffer.from(new Uint8Array(api.audit_memory.buffer, 0, len));
  const queries = [...oracle.keys(), 0, 1, 0x7fffffff, 0x80000000, P-1, P, P+1, P+4, 0xffffffff];
  function check() {
    for (const key of queries) {
      assert.equal(api.lookup(key) >>> 0, oracle.get(key) ?? 0, task.id+' lookup '+key);
      calls++;
    }
  }
  check();
  for (let j = 0; j < task.ops.length; j++) {
    const [key, value] = task.ops[j], present = oracle.has(key), old = oracle.get(key);
    const before = task.audit && task.mode === 'poly' ? snap() : null;
    assert.equal(api.set(key, value), +present, task.id+' set '+j);
    calls++;
    if (present) oracle.set(key, value);
    check();
    if (before) {
      const after = snap();
      assert(new Uint8Array(api.audit_memory.buffer, len).every(v => v === 0), 'scratch cleared');
      const stem = task.id+'-'+j;
      save(stem+'-before.bin', before); save(stem+'-after.bin', after);
      const expected = !present || old === value ? 'no_change' : key >= P ? 'public_exception' : 'recovered';
      snapshots.push({id: stem, before: stem+'-before.bin', after: stem+'-after.bin', expected,
        ...(expected === 'no_change' ? {} : {key, old, new: value})});
    }
  }
  // Two distinct nonzero changes must not be certified as one change.
  if (task.audit && task.mode === 'poly' && n >= 2) {
    const keys = task.items.filter(([k]) => k < P).slice(0,2).map(([k]) => k), before = snap();
    for (const k of keys) {
      const v = ((oracle.get(k) ?? 0)+1) >>> 0;
      assert.equal(api.set(k, v), 1); oracle.set(k, v); calls++;
    }
    check();
    const stem = task.id+'-multi';
    save(stem+'-before.bin', before); save(stem+'-after.bin', snap());
    snapshots.push({id: stem, before: stem+'-before.bin', after: stem+'-after.bin', expected: 'not_single_update'});
  }
  rows.push({id: task.id, calls: calls-start, validation: 'ok', status: 'ok', traps: 0});
}
save('snapshot-oracle.json', JSON.stringify(snapshots, null, 2));
console.log(JSON.stringify({node:process.version, v8:process.versions.v8, calls, mismatches:0, rows}));
