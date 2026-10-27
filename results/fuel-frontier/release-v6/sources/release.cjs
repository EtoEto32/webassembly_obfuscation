'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=process.argv[2],m=JSON.parse(fs.readFileSync(path.join(root,'manifest.json')));
class Stop extends Error{}
function engine(name){let budget,spent,events;const inst=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(root,name+'.wasm'))),{
 env:{mark(id,v){events.push([id>>>0,v>>>0,spent,budget]);}},fuel:{charge(v){v=Number(v);assert(Number.isSafeInteger(v)&&v>=0);if(v>budget)throw new Stop();budget-=v;spent+=v;},pad(total){const v=Number(total)-spent;assert(v>=0);if(v>budget)throw new Stop();budget-=v;spent+=v;}}
 });return(args,b)=>{budget=b;spent=0;events=[];let value=null,status='complete';try{value=inst.exports.run(...args)>>>0;}catch(e){if(!(e instanceof Stop))throw e;status='budget';}return{value,status,events,spent,budget};};}
const mix=x=>(Math.imul(x^13,1664525)+1013904223)>>>0;
function oracle(secret,payload){let x=payload>>>0,mid=0;for(let i=1;i<=13;i++){x=mix(x);if(i===(secret&1?12:1))mid=x>>>28;}return{value:x>>>24,events:[[100,mid]]};}
const project=r=>({value:r.value,events:r.events.map(e=>e.slice(0,2))});
const original=engine('original'),normalized=m.records.map(r=>[r,engine(r.name)]),matches=[];
let valueChecks=0,matchingPublicPairs=0,nonmatchingPublicPairs=0;
for(let i=0;i<1024;i++){
 const payload=Math.imul(i,1013904223)>>>0,values=[];
 for(const secret of [0,1]){
  const want=oracle(secret,payload),actual=original([secret,payload],10000);assert.deepEqual(project(actual),want);values.push(want);valueChecks++;
  for(const [rec,run]of normalized){assert.deepEqual(project(run([secret,payload],10000)),want);valueChecks++;}
 }
 if(JSON.stringify(values[0])===JSON.stringify(values[1])){matchingPublicPairs++;matches.push(payload);}else nonmatchingPublicPairs++;
}
const rows=[];
for(const rec of m.records.filter(r=>r.status==='accepted')){
 const s=rec.modes.frontier.summary,max=s.segment.reduce((a,b)=>a+b,0)+2;
 for(const mode of Object.keys(rec.modes)){
  const run=engine(rec.name+'-'+mode);let failedPairs=0,pairs=0;
  for(let i=0;i<1024;i++)for(const secret of [0,1]){const p=Math.imul(i,1013904223)>>>0,a=run([secret,p],10000);assert.deepEqual(project(a),oracle(secret,p));valueChecks++;
   if(mode==='dynamic'){const expected=rec.independentCost[secret].prefix;assert.equal(a.spent,expected.at(-1));a.events.forEach((e,j)=>assert.equal(e[2],expected[j]));expected.forEach((v,j)=>assert(v<=s.prefix[j]));}}
  for(const p of matches)for(let b=0;b<=max;b++){
   const a=run([0,p],b),c=run([1,p],b);if(JSON.stringify(a)!==JSON.stringify(c))failedPairs++;pairs++;
  }
  if(['frontier','whole','segment'].includes(mode))assert.equal(failedPairs,0);
  rows.push({pipeline:rec.name,mode,pairs,failedPairs,whole:s.prefix.at(-1),segment:s.segment.reduce((a,b)=>a+b,0),envelope:s.prefix});
 }
}
const result={valueChecks,matchingPublicPairs,nonmatchingPublicPairs,rows,coverage:m.records.map(r=>({name:r.name,status:r.status,reason:r.reason,ifs:r.ifs}))};
fs.writeFileSync(path.join(root,'results.json'),JSON.stringify(result,null,2));console.log(JSON.stringify({...result,coverage:result.coverage.map(r=>({...r,reason:r.reason?.slice(0,100)}))}));
