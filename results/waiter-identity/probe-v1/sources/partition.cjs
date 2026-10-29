'use strict';
// Requires exclusive ownership of the synchronization locations for this call.
// Bytes are read but never written. Wait queues are deliberately modified.
class Inconclusive extends Error{}
async function partition(memories,{byteOffset=0,deadlineMs=1000}={}){
  if(!Array.isArray(memories)||memories.length>256)throw new TypeError('memory list');
  if(!Number.isSafeInteger(byteOffset)||byteOffset<0||byteOffset%4)throw new TypeError('offset');
  if(!Number.isFinite(deadlineMs)||deadlineMs<=0)throw new TypeError('deadline');
  const views=memories.map(m=>{const b=m.buffer;if(!(b instanceof SharedArrayBuffer)||b.byteLength<byteOffset+4)throw new TypeError('shared memory with an accessible cell required');return new Int32Array(b,byteOffset,1);});
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
        await completion;if(failed)throw failed;
      }finally{clearTimeout(timer);batch=null;}
    }
    if(labels.some(x=>x<0))throw new Inconclusive('unclassified waiter');
    return {labels,registrations,notifications};
  }finally{
    closed=true;
    // Cleanup changes wait queues too; callers must maintain the exclusivity precondition.
    for(const view of views)Atomics.notify(view,0);
    // All owned waiters have been notified; do not infer identity from cleanup timing.
  }
}
module.exports={partition,Inconclusive};
