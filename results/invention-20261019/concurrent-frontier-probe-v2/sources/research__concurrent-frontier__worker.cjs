'use strict';
const {parentPort, workerData} = require('node:worker_threads');
const instance=new WebAssembly.Instance(workerData.module,{env:{memory:workerData.memory}});
const gate=new Int32Array(workerData.gate);
parentPort.on('message', m=>{
  try {
    Atomics.add(gate,0,1);Atomics.notify(gate,0);
    while(Atomics.load(gate,1)!==m.epoch) Atomics.wait(gate,1,Atomics.load(gate,1),100);
    instance.exports.work(workerData.id);
    parentPort.postMessage({done:m.epoch});
  } catch(e){parentPort.postMessage({error:String(e)});}
});
parentPort.postMessage({ready:true});
