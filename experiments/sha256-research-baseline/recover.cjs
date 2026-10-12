'use strict';
const fs=require('node:fs'),path=require('node:path'),cp=require('node:child_process'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const root=__dirname,dir=path.resolve(process.argv[2]||path.join(root,'artifacts')),out=path.join(dir,'recovery');
if(fs.existsSync(out))throw Error('Refuse overwrite recovery');fs.mkdirSync(out);
const toolRoot=process.env.WASM_TOOLS_ROOT||path.resolve(root,'../../.tools'),wabt=path.join(toolRoot,'wabt-1.0.42/bin');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const run=(tool,args)=>cp.execFileSync(path.join(wabt,tool+'.exe'),args,{encoding:'utf8',timeout:30000});
const index=JSON.parse(fs.readFileSync(path.join(dir,'inputs.json'))),input=fs.readFileSync(path.join(dir,'inputs.bin'));
assert.equal(sha(input),index.bundle_sha256);
const results=[];
// Match only a contiguous pure-local expression, where both operands stay unchanged.
const pattern=/local\.get (\d+)\s+local\.get (\d+)\s+i32\.xor\s+local\.get \1\s+local\.get \2\s+i32\.and\s+i32\.const 1\s+i32\.shl\s+i32\.add\b/g;
for(const file of fs.readdirSync(dir).filter(f=>f.endsWith('.wasm')).sort()){
 const start=process.hrtime.bigint(),binary=fs.readFileSync(path.join(dir,file));
 const before=run('wasm2wat',[path.join(dir,file)]);let replacements=0;
 const after=before.replace(pattern,(_,a,b)=>{replacements++;return `local.get ${a}\n    local.get ${b}\n    i32.add`;});
 fs.writeFileSync(path.join(out,file+'.before.wat'),before);fs.writeFileSync(path.join(out,file+'.after.wat'),after);
 run('wat2wasm',[path.join(out,file+'.after.wat'),'-o',path.join(out,file)]);
 const recovered=fs.readFileSync(path.join(out,file));
 const api=new WebAssembly.Instance(new WebAssembly.Module(recovered)).exports,mem=new Uint8Array(api.memory.buffer);
 const restore_ns=Number(process.hrtime.bigint()-start);
 for(const t of index.cases){
  const b=input.subarray(t.offset,t.offset+t.length);mem.set(b,1024);
  assert.equal(api.hash(t.length),512);assert.equal(Buffer.from(mem.slice(512,544)).toString('hex'),t.expected);
  assert.equal(sha(mem.subarray(1024,1024+t.length)),t.expected);
 }
 for(const length of [1048577,0x7fffffff,0x80000000,0xffffffff]){
  const beforeHash=sha(mem);assert.throws(()=>api.hash(length),WebAssembly.RuntimeError);assert.equal(sha(mem),beforeHash);
 }
 results.push({file,input_sha256:sha(binary),output_sha256:sha(recovered),replacements,bytes:recovered.length,restore_ns,checks:index.cases.length,mismatches:0,status:replacements?'local-pattern-restored':'no-supported-pattern'});
}
fs.writeFileSync(path.join(out,'results.json'),JSON.stringify({script_sha256:sha(fs.readFileSync(__filename)),plan_sha256:sha(fs.readFileSync(path.join(root,'attack-plan.json'))),results},null,2));
console.log(JSON.stringify(results,null,2));
