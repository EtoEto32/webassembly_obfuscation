'use strict';
// Differential checks and a separate fresh-process JS->Wasm timing diagnostic.
const fs=require('node:fs'), path=require('node:path'), assert=require('node:assert/strict');
const dir=path.resolve(process.argv[2]);
const manifest=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json'),'utf8'));
let seed=211021;
const rand=()=>{seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed>>>0;};
function setup(memory,kind){
 const bytes=new Uint8Array(memory.buffer);bytes.fill(0xA5);
 const view=new DataView(memory.buffer);
 for(let i=0;i<64;i++){
  view.setUint32(64+12*i,64+12*(kind===0?(i+1)%64:rand()%64),true);
  view.setUint32(68+12*i,64+12*(kind===0?(i+7)%64:rand()%64),true);
  view.setUint32(72+12*i,rand(),true);
 }
 return view;
}
function reference(view,n,forced,head,bits,iters){
 let p=head>>>0;
 const load=(p,off)=>{const a=(p>>>0)+off;if(a+4>view.byteLength)throw Error('bounds');return view.getUint32(a,true);};
 for(let i=0;i<n+(iters&31);i++)p=load(p,forced&&i===(iters&31)?4:((bits>>>(i&31))&1)*4);
 return load(p,8);
}
function invoke(fn,args){try{return {value:fn(...args)>>>0};}catch(e){if(e instanceof WebAssembly.RuntimeError)return {trap:true};throw e;}}
function expected(view,n,forced,args){try{return {value:reference(view,n,forced,...args)};}catch(e){return {trap:true};}}
function median(xs){xs=[...xs].sort((a,b)=>a-b);return xs[Math.floor(xs.length/2)];}
if(process.argv[3]==='bench'){
 const name=process.argv[4], row=manifest.rows.find(r=>r.file===name);assert(row);
 const e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(dir,name)))).exports;
 const view=setup(e.memory,1), count=16384, queries=Array.from({length:256},()=>[64,rand(),rand()]);
 let want=0;
 for(let j=0;j<count;j++)want=(Math.imul(want,1664525)+reference(view,row.n,!!row.forced,...queries[j&255])+j)>>>0;
 const batch=()=>{let sum=0;for(let j=0;j<count;j++)sum=(Math.imul(sum,1664525)+(e.run(...queries[j&255])>>>0)+j)>>>0;assert.equal(sum,want);};
 batch();batch(); // 32768 warmup calls, both checked.
 const samples=[];
 for(let r=0;r<9;r++){let t=process.hrtime.bigint();batch();samples.push(Number(process.hrtime.bigint()-t)/count);}
 console.log(JSON.stringify({file:name,n:row.n,mode:row.mode,node:process.version,v8:process.versions.v8,
  warmup_calls:count*2,batches:9,calls_per_batch:count,ns_per_call_median:median(samples),samples,
  peak_rss_kib:process.resourceUsage().maxRSS,scope:'JS to Wasm calls, not isolated native kernel'}));
}else{
 const report={scope:'finite differential tests; no all-input proof',node:process.version,v8:process.versions.v8,rows:[]};
 for(const row of manifest.rows){
  const bytes=fs.readFileSync(path.join(dir,row.file));assert(WebAssembly.validate(bytes));
  const e=new WebAssembly.Instance(new WebAssembly.Module(bytes)).exports;
  let calls=0,traps=0;
  for(let kind=0;kind<3;kind++){
   seed=211021+kind;const view=setup(e.memory,kind),snapshot=Buffer.from(new Uint8Array(e.memory.buffer));
   const args=[];
   for(const bits of [0,1,0x7fffffff,0x80000000,0xffffffff])
    for(const iters of [0,1,7,31,32,33,0x7fffffff,0x80000000,0xffffffff])args.push([64,bits,iters]);
   for(let k=0;k<512;k++)args.push([64+12*(rand()%64),rand(),rand()]);
   for(const head of [0,1,65523,65524,65525,65528,65532,65535,65536,0xffffffff])
    for(const bits of [0,1,0xffffffff])args.push([head,bits,0]);
   for(const a of args){const want=expected(view,row.n,!!row.forced,a),got=invoke(e.run,a);assert.deepEqual(got,want,JSON.stringify({file:row.file,a}));calls++;traps+=!!got.trap;}
   assert(Buffer.from(new Uint8Array(e.memory.buffer)).equals(snapshot),'read-only memory changed');
  }
  report.rows.push({file:row.file,calls,traps,mismatches:0,validation:true,memory_unchanged:true});
 }
 report.calls=report.rows.reduce((a,r)=>a+r.calls,0);report.traps=report.rows.reduce((a,r)=>a+r.traps,0);
 const out=path.join(dir,'checks.json');fs.writeFileSync(out,JSON.stringify(report,null,2),{flag:'wx'});
 console.log(JSON.stringify({modules:report.rows.length,calls:report.calls,traps:report.traps,mismatches:0}));
}
