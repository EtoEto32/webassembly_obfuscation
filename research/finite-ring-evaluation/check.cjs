'use strict';const fs=require('fs'),path=require('path'),assert=require('assert'),crypto=require('crypto');
const dir=process.argv[2],rows=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json'))),fullrows=JSON.parse(fs.readFileSync(path.join(dir,'full-manifest.json')));
const load=r=>new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(dir,r.file)))).exports;
const rotr=(a,n)=>(a>>>n)|(a<<(32-n));
const oracle=(a,b,c)=>((rotr(a,2)^rotr(a,13)^rotr(a,22))+((a&b)^(a&c)^(b&c)))>>>0;
let seed=211025;const rnd=()=>{seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed>>>0;};
const triples=[];for(const a of [0,0xffffffff,0x80000000,0x7fffffff])for(const b of [0,0xffffffff,0x80000000,0x7fffffff])for(const c of [0,0xffffffff,0x80000000,0x7fffffff])triples.push([a,b,c]);
for(let bit=0;bit<32;bit++)for(let k=0;k<3;k++){const a=[0,0,0];a[k]=(1<<bit)>>>0;triples.push(a);}
for(let i=0;i<96;i++)triples.push([rnd(),rnd(),rnd()]);
const instances=rows.map(load);let calls=0,states=0,bytes=0;const localResults=[];
for(let k=0;k<triples.length;k++){
 const xyz=triples[k],wanted=oracle(...xyz);let reference;
 for(let j=0;j<rows.length;j++){
  const row=rows[j],e=instances[j],m=row.state?Buffer.from(e.memory.buffer):null;
  if(m)m.fill((k*37+29)&255);
  const got=e.run(...xyz)>>>0;calls++;assert.strictEqual(got,wanted,row.file+' '+k);
  if(e.evaluations)assert.strictEqual(e.evaluations.value,k+1);
  if(m){if(!reference)reference=Buffer.from(m);else assert.strictEqual(Buffer.compare(m,reference),0,row.file+' memory '+k);states++;bytes+=m.length;}
 }
 localResults.push({input:xyz,expected:wanted});
}
const full=fullrows.map(load),base=path.resolve(__dirname,'../../experiments/sha256-research-baseline/artifacts'),index=JSON.parse(fs.readFileSync(path.join(base,'inputs.json'))),bundle=fs.readFileSync(path.join(base,'inputs.bin'));
const sha=x=>crypto.createHash('sha256').update(x).digest('hex');assert.strictEqual(sha(bundle),index.bundle_sha256);
let hashCalls=0,hashStates=0;const hashes=[];
for(const test of index.cases){
 const input=bundle.subarray(test.offset,test.offset+test.length),expected=sha(input);assert.strictEqual(expected,test.expected);let reference;
 for(let j=0;j<full.length;j++){
  const e=full[j],m=Buffer.from(e.memory.buffer);m.set(input,1024);m.fill(0xa5,1024+input.length,1024+input.length+64);
  const before=e.evaluations.value,ptr=e.hash(input.length),actual=m.subarray(ptr,ptr+32).toString('hex');hashCalls++;
  assert.strictEqual(ptr,512);assert.strictEqual(actual,expected,fullrows[j].file+' '+test.id);assert.strictEqual(e.evaluations.value,before+1);
  if(!reference)reference=Buffer.from(m);else assert.strictEqual(Buffer.compare(m,reference),0,'full state '+fullrows[j].file+' '+test.id);
  hashStates++;assert.strictEqual(sha(m.subarray(1024,1024+input.length)),expected);assert(m.subarray(1024+input.length,1024+input.length+64).every(x=>x===0xa5));
 }
 hashes.push({id:test.id,length:test.length,expected});
}
let traps=0;
for(let j=0;j<full.length;j++)for(const n of [1048577,0x7fffffff,0x80000000,0xffffffff]){
 const e=full[j],before=Buffer.from(new Uint8Array(e.memory.buffer)),counter=e.evaluations.value;
 assert.throws(()=>e.hash(n),WebAssembly.RuntimeError);traps++;assert.strictEqual(Buffer.compare(Buffer.from(e.memory.buffer),before),0);assert.strictEqual(e.evaluations.value,counter);
}
const report={local_targets:rows.length,local_inputs:triples.length,local_calls:calls,local_state_checks:states,local_bytes_compared:bytes,hash_targets:fullrows.length,hash_inputs:index.cases.length,hash_calls:hashCalls,hash_state_checks:hashStates,expected_traps:traps,mismatches:0,unexpected_traps:0,localResults,hashes,node:process.version,v8:process.versions.v8};
fs.writeFileSync(path.join(dir,'checks.json'),JSON.stringify(report,null,2),{flag:'wx'});
console.log(JSON.stringify({...report,localResults:undefined,hashes:undefined}));
