import fs from 'node:fs';import path from 'node:path';import assert from 'node:assert/strict';import {createHash} from 'node:crypto';
const dir=path.resolve(process.argv[2]),m=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json'))),rows=[];
function call(e,args){try{return {value:e.test(...args)??null};}catch(x){if(x instanceof WebAssembly.RuntimeError)return {trap:true};throw x;}}
for(const c of m.cases){
 if(c.expectedWitness===null){rows.push({name:c.name,status:'not-executed-recursion'});continue;}
 const module=new WebAssembly.Module(fs.readFileSync(path.join(dir,c.observed))),observations=[];
 for(const x of c.rows){
  const traces=[];
  for(const dropped of [false,true]){
   const e=new WebAssembly.Instance(module).exports;if(dropped)e.__ctx_drop();const trace=[];
   for(let n=0;n<2;n++)trace.push({result:call(e,x.args),memory:createHash('sha256').update(new Uint8Array(e.memory.buffer)).digest('hex')});traces.push(trace);
  }
  assert.deepEqual(traces,x.traces,c.name);observations.push({args:x.args,same:JSON.stringify(traces[0])===JSON.stringify(traces[1])});
 }
 rows.push({name:c.name,status:'matches-wasmtime',observations});
}
const summary={controls:rows.length,executed:rows.filter(x=>x.status==='matches-wasmtime').length,
 inputConditions:rows.reduce((n,r)=>n+(r.observations?.length??0),0),apiCallsPerEngine:rows.reduce((n,r)=>n+4*(r.observations?.length??0),0)};
fs.writeFileSync(path.join(dir,'results.json'),JSON.stringify({node:process.version,summary,rows},null,2));console.log(JSON.stringify(summary));
