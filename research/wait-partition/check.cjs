'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),c=require('./common.cjs');
const out=path.resolve(process.argv[2]),rows=JSON.parse(fs.readFileSync(path.join(out,'manifest.json'))),results=[];
for(const row of rows){
 const a=c.instantiate(path.join(out,`${row.profile}.plain.raw.wasm`)),b=c.instantiate(path.join(out,row.file)),identified=c.identify(path.join(out,row.file));
 c.initialize(a,'identity',22112026);c.initialize(b,row.codec,22112026);
 const rnd=c.rng(88901),ops=['load','store','add','sub','and','or','xor','xchg','cmpxchg','offset4','offset65532','offset4294967292','edge'];
 const boundary=[0,1,3,4,7,8,65528,65532,65533,65535,65536,0xfffffffc,0xffffffff];let calls=0,traps=0,snapshots=0,decode_pairs=0;
 const compare=(name,args)=>{const x=c.outcome(a.api[name],args),y=c.outcome(b.api[name],args);assert.deepEqual(y,x,JSON.stringify({file:row.file,name,args:args.map(String)}));calls++;traps+=!!x.trap;};
 const memory=()=>{for(let i=0;i<a.physical.length;i+=2){const pair=c.dec(b.physical[i],b.physical[i+1],identified.codec);assert.equal(pair[0],a.physical[i],row.file);assert.equal(pair[1],a.physical[i+1],row.file);decode_pairs++;}snapshots++;};
 for(let n=0;n<2048;n++){
  const addr=n<boundary.length*ops.length?boundary[Math.floor(n/ops.length)]:(rnd()%16384)*4;
  const op=ops[n%ops.length],v=rnd(),z=rnd();compare(op,op==='load'?[addr]:op==='cmpxchg'?[addr,v,z]:[addr,v]);
  if(n%64===0)memory();
 }
 for(const base of [0,8,65528]){
  for(const field of [0,4])if(a.api['wait'+field]){const expected=a.physical[(base+field)/4];compare('wait'+field,[base,expected,0n]);compare('wait'+field,[base,expected^1,0n]);}
  const expected=BigInt(a.physical[base/4])|(BigInt(a.physical[base/4+1])<<32n);
  compare('wait64',[base,BigInt.asIntN(64,expected),0n]);compare('wait64',[base,BigInt.asIntN(64,expected^1n),0n]);
 }
 for(const addr of boundary){compare('wait64',[addr,0n,0n]);compare('notify',[addr,1]);}
 for(const name of ['wait0','wait4'])if(a.api[name])compare(name,[65536,0,0n]);
 memory();results.push({file:row.file,calls,traps,full_memory_snapshots:snapshots,decoded_pairs:decode_pairs,identified,passed:true});
}
c.save(out,'correctness.json',{node:process.version,v8:process.versions.v8,results});
console.log(JSON.stringify({kind:'correctness',conditions:results.length,calls:results.reduce((s,x)=>s+x.calls,0),traps:results.reduce((s,x)=>s+x.traps,0),passed:true}));
