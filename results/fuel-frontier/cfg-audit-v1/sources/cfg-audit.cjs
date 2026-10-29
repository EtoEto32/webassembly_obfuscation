'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=process.argv[2],mf=JSON.parse(fs.readFileSync(path.join(root,'manifest.json')));let checks=0,bounds=0,budgetPairs=0;
class Stop extends Error{}
for(const r of mf.records){
 for(const mode of ['original','dynamic','late','whole','segment','frontier','frontier-O3','late-O3']){
  let spent,budget,events;
  function charge(v){v=Number(v);assert(v>=0);if(v>budget)throw new Stop();spent+=v;budget-=v;}
  const inst=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(root,String(r.case),mode+'.wasm'))),{env:{mark(id,value){events.push([id>>>0,value>>>0,spent]);}},fuel:{charge,pad(v){charge(Number(v)-spent);}}});
  function run(args,b){spent=0;budget=b;events=[];let value=null,status='complete';try{value=inst.exports.run(...args)>>>0;}catch(e){if(!(e instanceof Stop))throw e;status='budget';}return{value,status,events,spent,budget};}
  for(const sample of r.samples){
   const actual=run(sample.args,10000);assert.equal(actual.status,'complete');assert.equal(actual.value,sample.expected.value);assert.deepEqual(actual.events.map(e=>e.slice(0,2)),sample.expected.events);checks++;
   if(mode==='dynamic'){const p=sample.expected.prefix;assert.equal(actual.spent,p.at(-1));actual.events.forEach((e,i)=>assert.equal(e[2],p[i]));p.forEach((v,i)=>{assert(v<=r.summary.prefix[i]);bounds++;});}
  }
  if(mode.startsWith('frontier')||mode==='whole'||mode==='segment'){
   for(let b=0;b<=r.summary.segment.reduce((x,y)=>x+y,0)+2;b++){
    const x=run([0,123],b),y=run([1,123],b);
    // Payloads/results are explicit releases; compare accounting/event identity.
    const p=z=>[z.status,z.events.map(e=>[e[0],e[2]]),z.spent,z.budget];assert.deepEqual(p(x),p(y));budgetPairs++;
   }
  }
 }
}
const result={fixtures:32,checks,bounds,budgetPairs,allPassed:true};fs.writeFileSync(path.join(root,'results.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result));
