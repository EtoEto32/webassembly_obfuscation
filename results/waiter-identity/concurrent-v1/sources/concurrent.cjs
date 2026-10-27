'use strict';
const fs=require('fs'),path=require('path'),crypto=require('crypto'),assert=require('assert'),{Worker}=require('worker_threads');
const {partition,Inconclusive}=require('./partition-concurrent.cjs');
const workerCode=`
const {parentPort,workerData:d}=require('worker_threads');
const ctrl=new Int32Array(d.control), moduleObject=new WebAssembly.Module(d.binary);
const run=d.memories.map(memory=>new WebAssembly.Instance(moduleObject,{env:{memory}}).exports.run);
const counts=run.map(()=>0);const deadline=Date.now()+10000;let rounds=0;
function step(){
  if(Atomics.load(ctrl,0)||Date.now()>deadline||rounds>=4096){parentPort.postMessage({done:true,counts,rounds,reason:Atomics.load(ctrl,0)?'requested-stop':'hard-limit'});return;}
  for(let i=0;i<run.length;i++){run[i](4096);counts[i]+=4096;}
  rounds++;Atomics.store(ctrl,1,rounds);
  if(rounds===1)parentPort.postMessage({ready:true});
  setImmediate(step);
}
step();`;

async function main(out){
  const binary=fs.readFileSync(path.join(out,'writer.wasm')),certificate=JSON.parse(fs.readFileSync(path.join(out,'writer.json')));
  assert.strictEqual(crypto.createHash('sha256').update(binary).digest('hex'),certificate.sha256);
  assert(WebAssembly.validate(binary));const rows=[],tails=[];
  for(const n of [8,32,64])for(const k of [1,2,4])for(const retryLimit of [1,64]){
    const backing=Array.from({length:k},()=>new WebAssembly.Memory({initial:1,maximum:4,shared:true}));
    const labels=Array.from({length:n},(_,i)=>i%k),wrappers=labels.map(i=>structuredClone(backing[i]));
    const control=new SharedArrayBuffer(8),ctrl=new Int32Array(control),worker=new Worker(workerCode,{eval:true,workerData:{binary,memories:backing,control}});
    let done,readyResolve,doneResolve,errorReject;
    const ready=new Promise((resolve,reject)=>{readyResolve=resolve;errorReject=reject;});
    const stopped=new Promise(resolve=>{doneResolve=resolve;});
    worker.on('message',m=>{if(m.ready)readyResolve();if(m.done){done=m;doneResolve(m);}});worker.on('error',errorReject);
    const timer=setTimeout(()=>{worker.terminate();errorReject(new Error('worker deadline'));},15000);
    let successes=0,inconclusive=0,withWrites=0,attempts=0;const failures={};const samples=[];
    try{
      await ready;
      for(let i=0;i<100;i++){
        const before=backing.map(m=>Atomics.load(new Int32Array(m.buffer),0));const start=performance.now();
        try{
          const result=await partition(wrappers,{retryLimit,deadlineMs:1000});
          assert.deepStrictEqual(result.labels,labels);assert.strictEqual(result.registrations,n);assert.strictEqual(result.notifications,k);
          attempts+=result.registrationAttempts;successes++;
          const after=backing.map(m=>Atomics.load(new Int32Array(m.buffer),0));if(after.some((v,j)=>v!==before[j]))withWrites++;
          samples.push({status:'ok',ms:performance.now()-start,attempts:result.registrationAttempts,writesObserved:after.some((v,j)=>v!==before[j])});
        }catch(e){
          if(!(e instanceof Inconclusive))throw e;inconclusive++;failures[e.message]=(failures[e.message]||0)+1;samples.push({status:'inconclusive',reason:e.message,ms:performance.now()-start});
        }
      }
      Atomics.store(ctrl,0,1);await Promise.race([stopped,new Promise((_,reject)=>setTimeout(()=>reject(new Error('stop deadline')),2000))]);
      assert.strictEqual(done.reason,'requested-stop');
      for(let i=0;i<k;i++){
        assert.strictEqual(Atomics.load(new Int32Array(backing[i].buffer),0),done.counts[i]);
        assert(new Uint8Array(backing[i].buffer,4).every(v=>v===0));
      }
      rows.push({n,k,retryLimit,trials:100,successes,inconclusive,successWithConcurrentWrites:withWrites,successfulRegistrationAttempts:attempts,failures,worker:done,samples});
      tails.push({n,k,retryLimit,wholeTailUnchanged:true,writeCountersMatch:true});
    }finally{clearTimeout(timer);await worker.terminate();}
  }
  assert(rows.filter(r=>r.retryLimit===64).every(r=>r.successWithConcurrentWrites>0));
  const result={node:process.version,v8:process.versions.v8,certificate,rows,tails,scope:'One trusted worker harness and checked numeric Wasm per condition. No assertion of absence of unregistered external actors; no general wait-free progress claim.'};
  fs.writeFileSync(path.join(out,'results.json'),JSON.stringify(result,null,2));
  console.log(JSON.stringify({conditions:rows.length,trials:rows.reduce((s,r)=>s+r.trials,0),rows:rows.map(({n,k,retryLimit,successes,inconclusive,successWithConcurrentWrites,successfulRegistrationAttempts,failures})=>({n,k,retryLimit,successes,inconclusive,successWithConcurrentWrites,successfulRegistrationAttempts,failures}))}));
}
main(process.argv[2]).catch(e=>{console.error(e);process.exitCode=1;});
