'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=process.argv[2],manifest=JSON.parse(fs.readFileSync(path.join(root,'manifest.json')));
class FuelStop extends Error {}
function engine(bytes,mode,summary){
 let budget=0,spent=0,events=[],trace=[],j=0;
 function charge(amount){
  amount=Number(amount);assert(Number.isSafeInteger(amount)&&amount>=0);
  if(amount>budget){trace.push(['stop',spent,budget]);throw new FuelStop();}
  budget-=amount;spent+=amount;
 }
 const inst=new WebAssembly.Instance(new WebAssembly.Module(bytes),{
  env:{mark(x){events.push(x>>>0);trace.push(['mark',x>>>0,spent,budget]);
   if(mode==='manual'){j++;charge(summary.delta[j]);}}},
  fuel:{charge,pad(total){charge(Number(total)-spent);}}
 });
 return (args,b)=>{
  budget=b;spent=0;events=[];trace=[];j=0;let value=null,status='complete';
  try{if(mode==='manual')charge(summary.delta[0]);value=inst.exports.run(...args)>>>0;}
  catch(e){if(e instanceof FuelStop)status='budget';else throw e;}
  return {status,value,events,trace,spent,budget};
 };
}
let correctCalls=0,pairComparisons=0,budgetCalls=0,summaryUnderestimates=0;
const rows=[];
for(const f of manifest.fixtures){
 const dir=path.join(root,f.name),s=f.modes.frontier.summary;
 const originals=engine(fs.readFileSync(path.join(dir,'original.wasm')),'original',s);
 const runs={manual:engine(fs.readFileSync(path.join(dir,'original.wasm')),'manual',s)};
 for(const mode of ['dynamic','late','whole','segment','frontier'])for(const suffix of ['', '-O3'])
  runs[mode+suffix]=engine(fs.readFileSync(path.join(dir,mode+suffix+'.wasm')),mode,s);
 const maxBudget=Math.max(s.prefix.at(-1),s.segment.reduce((a,b)=>a+b,0))+2;
 for(const sample of f.inputs){
  const o=originals(sample.args,maxBudget);assert.equal(o.value,sample.expected.value);assert.deepEqual(o.events,sample.expected.events);
  for(let i=0;i<s.prefix.length;i++)if(sample.expected.prefix[i]>s.prefix[i])summaryUnderestimates++;
  for(const [mode,run] of Object.entries(runs)){
   const a=run(sample.args,maxBudget);assert.equal(a.status,'complete');assert.equal(a.value,o.value);assert.deepEqual(a.events,o.events);
   if(mode.startsWith('dynamic'))assert.equal(a.spent,sample.expected.prefix.at(-1));
   correctCalls++;
  }
 }
 const stats={};
 for(const [mode,run] of Object.entries(runs)){
  let leakBudgets=0,completed=0,eventCount=0;let firstLeak=null;
  for(let b=0;b<=maxBudget;b++){
   const records=[0,1,2,3].map(secret=>run([secret,123456789],b));budgetCalls+=4;
   const project=r=>JSON.stringify([r.status,r.events,r.trace,r.spent,r.budget]);
   const differs=records.some(r=>project(r)!==project(records[0]));
   if(differs){leakBudgets++;if(!firstLeak)firstLeak={budget:b,records};}
   if(['manual','whole','segment','frontier','whole-O3','segment-O3','frontier-O3'].includes(mode))assert(!differs,`${f.name} ${mode} budget ${b}`);
   completed+=records[0].status==='complete'?1:0;eventCount+=records[0].events.length;pairComparisons+=3;
   if(mode==='frontier')assert.deepEqual(records,[0,1,2,3].map(secret=>runs.manual([secret,123456789],b)));
  }
  stats[mode]={leakBudgets,completedBudgets:completed,publicEventsAcrossBudgets:eventCount,firstLeak};
 }
 rows.push({name:f.name,envelope:s.prefix,delta:s.delta,segment:s.segment,wholeTotal:s.prefix.at(-1),segmentTotal:s.segment.reduce((a,b)=>a+b,0),maxBudget,stats});
}
assert.equal(summaryUnderestimates,0);
const result={node:process.version,v8:process.versions.v8,correctCalls,budgetCalls,pairComparisons,summaryUnderestimates,rejected:manifest.rejected,rows};
fs.writeFileSync(path.join(root,'results.json'),JSON.stringify(result,null,2));
console.log(JSON.stringify({correctCalls,budgetCalls,pairComparisons,summaryUnderestimates,rows:rows.map(r=>({name:r.name,whole:r.wholeTotal,segment:r.segmentTotal,dynamicLeak:r.stats.dynamic.leakBudgets,lateLeak:r.stats.late.leakBudgets,frontierLeak:r.stats.frontier.leakBudgets,frontierEvents:r.stats.frontier.publicEventsAcrossBudgets,wholeEvents:r.stats.whole.publicEventsAcrossBudgets}))}));
