'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert');
const {call,snapshot,difference}=require('./observer.cjs');
const dir=process.argv[2],manifest=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json')));
const make=file=>new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(dir,file))));
const same=(a,b)=>assert.deepStrictEqual(a,b);
let seed=0x261024;function random(n){seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed%n;}
const rows=[],counter={originalApiCalls:0,probeCalls:0,nonMutationChecks:0,JStateComparisons:0,expectedTrapCalls:0};
function invoke(i,op){const r=call(i.exports[op[0]],op.slice(1));counter.originalApiCalls++;if(r.trap)counter.expectedTrapCalls++;return r;}
function observe(i,m){counter.probeCalls+=m.segments.filter(x=>x.probe).length+(m.memory?1:0)+(m.table?1:0);return snapshot(i,m);}
function native(i,m){const e=i.exports;return {
  memory:e.__sw_memory?Buffer.from(e.__sw_memory.buffer):null,
  table:e.__sw_table?Array.from({length:e.__sw_table.length},(_,j)=>e.__sw_table.get(j)):null,
  globals:m.globals.map(g=>call(e['__sw_global_'+g.index]))};}
function checkProbe(i,m,live){
  const before=native(i,m),a=observe(i,m),b=observe(i,m),after=native(i,m);
  same(difference(a,b),[]);same(before,after);counter.nonMutationChecks++;
  m.segments.forEach((s,j)=>{if(s.probe)same(a.segments[j],live[j]?{value:null}:{trap:true});});
}
function sequence(extra){
  const xs=[['ddrop'],['edrop'],['init',0,1,0],['tinit',0,1,0],['grow',1],['tgrow',3],['fault']];
  for(let i=0;i<64;i++){
    const index=random(12),addr=[0,1,3,65535,65536,262144,-1][random(7)],n=[0,1,2,4,-1][random(5)];
    xs.push([['put',addr,random(65536)],['fill',addr,random(255),n],['copy',addr,0,n],
      ['init',addr,random(16),n],['tinit',addr,random(5),n],['tfill',addr,n],['gput',random(0xffffffff)],
      ['get',addr],['call',random(100),random(7)],['grow',random(3)],['tgrow',random(3)],['work',random(128)]][index]);
  }
  if(extra)xs.push(['drop_extra'],['float_write']);
  return xs;
}
for(const row of manifest.rows){
  const ops=sequence(row.name.endsWith('-1')),m=row.manifest;
  for(const file of [row.full,row.optimized]){
    const seen=make(file),twin=make(file),raw=make(row.source),live=m.segments.map(s=>s.initialLive);
    checkProbe(seen,m,live);
    for(const op of ops){
      const x=invoke(seen,op);same(x,invoke(twin,op));same(x,invoke(raw,op));
      if(op[0]==='ddrop')m.segments.forEach((s,j)=>{if(s.kind==='data'&&s.index===1)live[j]=false;});
      if(op[0]==='edrop')m.segments.forEach((s,j)=>{if(s.kind==='elem'&&s.index===1)live[j]=false;});
      if(op[0]==='drop_extra')m.segments.forEach((s,j)=>{if((s.kind==='data'&&s.index===3)||(s.kind==='elem'&&s.index===4))live[j]=false;});
      checkProbe(seen,m,live);
    }
    // The twin did not receive any segment probes during the operation trace.
    same(difference(observe(seen,m),observe(twin,m)),[]);
    rows.push({name:row.name,kind:'non-destructive',file,operations:ops.length,ok:true});
  }
  // A memory/global/table-byte restoration cannot undo the native segment drops.
  const blind=make(row.full),before=observe(blind,m);
  invoke(blind,['ddrop']);invoke(blind,['edrop']);
  if(before.memory)new Uint8Array(blind.exports.__sw_memory.buffer).set(before.memory);
  const after=observe(blind,m),changed=difference(before,after);
  same(changed,['segments']);
  const fresh=make(row.source),originalWitness=[];
  for(const op of [['init',0,1,0],['tinit',0,1,0]]){
    const a=invoke(fresh,op),b=invoke(blind,op);assert.notDeepStrictEqual(a,b);originalWitness.push({op,fresh:a,restored:b});
  }
  rows.push({name:row.name,kind:'byte-oracle-miss',changed,originalWitness});
  if(before.length>=2){
    const tableInstance=make(row.full),a=observe(tableInstance,m);
    invoke(tableInstance,['tcopy',0,1,1]);const b=observe(tableInstance,m);
    same(difference(a,b),['table']);
    same(a.table.map(x=>x===null),b.table.map(x=>x===null));
    const original=make(row.source),first=invoke(original,['call',11,0]);
    invoke(original,['tcopy',0,1,1]);const second=invoke(original,['call',11,0]);assert.notDeepStrictEqual(first,second);
    rows.push({name:row.name,kind:'nullness-oracle-miss',changed:['table'],originalWitness:{first,second}});
  }
  if(row.name.endsWith('-1')){
    const floats=make(row.full);invoke(floats,['nan_a']);const a=observe(floats,m),hostA=floats.exports.__sw_global_host_2.value;
    invoke(floats,['nan_b']);const b=observe(floats,m),hostB=floats.exports.__sw_global_host_2.value;
    assert(Object.is(hostA,hostB));same(difference(a,b),['globals']);
    rows.push({name:row.name,kind:'numeric-NaN-oracle-miss',rawBefore:a.globals[2],rawAfter:b.globals[2]});
  }
  const nm=row.numericManifest,expected=observe(make(row.numeric),nm);
  for(const [mode,file] of Object.entries(row.J)){
    const instance=make(file),failures=[];
    for(let epoch=0;epoch<6;epoch++){
      for(const op of [['grow',1],['tgrow',3],['put8',0,91],['gput',333],['ddrop'],['edrop'],['fault']])invoke(instance,op);
      instance.exports.__lr_reset();
      const actual=observe(instance,nm),changed=difference(expected,actual);counter.JStateComparisons++;
      if(changed.length)failures.push({epoch,changed});
    }
    if(mode==='full')same(failures,[]);else assert(failures.length>0,mode+' mutant must be detected');
    rows.push({name:row.name,kind:'J-restore',mode,failures});
  }
}
const result={node:process.version,v8:process.versions.v8,platform:process.platform,seed:0x261024,counter,rows,
  limits:['Synthetic fixtures; no external product bug claim','Numeric profile checks nullness, not function identity',
          'Observers expose more state than the original API; original API witnesses recorded separately']};
fs.writeFileSync(path.join(dir,'results.json'),JSON.stringify(result,null,2));
console.log(JSON.stringify({counter,rows:rows.length}));
