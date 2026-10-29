'use strict';
// Semantic guardrail for candidate design, not an obfuscation algorithm.
const fs=require('node:fs'),path=require('node:path'),cp=require('node:child_process'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const root=__dirname,out=path.join(root,'artifacts');fs.mkdirSync(out,{recursive:true});
const bin=path.resolve(process.argv[2]);
const bodies={
  original:'(i32.store (i32.const 0) (i32.const 7)) (i32.div_u (i32.const 100) (local.get $d))',
  reordered:'(local.set $t (i32.div_u (i32.const 100) (local.get $d))) (i32.store (i32.const 0) (i32.const 7)) (local.get $t)',
  pure_prefix:'(local.set $d (i32.xor (local.get $d) (i32.const 0))) (i32.store (i32.const 0) (i32.const 7)) (i32.div_u (i32.const 100) (local.get $d))'
};
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const results=[];
for(const [name,body] of Object.entries(bodies)){
  const source=`(module (memory (export "memory") 1) (func (export "run") (param $d i32) (result i32) (local $t i32) ${body}))\n`;
  const wat=path.join(out,name+'.wat'),wasm=path.join(out,name+'.wasm');fs.writeFileSync(wat,source);
  const args=[wat,'-o',wasm],r=cp.spawnSync(path.join(bin,'wasm-as.exe'),args,{encoding:'utf8',timeout:10000});assert.equal(r.status,0,r.stderr);
  const bytes=fs.readFileSync(wasm),m=new WebAssembly.Module(bytes);assert.deepEqual(WebAssembly.Module.imports(m),[]);
  for(const denominator of [0,1,3,0xffffffff]){
    const inst=new WebAssembly.Instance(m,{});let outcome;
    try{outcome={kind:'return',value:inst.exports.run(denominator)};}catch(e){assert(e instanceof WebAssembly.RuntimeError);outcome={kind:'trap'};}
    const memory0=new DataView(inst.exports.memory.buffer).getUint32(0,true);
    results.push({name,denominator,outcome,memory0,source_sha256:sha(source),binary_sha256:sha(bytes),command:['wasm-as',...args]});
  }
}
const comparisons=[];
for(const d of [0,1,3,0xffffffff])for(const name of ['reordered','pure_prefix']){
  const a=results.find(r=>r.name==='original'&&r.denominator===d),b=results.find(r=>r.name===name&&r.denominator===d);
  comparisons.push({denominator:d,name,same_return_or_trap:JSON.stringify(a.outcome)===JSON.stringify(b.outcome),same_observable_memory:a.memory0===b.memory0});
}
assert(comparisons.find(r=>r.name==='reordered'&&r.denominator===0).same_return_or_trap);
assert(!comparisons.find(r=>r.name==='reordered'&&r.denominator===0).same_observable_memory);
assert(comparisons.filter(r=>r.name==='pure_prefix').every(r=>r.same_return_or_trap&&r.same_observable_memory));
fs.writeFileSync(path.join(out,'trap-state.json'),JSON.stringify({node:process.version,v8:process.versions.v8,script_sha256:sha(fs.readFileSync(__filename)),
  scope:'A hand-written counterexample to insufficient output/trap-only comparison. Does not test any published obfuscator.',results,comparisons},null,2)+'\n');
console.log(JSON.stringify(comparisons,null,2));
