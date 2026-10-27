'use strict';
const fs=require('fs'),path=require('path'),os=require('os'),assert=require('assert'),{partition}=require('./partition.cjs');
const mode=process.argv[2],median=a=>[...a].sort((a,b)=>a-b)[Math.floor(a.length/2)];
async function run(memories,registry){
  if(mode==='batch')return partition(memories);
  if(mode==='registry'){
    const ids=[],labels=memories.map(m=>{const id=registry.get(m);let p=ids.indexOf(id);if(p<0){p=ids.length;ids.push(id);}return p;});return {labels,registrations:0,notifications:0};
  }
  if(mode==='representative-pairs'){
    const reps=[],labels=[];let registrations=0,notifications=0;
    for(const m of memories){let label=-1;for(let j=0;j<reps.length;j++){const p=await partition([reps[j],m]);registrations+=p.registrations;notifications+=p.notifications;if(p.labels[0]===p.labels[1]){label=j;break;}}if(label<0){label=reps.length;reps.push(m);}labels.push(label);}
    return {labels,registrations,notifications};
  }
  throw new Error('mode');
}
async function main(){
  const rows=[];
  for(const n of [8,16,32,64])for(const shape of ['same','four','distinct']){
    const k=shape==='same'?1:shape==='four'?4:n,base=Array.from({length:k},()=>new WebAssembly.Memory({initial:1,maximum:4,shared:true})),expected=Array.from({length:n},(_,i)=>i%k),memories=expected.map(i=>structuredClone(base[i])),registry=new WeakMap(memories.map((m,i)=>[m,base[expected[i]]]));
    for(let i=0;i<3;i++)assert.deepStrictEqual((await run(memories,registry)).labels,expected);
    const ms=[];let counts;
    for(let i=0;i<9;i++){const begin=process.hrtime.bigint();counts=await run(memories,registry);ms.push(Number(process.hrtime.bigint()-begin)/1e6);assert.deepStrictEqual(counts.labels,expected);}
    rows.push({n,k,shape,ms,median:median(ms),registrations:counts.registrations,notifications:counts.notifications});
  }
  console.log(JSON.stringify({mode,rows,node:process.version,v8:process.versions.v8,cpu:os.cpus()[0].model,memory:process.memoryUsage(),resourceUsage:process.resourceUsage(),warmup:3,repetitions:9,unit:'milliseconds per partition, allocation excluded, registry already populated'}));
}
main().catch(e=>{console.error(e);process.exitCode=1;});
