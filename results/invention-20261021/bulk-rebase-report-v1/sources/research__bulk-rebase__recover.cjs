'use strict';const fs=require('fs'),path=require('path'),assert=require('assert');
const dir=process.argv[2],targets=JSON.parse(fs.readFileSync(path.join(dir,'targets.json')));
// Known family: E_a(v)=P(lo(v)) | P(hi(v))<<4, xor a period-16 mask.
// Only the instrumented binary and its write API are supplied to this learner.
function learn(moduleObject){
  const e=new WebAssembly.Instance(moduleObject).exports,m=new Uint8Array(e.memory.buffer),delta=[],zero=[];let queries=0;
  for(let v=0;v<16;v++){e.write(0,v);queries++;delta.push(m[0]);}
  zero[0]=delta[0];for(let v=0;v<16;v++)delta[v]^=zero[0];
  for(let a=1;a<16;a++){e.write(a,0);queries++;zero[a]=m[a];}
  const table=[];
  for(let a=0;a<16;a++){
    const decoder=Array(256).fill(-1);
    for(let v=0;v<256;v++){
      const physical=zero[a]^delta[v&15]^(delta[v>>>4]<<4);
      assert(physical>=0&&physical<256&&decoder[physical]===-1);decoder[physical]=v;
    }
    table.push(decoder);
  }
  return {table,queries};
}
const records=[];
for(const row of targets){
  const moduleObject=new WebAssembly.Module(fs.readFileSync(path.join(dir,row.file))),start=process.hrtime.bigint();
  const recovered=learn(moduleObject),learning_ms=Number(process.hrtime.bigint()-start)/1e6;
  // Independent verification follows learning; these observations never feed back.
  const e=new WebAssembly.Instance(moduleObject).exports,m=new Uint8Array(e.memory.buffer),size=m.length,oracle=new Uint8Array(size);
  let chosenChecks=0;
  for(let a=0;a<16;a++)for(let v=0;v<256;v++){e.write(a,v);assert.strictEqual(recovered.table[a][m[a]],v);chosenChecks++;}
  let seed=0x31415926;for(let i=0;i<size;i++){seed=(Math.imul(seed,1664525)+1013904223)|0;oracle[i]=seed>>>24;}
  e.fill(0x31415926);
  for(const [d,s,n] of [[1,0,4097],[0,3,4096],[16385,1024,4096],[65500,2,31],[19,17,33]]){e.copy(d,s,n);oracle.copyWithin(d,s,s+n);}
  e.splice(101,49,215);oracle.copyWithin(101,102,150);oracle[149]=215;
  let trapped=false;try{e.markcopy(size-1,1,2,87);}catch(x){assert(x instanceof WebAssembly.RuntimeError);trapped=true;}
  assert(trapped);oracle[0]=87;
  const t=process.hrtime.bigint(),decoded=new Uint8Array(size);
  for(let a=0;a<size;a++)decoded[a]=recovered.table[a&15][m[a]];
  const decode_ms=Number(process.hrtime.bigint()-t)/1e6;
  assert.deepStrictEqual(decoded,oracle);
  records.push({file:row.file,status:'recovered',learning_queries:recovered.queries,chosen_verification_checks:chosenChecks,decoded_bytes:size,learning_ms,decode_ms});
}
fs.writeFileSync(path.join(dir,'recovery.json'),JSON.stringify({task:'Learn equivalent position-dependent byte decoder from own instrumented clone; no source/seed/mask/encoding metadata',records,recovered:records.length,unsupported:0,crashes:0,timeouts:0,mismatches:0},null,2),{flag:'wx'});
console.log(JSON.stringify({targets:records.length,queries_per_target:31,decoded_bytes:records.reduce((a,r)=>a+r.decoded_bytes,0)}));
