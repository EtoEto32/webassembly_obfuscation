'use strict';
const fs=require('fs'),assert=require('assert');
const t=performance.now(),e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(process.argv[2]))).exports;
const n=e.arity.value;assert(n>=2&&n<=20);const words=new Uint32Array(e.memory.buffer),truth=[];
let queries=0;const q0=performance.now();
for(let base=0;base<(1<<n);base+=128){
 for(let v=0;v<n;v++)for(let w=0;w<4;w++){
  let word=0;for(let b=0;b<32;b++)word|=(((base+32*w+b)>>>v)&1)<<b;
  words[4*v+w]=word>>>0;
 }
 e.run();queries++;
 for(let b=0;b<Math.min(128,(1<<n)-base);b++)truth.push((words[4*n+(b>>>5)]>>>(b&31))&1);
}
console.log(JSON.stringify({arity:n,queries,boolean_inputs:1<<n,query_ms:performance.now()-q0,node_body_ms:performance.now()-t,truth}));
