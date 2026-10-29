import fs from 'node:fs';import path from 'node:path';import assert from 'node:assert/strict';
const dir=process.argv[2],manifest=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json')));
const counts={apiCalls:0,hostCalls:0,cellWrites:0,pureTagCalls:0,preparationCalls:0};
for(const row of manifest.rows){const traces=[];for(let side=0;side<2;side++){
 let ex,hostTrace=[],current=new Map();const snapshot=()=>{const f=ex.public.get(0);if(f){counts.pureTagCalls++;return f();}return null;};
 const touch=()=>{counts.hostCalls++;hostTrace.push({name:'touch',read:row.reads==='public'?snapshot():null});for(const [cell,value]of current.get(0)??[]){assert.equal(cell,4294967296);assert.equal(value,256);ex.public.set(0,null);counts.cellWrites++;}};
 ex=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(dir,row.source))),{env:{touch}}).exports;ex[side===0?'retire':'release_b']();counts.preparationCalls++;const output=[];
 for(const call of row.word){current=new Map(call.writes.map(b=>[b.block,b.cells]));hostTrace=[];let outcome='return';try{ex[call.name]();}catch(err){if(!(err instanceof WebAssembly.RuntimeError))throw err;outcome='trap';}counts.apiCalls++;
 output.push({api:call.name,outcome,hostTrace,public:snapshot()});}traces.push(output);
}assert.deepEqual(traces,row.traces,row.name);}
for(const [key,value]of Object.entries(counts))assert.equal(value,manifest[key],key);
const result={contracts:manifest.contracts,negativeWitnesses:manifest.negativeWitnesses,maxApiLength:manifest.maxApiLength,...counts,node:process.version};fs.writeFileSync(path.join(dir,'results.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result));
