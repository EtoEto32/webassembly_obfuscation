import fs from 'node:fs';import path from 'node:path';import assert from 'node:assert/strict';
import observer from './observer.cjs';const {call,snapshot,difference}=observer;
const source=path.resolve(process.argv[2]),out=path.resolve(process.argv[3]);
const m=JSON.parse(fs.readFileSync(path.join(source,'manifest.json'))),profiles=JSON.parse(fs.readFileSync(path.join(out,'profiles.json'))),rows=[];
const key=s=>JSON.stringify({...s,...(s.memory?{memory:s.memory.toString('base64')}:{})});
function normalize(module,c,state){
 const x=new WebAssembly.Instance(module),e=x.exports,meta=c.observer;
 if(meta.memory){assert.equal(e.__sw_pages(),state.pages);new Uint8Array(e.__sw_memory.buffer).set(state.memory);}
 for(let t=0;t<meta.tableCount;t++){
  const suffix=t?'_'+t:'',table=e['__sw_table'+suffix],refs=state['table'+suffix];assert.equal(table.length,refs.length);
  for(let i=0;i<refs.length;i++)table.set(i,refs[i]===null?null:e['__sw_func_'+refs[i][0]]);
 }
 for(let i=0;i<meta.segments.length;i++){const s=meta.segments[i];if(s.initialLive&&state.segments[i].trap)e[`__ctx_drop_${s.kind}_${s.index}`]();}
 assert.deepEqual(difference(snapshot(x,meta),state),[]);return x;
}
function closure(module,c,profile,left,right){
 if(profile.status!=='accepted')return {status:'unsupported',reason:profile.reason};
 const queue=[[left,right,[]]],seen=new Set(),edges=[];
 for(let at=0;at<queue.length;at++){
  if(at>=128)return {status:'state-bound',nodes:seen.size,edges};
  const [l,r,prefix]=queue[at],pair=key(l)+'|'+key(r);if(key(l)===key(r)||seen.has(pair))continue;seen.add(pair);
  for(const action of profile.actions){
   if(action.kind==='all-i32-readonly-self-loop'){
    assert(l.memory.equals(r.memory));edges.push({node:at,api:action.name,kind:action.kind});continue;
   }
   const a=normalize(module,c,l),b=normalize(module,c,r),ao=call(a.exports[action.name]),bo=call(b.exports[action.name]);
   const as=snapshot(a,c.observer),bs=snapshot(b,c.observer),diff=difference(as,bs),suffix=[...prefix,action.name];
   edges.push({node:at,api:action.name,baseline:ao,changed:bo,stateDifferences:diff});
   if(JSON.stringify(ao)!==JSON.stringify(bo))return {status:'api-witness',witness:suffix,nodes:seen.size,edges};
   if(diff.some(x=>x!=='segments'))return {status:'unresolved-store-divergence',nodes:seen.size,edges};
   queue.push([as,bs,suffix]);
  }
 }
 return {status:'closed-original-api-model',nodes:seen.size,edges};
}
for(const c of m.cases){
 const module=new WebAssembly.Module(fs.readFileSync(path.join(source,c.file)));
 for(const target of c.segments){
  const a=new WebAssembly.Instance(module),b=new WebAssembly.Instance(module),s=target.segment;
  b.exports[`__ctx_drop_${s.kind}_${s.index}`]();
  const result=closure(module,c,profiles[c.source],snapshot(a,c.observer),snapshot(b,c.observer));
  assert(!(target.certificate.status==='certified-no-segment-effect'&&result.status==='api-witness'));
  rows.push({source:c.source,sourceSha256:c.sourceSha256,segment:{kind:s.kind,index:s.index},result});
 }
}
const counts=rs=>Object.fromEntries([...new Set(rs.map(r=>r.result.status))].map(s=>[s,rs.filter(r=>r.result.status===s).length]));
const unique=[...new Map(rows.map(r=>[[r.sourceSha256,r.segment.kind,r.segment.index].join(':'),r])).values()];
const summary={pairs:rows.length,counts:counts(rows),uniquePairs:unique.length,uniqueCounts:counts(unique)};
fs.writeFileSync(path.join(out,'results.json'),JSON.stringify({node:process.version,summary,rows},null,2));console.log(JSON.stringify(summary));
