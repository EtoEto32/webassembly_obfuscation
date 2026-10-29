import fs from 'node:fs';import path from 'node:path';import assert from 'node:assert/strict';
const dir=process.argv[2],m=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json'))),BASE=2**32;let calls=0,negative=0,positive=0,terminated=0;const rows=[];
function snapshot(e,row){const out={},refs=new Map([[null,256]]);for(let i=0;i<row.proof.functions;i++)refs.set(e['__guard_func_'+i],i+257);
 for(const r of row.proof.observedResources){const info=row.proof.resources[r],x=e['__guard_resource_'+r];out[r]=info.kind==='memory'?Buffer.from(x.buffer):Array.from({length:x.length},(_,i)=>{assert(refs.has(x.get(i)));return refs.get(x.get(i));});}return out;
}
function same(a,b,row){return row.proof.observedResources.every(r=>row.proof.resources[r].kind==='memory'?a[r].equals(b[r]):JSON.stringify(a[r])===JSON.stringify(b[r]));}
for(const row of m.rows){const module=new WebAssembly.Module(fs.readFileSync(path.join(dir,row.prepared))),samples=[];
 for(const s of row.samples){const sequences=s.witness?[s.witness.calls]:s.positiveSequences;const observations=[];if(s.witness)negative++;else positive++;
  for(const seq of sequences){const pair=[row.left,row.right].map(flags=>{const e=new WebAssembly.Instance(module).exports;for(const [key,value] of s.patches){const r=Math.floor(key/BASE),i=key%BASE,x=e['__guard_resource_'+r];if(row.proof.resources[r].kind==='memory')new Uint8Array(x.buffer)[i]=value;else x.set(i,value===256?null:e['__guard_func_'+(value-257)]);}flags.forEach((v,i)=>{if(!v)e['__guard_drop_'+i]();});return e;});let difference=null,terminalAt=null,executed=0;
   for(let i=0;i<seq.length;i++){const outcomes=pair.map(e=>{calls++;try{return ['return',e[seq[i].name](...seq[i].args)];}catch(err){if(!(err instanceof WebAssembly.RuntimeError))throw err;return ['trap'];}});executed++;
    if(JSON.stringify(outcomes[0])!==JSON.stringify(outcomes[1])||!same(snapshot(pair[0],row),snapshot(pair[1],row),row)){difference=i+1;break;}
    if(row.proof.protocol==='terminal' && outcomes[0][0]==='trap'){terminalAt=i+1;terminated++;break;}}
   assert.equal(difference,s.witness?seq.length:null);if(s.witness)assert.equal(executed,seq.length);observations.push({difference,terminalAt,executed});
  }samples.push({negative:!!s.witness,sequences:observations});
 }rows.push({name:row.name,contract:row.proof.contract,status:row.proof.status,samples});
}
const result={node:process.version,rows,contracts:rows.length,positiveStores:positive,negativeStores:negative,apiCalls:calls,terminatedSequences:terminated,regressionCounts:m.regressionCounts};
fs.writeFileSync(path.join(dir,'results.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(Object.fromEntries(Object.entries(result).filter(([k])=>k!=='rows'))));
