import fs from 'node:fs';import path from 'node:path';import assert from 'node:assert/strict';
const dir=process.argv[2],manifest=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json')));let calls=0;const rows=[];
function seqs(actions,depth){const out=[];let frontier=[[]];for(let n=0;n<depth;n++){frontier=frontier.flatMap(s=>actions.map(a=>[...s,a]));out.push(...frontier);}return out;}
for(const row of manifest.rows){
 const module=new WebAssembly.Module(fs.readFileSync(path.join(dir,row.prepared))),sequences=seqs(row.actions,manifest.depth);
 const baseline=fs.readFileSync(path.join(dir,row.memory)),samples=[];
 for(const sample of row.samples){let witness=null;const data=Buffer.from(baseline);for(const [i,v] of sample.patches)data[i]=v;
  for(const seq of sequences){const traces=[];
   for(const alive of [row.left,row.right]){
    const e=new WebAssembly.Instance(module).exports;new Uint8Array(e.memory.buffer).set(data);alive.forEach((v,i)=>{if(!v)e['__guard_drop_'+i]();});const trace=[];
    for(const api of seq){let outcome='return';try{e[api]();}catch(err){if(!(err instanceof WebAssembly.RuntimeError))throw err;outcome='trap';}calls++;
     trace.push({outcome,memory:Buffer.from(e.memory.buffer)});
    }traces.push(trace);
   }
   if(traces[0].some((x,i)=>x.outcome!==traces[1][i].outcome||!x.memory.equals(traces[1][i].memory))){witness=seq;break;}
  }
  assert.equal(witness===null,sample.satisfies);assert.deepEqual(witness,sample.witness);samples.push({satisfies:sample.satisfies,witness});
 }rows.push({name:row.name,status:row.proof.status,guard:row.proof.guard,iterations:row.proof.iterations,samples});
}
assert.equal(calls,manifest.wasmtimeApiCalls);
const r={rows,node:process.version,apiCallsPerEngine:calls,samples:rows.reduce((n,r)=>n+r.samples.length,0),
 note:'Concrete checks to depth 4; no new product defect count and no machine-checked theorem.'};
fs.writeFileSync(path.join(dir,'results.json'),JSON.stringify(r,null,2));console.log(JSON.stringify({cases:rows.length,callsPerEngine:calls,samples:r.samples}));
