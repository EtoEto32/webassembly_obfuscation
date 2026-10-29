// Respect the public Weave driver lifecycle: a trapped drive is terminal.
import fs from 'node:fs';import path from 'node:path';import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';import {pathToFileURL} from 'node:url';
const source=path.resolve(process.argv[2]),out=path.resolve(process.argv[3]);fs.mkdirSync(out,{recursive:false});
const {WeaveInstance}=await import(pathToFileURL(path.join(source,'weave.mjs')));
const input=JSON.parse(fs.readFileSync(path.join(source,'manifest.json'))),rows=[];
const bytes=n=>fs.readFileSync(path.join(source,n)),eq=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
function call(f){try{const x=f();return {return:x??null};}catch(e){if(e instanceof WebAssembly.RuntimeError)return {trap:true};throw e;}}
function publicValue(ex){const f=ex.public.get(0);return f===null?null:f();}
function raw(module){const x=new WebAssembly.Instance(module);return {ex:x.exports,run:async n=>call(x.exports[n])};}
function migrate(module,stop,saved){let x,polls=0,requested=false;const imports={host:{should_migrate:()=>{const b=polls++===stop;requested||=b;return Number(b);},restore_memory:()=>{
    if(saved)for(const [n,data] of Object.entries(saved))new Uint8Array(x.exports[n].buffer).set(data);
}}};x=new WebAssembly.Instance(module,imports);return {ex:x.exports,run:async n=>call(x.exports[n]),stats:()=>({polls,requested}),
  save:()=>Object.fromEntries(['memory','checkpoint_memory'].map(n=>[n,Buffer.from(x.exports[n].buffer)]))};}
async function weave(binary,stop,saved){const x=await new WeaveInstance(binary,new Map(),{yieldMs:1e9}).instantiate();if(saved)x.restore(saved);else x.init();x.pollMode={afterPolls:stop};
 return {ex:x.ex(),instance:x,run:async n=>{try{const r=await x.drive(n,[],()=> 'hold');return r.status==='held'?{held:true}:{return:r.results.length?r.results:null};}
 catch(e){if(e instanceof WebAssembly.RuntimeError)return {trap:true};throw e;}},stats:()=>({polls:x.pollCount})};}
async function diagnose(h,sequence,backend){const trace=[];let terminal=null;
 for(const api of sequence){const result=await h.run(api);assert(!result.held,'no diagnostic checkpoint requested');const value=publicValue(h.ex);trace.push({api,result,publicValue:value});
  if(result.trap&&backend==='weave'){
   assert.equal(h.instance.lifecycle,'failed');let rejection=null;
   try{await h.run('copy');}catch(e){rejection={name:e.name,message:e.message};}
   assert(rejection,'failed driver must reject another call');terminal={status:'trap-terminal',lifecycle:h.instance.lifecycle,reentryRejection:rejection};break;
  }
 }
 return {trace,terminal};
}
try{
 for(const r of input.rows){
  const controls=[];
  for(const name of ['original','adapted','cut']){const h=raw(new WebAssembly.Module(bytes(r[name])));const entry=await h.run('retire');const trace=await diagnose(h,r.sequence,'raw');controls.push({name,entry,...trace});}
  assert(controls.every(c=>eq(c.entry,controls[0].entry)&&eq(c.trace,controls[0].trace)));assert.equal(controls[0].trace.at(-1).publicValue,r.repair?101:202);
  for(const v of r.variants){const row={name:r.name,length:r.length,repair:r.repair,backend:v.backend,transformStatus:v.status,controls};rows.push(row);if(v.status!=='valid')continue;
   const binary=bytes(v.binary),module=new WebAssembly.Module(binary),make=async(stop,saved)=>v.backend==='migrate'?migrate(module,stop,saved):weave(binary,stop<0?1e9:stop,saved);
   const continuous=await make(-1),entry=await continuous.run('retire'),count=continuous.stats().polls;const diag=await diagnose(continuous,r.sequence,v.backend);
   Object.assign(row,{continuous:{entry,...diag},polls:count,scenarios:[]});assert(count<=32);
   const controlTrace=v.backend==='weave'?controls[0].trace.slice(0,1):controls[0].trace;
   row.continuousMatches=eq(entry,controls[0].entry)&&eq(diag.trace,controlTrace);
   if(!row.continuousMatches){row.status='continuous-mismatch';continue;}row.status='executed';
   for(let stop=0;stop<=count;stop++){
    const first=await make(stop),firstOutcome=await first.run('retire');const reached=v.backend==='migrate'?first.stats().requested:!!firstOutcome.held;
    if(!reached){row.scenarios.push({stop,status:'checkpoint-not-reached',firstOutcome});continue;}
    const saved=v.backend==='migrate'?first.save():first.instance.checkpoint(),second=await make(-1,saved);
    const restoredOutcome=await second.run(v.backend==='migrate'?'retire':null),restored=await diagnose(second,r.sequence,v.backend);
    const differences=restored.trace.map((t,i)=>eq(t,diag.trace[i])?null:i+1).filter(x=>x!==null);
    row.scenarios.push({stop,status:'restored',firstOutcome,restoredOutcome,entryMatches:eq(entry,restoredOutcome),...restored,
      publicObservationMatches:eq(restored.trace,diag.trace),firstDifference:differences[0]??null});
   }
  }
 }
 const summary=['migrate','weave'].map(backend=>{const rr=rows.filter(r=>r.backend===backend),ss=rr.flatMap(r=>r.scenarios??[]);return {backend,conditions:rr.length,
  continuousMismatches:rr.filter(r=>!r.continuousMatches).length,restored:ss.filter(s=>s.status==='restored').length,notReached:ss.filter(s=>s.status==='checkpoint-not-reached').length,
  entryMismatches:ss.filter(s=>s.status==='restored'&&!s.entryMatches).length,publicObservationMismatches:ss.filter(s=>s.status==='restored'&&!s.publicObservationMatches).length,
  terminalSequences:ss.filter(s=>s.terminal).length};});
 fs.writeFileSync(path.join(out,'results.json'),JSON.stringify({node:process.version,v8:process.versions.v8,summary,rows,
  contract:'Weave public drive treats trap as terminal. Migrate non-entry calls use an experimental adapter; author support for re-entry is unverified.'},null,2));console.log(JSON.stringify(summary));
}catch(e){fs.writeFileSync(path.join(out,'failure.json'),JSON.stringify({message:e.message,stack:e.stack,rows},null,2));throw e;}
finally{fs.copyFileSync(new URL(import.meta.url),path.join(out,'guard-external-run.mjs'));fs.writeFileSync(path.join(out,'sha256.json'),JSON.stringify(Object.fromEntries(fs.readdirSync(out).map(n=>[n,createHash('sha256').update(fs.readFileSync(path.join(out,n))).digest('hex')])),null,2));}
