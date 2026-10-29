import fs from 'node:fs';import path from 'node:path';import assert from 'node:assert/strict';
const dir=process.argv[2],m=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json'))),BASE=2**32;let calls=0,positives=0,negatives=0;const rows=[];
function snapshot(e,row){const out={};const refs=new Map([[null,256]]);for(let i=0;i<row.proof.functions;i++)refs.set(e['__guard_func_'+i],i+257);
 for(const [r,info] of Object.entries(row.proof.resources)){const x=e['__guard_resource_'+r];out[r]=info.kind==='memory'?Buffer.from(x.buffer):Array.from({length:x.length},(_,i)=>{assert(refs.has(x.get(i)));return refs.get(x.get(i));});}return out;
}
function same(a,b,resources){return Object.keys(resources).every(r=>resources[r].kind==='memory'?a[r].equals(b[r]):JSON.stringify(a[r])===JSON.stringify(b[r]));}
for(const row of m.rows){const module=new WebAssembly.Module(fs.readFileSync(path.join(dir,row.prepared))),results=[];
 for(const s of row.samples){if(s.witness===null){assert(s.satisfies);positives++;results.push(null);continue;}negatives++;
  const pair=[row.left,row.right].map(flags=>{const e=new WebAssembly.Instance(module).exports;
   for(const [key,value] of s.patches){const r=Math.floor(key/BASE),i=key%BASE,x=e['__guard_resource_'+r];if(row.proof.resources[r].kind==='memory')new Uint8Array(x.buffer)[i]=value;else x.set(i,value===256?null:e['__guard_func_'+(value-257)]);}
   flags.forEach((v,i)=>{if(!v)e['__guard_drop_'+i]();});return e;});
  const word=s.witness.word;let firstDifference=null;
  for(let i=0;i<word.length;i++){const outcomes=pair.map(e=>{calls++;try{e[word[i]]();return 'return';}catch(err){if(!(err instanceof WebAssembly.RuntimeError))throw err;return 'trap';}});
   if(outcomes[0]!==outcomes[1]||!same(snapshot(pair[0],row),snapshot(pair[1],row),row.proof.resources)){firstDifference=i+1;break;}}
  assert.equal(firstDifference,word.length);results.push({word,firstDifference});
 }rows.push({name:row.name,results});
}
const result={node:process.version,cases:rows.length,positiveClassifications:positives,replayedNegativeWitnesses:negatives,apiCalls:calls,
 longChainCases:rows.filter(r=>r.name.startsWith('chain-')).length,rows};
fs.writeFileSync(path.join(dir,'results.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(Object.fromEntries(Object.entries(result).filter(([k])=>k!=='rows'))));
