import fs from 'node:fs';import path from 'node:path';import assert from 'node:assert/strict';
const dir=process.argv[2],manifest=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json'))),counts={apiCalls:0,preparationCalls:0,hostCalls:0,cellWrites:0,pureTagCalls:0};
// A valid foreign Wasm reference, used only as a pure identity tag.
const bytes=Uint8Array.from([0,97,115,109,1,0,0,0,1,5,1,96,0,1,127,3,2,1,0,7,5,1,1,102,0,0,10,7,1,5,0,65,175,2,11]);
const foreign=new WebAssembly.Instance(new WebAssembly.Module(bytes)).exports.f;
let comparisons=0;const cache=new Map();
for(const row of manifest.rows){
 if(!cache.has(row.source))cache.set(row.source,new WebAssembly.Module(fs.readFileSync(path.join(dir,row.source))));
 for(const sample of row.samples)for(const run of sample.runs){const traces=[];
  for(let side=0;side<2;side++){
   let ex,refs,hostTrace=[],current=new Map(),block=0;
   const snapshot=()=>row.kind==='memory'?Array.from(new Uint8Array(ex.resource.buffer,0,2)):Array.from({length:2},(_,n)=>{const f=ex.resource.get(n);if(f===null)return 256;counts.pureTagCalls++;return new Map([[101,258],[202,259],[303,260]]).get(f());});
   const touch=()=>{const event={name:'env.touch'},summary=row.proof.hostSummaries[0];if(summary.reads==='public')event.read=snapshot();hostTrace.push(event);counts.hostCalls++;
    if(summary.writes==='public'||summary.writes==='may-public')for(const [cell,value]of current.get(block)??[]){if(row.kind==='memory')new Uint8Array(ex.resource.buffer)[cell]=value;else ex.resource.set(cell%2**32,refs.get(value));counts.cellWrites++;}block++;};
   ex=new WebAssembly.Instance(cache.get(row.source),{env:{touch}}).exports;refs=row.kind==='table'?new Map([[256,null],[258,ex.resource.get(0)],[259,ex.resource.get(1)],[260,foreign]]):null;
   ex[side===0?'retire':'release_b']();counts.preparationCalls++;
   for(const [cell,value]of sample.values)if(row.kind==='memory')new Uint8Array(ex.resource.buffer)[cell]=value;else ex.resource.set(cell%2**32,refs.get(value));
   const outputs=[];for(const call of run.word){current=new Map(call.writes.map(r=>[r.block,r.cells]));block=0;hostTrace=[];let outcome='return';try{ex[call.name]();}catch(err){if(!(err instanceof WebAssembly.RuntimeError))throw err;outcome='trap';}counts.apiCalls++;
    outputs.push({name:call.name,outcome,hostTrace,public:row.proof.contract==='returns'?null:snapshot()});if(outcome==='trap'&&row.proof.protocol==='terminal')break;
   }traces.push(outputs);
  }
  assert.deepEqual(traces,run.traces,row.name);assert.equal(JSON.stringify(traces[0])===JSON.stringify(traces[1]),run.equal,row.name);comparisons++;
 }
}
for(const [key,value]of Object.entries(counts))assert.equal(value,manifest[key],key);assert.equal(comparisons,manifest.runtimeComparisons);
const result={contracts:manifest.contracts,runtimeComparisons:comparisons,...counts,node:process.version};fs.writeFileSync(path.join(dir,'results.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result));
