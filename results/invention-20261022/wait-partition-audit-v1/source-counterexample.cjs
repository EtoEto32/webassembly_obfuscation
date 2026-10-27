'use strict';
const path=require('node:path'),assert=require('node:assert/strict'),{Worker,isMainThread,workerData,parentPort}=require('node:worker_threads'),c=require('./common.cjs');
if(!isMainThread){
 const api=new WebAssembly.Instance(workerData.module,{env:{memory:workerData.memory}}).exports;
 const snapshot=api.prepare();parentPort.postMessage({snapshot});
 Atomics.wait(new Int32Array(workerData.control),0,0);
 parentPort.postMessage({result:api.commit(snapshot)});
}else{
 const out=path.resolve(process.argv[2]);
 async function witness(label){
  const o=c.instantiate(path.join(out,`witness.${label}.wasm`)),control=new SharedArrayBuffer(4);let readyResolve,doneResolve,result;
  const ready=new Promise(r=>readyResolve=r),done=new Promise(r=>doneResolve=r);
  const w=new Worker(__filename,{workerData:{module:o.module,memory:o.memory,control}});let error;
  w.on('error',e=>error=e);w.on('message',m=>{if('snapshot'in m)readyResolve(m.snapshot);else{result=m.result;doneResolve(result);}});
  const started=performance.now();
  try{
   while(!error&&performance.now()-started<10000){const got=await Promise.race([ready,new Promise(r=>setTimeout(()=>r(null),5))]);if(got!==null)break;}
   if(error)throw error;if(performance.now()-started>=10000)throw Error('prepare timeout');
   o.api.write(1n+(0x02000000n<<32n));const first=o.api.notify();
   Atomics.store(new Int32Array(control),0,1);Atomics.notify(new Int32Array(control),0);
   let second=0,attempts=0;
   while(result===undefined){if(error)throw error;if(performance.now()-started>10000)throw Error('commit timeout');second+=o.api.notify();attempts++;await new Promise(r=>setTimeout(r,1));}
   await done;assert.equal(first,0);assert.equal(result,label==='bad'?0:1);assert.equal(second,label==='bad'?1:0);
   return{label,first_notify:first,cleanup_notifies:second,result,attempts,physical_after_write:Array.from(o.physical.slice(0,2)),logical_after_write:[1,0x02000000],passed:true};
  }finally{await w.terminate();}
 }
 (async()=>{const results=[];for(let repeat=0;repeat<5;repeat++)for(const label of ['plain','compatible','bad'])results.push({repeat,...await witness(label)});
 c.save(out,'counterexample.json',{instrumentation:'prepare/commit split forces scheduler preemption inside naive translation; not part of protected program',results});console.log(JSON.stringify({kind:'counterexample',conditions:results.length,invalid_histories:results.filter(x=>x.label==='bad').length,passed:true}));
 })().catch(e=>{console.error(e);process.exitCode=1;});
}
