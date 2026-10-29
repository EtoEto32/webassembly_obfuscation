'use strict';
const fs=require('node:fs'),path=require('node:path'),cp=require('node:child_process'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const root=__dirname,out=path.join(root,'wasm');if(fs.existsSync(out))throw Error('Refuse overwrite wasm');fs.mkdirSync(out);
const tools=process.env.WASM_TOOLS_ROOT||path.resolve(root,'../../.tools'),wabt=path.join(tools,'wabt-1.0.42/bin'),opt=path.join(tools,'binaryen-version_133/bin/wasm-opt.exe');
const run=(exe,args)=>cp.execFileSync(exe,args,{encoding:'utf8',timeout:30000}).trim();
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const observationBytes=fs.readFileSync(path.join(root,'i32-observations.json')),observations=JSON.parse(observationBytes);
const checks=JSON.parse(fs.readFileSync(path.join(root,'results.json')));assert.equal(sha(observationBytes),checks.observations['i32-observations.json']);
// This is only a representation primitive, not a compiler for encoded SHA operations.
const enc=Array.from({length:32},(_,j)=>`(i32.store (i32.const ${j*4}) (i32.xor (i32.add (local.get $x) (i32.const ${2**j|0})) (local.get $x)))`).join('\n');
const terms=Array.from({length:31},(_,j)=>`(i32.shl (i32.and (i32.shr_u (i32.load (i32.const ${j*4})) (i32.const ${j+1})) (i32.const 1)) (i32.const ${j}))`);
const recovered=terms.reduce((a,b)=>`(i32.or ${a} ${b})`,'(i32.shl (i32.load (i32.const 128)) (i32.const 31))');
const after=`(module (memory (export "memory") 1)
 (func (export "encode") (param $x i32) ${enc}
  (i32.store (i32.const 128) (i32.shr_u (local.get $x) (i32.const 31))))
 (func (export "recover") (result i32) ${recovered}))`;
const before='(module (memory (export "memory") 1) (func (export "encode") (param $x i32) (i32.store (i32.const 0) (local.get $x))) (func (export "recover") (result i32) (i32.load (i32.const 0))))';
const report={node:process.version,v8:process.versions.v8,wabt:run(path.join(wabt,'wat2wasm.exe'),['--version']),binaryen:run(opt,['--version']),script_sha256:sha(fs.readFileSync(__filename)),inputs_sha256:sha(observationBytes),rows:[]};
for(const [name,wat] of [['before',before],['after-repaired',after]]){
 fs.writeFileSync(path.join(out,name+'.wat'),wat);run(path.join(wabt,'wat2wasm.exe'),[path.join(out,name+'.wat'),'-o',path.join(out,name+'.raw.wasm')]);
 for(const mode of ['raw','O2']){
  const file=name+'.'+mode+'.wasm',target=path.join(out,file);
  if(mode==='O2')run(opt,[path.join(out,name+'.raw.wasm'),'-O2','-o',target]);
  run(path.join(wabt,'wasm2wat.exe'),[target,'-o',target.replace('.wasm','.wat')]);
  const bin=fs.readFileSync(target),api=new WebAssembly.Instance(new WebAssembly.Module(bin)).exports,mem=new DataView(api.memory.buffer);
  let badAnchorDetected=0;
  for(const t of observations){
   api.encode(t.x);assert.equal(api.recover()>>>0,t.x);
   if(name==='after-repaired'){
    t.profile.forEach((v,j)=>assert.equal(mem.getUint32(j*4,true),v));assert.equal(mem.getUint32(128,true),t.anchor);
    mem.setUint32(128,t.anchor^1,true);assert.equal(api.recover()>>>0,(t.x^0x80000000)>>>0);badAnchorDetected++;
   }
  }
  report.rows.push({file,bytes:bin.length,sha256:sha(bin),source_sha256:sha(wat),checks:observations.length,mismatches:0,wrong_anchor_tests:badAnchorDetected});
 }
}
fs.writeFileSync(path.join(out,'results.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report.rows,null,2));
