'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const root=process.argv[2],mf=JSON.parse(fs.readFileSync(path.join(root,'manifest.json'))),refs=JSON.parse(fs.readFileSync(path.join(root,'reference.json'))),groups=new Map();
for(const r of refs){const key=r.fixture+'/'+r.alias;if(!groups.has(key))groups.set(key,[]);groups.get(key).push(r);}
let checks=0,traps=0,memchecks=0,instances=0;
for(const rec of mf.records)for(const alias of rec.aliases){
 const p=alias.partition,memories=Array.from({length:Math.max(...p)+1},(_,c)=>{const m=new WebAssembly.Memory({initial:1,maximum:3});new Uint8Array(m.buffer).set(Uint8Array.from({length:65536},(_,i)=>(i*17+c*13)&255));return m;});
 const host={};alias.representatives.forEach(i=>host['m'+i]=memories[p[i]]);
 const bytes=fs.readFileSync(path.join(root,rec.folder,'merge'+alias.id+'.wasm'));assert(WebAssembly.validate(bytes));
 const inst=new WebAssembly.Instance(new WebAssembly.Module(bytes),{host});instances++;
 for(let i=0;i<rec.n;i++)for(let j=0;j<rec.n;j++)assert.equal(inst.exports['m'+i]===inst.exports['m'+j],p[i]===p[j]);
 for(const r of groups.get(rec.folder+'/'+alias.id)){
  let status='complete',value=null;try{value=inst.exports.run(...r.args)>>>0;}catch(e){if(!(e instanceof WebAssembly.RuntimeError))throw e;status='trap';traps++;}
  assert.deepEqual({status,value},r.expected);checks++;
  memories.forEach((m,c)=>{assert.deepEqual({bytes:m.buffer.byteLength,sha256:crypto.createHash('sha256').update(new Uint8Array(m.buffer)).digest('hex')},r.memories[c]);memchecks++;});
 }
}
const result={node:process.version,v8:process.versions.v8,instances,checks,traps,memoryChecks:memchecks,claim:'Existing wasm-merge plus a generated re-export wrapper implements the same tested alias quotient. No new quotient primitive is established.'};
fs.writeFileSync(path.join(root,'results.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result));
