// Compare original-program contexts after reconstructing measured guest states.
// Do not equate these contexts with the transform's internal resume protocol.
import fs from 'node:fs';import path from 'node:path';import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
const input=path.resolve(process.argv[2]),out=path.resolve(process.argv[3]);fs.mkdirSync(out,{recursive:false});
const m=JSON.parse(fs.readFileSync(path.join(input,'manifest.json'))),rows=[];
const raw=n=>fs.readFileSync(path.join(m.source,n));
function invoke(e,n,args=[]){try {const v=e[n](...args);return {value:v??null};}
 catch(x){if(x instanceof WebAssembly.RuntimeError)return {trap:true};throw x;}}
function migrate(module,c,stop,saved){
 let instance,polls=0,requested=false;
 instance=new WebAssembly.Instance(module,{host:{should_migrate:()=>{const yes=polls++===stop;requested||=yes;return +yes;},restore_memory:()=>{
  if(saved)for(const [n,b] of Object.entries(saved))new Uint8Array(instance.exports[n].buffer).set(b);
 }}});
 return {e:instance.exports,run:()=>invoke(instance.exports,c.entry),reached:()=>requested,
 save:()=>Object.fromEntries(['memory','checkpoint_memory'].map(n=>[n,Buffer.from(instance.exports[n].buffer)]))};
}
function capture(e,c,observed){
 const tables=Array.from({length:c.tables},(_,i)=>{const t=e['__audit_table_'+i];return Array.from({length:t.length},(_,j)=>t.get(j)?.()??null);});
 return {memory:Buffer.from(new Uint8Array(e.memory.buffer,0,c.guestPages*65536)),tables,
  segments:observed?c.observer.segments.map(s=>s.probe?invoke(e,s.probe):{unobservable:true}):null};
}
function norm(module,c,s){
 const e=new WebAssembly.Instance(module).exports;new Uint8Array(e.memory.buffer).set(s.memory);
 assert.equal(new Set(Object.values(c.tags)).size,Object.values(c.tags).length,'unique constant tags only');
 for(let i=0;i<c.tables;i++){const t=e['__audit_table_'+i];assert.equal(t.length,s.tables[i].length);
  for(let j=0;j<t.length;j++){const tag=s.tables[i][j];const index=tag===null?null:Object.keys(c.tags).find(k=>c.tags[k]===tag);
   assert(tag===null||index!==undefined);t.set(j,tag===null?null:e['__ctx_func_'+index]);}}
 for(let i=0;i<c.observer.segments.length;i++){
  const seg=c.observer.segments[i],live=seg.observable&&!s.segments[i].trap;
  if(!live)e[`__ctx_drop_${seg.kind}_${seg.index}`]();
 }
 return e;
}
function publicState(e,c){const s=capture(e,c,false);return {memory:s.memory.toString('base64'),tables:s.tables};}
function asJson(s){return {...s,memory:s.memory.toString('base64')};}
function productClosure(module,c,profile,left,right){
 if(profile.status!=='accepted')return {status:'unsupported',reason:profile.reason};
 const key=s=>JSON.stringify(asJson(s)),queue=[[left,right,[]]],seen=new Set(),edges=[];
 for(let index=0;index<queue.length;index++){
  if(index>=128)return {status:'state-bound',nodes:index,edges};
  const [a,b,prefix]=queue[index],pair=key(a)+'|'+key(b);
  if(key(a)===key(b)||seen.has(pair))continue;seen.add(pair);
  for(const action of profile.actions){
   if(action.kind==='all-i32-readonly-self-loop'){
    assert(a.memory.equals(b.memory));edges.push({node:index,api:action.name,kind:action.kind});continue;
   }
   const x=norm(module,c,a),y=norm(module,c,b),xo=invoke(x,action.name),yo=invoke(y,action.name);
   const xs=capture(x,c,true),ys=capture(y,c,true),suffix=[...prefix,{name:action.name,args:[]}];
   const outcomeMatches=JSON.stringify(xo)===JSON.stringify(yo);
   const guestStateMatches=xs.memory.equals(ys.memory)&&JSON.stringify(xs.tables)===JSON.stringify(ys.tables);
   edges.push({node:index,api:action.name,baseline:xo,restored:yo,outcomeMatches,guestStateMatches});
   if(!outcomeMatches||!guestStateMatches)return {status:'witness',nodes:seen.size,edges,witness:suffix};
   queue.push([xs,ys,suffix]);
  }
 }
 return {status:'closed-original-api-model',nodes:seen.size,edges};
}
for(const item of m.cases){
 const c=item.case,original=new WebAssembly.Module(raw(c.originalObserved));
 const migrated=new WebAssembly.Module(raw(c.entries.find(e=>e.backend==='migrate'&&e.kind==='observed').output));
 const normalized=new WebAssembly.Module(fs.readFileSync(path.join(input,item.normalized)));
 const baseline=new WebAssembly.Instance(original);const expected=invoke(baseline.exports,c.entry),bs=capture(baseline.exports,c,true);
 const alphabet=item.api.flatMap(a=>a.params.length===0?[{name:a.name,args:[]}]:
   a.params.length===1&&a.params[0]==='i32'?[0,1,7,65535,65536,-1].map(x=>({name:a.name,args:[x]})):[]);
 for(const scenario of item.scenarios){
  const first=migrate(migrated,c,scenario.stopAt);first.run();assert(first.reached());
  const second=migrate(migrated,c,-1,first.save());assert.deepEqual(second.run(),expected);
  const rs=capture(second.e,c,true);assert(bs.memory.equals(rs.memory));assert.deepEqual(bs.tables,rs.tables);
  const closure=productClosure(normalized,c,item.finiteProfile,bs,rs);
  let queue=[[]],checked=0,witness=null;
  for(let depth=0;depth<=4&&!witness;depth++){
   const next=[];
   for(const suffix of queue){
    const a=norm(normalized,c,bs),b=norm(normalized,c,rs),at=[],bt=[];
    for(const call of suffix){at.push({outcome:invoke(a,call.name,call.args),state:publicState(a,c)});bt.push({outcome:invoke(b,call.name,call.args),state:publicState(b,c)});}
    checked++;
    if(JSON.stringify(at)!==JSON.stringify(bt)){witness={suffix,baseline:at.map(x=>x.outcome),restored:bt.map(x=>x.outcome),
      guestStateMatches:at.map((x,i)=>JSON.stringify(x.state)===JSON.stringify(bt[i].state))};break;}
    if(depth<4)for(const call of alphabet)next.push([...suffix,call]);
   }
   queue=next;
  }
  if(scenario.certificate.status==='certified-no-segment-effect')assert.equal(witness,null);
  const stem=`case-${c.id}-stop-${scenario.stopAt}`;
  fs.writeFileSync(path.join(out,stem+'.json'),JSON.stringify({baseline:asJson(bs),restored:asJson(rs)},null,2));
  rows.push({id:c.id,source:c.source,stopAt:scenario.stopAt,differing:scenario.differing,certificate:scenario.certificate,
    finiteClosure:closure,alphabet,depthLimit:4,checked,witness,stateFile:stem+'.json'});
 }
}
const summary={scenarios:rows.length,certified:rows.filter(r=>r.certificate.status==='certified-no-segment-effect').length,
 witnessed:rows.filter(r=>r.witness).length,unresolved:rows.filter(r=>r.certificate.status!=='certified-no-segment-effect'&&!r.witness).length,
 closedModels:rows.filter(r=>r.finiteClosure.status==='closed-original-api-model').length,
 closureWitnesses:rows.filter(r=>r.finiteClosure.status==='witness').length,
 checkedSuffixes:rows.reduce((s,r)=>s+r.checked,0)};
fs.writeFileSync(path.join(out,'results.json'),JSON.stringify({node:process.version,v8:process.versions.v8,summary,rows},null,2));
fs.copyFileSync(new URL(import.meta.url),path.join(out,'context-run.mjs'));
fs.writeFileSync(path.join(out,'sha256.json'),JSON.stringify(Object.fromEntries(fs.readdirSync(out).map(n=>[n,createHash('sha256').update(fs.readFileSync(path.join(out,n))).digest('hex')])),null,2));
console.log(JSON.stringify(summary));
