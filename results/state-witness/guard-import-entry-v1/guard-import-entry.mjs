import fs from 'node:fs';import path from 'node:path';import {pathToFileURL} from 'node:url';import {createHash} from 'node:crypto';import assert from 'node:assert/strict';
const source=path.resolve(process.argv[2]),out=path.resolve(process.argv[3]);fs.mkdirSync(out,{recursive:false});
const input=JSON.parse(fs.readFileSync(path.join(source,'manifest.json'))),{WeaveInstance}=await import(pathToFileURL(path.join(source,'weave.mjs'))),rows=[];
const bytes=n=>fs.readFileSync(path.join(source,n)),equal=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
function call(f){try{return {return:f()??null};}catch(err){if(err instanceof WebAssembly.RuntimeError)return {trap:true};throw err;}}
function observe(host){const memory=Buffer.from(host.ex.memory.buffer).subarray(0,65536);return {hostTrace:host.trace(),memory:{sha256:createHash('sha256').update(memory).digest('hex'),bytes7to10:[...memory.subarray(7,11)]}};}
function raw(module,write){let x;const trace=[];x=new WebAssembly.Instance(module,{env:{touch:()=>{trace.push({name:'touch',write});if(write)new Uint8Array(x.exports.memory.buffer)[7]=0;}}});return {ex:x.exports,run:async()=>call(x.exports.entry),trace:()=>trace.slice()};}
function migrate(module,stop,write,saved){let x,polls=0,requested=false;const trace=saved?structuredClone(saved.trace):[];
 const imports={env:{touch:()=>{trace.push({name:'touch',write});if(write)new Uint8Array(x.exports.memory.buffer)[7]=0;}},host:{should_migrate:()=>{const yes=polls++===stop;requested||=yes;return Number(yes);},restore_memory:()=>{if(saved)for(const [name,value]of Object.entries(saved.memories))new Uint8Array(x.exports[name].buffer).set(value);}}};
 x=new WebAssembly.Instance(module,imports);return {ex:x.exports,run:async()=>call(x.exports.entry),stats:()=>({polls,requested}),trace:()=>trace.slice(),save:()=>({trace:trace.slice(),memories:Object.fromEntries(['memory','checkpoint_memory'].map(n=>[n,Buffer.from(x.exports[n].buffer)]))})};}
async function weave(binary,stop,write,saved){let x,trace=[];
 const service={imports:{env:{touch:()=>{trace.push({name:'touch',write});if(write)new Uint8Array(x.ex().memory.buffer)[7]=0;}}},snapshot:()=>new TextEncoder().encode(JSON.stringify(trace)),restore:data=>{trace=JSON.parse(new TextDecoder().decode(data));}};
 x=await new WeaveInstance(binary,new Map([['touch-service',service]]),{yieldMs:1e9}).instantiate();if(saved)x.restore(saved);else x.init();x.pollMode={afterPolls:stop<0?1e9:stop};
 return {ex:x.ex(),instance:x,trace:()=>trace.slice(),stats:()=>({polls:x.pollCount}),run:async(resume=false)=>{try{const r=await x.drive(resume?null:'entry',[],()=> 'hold');return r.status==='held'?{held:true}:{return:r.results.length?r.results:null};}catch(err){if(err instanceof WebAssembly.RuntimeError)return {trap:true};throw err;}}};}
try{
 for(const r of input.rows)for(const write of [false,true]){
  const original=raw(new WebAssembly.Module(bytes(r.original)),write),reference={outcome:await original.run(),...observe(original)};assert(reference.outcome.trap);assert.deepEqual(reference.hostTrace,[{name:'touch',write}]);
  for(const v of r.variants){const row={name:r.name,write,backend:v.backend,transformStatus:v.status,reference};rows.push(row);if(v.status!=='valid')continue;
   const binary=bytes(v.binary),module=new WebAssembly.Module(binary),make=async(stop,saved)=>v.backend==='migrate'?migrate(module,stop,write,saved):weave(binary,stop,write,saved);
   const continuous=await make(-1),outcome=await continuous.run();row.continuous={outcome,...observe(continuous)};row.continuousMatches=equal(reference,row.continuous);row.polls=continuous.stats().polls;row.scenarios=[];
   if(!row.continuousMatches){row.status='continuous-mismatch';continue;}assert(row.polls<=64);row.status='executed';
   for(let stop=0;stop<=row.polls;stop++){
    const first=await make(stop),firstOutcome=await first.run(),reached=v.backend==='migrate'?first.stats().requested:!!firstOutcome.held;
    if(!reached){row.scenarios.push({stop,status:'checkpoint-not-reached',firstOutcome});continue;}
    const before=observe(first),saved=v.backend==='migrate'?first.save():first.instance.checkpoint(),second=await make(-1,saved),resumedOutcome=await second.run(true),after=observe(second);
    row.scenarios.push({stop,status:'restored',firstOutcome,before,outcome:resumedOutcome,...after,entryMatches:equal(resumedOutcome,reference.outcome),hostTraceMatches:equal(after.hostTrace,reference.hostTrace),memoryMatches:equal(after.memory,reference.memory)});
   }
  }
 }
 const summary=['migrate','weave'].map(backend=>{const rr=rows.filter(r=>r.backend===backend),ss=rr.flatMap(r=>r.scenarios??[]);return {backend,conditions:rr.length,invalidOutputs:rr.filter(r=>r.transformStatus!=='valid').length,continuousMismatches:rr.filter(r=>r.continuousMatches===false).length,restored:ss.filter(s=>s.status==='restored').length,notReached:ss.filter(s=>s.status==='checkpoint-not-reached').length,entryMismatches:ss.filter(s=>s.entryMatches===false).length,hostTraceMismatches:ss.filter(s=>s.hostTraceMatches===false).length,memoryMismatches:ss.filter(s=>s.memoryMatches===false).length};});
 fs.writeFileSync(path.join(out,'results.json'),JSON.stringify({node:process.version,rows,summary,scope:'Only original entry and public guest memory; local host import with explicitly snapshotted trace. Outside the closed analyser profile.'},null,2));console.log(JSON.stringify(summary));
}catch(err){fs.writeFileSync(path.join(out,'failure.json'),JSON.stringify({message:err.message,stack:err.stack,rows},null,2));throw err;}
finally{fs.copyFileSync(new URL(import.meta.url),path.join(out,'guard-import-entry.mjs'));fs.writeFileSync(path.join(out,'sha256.json'),JSON.stringify(Object.fromEntries(fs.readdirSync(out).map(n=>[n,createHash('sha256').update(fs.readFileSync(path.join(out,n))).digest('hex')])),null,2));}
