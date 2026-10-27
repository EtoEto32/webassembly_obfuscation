// Targeted checkpoint testing of official-derived seeds, not a runtime exploit.
import fs from 'node:fs';import path from 'node:path';import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';import {pathToFileURL} from 'node:url';
import observer from './observer.cjs';
const {call}=observer,source=path.resolve(process.argv[2]),out=path.resolve(process.argv[3]);
fs.mkdirSync(out,{recursive:false});
const {WeaveInstance}=await import(pathToFileURL(path.join(source,'weave.mjs')));
const manifest=JSON.parse(fs.readFileSync(path.join(source,'manifest.json'))),rows=[];
const bytes=n=>fs.readFileSync(path.join(source,n));
const moduleFor=n=>new WebAssembly.Module(bytes(n));
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
function segments(e,c){return c.observer.segments.map(s=>s.probe?call(e[s.probe]):{unobservable:true});}
function capture(e,c,observed){
  const memory=Buffer.from(new Uint8Array(e.memory.buffer,0,c.guestPages*65536));
  const tables=Array.from({length:c.tables},(_,i)=>{
    const t=e['__audit_table_'+i];return Array.from({length:t.length},(_,j)=>{
      const f=t.get(j);if(f===null)return null;
      const value=f();assert(Object.values(c.tags).includes(value));return value;
    });
  });
  return {memory,tables,segments:observed?segments(e,c):null};
}
function compare(a,b){return {guestMemory:a.memory.equals(b.memory),tableTags:same(a.tables,b.tables),segments:same(a.segments,b.segments)};}
function view(a){return {...a,memory:{bytes:a.memory.length,sha256:createHash('sha256').update(a.memory).digest('hex')}};}
function migrateHost(module,entry,stop,saved){
  let instance,polls=0,requested=false;
  const imports={host:{should_migrate:()=>{const b=polls++===stop;requested||=b;return Number(b);},restore_memory:()=>{
    if(saved)for(const [n,data] of Object.entries(saved)){const dest=new Uint8Array(instance.exports[n].buffer);assert(dest.length>=data.length);dest.set(data);}
  }}};
  instance=new WebAssembly.Instance(module,imports);
  return {ex:instance.exports,run:()=>call(instance.exports[entry]),stats:()=>({polls,requested}),
    save:()=>Object.fromEntries(['memory','checkpoint_memory'].map(n=>[n,Buffer.from(instance.exports[n].buffer)]))};
}
async function weaveMake(b){return new WeaveInstance(b,new Map(),{yieldMs:1e9}).instantiate();}
async function weaveRun(x,entry){try{const r=await x.drive(entry,[],()=> 'hold');return r.status==='held'?{held:true}:{value:null};}catch(e){if(e instanceof WebAssembly.RuntimeError)return {trap:true};throw e;}}
for(const c of manifest.cases){
  const expect={};
  for(const [kind,orig,cut] of [['plain',c.original,c.cut],['observed',c.originalObserved,c.observed]]){
    const a=new WebAssembly.Instance(moduleFor(orig)),b=new WebAssembly.Instance(moduleFor(cut));
    const ao=call(a.exports[c.entry]),bo=call(b.exports[c.entry]);const as=capture(a.exports,c,kind==='observed'),bs=capture(b.exports,c,kind==='observed');
    assert(same(ao,bo));assert(Object.values(compare(as,bs)).every(Boolean));
    expect[kind]={outcome:ao,state:as};
  }
  assert(same(expect.plain.outcome,expect.observed.outcome));
  assert(expect.plain.state.memory.equals(expect.observed.state.memory));assert(same(expect.plain.state.tables,expect.observed.state.tables));
  for(const item of c.entries){
    const row={id:c.id,source:c.source,operation:c.operation,backend:item.backend,kind:item.kind,transformStatus:item.status};
    if(item.status!=='valid'){rows.push(row);continue;}
    const observed=item.kind==='observed',baseline=expect[item.kind],binary=bytes(item.output),module=new WebAssembly.Module(binary);
    let count,co,cs;
    if(item.backend==='migrate'){
      const continuous=migrateHost(module,c.entry,-1);co=continuous.run();count=continuous.stats().polls;cs=capture(continuous.ex,c,observed);
    }else{
      const continuous=await weaveMake(binary);continuous.init();continuous.pollMode={afterPolls:1e9};co=await weaveRun(continuous,c.entry);count=continuous.pollCount;cs=capture(continuous.ex(),c,observed);
    }
    Object.assign(row,{expected:baseline.outcome,expectedState:view(baseline.state),continuous:co,
      continuousState:view(cs),continuousComparison:compare(baseline.state,cs),polls:count,scenarios:[]});
    if(!same(co,baseline.outcome)||!Object.values(row.continuousComparison).every(Boolean)){
      row.status='continuous-mismatch';rows.push(row);continue;
    }
    row.status='executed';assert(count<=32,'bounded poll profile');
    for(let stop=0;stop<=count;stop++){
      let first,firstOutcome,saved,sourceSegments=null,restoredSegments=null,result,state;
      if(item.backend==='migrate'){
        first=migrateHost(module,c.entry,stop);firstOutcome=first.run();
        if(!first.stats().requested){row.scenarios.push({stopAt:stop,status:'checkpoint-not-reached',outcome:firstOutcome});continue;}
        saved=first.save();if(observed)sourceSegments=segments(first.ex,c);
        const second=migrateHost(module,c.entry,-1,saved);
        if(observed)restoredSegments=segments(second.ex,c); // Native segments exist before memory restoration too.
        result=second.run();state=capture(second.ex,c,observed);
      }else{
        first=await weaveMake(binary);first.init();first.pollMode={afterPolls:stop};firstOutcome=await weaveRun(first,c.entry);
        if(!firstOutcome.held){row.scenarios.push({stopAt:stop,status:'checkpoint-not-reached',outcome:firstOutcome});continue;}
        saved=first.checkpoint();
        if(observed){sourceSegments=segments(first.ex(),c);const inspect=await weaveMake(binary);inspect.restore(saved);restoredSegments=segments(inspect.ex(),c);}
        const second=await weaveMake(binary);second.restore(saved);second.pollMode={afterPolls:1e9};result=await weaveRun(second,null);state=capture(second.ex(),c,observed);
      }
      const comparison=compare(baseline.state,state);
      row.scenarios.push({stopAt:stop,status:'restored',firstOutcome,outcome:result,state:view(state),
        entryMatches:same(result,baseline.outcome),comparison,checkpointSegments:observed?{source:sourceSegments,restored:restoredSegments,matches:same(sourceSegments,restoredSegments)}:null});
    }
    rows.push(row);
  }
}
const summary=[];
for(const backend of ['migrate','weave'])for(const kind of ['plain','observed']){
 const r=rows.filter(x=>x.backend===backend&&x.kind===kind),s=r.flatMap(x=>x.scenarios??[]).filter(x=>x.status==='restored');
 summary.push({backend,kind,conditions:r.length,continuousMismatches:r.filter(x=>x.status==='continuous-mismatch').length,
   restored:s.length,entryMismatches:s.filter(x=>!x.entryMatches).length,
   guestStoreMismatches:s.filter(x=>!x.comparison.guestMemory||!x.comparison.tableTags).length,
   segmentMismatches:s.filter(x=>!x.comparison.segments).length,
   checkpointSegmentMismatches:s.filter(x=>x.checkpointSegments&&!x.checkpointSegments.matches).length,
   notReached:r.flatMap(x=>x.scenarios??[]).filter(x=>x.status==='checkpoint-not-reached').length});
}
fs.writeFileSync(path.join(out,'results.json'),JSON.stringify({node:process.version,v8:process.versions.v8,summary,rows},null,2));
fs.copyFileSync(new URL(import.meta.url),path.join(out,'cut-run.mjs'));
fs.writeFileSync(path.join(out,'sha256.json'),JSON.stringify(Object.fromEntries(fs.readdirSync(out).map(n=>[n,createHash('sha256').update(fs.readFileSync(path.join(out,n))).digest('hex')])),null,2));
console.log(JSON.stringify(summary));
