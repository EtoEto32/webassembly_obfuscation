'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const [root,mode]=process.argv.slice(2),mf=JSON.parse(fs.readFileSync(path.join(root,'manifest.json'))),rows=[];
for(const rec of mf.records.filter(r=>r.status==='accepted')){
 const p=rec.modes.frontier.summary.prefix.map((_,i)=>Math.max(...rec.independentCost.map(x=>x.prefix[i])));
 assert.deepEqual(p,rec.modes.frontier.summary.prefix);
 const delta=[p[0],...p.slice(1).map((v,i)=>v-p[i])];
 let budget,spent,j,hash,charges;
 function charge(v){v=Number(v);if(!Number.isSafeInteger(v)||v<0||v>budget)throw Error('budget');budget-=v;spent+=v;charges++;}
 const bytes=fs.readFileSync(path.join(root,rec.name+'-'+(mode==='manual'?'original':mode)+'.wasm'));
 const begin=process.hrtime.bigint();
 const instance=new WebAssembly.Instance(new WebAssembly.Module(bytes),{
  env:{mark(id,value){hash=(Math.imul(hash,31)^id^value)>>>0;if(mode==='manual')charge(delta[++j]);}},
  fuel:{charge,pad(total){charge(Number(total)-spent);}}
 });
 const setupNs=Number(process.hrtime.bigint()-begin);
 function one(i){budget=10000;spent=0;j=0;hash=0;charges=0;if(mode==='manual')charge(delta[0]);return(instance.exports.run(i%2,Math.imul(i,1013904223))^hash)>>>0;}
 for(let i=0;i<2000;i++)one(i);
 const samples=[],checks=[];
 for(let rep=0;rep<9;rep++){
  let checksum=0;const start=process.hrtime.bigint();
  for(let i=0;i<5000;i++)checksum=(Math.imul(checksum,31)+one(i))>>>0;
  samples.push(Number(process.hrtime.bigint()-start)/5000);checks.push(checksum);
 }
 assert(checks.every(x=>x===checks[0]));
 rows.push({name:rec.name,mode,nsPerCall:samples,medianNs:[...samples].sort((a,b)=>a-b)[4],checksum:checks[0],bytes:bytes.length,setupNs,lastCharges:charges,lastSpent:spent});
}
if(global.gc)global.gc();
console.log(JSON.stringify({mode,node:process.version,v8:process.versions.v8,rows,memory:process.memoryUsage(),resourceUsage:process.resourceUsage()}));
