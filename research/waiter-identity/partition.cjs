'use strict';
// Requires exclusive ownership of the synchronization locations for this call.
// Bytes are read but never written. Wait queues are deliberately modified.
class Inconclusive extends Error{}
const memoryBuffer=Object.getOwnPropertyDescriptor(WebAssembly.Memory.prototype,'buffer').get;
const sharedLength=Object.getOwnPropertyDescriptor(SharedArrayBuffer.prototype,'byteLength').get;
const apply=Reflect.apply;
async function partition(memories,{byteOffset=0,deadlineMs=1000}={}){
  if(!Array.isArray(memories)||memories.length>256)throw new TypeError('memory list');
  if(!Number.isSafeInteger(byteOffset)||byteOffset<0||byteOffset>Number.MAX_SAFE_INTEGER-4||byteOffset%4)throw new TypeError('offset');
  if(!Number.isFinite(deadlineMs)||deadlineMs<=0)throw new TypeError('deadline');
  const snapshot=[];const length=memories.length;
  for(let i=0;i<length;i++)snapshot.push(memories[i]);
  const views=snapshot.map(m=>{const b=apply(memoryBuffer,m,[]);if(apply(sharedLength,b,[])<byteOffset+4)throw new TypeError('shared memory with an accessible cell required');return new Int32Array(b,byteOffset,1);});
  const labels=Array(views.length).fill(-1),promises=[];let batch=null,failed=null,closed=false,registrations=0,notifications=0;
  function fail(message){failed=new Inconclusive(message);if(batch)batch.reject(failed);}
  function settle(i,status){
    if(closed)return;
    if(status!=='ok'||!batch||labels[i]!==-1){fail('unexpected waiter resolution');return;}
    labels[i]=batch.label;batch.arrived++;
    if(batch.arrived>batch.count)fail('waiter count exceeded');else if(batch.arrived===batch.count)batch.resolve();
  }
  try{
    for(let i=0;i<views.length;i++){
      const waiter=Atomics.waitAsync(views[i],0,Atomics.load(views[i],0));registrations++;
      if(!waiter.async)throw new Inconclusive('registration raced');
      promises.push(waiter.value.then(status=>settle(i,status)));
    }
    let classes=0;
    for(let i=0;i<views.length;i++){
      if(failed)throw failed;if(labels[i]!==-1)continue;
      let resolve,reject;const completion=new Promise((a,b)=>{resolve=a;reject=b;});
      batch={label:classes++,count:-1,arrived:0,resolve,reject};
      const timer=setTimeout(()=>reject(new Inconclusive('notification completion deadline')),deadlineMs);
      try{
        batch.count=Atomics.notify(views[i],0);notifications++;
        if(batch.count<1||batch.count>views.length)throw new Inconclusive('unexpected notified count');
        await completion;if(failed)throw failed;if(labels[i]!==batch.label)throw new Inconclusive('representative missing from wake cohort');
      }finally{clearTimeout(timer);batch=null;}
    }
    if(labels.some(x=>x<0))throw new Inconclusive('unclassified waiter');
    return {labels:Object.freeze(labels),memories:Object.freeze(snapshot),registrations,notifications};
  }finally{
    closed=true;
    // Cleanup changes wait queues too; callers must maintain the exclusivity precondition.
    for(let i=0;i<views.length;i++)if(labels[i]<0)Atomics.notify(views[i],0);
    // All owned waiters have been notified; do not infer identity from cleanup timing.
  }
}
module.exports={partition,Inconclusive};
