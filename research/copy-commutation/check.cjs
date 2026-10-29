'use strict';
const fs=require('node:fs'),path=require('node:path');const dir=process.argv[2];
const rows=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json')));let calls=0;
const cases=[[0,1,1],[1,0,1],[0,2,2],[2,0,2],[0,0,65536],[65535,65534,1],[65534,65535,1],[65536,65536,0],[65537,0,0],[0,65536,0],[0xffffffff,0,0],[0,0,0xffffffff],[65535,0,2],[0,65535,2]];
for(const d of [0,1,65535,65536,0xffffffff])for(const s of [0,1,65535,65536,0xffffffff])for(const n of [0,1,2,65536])cases.push([d,s,n]);
let seed=20261019;function rnd(){seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed>>>0;}
for(let i=0;i<128;i++)cases.push(i%4===0?[rnd(),rnd(),rnd()]:[rnd()%65537,rnd()%65537,rnd()%512]);
const rol=(x,r)=>((x<<r)|(x>>>(8-r)))&255;
function encode(x,mode){
 const y=new Uint8Array(x.length);
 for(let i=0;i<x.length;i++)y[i]=mode==='uniform'?rol((x[i]*5)&255,3):mode==='position'?rol(x[i],i%8):x[i];
 if(mode==='coupled')for(let i=0;i<x.length;i+=2)if((y[i]^y[i+1])&1)[y[i],y[i+1]]=[y[i+1],y[i]];
 return y;
}
function call(f,...args){calls++;try{return {value:f(...args)}}catch(e){if(!(e instanceof WebAssembly.RuntimeError))throw e;return {trap:true}}}
function equal(a,b){return a.trap===b.trap&&a.value===b.value;}
const results=[];let positive_mismatches=0,negative_with_counterexample=0,unmodified_copy_counts=0;
for(const row of rows){
 const src=new WebAssembly.Module(fs.readFileSync(path.join(dir,row.source))),target=new WebAssembly.Module(fs.readFileSync(path.join(dir,row.file))),probe=new WebAssembly.Module(fs.readFileSync(path.join(dir,row.probe)));
 const initial=new Uint8Array(fs.readFileSync(path.join(dir,`initial-${row.seed}.bin`)));
 let badRead=0,badMemory=0,badTrap=0,traps=0,first=null;
 for(const args of cases){
  const original=new WebAssembly.Instance(src).exports,output=new WebAssembly.Instance(target).exports,view=new WebAssembly.Instance(probe).exports;
  let [d,s,n]=args.map(x=>row.alignment===1?x>>>0:(x&-2)>>>0);const expected=new Uint8Array(initial),trap=d+n>65536||s+n>65536;
  if(!trap)expected.copyWithin(d,s,s+n);else traps++;
  for(const inst of [original,output,view]){const got=call(inst.copy,...args);if(!!got.trap!==trap)badTrap++;}
  const mem=new Uint8Array(view.memory.buffer),enc=encode(expected,row.mode);let index=-1;
  for(let i=0;i<65536;i++)if(mem[i]!==enc[i]){index=i;break;}
  if(index>=0){badMemory++;first??={input:args,effective:[d,s,n],offset:index,expected:enc[index],actual:mem[index],trap};}
  for(const addr of [0,1,2,3,d&65535,s&65535,65534,65535,65536,0xffffffff]){
   const want=addr>=65536?{trap:true}:{value:expected[addr]};
   for(const inst of [original,output,view])if(!equal(call(inst.read,addr),want))badRead++;
  }
  unmodified_copy_counts++;
 }
 const rowResult={file:row.file,mode:row.mode,alignment:row.alignment,legal:row.legal,cases:cases.length,copy_traps:traps,bad_reads:badRead,bad_memory_cases:badMemory,bad_traps:badTrap,first_counterexample:first};results.push(rowResult);
 if(row.legal)positive_mismatches+=badRead+badMemory+badTrap;else if(badRead&&badMemory)negative_with_counterexample++;
 console.log(row.file,badMemory);
}
fs.writeFileSync(path.join(dir,'native.json'),JSON.stringify({cases,total_calls:calls,positive_mismatches,negative_with_counterexample,unmodified_copy_counts,results},null,2));
if(positive_mismatches||negative_with_counterexample!==rows.filter(r=>!r.legal).length)throw new Error('classification mismatch');
