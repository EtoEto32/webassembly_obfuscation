'use strict';
// Semantic feasibility probes, not an obfuscation or resistance benchmark.
const fs = require('node:fs');
const path = require('node:path');
const cp = require('node:child_process');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const root = __dirname;
const bin = path.resolve(process.argv[2]);
const hash = b => crypto.createHash('sha256').update(b).digest('hex');
const out = path.join(root, 'results'); fs.mkdirSync(out, {recursive:true});
const cases = [
  ['gc-same-shape', 1], ['gc-different-shape', 0],
  ['exception-tag-identity', 17], ['select-eager-trap', 'trap'], ['if-lazy-safe', 7]
];
const log = [];
for (const [name, expected] of cases) {
  const source = path.join(root, 'probes', name + '.wat');
  const dest = path.join(out, name + '.wasm');
  const args = [source, '--all-features', '-o', dest];
  const assembled = cp.spawnSync(path.join(bin, 'wasm-as.exe'), args, {encoding:'utf8', timeout:10000});
  const entry = {name, expected, source_sha256:hash(fs.readFileSync(source)), assemble_exit:assembled.status,
    assemble_stderr:assembled.stderr, command:['wasm-as',...args]};
  if (assembled.status !== 0) { entry.status='assembler-rejected'; log.push(entry); continue; }
  const binary = fs.readFileSync(dest);
  entry.wasm_sha256=hash(binary); entry.bytes=binary.length;
  entry.engine_valid=WebAssembly.validate(binary);
  if (!entry.engine_valid) { entry.status='engine-rejected'; log.push(entry); continue; }
  const module = new WebAssembly.Module(binary);
  assert.deepEqual(WebAssembly.Module.imports(module), []);
  const instance = new WebAssembly.Instance(module, {});
  try { entry.actual=instance.exports.run(); }
  catch(error) {
    entry.actual = error instanceof WebAssembly.RuntimeError ? 'trap' : 'unexpected-error';
    entry.error_type=error.constructor.name; entry.error_message=error.message;
  }
  entry.status = entry.actual === expected ? 'expected-observation' : 'unexpected-observation';
  log.push(entry);
}
const version=cp.spawnSync(path.join(bin,'wasm-as.exe'),['--version'],{encoding:'utf8'});
const report={node:process.version,v8:process.versions.v8,binaryen:version.stdout.trim(),
  script_sha256:hash(fs.readFileSync(__filename)), results:log,
  limitation:'Five semantic probes only; no novelty, obfuscation strength or overhead claim.'};
fs.writeFileSync(path.join(out,'probe.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(log.map(({name,status,actual,assemble_stderr})=>({name,status,actual,assemble_stderr}))));
if(log.some(r=>r.status!=='expected-observation')) process.exitCode=1;
