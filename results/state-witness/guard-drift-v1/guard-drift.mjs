import fs from 'node:fs';import path from 'node:path';import assert from 'node:assert/strict';
const dir=process.argv[2],m=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json'))),rows=[];let calls=0,prefixes=0;
for(const row of m.rows){const module=new WebAssembly.Module(fs.readFileSync(path.join(dir,row.source))),traces=[];
 for(const scenario of row.traces){const pair=[new WebAssembly.Instance(module).exports,new WebAssembly.Instance(module).exports];pair[0].retire();pair[1].release_b();prefixes+=2;const trace=[];let difference=null;
  for(let i=0;i<scenario.sequence.length;i++){const api=scenario.sequence[i],outcomes=pair.map(e=>{calls++;try{return ['return',e[api]()??null];}catch(err){if(!(err instanceof WebAssembly.RuntimeError))throw err;return ['trap'];}});
   const memories=pair.map(e=>Buffer.from(e.memory.buffer)),memoryEqual=memories[0].equals(memories[1]);trace.push({api,outcomes,firstBytes:memories.map(x=>x[0]),memoryEqual});
   if(JSON.stringify(outcomes[0])!==JSON.stringify(outcomes[1])||(row.proof.contract!=='returns'&&!memoryEqual)){difference=i+1;break;}
   if(row.proof.protocol==='terminal'&&outcomes[0][0]==='trap')break;
  }traces.push({sequence:scenario.sequence,difference,trace});
 }assert.deepEqual(traces,row.traces);rows.push({name:row.name,status:row.proof.status,traces});}
assert.equal(calls,m.wasmtimeApiCalls);assert.equal(prefixes,m.preparationApiCalls);const result={node:process.version,rows,apiCalls:calls,preparationApiCalls:prefixes,contracts:rows.length};
fs.writeFileSync(path.join(dir,'results.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(Object.fromEntries(Object.entries(result).filter(([k])=>k!=='rows'))));
