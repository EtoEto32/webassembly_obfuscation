import fs from 'node:fs';import path from 'node:path';import assert from 'node:assert/strict';
const dir=process.argv[2],out=process.argv[3],m=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json'))),BASE=2**32;
fs.mkdirSync(out,{recursive:false});const foreign=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(dir,'foreign.wasm')))).exports.foreign;
let apiCalls=0,cellWrites=0,positiveStores=0,negativeStores=0,terminatedSequences=0;const rows=[];
function snapshot(e,row){const data={},refs=new Map([[null,256],[foreign,row.proof.foreignReference]]);for(let i=0;i<row.proof.functions;i++)refs.set(e['__guard_func_'+i],i+257);
 for(const r of row.proof.observedResources){const x=e['__guard_resource_'+r];data[r]=row.proof.resources[r].kind==='memory'?Buffer.from(x.buffer):Array.from({length:x.length},(_,i)=>{assert(refs.has(x.get(i)));return refs.get(x.get(i));});}return data;
}
function same(a,b,row){return row.proof.observedResources.every(r=>row.proof.resources[r].kind==='memory'?a[r].equals(b[r]):JSON.stringify(a[r])===JSON.stringify(b[r]));}
function patch(e,row,cells,external){for(const [cell,value] of cells){const r=Math.floor(cell/BASE),i=cell%BASE,x=e['__guard_resource_'+r];
 if(external)assert(row.proof.writableCells.includes(cell));
 if(row.proof.resources[r].kind==='memory')new Uint8Array(x.buffer)[i]=value;
 else x.set(i,value===256?null:value===row.proof.foreignReference?foreign:e['__guard_func_'+(value-257)]);
 if(external)cellWrites++;
}}
for(const row of m.rows){const mod=new WebAssembly.Module(fs.readFileSync(path.join(dir,row.prepared))),samples=[];
 for(const sample of row.samples){const words=sample.witness?[sample.witness.steps]:sample.positiveSequences,observations=[];if(sample.witness)negativeStores++;else positiveStores++;
  for(const word of words){const pair=[row.left,row.right].map(flags=>{const e=new WebAssembly.Instance(mod).exports;patch(e,row,sample.patches,false);flags.forEach((v,i)=>{if(!v)e['__guard_drop_'+i]();});return e;});let difference=null,terminalAt=null,executed=0;
   for(let i=0;i<word.length;i++){const step=word[i];let outcomes;
    if(step.kind==='write'){pair.forEach(e=>patch(e,row,step.cells,true));outcomes=[['write'],['write']];}
    else outcomes=pair.map(e=>{apiCalls++;try{return ['return',e[step.name](...step.args)??null];}catch(err){if(!(err instanceof WebAssembly.RuntimeError))throw err;return ['trap'];}});
    executed++;
    if(JSON.stringify(outcomes[0])!==JSON.stringify(outcomes[1])||!same(snapshot(pair[0],row),snapshot(pair[1],row),row)){difference=i+1;break;}
    if(row.proof.protocol==='terminal'&&outcomes[0][0]==='trap'){terminalAt=i+1;terminatedSequences++;break;}
   }
   assert.equal(difference,sample.witness?word.length:null,row.name);observations.push({difference,terminalAt,executed});
  }
  samples.push({negative:!!sample.witness,sequences:observations});
 }
 rows.push({name:row.name,status:row.proof.status,samples});
}
const result={node:process.version,rows,contracts:rows.length,positiveStores,negativeStores,apiCalls,cellWrites,terminatedSequences};
fs.writeFileSync(path.join(out,'results.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(Object.fromEntries(Object.entries(result).filter(([k])=>k!=='rows'))));
