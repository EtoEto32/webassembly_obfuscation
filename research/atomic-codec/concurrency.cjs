'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),{Worker}=require('node:worker_threads');
const out=path.resolve(process.argv[2]),dest=path.join(out,'concurrency.json');if(fs.existsSync(dest))throw Error('refuse overwrite');
const rows=JSON.parse(fs.readFileSync(path.join(out,'manifest.json'))),results=[];
function update(op,x,y,z){switch(op){case'load':return[null,x];case'store':return[null,y];case'add':return[x,(x+y)>>>0];case'sub':return[x,(x-y)>>>0];case'and':return[x,(x&y)>>>0];case'or':return[x,(x|y)>>>0];case'xor':return[x,(x^y)>>>0];case'xchg':return[x,y];case'cmpxchg':return[x,x===y?z:x];}}
async function run(row,kind,count,jobs){
 const memory=new WebAssembly.Memory({initial:1,maximum:1,shared:true}),physical=new Uint32Array(memory.buffer);physical.fill(row.b);
 const module=new WebAssembly.Module(fs.readFileSync(path.join(out,row.file))),api=new WebAssembly.Instance(module,{env:{memory}}).exports;
 if(kind==='mixed')for(let j=0;j<jobs.length;j++)api.store(16*(j+1),jobs[j].initial);
 const control=new SharedArrayBuffer(4),workers=[],n=kind==='ticket'?4:3;let ready=0;
 const promises=Array.from({length:n},(_,i)=>new Promise((resolve,reject)=>{
  const w=new Worker(path.join(__dirname,'worker.cjs'),{workerData:{module,memory,control,kind,count,jobs:jobs?.map(x=>x.threads[i])}});workers.push(w);
  w.on('error',reject);w.on('message',m=>{if(m.ready){if(++ready===n){Atomics.store(new Int32Array(control),0,1);Atomics.notify(new Int32Array(control),0,n);}}else resolve(m.values);});w.on('exit',c=>{if(c)reject(Error('worker exit '+c));});
 }));let timer;
 try{
  const values=await Promise.race([Promise.all(promises),new Promise((_,reject)=>{timer=setTimeout(()=>reject(Error('worker timeout')),30000);})]);
  if(kind==='ticket'){
   const sorted=values.flatMap(x=>Array.from(x)).sort((a,b)=>a-b),final=api.load(0)>>>0;
   return {kind,workers:n,operations:n*count,final,valid:final===n*count&&sorted.every((v,i)=>v===i),unique:new Set(sorted).size};
  }
  const histories=jobs.map((job,j)=>{
   const observed=values.map(v=>v[j]),final=api.load(16*(j+1))>>>0;
   function dfs(indices,state,order){
    if(indices.every(x=>x===2))return state===final?order:null;
    for(let t=0;t<3;t++){const i=indices[t];if(i===2)continue;const op=job.threads[t][i],r=update(op.op,state,...op.args);if(op.op==='load')r[0]=state;
     if(r[0]!==observed[t][i])continue;const next=indices.slice();next[t]++;const found=dfs(next,r[1],[...order,t]);if(found)return found;
    }return null;
   }
   const order=dfs([0,0,0],job.initial,[]);return{job,observed,final,order,valid:!!order};
  });return {kind,workers:n,operations:jobs.length*6,histories,valid:histories.every(x=>x.valid)};
 }finally{clearTimeout(timer);await Promise.all(workers.map(w=>w.terminate()));}
}
(async()=>{
 const jobs=Array.from({length:16},(_,i)=>({initial:i%2?0xffffffff:0x12345678,threads:[[{op:'add',args:[i+1]},{op:'and',args:[0xff00ff00]}],[{op:'xor',args:[0x89abcdef]},{op:'or',args:[0xf0f0f0f0]}],[{op:i%2?'xchg':'cmpxchg',args:i%2?[i]:[0x12345678,i]},{op:'sub',args:[7]}]]}));
 for(const row of rows.filter(r=>r.profile==='counter')){
  const r=await run(row,'ticket',8192);if(row.mode!=='bad-split')assert(r.valid,JSON.stringify({row,r}));results.push({file:row.file,negative:row.negative,...r});
 }
 for(const row of rows.filter(r=>r.profile==='full'&&!r.negative)){
  const r=await run(row,'mixed',0,jobs);assert(r.valid,row.file);results.push({file:row.file,negative:false,...r});
 }
 fs.writeFileSync(dest,JSON.stringify({node:process.version,results},null,2));console.log(JSON.stringify({conditions:results.length,operations:results.reduce((s,x)=>s+x.operations,0),invalid:results.filter(x=>!x.valid).length}));
})().catch(e=>{console.error(e);process.exitCode=1;});
