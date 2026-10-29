import fs from 'node:fs';import path from 'node:path';import {pathToFileURL} from 'node:url';import {createHash} from 'node:crypto';import assert from 'node:assert/strict';
const source=path.resolve(process.argv[2]),out=path.resolve(process.argv[3]);fs.mkdirSync(out,{recursive:false});
const input=JSON.parse(fs.readFileSync(path.join(source,'manifest.json'))),{WeaveInstance}=await import(pathToFileURL(path.join(source,'weave.mjs')));const rows=[];
const bytes=n=>fs.readFileSync(path.join(source,n)),equal=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
function call(f){try{return {return:f()??null};}catch(err){if(err instanceof WebAssembly.RuntimeError)return {trap:true};throw err;}}
function observe(ex){const data=Buffer.from(ex.memory.buffer).subarray(0,65536);return {sha256:createHash('sha256').update(data).digest('hex'),bytes7to10:[...data.subarray(7,11)]};}
function raw(module){const x=new WebAssembly.Instance(module);return {ex:x.exports,run:async n=>call(x.exports[n])};}
function migrate(module,stop,saved){let x,polls=0,requested=false;const imports={host:{should_migrate:()=>{const yes=polls++===stop;requested||=yes;return Number(yes);},restore_memory:()=>{if(saved)for(const [key,value]of Object.entries(saved))new Uint8Array(x.exports[key].buffer).set(value);}}};
 x=new WebAssembly.Instance(module,imports);return {ex:x.exports,run:async n=>call(x.exports[n]),stats:()=>({polls,requested}),save:()=>Object.fromEntries(['memory','checkpoint_memory'].map(n=>[n,Buffer.from(x.exports[n].buffer)]))};}
async function weave(binary,stop,saved){const x=await new WeaveInstance(binary,new Map(),{yieldMs:1e9}).instantiate();if(saved)x.restore(saved);else x.init();x.pollMode={afterPolls:stop<0?1e9:stop};
 return {ex:x.ex(),instance:x,stats:()=>({polls:x.pollCount}),run:async n=>{try{const r=await x.drive(n,[],()=> 'hold');return r.status==='held'?{held:true}:{return:r.results.length?r.results:null};}catch(err){if(err instanceof WebAssembly.RuntimeError)return {trap:true};throw err;}}};}
async function diagnose(host,write,backend){const before=observe(host.ex);if(write)new Uint8Array(host.ex.memory.buffer)[7]=0;const afterWrite=observe(host.ex),outcome=await host.run('mask'),after=observe(host.ex);
 if(backend==='weave'&&outcome.trap)assert.equal(host.instance.lifecycle,'failed');return {before,afterWrite,outcome,after};}
try{
 for(const r of input.rows){
  const controls=[];for(const write of [false,true])for(const variant of ['original','cut']){const h=raw(new WebAssembly.Module(bytes(r[variant]))),entry=await h.run('retire');controls.push({variant,write,entry,...await diagnose(h,write,'raw')});}
  for(const write of [false,true]){const [a,b]=controls.filter(c=>c.write===write);assert(equal({...a,variant:null},{...b,variant:null}));assert(a.outcome.trap);}
  for(const v of r.variants){const row={name:r.name,backend:v.backend,transformStatus:v.status,controls};rows.push(row);if(v.status!=='valid')continue;
   const binary=bytes(v.binary),module=new WebAssembly.Module(binary),make=async(stop,saved)=>v.backend==='migrate'?migrate(module,stop,saved):weave(binary,stop,saved);row.continuous=[];row.scenarios=[];let count;
   for(const write of [false,true]){const host=await make(-1),entry=await host.run('retire');count=host.stats().polls;const diag=await diagnose(host,write,v.backend),control=controls.find(c=>c.variant==='original'&&c.write===write);assert(equal(entry,control.entry)&&equal(diag,{before:control.before,afterWrite:control.afterWrite,outcome:control.outcome,after:control.after}));row.continuous.push({write,entry,...diag});}
   row.polls=count;assert(count<=32);
   for(let stop=0;stop<=count;stop++){
    const first=await make(stop),firstOutcome=await first.run('retire'),reached=v.backend==='migrate'?first.stats().requested:!!firstOutcome.held;
    if(!reached){row.scenarios.push({stop,status:'checkpoint-not-reached',firstOutcome});continue;}
    const saved=v.backend==='migrate'?first.save():first.instance.checkpoint();
    for(const write of [false,true]){const second=await make(-1,saved),entry=await second.run(v.backend==='migrate'?'retire':null),diag=await diagnose(second,write,v.backend),base=row.continuous.find(c=>c.write===write);
     row.scenarios.push({stop,write,status:'restored',firstOutcome,entry,entryMatches:equal(entry,base.entry),preDiagnosticMemoryMatches:equal(diag.before,base.before),diagnosticMatches:equal(diag.outcome,base.outcome)&&equal(diag.after,base.after),...diag});}
   }
  }
 }
 const summary=['migrate','weave'].map(backend=>{const rr=rows.filter(r=>r.backend===backend),ss=rr.flatMap(r=>r.scenarios??[]);return {backend,inputs:rr.length,invalidOutputs:rr.filter(r=>r.transformStatus!=='valid').length,restored:ss.filter(s=>s.status==='restored').length,notReached:ss.filter(s=>s.status==='checkpoint-not-reached').length,entryMismatches:ss.filter(s=>s.entryMatches===false).length,preMemoryMismatches:ss.filter(s=>s.preDiagnosticMemoryMatches===false).length,diagnosticMismatches:ss.filter(s=>s.diagnosticMatches===false).map(s=>({stop:s.stop,write:s.write}))};});
 fs.writeFileSync(path.join(out,'results.json'),JSON.stringify({node:process.version,rows,summary,scope:'Original guest 1page memory prefix; one diagnostic call, no reentry after trap. Migrate non-entry API support is not author-confirmed.'},null,2));console.log(JSON.stringify(summary));
}catch(err){fs.writeFileSync(path.join(out,'failure.json'),JSON.stringify({message:err.message,stack:err.stack,rows},null,2));throw err;}
finally{fs.copyFileSync(new URL(import.meta.url),path.join(out,'guard-environment-external.mjs'));fs.writeFileSync(path.join(out,'sha256.json'),JSON.stringify(Object.fromEntries(fs.readdirSync(out).map(n=>[n,createHash('sha256').update(fs.readFileSync(path.join(out,n))).digest('hex')])),null,2));}
