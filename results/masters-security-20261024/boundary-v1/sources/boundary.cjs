'use strict';
const fs=require('fs'),path=require('path'),crypto=require('crypto'),assert=require('assert/strict');
const out=path.resolve(process.argv[2]),manifest=JSON.parse(fs.readFileSync(path.join(out,'manifest.json')));
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
function union(a){const r=[];for(const [l,h] of a.filter(x=>x[0]<x[1]).sort((x,y)=>x[0]-y[0])){const p=r.at(-1);if(p&&l<=p[1])p[1]=Math.max(p[1],h);else r.push([l,h]);}return r;}
function val(e,args){if(e[0]==='const')return e[1];if(e[0]==='arg')return args[e[1]]>>>0;const a=val(e[1],args),b=val(e[2],args);if(e[0]==='add')return(a+b)>>>0;if(e[0]==='sub')return(a-b)>>>0;if(e[0]==='and')return(a&b)>>>0;throw Error('bad expression');}
function intersection(a,b){return union(a.flatMap(([l,h])=>b.map(([x,y])=>[Math.max(l,x),Math.min(h,y)])));}
function ranges(summary,args,R){if(summary.kind==='reject')throw Error('rejected');if(summary.kind==='full')return R;return intersection(R,summary.writes.map(w=>{const l=val(w.addr,args)+w.offset;return[l,l+val(w.length,args)];}));}
function runMemoryView(memory,kept,R){const view=new Uint8Array(memory.buffer);return R.map(([l,h])=>{const b=view.slice(l,h);for(const [x,y] of kept){const low=Math.max(l,x),high=Math.min(h,x+y.length);if(low<high)b.set(y.subarray(low-x,high-x),low-l);}return b;});}
async function check(e){
 const bytes=fs.readFileSync(path.join(out,e.file));assert.equal(hash(bytes),e.sha256);assert(WebAssembly.validate(bytes));
 let instance,depth=0,maxDepth=0,current,rows=[];
 const host={
  mutate:()=>{const v=new Uint8Array(instance.exports.memory.buffer);v[512]^=255;},
  before:()=>{
   depth++;maxDepth=Math.max(maxDepth,depth);
   try{
    const memory=instance.exports.memory,original=new Uint8Array(memory.buffer),dv=new DataView(memory.buffer);
    // Typed read contract: the descriptor and a bounded slice identified by it.
    const length=dv.getUint32(0,true),pointer=dv.getUint32(4,true);
    assert(length<=4096 && pointer+length<=original.length);
    const R=union([[0,8],[pointer,pointer+length],[pointer+4,pointer+Math.min(length,24)]]);
    const oracle=R.map(([l,h])=>original.slice(l,h));
    const selected=ranges(e.summary,current,R),kept=selected.map(([l,h])=>[l,original.slice(l,h)]);
    let trap=false;
    try{instance.exports.callback(...current);}catch(err){assert(err instanceof WebAssembly.RuntimeError);trap=true;}
    const result=runMemoryView(memory,kept,R);
    for(let i=0;i<result.length;i++)assert.deepEqual(result[i],oracle[i],e.file);
    const restored=runMemoryView(memory,[],R);let noCopyMismatch=false;
    for(let i=0;i<restored.length;i++)if(!Buffer.from(restored[i]).equals(Buffer.from(oracle[i])))noCopyMismatch=true;
    rows.push({arguments:current,readRanges:R,saveRanges:selected,savedBytes:kept.reduce((s,x)=>s+x[1].length,0),fullBytes:R.reduce((s,[l,h])=>s+h-l,0),trap,noCopyMismatch});
   }finally{depth--;}
  }
 };
 instance=(await WebAssembly.instantiate(bytes,{host})).instance;
 let seed=20261024;
 const rand=()=>{seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed>>>0;};
 const cases=[[512,255,0],[516,255,8],[8,255,16],[4096,255,64],[-1,255,2],[-4,255,16],[131071,255,64]];
 for(let i=0;i<100;i++)cases.push([rand()%9000,rand()|0,rand()%65]);
 for(let i=0;i<cases.length;i++){
  const memory=instance.exports.memory,v=new Uint8Array(memory.buffer);for(let j=0;j<v.length;j++)v[j]=(j*7+1)&255;
  const d=new DataView(memory.buffer);d.setUint32(0,[0,8,64,1024,4096][i%5],true);d.setUint32(4,512,true);
  current=cases[i];instance.exports.drive();assert.equal(depth,0);
 }
 assert.equal(maxDepth,1);
 return{file:e.file,summary:e.summary,cases:rows.length,traps:rows.filter(x=>x.trap).length,noCopyMismatches:rows.filter(x=>x.noCopyMismatch).length,savedBytes:rows.reduce((s,x)=>s+x.savedBytes,0),fullBytes:rows.reduce((s,x)=>s+x.fullBytes,0),mismatches:0,actualReentry:true,rows};
}
(async()=>{const result={scope:'Core Wasm drive -> host import -> same instance callback; not Component Model ABI',entries:[]};for(const e of manifest)result.entries.push(await check(e));fs.writeFileSync(path.join(out,'results.json'),JSON.stringify(result,null,2));console.log(JSON.stringify({modules:result.entries.length,cases:result.entries.reduce((s,x)=>s+x.cases,0),mismatches:0,traps:result.entries.reduce((s,x)=>s+x.traps,0)}));})().catch(e=>{console.error(e.stack);process.exitCode=1;});
