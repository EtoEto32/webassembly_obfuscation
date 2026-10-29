'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert/strict');
const out=path.resolve(process.argv[2]),{project}=require(path.join(out,'project.cjs'));
const handles=[{slot:0,generation:3},{slot:1,generation:7},{slot:2,generation:4}];
const clone=x=>JSON.parse(JSON.stringify(x));
// Independent application-specific meaning, not traversal of the generated AST.
function manual(r){const d=(h,p)=>({slot:h.slot,generation:h.generation,permission:p});
 switch(r.tag){case'read':return[d(r.val,'read')];case'write':return[d(r.val,'write')];
 case'copy':return[d(r.val.source,'read'),d(r.val.destination,'write')];case'batch':return r.val.map(h=>d(h,'write'));
 case'optional':return[d(r.val.primary,'write'),...(r.val.backup===null?[]:[d(r.val.backup,'write')])];case'idle':return[];default:throw Error('tag');}}
function state(){return{slots:[{object:0,generation:3},{object:1,generation:7},{object:0,generation:4}],grants:[[0,0],[0,0],[0,0]]};}
function prepare(ds,s){return{slots:ds.map(d=>({slot:d.slot,generation:d.generation,object:s.slots[d.slot].object})),
 grants:[...new Set(ds.map(d=>s.slots[d.slot].object+':'+(d.permission==='write'?1:0)))].map(k=>{const[o,p]=k.split(':').map(Number);return{o,p,epoch:s.grants[o][p]};})};}
function changed(s,event){s=clone(s);if(event.kind==='permission')s.grants[event.object][event.op]++;
 if(event.kind==='reuse')s.slots[event.slot]={object:2,generation:s.slots[event.slot].generation+1};return s;}
function valid(t,s){return t.slots.every(d=>s.slots[d.slot].generation===d.generation&&s.slots[d.slot].object===d.object)&&t.grants.every(d=>s.grants[d.o][d.p]===d.epoch);}
const requests=[{tag:'idle'}];for(const h of handles)for(const tag of ['read','write'])requests.push({tag,val:h});
for(const a of handles)for(const b of handles){requests.push({tag:'copy',val:{source:a,destination:b}});requests.push({tag:'optional',val:{primary:a,backup:b}});}
for(const a of handles)requests.push({tag:'optional',val:{primary:a,backup:null}});
let seed=20261024;function rand(){seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed>>>0;}
for(let i=0;i<2048;i++)requests.push({tag:'batch',val:Array.from({length:rand()%17},()=>handles[rand()%3])});
const events=[{kind:'none'}];for(let o=0;o<3;o++)for(let op=0;op<2;op++)events.push({kind:'permission',object:o,op});for(let slot=0;slot<3;slot++)events.push({kind:'reuse',slot});
let comparisons=0,decisions=0;const baseline={entryUnsafe:0,globalFalseRejects:0};
for(const r of requests){const input=clone(r),got=project(input),want=manual(r);assert.deepEqual(got,want);comparisons++;
 const s=state(),ticket=prepare(got,s);for(const event of events){const after=changed(s,event);
  // Compute expected revocation directly from application obligations and event.
  const invalid=want.some(d=>event.kind==='reuse'?d.slot===event.slot:event.kind==='permission'?s.slots[d.slot].object===event.object&&(d.permission==='write'?1:0)===event.op:false);
  assert.equal(valid(ticket,after),!invalid);decisions++;if(invalid)baseline.entryUnsafe++;
  if(event.kind!=='none'&&want.length>0&&!invalid)baseline.globalFalseRejects++;
 }
 if(input.tag==='batch'&&input.val.length){input.val[0].slot=99;assert(!ticket.slots.some(x=>x.slot===99));}
}
const malformed=[{tag:'absent'},{tag:'read',val:{slot:-1,generation:0}},{tag:'idle',val:handles[0]},
 {tag:'copy',val:{source:handles[0]}},{tag:'optional',val:{primary:handles[0],backup:undefined}},
 {tag:'batch',val:Array(4097).fill(handles[0])}];
for(const r of malformed)assert.throws(()=>project(r));
const times=[];
for(const n of [0,1,8,64,1024,4096]){const r={tag:'batch',val:Array(n).fill(handles[0])};
 for(let j=0;j<100;j++)project(r);const samples=[];let check=0;
 for(let k=0;k<9;k++){const start=process.hrtime.bigint();for(let j=0;j<100;j++)check+=project(r).length;samples.push(Number(process.hrtime.bigint()-start)/100/1000);}
 assert.equal(check,n*900);times.push({dependencies:n,samples_us:samples});}
const result={requestComparisons:comparisons,eventDecisions:decisions,mismatches:0,malformedRejected:malformed.length,baseline,times,
 scope:'officially validated WIT; generated extraction over host slot records; not end-to-end Canonical ABI asynchronous admission'};
fs.writeFileSync(path.join(out,'results.json'),JSON.stringify(result,null,2));console.log(JSON.stringify({...result,times:undefined}));
