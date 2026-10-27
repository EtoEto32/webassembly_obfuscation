'use strict';
// All registrations and notifications run in this agent, in one synchronous job.
// External wait/notify operations must be excluded by the calling host.
class Inconclusive extends Error{}
const memoryBuffer=Object.getOwnPropertyDescriptor(WebAssembly.Memory.prototype,'buffer').get;
const sharedLength=Object.getOwnPropertyDescriptor(SharedArrayBuffer.prototype,'byteLength').get;
const apply=Reflect.apply;
async function partition(memories,{byteOffset=0,deadlineMs=1000,retryLimit=1}={}){
  if(!Array.isArray(memories)||memories.length>256)throw new TypeError('memory list');
  if(!Number.isSafeInteger(byteOffset)||byteOffset<0||byteOffset>Number.MAX_SAFE_INTEGER-4||byteOffset%4)throw new TypeError('offset');
  if(!Number.isFinite(deadlineMs)||deadlineMs<=0)throw new TypeError('deadline');
  if(!Number.isSafeInteger(retryLimit)||retryLimit<1||retryLimit>4096)throw new TypeError('retry limit');
  const snapshot=[];const length=memories.length;for(let i=0;i<length;i++)snapshot.push(memories[i]);
  const views=snapshot.map(m=>{const b=apply(memoryBuffer,m,[]);if(apply(sharedLength,b,[])<byteOffset+4)throw new TypeError('shared memory with accessible cell required');return new Int32Array(b,byteOffset,1);});
  const order=[],promises=[],groups=[];let registrations=0,notifications=0,registrationAttempts=0,closed=false,successful=false,timer;
  try{
    for(let i=0;i<views.length;i++){
      let waiter;
      for(let attempt=0;attempt<retryLimit;attempt++){
        waiter=Atomics.waitAsync(views[i],0,Atomics.load(views[i],0));registrationAttempts++;
        if(waiter.async)break;
        if(waiter.value!=='not-equal')throw new Inconclusive('unexpected synchronous registration');
      }
      if(!waiter.async)throw new Inconclusive('registration retry limit');registrations++;
      promises.push(waiter.value.then(status=>{if(closed)return;if(status!=='ok')throw new Inconclusive('unexpected waiter result');order.push(i);}));
    }
    let total=0;
    for(let i=0;i<views.length;i++){
      const count=Atomics.notify(views[i],0);notifications++;
      if(count<0||count>views.length)throw new Inconclusive('notified count');
      if(count)groups.push({representative:i,count});total+=count;
    }
    if(total!==views.length)throw new Inconclusive('total notification count');
    await Promise.race([Promise.all(promises),new Promise((_,reject)=>{timer=setTimeout(()=>reject(new Inconclusive('completion deadline')),deadlineMs);})]);
    if(order.length!==views.length||new Set(order).size!==views.length)throw new Inconclusive('completion count');
    const labels=Array(views.length).fill(-1);let start=0;
    for(let label=0;label<groups.length;label++){
      const end=start+groups[label].count;
      for(let j=start;j<end;j++)labels[order[j]]=label;
      if(labels[groups[label].representative]!==label)throw new Inconclusive('representative outside its ordered cohort');
      start=end;
    }
    successful=true;
    return {labels:Object.freeze(labels),memories:Object.freeze(snapshot),registrations,notifications,registrationAttempts,barriers:1};
  }finally{
    closed=true;if(timer!==undefined)clearTimeout(timer);
    if(!successful)for(const view of views)Atomics.notify(view,0);
    // Drain reactions after exceptional cleanup; no identity inference from it.
    if(!successful)void Promise.allSettled(promises);
  }
}
module.exports={partition,Inconclusive};
