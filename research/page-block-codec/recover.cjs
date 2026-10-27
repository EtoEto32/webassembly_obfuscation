'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),{performance}=require('node:perf_hooks');
const dir=process.argv[2],e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(dir,'exposed.wasm')))).exports;
const view=new DataView(e.__physical.buffer),candidates=Object.keys(e).filter(k=>k.startsWith('__candidate'));
let survivors=[...candidates];const queries=[];const start=performance.now();
for(const words of [[0,0,0,0],[0x12345678,0x89abcdef,0xffffffff,0x13579bdf],[0x80000000,1,0x7fffffff,0x2468ace0]]){
  for(let i=0;i<4;i++)e.i32_st4(32+i*4,words[i]);
  const cipher=[0,1,2,3].map(i=>view.getUint32(32+4*i,true));
  survivors=survivors.filter(k=>e[k](...cipher).every((v,i)=>(v>>>0)===words[i]));queries.push({words,cipher,survivors:[...survivors]});
}
assert.equal(survivors.length,1);const identify_ms=performance.now()-start,decoder=e[survivors[0]];
const bench=e.bench(257,13); // Public workload, after the chosen writes.
const physical=Buffer.from(new Uint8Array(e.__physical.buffer)),physicalView=new DataView(physical.buffer,physical.byteOffset,physical.byteLength),logical=Buffer.alloc(physical.length);
const times=[];
for(let rep=0;rep<7;rep++){
  const t=performance.now();
  for(let at=0;at<physical.length;at+=16){
    const a=decoder(physicalView.getUint32(at,true),physicalView.getUint32(at+4,true),physicalView.getUint32(at+8,true),physicalView.getUint32(at+12,true));
    for(let j=0;j<4;j++)logical.writeUInt32LE(a[j]>>>0,at+4*j);
  }
  times.push(performance.now()-t);
}
fs.writeFileSync(path.join(dir,'physical.bin'),physical);fs.writeFileSync(path.join(dir,'logical.bin'),logical);
const result={node:process.version,candidates,survivors,queries,chosenWrites:12,identify_ms,bytes:physical.length,blocks:physical.length/16,dump_ms:times,median_dump_ms:[...times].sort((a,b)=>a-b)[3],bench};
fs.writeFileSync(path.join(dir,'recovery.json'),JSON.stringify(result,null,2));console.log(JSON.stringify({...result,queries:undefined}));
