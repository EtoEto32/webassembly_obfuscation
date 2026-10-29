import fs from 'node:fs';import path from 'node:path';import assert from 'node:assert/strict';
const dir=process.argv[2],m=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json'))),module=new WebAssembly.Module(fs.readFileSync(path.join(dir,m.prepared)));let calls=0;const traces=[];
for(const test of m.traces){const pair=[new WebAssembly.Instance(module).exports,new WebAssembly.Instance(module).exports];pair[0].__drop();const trace=[];
 for(const api of test.sequence){const outcomes=pair.map(e=>{calls++;try{return ['return',e[api]()??null];}catch(err){if(!(err instanceof WebAssembly.RuntimeError))throw err;return ['trap'];}});trace.push({api,outcomes});if(outcomes.some(x=>x[0]==='trap'))break;}
 traces.push({sequence:test.sequence,trace});}
assert.deepEqual(traces,m.traces);assert.equal(calls,m.wasmtimeApiCalls);const result={node:process.version,apiCalls:calls,rejectedProfile:m.rejectedProfile,traces};fs.writeFileSync(path.join(dir,'results.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result));
