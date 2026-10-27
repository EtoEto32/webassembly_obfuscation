'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const [root,mode]=process.argv.slice(2),manifest=JSON.parse(fs.readFileSync(path.join(root,'manifest.json')));
const rows=[];const median=a=>[...a].sort((x,y)=>x-y)[Math.floor(a.length/2)];
for(const f of manifest.fixtures){
 const s=f.modes.frontier.summary;
 const mp=s.prefix.map((_,i)=>Math.max(...f.inputs.map(x=>x.expected.prefix[i])));
 const delta=[mp[0],...mp.slice(1).map((v,i)=>v-mp[i])];
 let budget=0,spent=0,j=0,events=0,charges=0;
 function charge(v){v=Number(v);if(!Number.isSafeInteger(v)||v<0||v>budget)throw Error('bad charge');budget-=v;spent+=v;charges++;}
 const bytes=fs.readFileSync(path.join(root,f.name,(mode==='manual'?'original':mode)+'-O3.wasm'));
 const start=process.hrtime.bigint();
 const inst=new WebAssembly.Instance(new WebAssembly.Module(bytes),{
  env:{mark(x){events=(Math.imul(events,33)+(x>>>0))>>>0;if(mode==='manual')charge(delta[++j]);}},
  fuel:{charge,pad(total){charge(Number(total)-spent);}}
 });
 const setupNs=Number(process.hrtime.bigint()-start);
 function one(i){budget=100000;j=0;spent=0;events=0;charges=0;if(mode==='manual')charge(delta[0]);const v=inst.exports.run(i%4,Math.imul(i,123456789))>>>0;return (v^events)>>>0;}
 for(let i=0;i<2000;i++)one(i);
 const samples=[],checks=[];
 for(let r=0;r<9;r++){
  let c=0;const now=process.hrtime.bigint();
  for(let i=0;i<5000;i++)c=(Math.imul(c,31)+one(i))>>>0;
  samples.push(Number(process.hrtime.bigint()-now)/5000);checks.push(c);
 }
 assert(checks.every(x=>x===checks[0]));
 rows.push({name:f.name,mode,nsPerCall:samples,medianNs:median(samples),checksum:checks[0],setupNs,bytes:bytes.length,lastCharges:charges,lastLogicalSpent:spent});
}
if(global.gc)global.gc();
console.log(JSON.stringify({mode,node:process.version,v8:process.versions.v8,warmup:2000,repeats:9,callsPerRepeat:5000,rows,memory:process.memoryUsage(),resourceUsage:process.resourceUsage()}));
