'use strict';
// Non-mining, bounded helper module only. No networking or whole miner imports.
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const root = path.resolve(__dirname, '../results/countermeasures/flattening-xor');
const manifest = JSON.parse(fs.readFileSync(path.join(root, 'manifest.json')));
const binary = fs.readFileSync(path.join(root, 'isolated-xor.wasm'));
if (crypto.createHash('sha256').update(binary).digest('hex') !== manifest.wasm_sha256 || manifest.hashing !== false) throw Error('fixture mismatch');
const module_ = new WebAssembly.Module(binary);
if (WebAssembly.Module.imports(module_).length) throw Error('isolated helper must have no imports');
const instance = new WebAssembly.Instance(module_, {});
const expectedExports = ['memory','stack','xor8_ref','xor8_flat','xor16_ref','xor16_flat'].sort();
if (JSON.stringify(Object.keys(instance.exports).sort()) !== JSON.stringify(expectedExports)) throw Error('unexpected fixture exports');
const memory = new Uint8Array(instance.exports.memory.buffer);
if (memory.length !== 65536) throw Error('memory bound mismatch');
const input = fs.readFileSync(path.join(root, 'cases.json'));
if (crypto.createHash('sha256').update(input).digest('hex') !== manifest.cases_sha256) throw Error('case mismatch');
const cases = JSON.parse(input);
const results = [];
for (let index=0; index<cases.length; index++) {
  const test=cases[index];
  const initial=new Uint8Array(65536);
  for (const [address,value] of test.initial) initial[address]=value;
  const expected=initial.slice();
  // Sequential memory update also models overlapping input/output pointers.
  for (let i=0;i<test.length;i++) expected[test.destination+i] ^= expected[test.source+i];
  for (const role of ['ref','flat']) {
    memory.set(initial); instance.exports.stack.value=32768;
    instance.exports[`xor${test.length}_${role}`](test.destination,test.source);
    if (instance.exports.stack.value !== 32768) throw Error(`stack changed at case ${index}`);
    // Original and flattened functions use different temporary stack frames.
    // Do not claim equality of their scratch bytes; compare all other memory.
    for (let address=0;address<memory.length;address++) {
      if (address>=32736 && address<32768) continue;
      if (memory[address]!==expected[address]) throw Error(`mismatch case ${index} role ${role} address ${address}`);
    }
    results.push({case:index,length:test.length,label:test.label,role,matched:true});
  }
}
const report={passed:true,cases:cases.length,helper_calls:results.length,records:results,node:process.version,
  evaluator_sha256:crypto.createHash('sha256').update(fs.readFileSync(__filename)).digest('hex'),
  wasm_sha256:manifest.wasm_sha256,cases_sha256:manifest.cases_sha256,
  mining_executed:false,mining_hash_computation_executed:false,whole_miner_loaded:false,imports:[],
  ignored_scratch_range:[32736,32768],
  scope:'Finite isolated XOR helper output and non-scratch memory checks; not full miner equivalence, dynamic hash-path coverage or performance.'};
fs.writeFileSync(path.join(root,'checks.json'),JSON.stringify(report,null,2));
process.stdout.write(JSON.stringify({passed:true,cases:cases.length,helper_calls:results.length,mining_executed:false})+'\n');
