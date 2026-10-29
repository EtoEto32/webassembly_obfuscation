import fs from 'node:fs';import path from 'node:path';import assert from 'node:assert/strict';import {createHash} from 'node:crypto';
import {WeaveInstance} from './weave.mjs';import observer from './observer.cjs';import directory from './directory-observer.cjs';
const [inputs,name,kind,mode,out]=process.argv.slice(2),m=JSON.parse(fs.readFileSync(path.join(inputs,name+'-manifest.json')));
const load=n=>fs.readFileSync(path.join(inputs,n)),hash=b=>createHash('sha256').update(b).digest('hex');
const memoryName=JSON.parse(m.originalExports.find(x=>x[2][0]==='memory')[1]);
const result={name,kind,mode,node:process.version,v8:process.versions.v8,phases:[],inputHashes:{}};
const save=()=>fs.writeFileSync(out,JSON.stringify(result,null,2));
function phase(label,x){result.phases.push({label,...x});save();}
function makeRaw(file){const b=load(file);result.inputHashes[file]=hash(b);return new WebAssembly.Instance(new WebAssembly.Module(b));}
const raw=makeRaw(name+'.wasm'),expectedOutcome=observer.call(raw.exports._start),memory=Buffer.from(raw.exports[memoryName].buffer);
phase('original',{outcome:expectedOutcome,memoryBytes:memory.length,memorySha256:hash(memory)});
let expected=null;
if(kind==='directory'){
  const instrumented=makeRaw(name+'-directory.wasm');assert.deepEqual(observer.call(instrumented.exports._start),expectedOutcome);
  expected=directory.snapshot(instrumented.exports,m);assert(expected.memory.equals(memory));
  assert.deepEqual(observer.difference(expected,directory.snapshot(instrumented.exports,m)),[]);
  phase('directory-baseline',{status:'compared'});
}
const file=name+'-'+kind+'-woven.wasm',bytes=load(file);result.inputHashes[file]=hash(bytes);
const make=async()=>new WeaveInstance(bytes,new Map(),{yieldMs:1e9}).instantiate();
let inst=await make();inst.init();inst.pollMode={afterPolls:mode==='restore'?0:1e12};
async function drive(x,entry){
  try{return await x.drive(entry,[],()=> 'hold');}
  catch(e){if(e instanceof WebAssembly.RuntimeError)return {trap:true,detail:e.message};throw e;}
}
let outcome=await drive(inst,'_start');phase('first-execution',{outcome,polls:inst.pollCount});
let reached=false;
if(outcome.status==='held'){
  reached=true;const saved=inst.checkpoint();inst=await make();inst.restore(saved);inst.pollMode={afterPolls:1e12};
  outcome=await drive(inst,null);phase('resumed',{outcome,polls:inst.pollCount});
}
const api=outcome.trap?{trap:true}:{value:outcome.results?.[0]??null};
const differences=[];if(JSON.stringify(api)!==JSON.stringify(expectedOutcome))differences.push('API');
const prefix=Buffer.from(new Uint8Array(inst.ex()[memoryName].buffer,0,memory.length));
if(!prefix.equals(memory))differences.push('memory-prefix');
if(kind==='directory'&&outcome.status==='done'){
  try{
    const state=directory.snapshot(inst.ex(),m);differences.push(...observer.difference(expected,state));
    const repeated=directory.snapshot(inst.ex(),m);assert.deepEqual(observer.difference(state,repeated),[]);
    const {memory:_,...details}=state;result.finalState={...details,memorySha256:hash(state.memory)};
  }catch(e){result.observerFailure={name:e.name,message:e.message};}
}
result.status=result.observerFailure?'observer-failure':differences.length?'difference':mode==='restore'&&!reached?'checkpoint-not-reached':'compared';
Object.assign(result,{differences,restorationReached:reached,api,expectedOutcome,physicalPages:inst.ex()[memoryName].buffer.byteLength/65536,
  memoryPrefixSha256:hash(prefix),rss:process.memoryUsage().rss});save();
console.log(JSON.stringify({name,kind,mode,status:result.status,differences}));
