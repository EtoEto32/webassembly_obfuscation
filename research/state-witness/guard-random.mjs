import fs from 'node:fs';import path from 'node:path';import assert from 'node:assert/strict';
const dir=process.argv[2],m=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json')));let calls=0;const rows=[];
function seqs(actions,depth){const out=[];let frontier=[[]];for(let n=0;n<depth;n++){frontier=frontier.flatMap(s=>actions.map(a=>[...s,a]));out.push(...frontier);}return out;}
for(const row of m.rows){
 const module=new WebAssembly.Module(fs.readFileSync(path.join(dir,row.prepared))),sequences=seqs(row.actions,m.depth),samples=[];
 for(const s of row.samples){const data=Buffer.alloc(row.proof.memoryBytes);for(const [i,v] of s.patches)data[i]=v;let witness=null;
  for(const seq of sequences){
   const pair=[row.left,row.right].map(flags=>{const e=new WebAssembly.Instance(module).exports;new Uint8Array(e.memory.buffer).set(data);flags.forEach((v,i)=>{if(!v)e['__guard_drop_'+i]();});return e;});
   for(let step=0;step<seq.length;step++){
    const outcomes=pair.map(e=>{calls++;try{e[seq[step]]();return 'return';}catch(err){if(!(err instanceof WebAssembly.RuntimeError))throw err;return 'trap';}});
    if(outcomes[0]!==outcomes[1]||!Buffer.from(pair[0].memory.buffer).equals(Buffer.from(pair[1].memory.buffer))){witness=seq.slice(0,step+1);break;}
   }
   if(witness)break;
  }
  assert.deepEqual(witness,s.witness);if(s.satisfies)assert.equal(witness,null);samples.push({satisfies:s.satisfies,witness});
 }rows.push({name:row.name,status:row.proof.status,iterations:row.proof.iterations,samples});
}
assert.equal(calls,m.wasmtimeApiCalls);
const counts=Object.fromEntries([...new Set(rows.map(x=>x.status))].map(s=>[s,rows.filter(r=>r.status===s).length]));
const result={node:process.version,cases:rows.length,samples:rows.reduce((n,r)=>n+r.samples.length,0),counts,apiCallsPerEngine:calls,
 boundedUnresolved:m.boundedUnresolved,rows};fs.writeFileSync(path.join(dir,'results.json'),JSON.stringify(result,null,2));
console.log(JSON.stringify({cases:rows.length,samples:result.samples,counts,callsPerEngine:calls,unresolved:m.boundedUnresolved.length}));
