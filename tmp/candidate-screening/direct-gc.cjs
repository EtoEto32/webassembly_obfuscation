'use strict';
// Directly encode tiny, import-free Wasm modules: no assembler can merge types.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const hash = b => crypto.createHash('sha256').update(b).digest('hex');
const uleb = n => { const b=[]; do { let x=n&127; n>>>=7; b.push(x|(n?128:0)); } while(n); return b; };
const section = (id, p) => [id,...uleb(p.length),...p];
const struct = field => [0x5f,1,field,0];
const a = struct(0x7f), b = struct(0x7e);
const rec = ts => [0x4e,...uleb(ts.length),...ts.flat()];
const cases = [
  {name:'implicit-duplicate', groups:[a,a], typeCount:2, source:0, target:1, expected:1},
  {name:'different-field', groups:[a,b], typeCount:2, source:0, target:1, expected:0},
  {name:'explicit-singletons', groups:[rec([a]),rec([a])], typeCount:2, source:0, target:1, expected:1},
  {name:'same-pair-cross-index', groups:[rec([a,a])], typeCount:2, source:0, target:1, expected:0},
  {name:'duplicate-pairs-same-index', groups:[rec([a,a]),rec([a,a])], typeCount:4, source:0, target:2, expected:1},
  {name:'duplicate-pairs-cross-index', groups:[rec([a,a]),rec([a,a])], typeCount:4, source:0, target:3, expected:0},
  {name:'singleton-versus-pair', groups:[a,rec([a,a])], typeCount:3, source:0, target:1, expected:0},
];
const out=path.join(__dirname,'results','direct-gc'); fs.mkdirSync(out,{recursive:true});
const results=[];
for(const c of cases) {
  const typePayload=[...uleb(c.groups.length+1),...c.groups.flat(),0x60,0,1,0x7f];
  const body=[0,0x41,7,0xfb,0,...uleb(c.source),0xfb,0x14,...uleb(c.target),0x0b];
  const binary=Buffer.from([0,97,115,109,1,0,0,0,
    ...section(1,typePayload),...section(3,[1,...uleb(c.typeCount)]),
    ...section(7,[1,3,114,117,110,0,0]),
    ...section(10,[1,...uleb(body.length),...body])]);
  fs.writeFileSync(path.join(out,c.name+'.wasm'),binary);
  const r={...c,sha256:hash(binary),bytes:binary.length,valid:WebAssembly.validate(binary)};
  try {
    const m=new WebAssembly.Module(binary); assert.deepEqual(WebAssembly.Module.imports(m),[]);
    r.actual=new WebAssembly.Instance(m,{}).exports.run();
    r.passed=r.actual===c.expected;
  } catch(e) {r.passed=false; r.error=e.message;}
  results.push(r);
}
const report={node:process.version,v8:process.versions.v8,script_sha256:hash(fs.readFileSync(__filename)),
  purpose:'Check type identity without assembler canonicalization; not a new obfuscator or resistance evaluation.',
  results};
fs.writeFileSync(path.join(out,'results.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(results.map(({name,actual,expected,passed,error})=>({name,actual,expected,passed,error})),null,2));
if(results.some(r=>!r.passed)) process.exitCode=1;
