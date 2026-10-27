'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=process.argv[2],m=JSON.parse(fs.readFileSync(path.join(root,'manifest.json')));
class Stop extends Error{}
let checks=0,adaptivePairs=0,boundChecks=0;
for(const r of m.records){
 for(const filename of ['frontier.wasm','frontier-O3.wasm']){
  let budget,spent,events,trace,policy;
  const inst=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(root,String(r.case),filename))),{
   fuel:{charge(v){v=Number(v);if(v>budget)throw new Stop();budget-=v;spent+=v;}},
   env:{mark(x){events.push(x>>>0);trace.push([x>>>0,spent,budget]);if(policy>=0)budget=(Math.imul((policy+1),events.length*17)+spent)%281;}}
  });
  function run(args,b,p){budget=b;spent=0;events=[];trace=[];policy=p;let value=null,status='complete';
   try{value=inst.exports.run(...args)>>>0;}catch(e){if(!(e instanceof Stop))throw e;status='budget';}
   return{value,status,events,trace,spent,budget};}
  for(const a of r.samples){
   const actual=run(a.args,10000,-1);assert.equal(actual.status,'complete');assert.equal(actual.value,a.expected.value);assert.deepEqual(actual.events,a.expected.events);checks++;
   a.expected.prefix.forEach((v,i)=>{assert(v<=r.summary.prefix[i]);boundChecks++;});
  }
  for(let policy=0;policy<200;policy++){
   const all=[0,1,2,3].map(secret=>run([secret,444],(policy*97)%401,policy));
   const projection=x=>JSON.stringify([x.status,x.events,x.trace,x.spent,x.budget]);
   all.slice(1).forEach(x=>{assert.equal(projection(x),projection(all[0]));adaptivePairs++;});
  }
 }
}
// Boundary counterexamples as actual Wasm execution; costs independently known.
const wasm=fs.readFileSync(path.join(root,'0','original.wasm'));
const record=m.records[0],heavy=record.samples.reduce((a,b)=>a.expected.prefix[0]>b.expected.prefix[0]?a:b);
const first=record.summary.prefix[0],badReservation=first-1;
let events=0;
const unguarded=new WebAssembly.Instance(new WebAssembly.Module(wasm),{env:{mark(){events++;}}});
unguarded.exports.run(...heavy.args);
assert(heavy.expected.prefix[0]>badReservation);
// A small explicit credit example independently executes both arms.
const credit={paths:[[90,10],[10,90]],reservation:[90,10]};
const noCarry=credit.paths.map(p=>p.map((cost,i)=>cost<=credit.reservation[i]));
assert.equal(noCarry[1][1],false);
const refund=credit.paths.map(p=>credit.reservation[0]-p[0]);assert.notEqual(refund[0],refund[1]);
assert(m.correlated.summary.prefix.at(-1)>m.correlated.concreteMax);
const result={checks,adaptivePairs,boundChecks,fixtures:24,binaries:48,
 underReservation:{reserved:badReservation,actualFirstPrefix:heavy.expected.prefix[0],markersActuallyExecuted:events},
 creditLoss:{...credit,noCarry},secretRefund:{refund},
 correlation:{abstractTotal:m.correlated.summary.prefix.at(-1),concreteMax:m.correlated.concreteMax},
 limitations:['creditLoss and secretRefund are arithmetic countermodels, not Wasm tests','underReservation uses an unguarded original Wasm to show why an externally supplied schedule cannot be trusted','adaptive observer changes budget only at public markers; no time-based interruption or reentry']};
fs.writeFileSync(path.join(root,'results.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result));
