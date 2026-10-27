'use strict';
const fs=require('fs'),path=require('path'),os=require('os');
const main=process.argv[2],perf=process.argv[3];
const models=JSON.parse(fs.readFileSync(path.join(main,'manifest.json'),'utf8')).models;
const summary=JSON.parse(fs.readFileSync(path.join(perf,'performance.json'),'utf8')).summary;
function oracle(m,x){const vs=[],get=a=>a[0]==='input'?(x>>>a[1])&1:vs[a[1]];
for(const [op,a,b] of m.gates){let u=get(a),v=get(b);vs.push(op==='and'?u&v:op==='or'?u|v:u^v);}return vs.at(-1);}
const rows=[];
for(const t of summary){
 const run=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(perf,`${t.name}-${t.mode}-optimized.wasm`)))).exports.run;
 const bench=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(perf,t.file)))).exports.bench,m=models[t.name];
 let calls=0,seed=0x20261022;
 for(let i=0;i<(1<<m.inputs)+2048;i++){seed=(Math.imul(seed,1664525)+1013904223)>>>0;const x=i<(1<<m.inputs)?i:seed;if(run(x)!==oracle(m,x))throw Error('Optimized mismatch');calls++;}
 let benchCalls=0;
 for(const n of [1,3,31])for(const initial of [0,1,-1,0x80000000]){
   let x=initial,total=0;for(let i=0;i<n;i++){x=(Math.imul(x,1664525)+1013904223)>>>0;total=(total+oracle(m,x))|0;}
   if(bench(n,initial)!==total)throw Error('Wrapper checksum mismatch');benchCalls++;
 }
 rows.push({name:t.name,mode:t.mode,run_calls:calls,bench_calls:benchCalls});
}
process.stdout.write(JSON.stringify({rows,cpu:os.cpus()[0].model,os:os.platform(),arch:os.arch(),node:process.version,v8:process.versions.v8}));
