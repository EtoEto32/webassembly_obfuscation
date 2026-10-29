'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),{Worker,isMainThread,workerData,parentPort}=require('node:worker_threads'),c=require('./common.cjs');
if(!isMainThread){
 const {module,memory,control,kind,field,count,expected,width}=workerData,api=new WebAssembly.Instance(module,{env:{memory}}).exports;
 parentPort.postMessage({ready:true});Atomics.wait(new Int32Array(control),0,0);
 if(kind==='ticket'){const values=new Uint32Array(count);for(let i=0;i<count;i++)values[i]=api.add(field,1)>>>0;parentPort.postMessage({values});}
 else{const result=width===64?api.wait64(0,expected,-1n):api['wait'+field](0,expected,-1n);parentPort.postMessage({result});}
}else{
 const out=path.resolve(process.argv[2]),rows=JSON.parse(fs.readFileSync(path.join(out,'manifest.json'))),results=[];
 async function tickets(file){
  const o=c.instantiate(file),control=new SharedArrayBuffer(4),workers=[];let ready=0,timer;
  const tasks=Array.from({length:4},(_,i)=>new Promise((resolve,reject)=>{
   const w=new Worker(__filename,{workerData:{module:o.module,memory:o.memory,control,kind:'ticket',field:(i%2)*4,count:4096}});workers.push(w);
   w.on('error',reject);w.on('message',m=>{if(m.ready){if(++ready===4){Atomics.store(new Int32Array(control),0,1);Atomics.notify(new Int32Array(control),0);}}else resolve(m.values);});w.on('exit',code=>{if(code)reject(Error('worker exit '+code));});
  }));
  try{const values=await Promise.race([Promise.all(tasks),new Promise((_,reject)=>{timer=setTimeout(()=>reject(Error('ticket timeout')),20000);})]);
   for(let f=0;f<2;f++){const all=[...values[f],...values[f+2]].sort((a,b)=>a-b);assert(all.every((x,i)=>x===i));assert.equal(o.api.load(f*4),8192);}
   return{operations:16384,fields:2,workers:4,passed:true};
  }finally{clearTimeout(timer);await Promise.all(workers.map(w=>w.terminate()));}
 }
 async function wake(file,field,width){
  const o=c.instantiate(file),control=new SharedArrayBuffer(4);o.api.store(0,19);o.api.store(4,23);
  let readyResolve,doneResolve,rejectWorker;const ready=new Promise(r=>readyResolve=r),done=new Promise((r,j)=>{doneResolve=r;rejectWorker=j;});
  const w=new Worker(__filename,{workerData:{module:o.module,memory:o.memory,control,kind:'wait',field,width,expected:width===64?19n+(23n<<32n):field?23:19}});
  w.on('error',rejectWorker);w.on('message',m=>m.ready?readyResolve():doneResolve(m.result));
  let timer;try{
   return await Promise.race([(async()=>{await ready;Atomics.store(new Int32Array(control),0,1);Atomics.notify(new Int32Array(control),0);
    let notified=0,wrong=0,attempts=0;while(!notified){wrong+=o.api.notify(field===0?4:0,1);notified=o.api.notify(field,1);attempts++;if(!notified)await new Promise(r=>setTimeout(r,1));}
    const result=await done;assert.equal(result,0);assert.equal(wrong,0);return{field,width,result,notified,wrong_address_wake:wrong,attempts,passed:true};
   })(),new Promise((_,j)=>{timer=setTimeout(()=>j(Error('wait timeout')),10000);})]);
  }finally{clearTimeout(timer);await w.terminate();}
 }
 (async()=>{for(const row of rows){
  const file=path.join(out,row.file),waits=[];
  for(const field of row.profile==='low'?[0]:row.profile==='high'?[4]:row.profile==='both'?[0,4]:[])waits.push(await wake(file,field,32));
  waits.push(await wake(file,0,64));results.push({file:row.file,tickets:await tickets(file),waits});
 }
 c.save(out,'parallel.json',{results});console.log(JSON.stringify({kind:'parallel',conditions:results.length,updates:results.reduce((s,x)=>s+x.tickets.operations,0),waits:results.reduce((s,x)=>s+x.waits.length,0),passed:true}));
 })().catch(e=>{console.error(e);process.exitCode=1;});
}
