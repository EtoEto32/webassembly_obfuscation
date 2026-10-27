'use strict';
const{parentPort,workerData:d}=require('node:worker_threads');
const api=new WebAssembly.Instance(d.module,{env:{memory:d.memory}}).exports,ctrl=new Int32Array(d.control);
parentPort.postMessage({ready:true});Atomics.wait(ctrl,0,0);
if(d.kind==='ticket'){
 const values=new Uint32Array(d.count);for(let i=0;i<values.length;i++)values[i]=api.add(0,1)>>>0;
 parentPort.postMessage({values});
}else{
 const values=d.jobs.map((ops,j)=>ops.map(op=>{const r=api[op.op](16*(j+1),...op.args);return r===undefined?null:r>>>0;}));
 parentPort.postMessage({values});
}
