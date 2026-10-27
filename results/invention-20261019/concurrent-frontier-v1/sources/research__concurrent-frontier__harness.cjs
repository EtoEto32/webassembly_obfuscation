'use strict';
const fs=require('node:fs');const path=require('node:path');const {Worker}=require('node:worker_threads');
function once(w,expected){return new Promise((resolve,reject)=>{
 const timer=setTimeout(()=>{cleanup();reject(new Error('worker timeout'))},10000);
 function cleanup(){clearTimeout(timer);w.off('message',message);w.off('error',error);}
 function message(m){if(m.error){cleanup();reject(new Error(m.error))}else if(m[expected]){cleanup();resolve(m)}}
 function error(e){cleanup();reject(e)}w.on('message',message);w.on('error',error);
});}
async function pool(file,workers){
 const module=new WebAssembly.Module(fs.readFileSync(file));
 const memory=new WebAssembly.Memory({initial:1,maximum:1,shared:true});
 const instance=new WebAssembly.Instance(module,{env:{memory}}),heap=new Int32Array(memory.buffer);
 const gate=new SharedArrayBuffer(8),g=new Int32Array(gate);let epoch=0;
 const ws=[];const ready=[];
 for(let i=0;i<workers;i++){const w=new Worker(path.join(__dirname,'worker.cjs'),{workerData:{module,memory,gate,id:i}});ws.push(w);ready.push(once(w,'ready'));}
 await Promise.all(ready); // Every active data segment is initialized before jobs start.
 return {heap,memory,instance,async run(input){
   instance.exports.init(...input);Atomics.store(g,0,0);const e=++epoch;
   const done=ws.map(w=>once(w,'done'));ws.forEach(w=>w.postMessage({epoch:e}));
   const deadline=Date.now()+10000;
   while(Atomics.load(g,0)!==workers){if(Date.now()>deadline)throw new Error('barrier timeout');const v=Atomics.load(g,0);Atomics.wait(g,0,v,100);}
   Atomics.store(g,1,e);Atomics.notify(g,1);await Promise.all(done);
   return instance.exports.result();
 },close:()=>Promise.all(ws.map(w=>w.terminate()))};
}
function inputs(randomN=256){
 const b=[0,1,-1,0x7fffffff,-2147483648,31,32,0x55555555],a=[];
 for(const x of b)for(const y of b)for(const z of b)a.push([x,y,z]);
 let s=20261019;function r(){s^=s<<13;s^=s>>>17;s^=s<<5;return s|0;}
 for(let i=0;i<randomN;i++)a.push([r(),r(),r()]);return a;
}
function owners(heap){let count={};const n=heap[0];for(let i=0;i<n;i++){const at=64+8*i;if(heap[at]>=2){const w=heap[at+6];count[w]=(count[w]||0)+1;if(heap[at+5]!==3)throw new Error('unfinished node');}}return count;}
module.exports={pool,inputs,owners};
