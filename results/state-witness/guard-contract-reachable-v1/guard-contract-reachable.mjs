import fs from 'node:fs';import path from 'node:path';import assert from 'node:assert/strict';
const dir=process.argv[2],m=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json')));const rows=[];let calls=0,prefixcalls=0,probes=0;
for(const row of m.rows){const module=new WebAssembly.Module(fs.readFileSync(path.join(dir,row.source)));
 assert.deepEqual(WebAssembly.Module.exports(module).map(e=>e.name).sort(),['public','a','b','retire','release_b','mask','copy','publish'].sort());
 const pair=[new WebAssembly.Instance(module).exports,new WebAssembly.Instance(module).exports];pair[0].retire();pair[1].release_b();prefixcalls+=2;
 const trace=[];let difference=null;
 for(let i=0;i<row.sequence.length;i++){const api=row.sequence[i],outcomes=[],observed=[];
  for(const e of pair){calls++;try{outcomes.push(['return',e[api]()??null]);}catch(err){if(!(err instanceof WebAssembly.RuntimeError))throw err;outcomes.push(['trap']);}
   const f=e.public.get(0);if(f===null)observed.push(null);else{assert(f===e.a||f===e.b);observed.push(f());probes++;}}
  trace.push({api,outcomes,publicFunctionResults:observed});if(JSON.stringify(outcomes[0])!==JSON.stringify(outcomes[1])||observed[0]!==observed[1])difference??=i+1;
 }assert.deepEqual(trace,row.trace);assert.equal(difference,row.firstDifference);rows.push({name:row.name,firstDifference:difference,finalPublicResults:trace.at(-1).publicFunctionResults});
}
assert.equal(calls,m.wasmtimeDiagnosticApiCalls);assert.equal(prefixcalls,m.wasmtimePreparationApiCalls);assert.equal(probes,m.wasmtimePublicFunctionCalls);
const result={rows,node:process.version,originalBinaries:rows.length,diagnosticApiCallsPerEngine:calls,preparationApiCallsPerEngine:prefixcalls,publicFunctionCallsPerEngine:probes,
 scope:m.scope};fs.writeFileSync(path.join(dir,'results.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(Object.fromEntries(Object.entries(result).filter(([k])=>k!=='rows'))));
