import fs from 'node:fs';import path from 'node:path';import assert from 'node:assert/strict';
const dir=process.argv[2],m=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json')));let calls=0;const rows=[];
for(const row of m.rows){const module=new WebAssembly.Module(fs.readFileSync(path.join(dir,row.prepared)));const samples=[];
 for(const s of row.samples){const pair=[row.left,row.right].map(flags=>{const e=new WebAssembly.Instance(module).exports;new Uint8Array(e.__guard_resource_0.buffer)[0]=s.byte;flags.forEach((v,i)=>{if(!v)e['__guard_drop_'+i]();});return e;});let difference=null;
  for(let i=0;i<row.sequence.length;i++){const outcomes=pair.map(e=>{calls++;try{e[row.sequence[i]]();return 'return';}catch(err){if(!(err instanceof WebAssembly.RuntimeError))throw err;return 'trap';}});
   if(outcomes[0]!==outcomes[1]||!Buffer.from(pair[0].__guard_resource_0.buffer).equals(Buffer.from(pair[1].__guard_resource_0.buffer))){difference=i+1;break;}}
  assert.equal(difference,s.firstDifference);samples.push({byte:s.byte,firstDifference:difference});
 }rows.push({name:row.name,samples});
}
assert.equal(calls,m.wasmtimeApiCalls);const result={node:process.version,rows,apiCallsPerEngine:calls,priorModules:m.regressions.length,priorSamples:m.priorSamples,changedWitnessWords:m.changedWitnessWords,officialPairs:m.official.length,newCases:rows.length,newStores:rows.reduce((n,r)=>n+r.samples.length,0)};
fs.writeFileSync(path.join(dir,'results.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(Object.fromEntries(Object.entries(result).filter(([k])=>k!=='rows'))));
