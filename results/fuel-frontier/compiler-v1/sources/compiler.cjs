'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=process.argv[2],mf=JSON.parse(fs.readFileSync(path.join(root,'manifest.json')));
const mix=x=>(Math.imul(x^13,1664525)+1013904223)>>>0;
let checks=0,transformedChecks=0,secretPairs=0;
class Stop extends Error{}
for(const r of mf.records){
 let events=[],budget=10000,spent=0;
 const imports={env:{mark(x){events.push([x>>>0,spent,budget]);}},fuel:{charge(v){v=Number(v);if(v>budget)throw new Stop();budget-=v;spent+=v;}}};
 const original=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(root,r.binary))),imports);
 const transformed=r.status==='accepted'?new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(root,r.binary.replace('.wasm','-frontier.wasm')))),imports):null;
 const inputs=[0,1,0x7fffffff,0x80000000,0xffffffff,...Array.from({length:100},(_,i)=>Math.imul(i,1013904223)>>>0)];
 for(const payload of inputs)for(const secret of [0,1,2,3]){
  let expected=payload>>>0;if(r.case==='classify')expected=Math.imul(expected,3)>>>0;else for(let i=0;i<5;i++)expected=mix(expected);
  budget=10000;spent=0;events=[];const val=original.exports.run(secret,payload)>>>0;assert.equal(val,expected);checks++;
  if(transformed){budget=10000;spent=0;events=[];assert.equal(transformed.exports.run(secret,payload)>>>0,expected);transformedChecks++;}
 }
 if(transformed)for(let b=0;b<=r.summary.prefix.at(-1)+2;b++){
  const traces=[];
  for(const secret of [0,1]){budget=b;spent=0;events=[];let status='complete';try{transformed.exports.run(secret,123);}catch(e){if(!(e instanceof Stop))throw e;status='budget';}traces.push([status,events,spent,budget]);}
  assert.deepEqual(traces[0],traces[1]);secretPairs++;
 }
}
const result={checks,transformedChecks,secretPairs,accepted:mf.records.filter(x=>x.status==='accepted').length,total:mf.records.length};
fs.writeFileSync(path.join(root,'results.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result));
