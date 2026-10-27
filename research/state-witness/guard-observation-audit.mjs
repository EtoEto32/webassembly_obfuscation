import fs from 'node:fs';import path from 'node:path';import assert from 'node:assert/strict';
const dir=process.argv[2],m=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json'))),BASE=2**32;const rows=[];let calls=0;
function snapshot(e,row){const out={},refs=new Map([[null,256]]);for(let i=0;i<row.proof.functions;i++)refs.set(e['__guard_func_'+i],i+257);
 for(const [r,info] of Object.entries(row.proof.resources)){const x=e['__guard_resource_'+r];out[r]=info.kind==='memory'?Buffer.from(x.buffer):Array.from({length:x.length},(_,i)=>{assert(refs.has(x.get(i)));return refs.get(x.get(i));});}return out;
}
for(const row of m.rows){const module=new WebAssembly.Module(fs.readFileSync(path.join(m.source,row.prepared)));const samples=[];
 for(let si=0;si<row.samples.length;si++){const s=row.samples[si];if(s.witness===null)continue;
  const pair=[row.left,row.right].map(flags=>{const e=new WebAssembly.Instance(module).exports;for(const [key,value] of s.patches){const r=Math.floor(key/BASE),i=key%BASE,x=e['__guard_resource_'+r];if(row.proof.resources[r].kind==='memory')new Uint8Array(x.buffer)[i]=value;else x.set(i,value===256?null:e['__guard_func_'+(value-257)]);}flags.forEach((v,i)=>{if(!v)e['__guard_drop_'+i]();});return e;});
  let evidence=null;for(let i=0;i<s.witness.word.length;i++){const api=s.witness.word[i];const outcomes=pair.map(e=>{calls++;try{e[api]();return 'return';}catch(err){if(!(err instanceof WebAssembly.RuntimeError))throw err;return 'trap';}});
   const [a,b]=pair.map(e=>snapshot(e,row));const different=Object.keys(row.proof.resources).filter(r=>row.proof.resources[r].kind==='memory'?!a[r].equals(b[r]):JSON.stringify(a[r])!==JSON.stringify(b[r]));
   if(outcomes[0]!==outcomes[1]||different.length){assert.equal(i+1,s.witness.word.length);let category='instrumentation-only-store';
    if(outcomes[0]!==outcomes[1])category='original-return-or-trap';
    else if(row.publicResources.some(x=>x.kind==='memory'&&different.includes(String(x.resource))))category='original-exported-memory';
    else if(row.publicResources.some(x=>x.kind==='table'&&different.includes(String(x.resource))))category='original-exported-table-descriptor';
    else if(row.hasMemoryReadApi)category='private-memory-with-read-api-needs-suffix';
    evidence={sample:si,category,outcomes,differentResources:different,wordLength:i+1};break;}
  }assert(evidence);samples.push(evidence);
 }rows.push({name:row.name,publicResources:row.publicResources,returnTrapContract:row.returnTrapContract,samples});
}
const counts={};for(const r of rows)for(const s of r.samples)counts[s.category]=(counts[s.category]??0)+1;
const privateEquivalent=rows.filter(r=>r.publicResources.length===0&&r.returnTrapContract.status==='equivalent-under-return-trap-contract').reduce((n,r)=>n+r.samples.filter(s=>s.category==='instrumentation-only-store').length,0);
const result={rows,counts,apiCalls:calls,privateStoreWitnessesWithEquivalentOriginalFunctionReturns:privateEquivalent,node:process.version,
 scope:'Categories refer to the generated word and original resource exports. Table descriptors alone are not a general contextual-equivalence counterexample.'};
fs.writeFileSync(path.join(dir,'results.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(Object.fromEntries(Object.entries(result).filter(([k])=>k!=='rows'))));
