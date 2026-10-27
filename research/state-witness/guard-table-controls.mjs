import fs from 'node:fs';import path from 'node:path';import assert from 'node:assert/strict';
const dir=process.argv[2],m=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json'))),BASE=2**32;let calls=0;const rows=[];
function seqs(actions,depth){const out=[];let frontier=[[]];for(let n=0;n<depth;n++){frontier=frontier.flatMap(s=>actions.map(a=>[...s,a]));out.push(...frontier);}return out;}
function snapshot(e,row){const out={};const refs=new Map([[null,256]]);for(let i=0;i<row.proof.functions;i++)refs.set(e['__guard_func_'+i],i+257);
 for(const [r,info] of Object.entries(row.proof.resources)){
  const x=e['__guard_resource_'+r];if(info.kind==='memory')out[r]=Buffer.from(x.buffer);else out[r]=Array.from({length:x.length},(_,i)=>{assert(refs.has(x.get(i)));return refs.get(x.get(i));});
 }return out;
}
function same(a,b,resources){return Object.keys(resources).every(r=>resources[r].kind==='memory'?a[r].equals(b[r]):JSON.stringify(a[r])===JSON.stringify(b[r]));}
for(const row of m.rows){const module=new WebAssembly.Module(fs.readFileSync(path.join(dir,row.prepared))),sequences=seqs(row.actions,m.depth),samples=[];
 for(const sample of row.samples){let witness=null;
  for(const seq of sequences){const pair=[row.left,row.right].map(alive=>{
   const e=new WebAssembly.Instance(module).exports;
   for(const [key,value] of sample.patches){const r=Math.floor(key/BASE),i=key%BASE,x=e['__guard_resource_'+r];
    if(row.proof.resources[r].kind==='memory')new Uint8Array(x.buffer)[i]=value;else x.set(i,value===256?null:e['__guard_func_'+(value-257)]);
   }alive.forEach((v,i)=>{if(!v)e['__guard_drop_'+i]();});return e;
  });
   for(let step=0;step<seq.length;step++){
    const outcome=pair.map(e=>{calls++;try{e[seq[step]]();return 'return';}catch(err){if(!(err instanceof WebAssembly.RuntimeError))throw err;return 'trap';}});
    if(outcome[0]!==outcome[1]||!same(snapshot(pair[0],row),snapshot(pair[1],row),row.proof.resources)){witness=seq.slice(0,step+1);break;}
   }if(witness)break;
  }assert.equal(witness===null,sample.satisfies);samples.push({satisfies:sample.satisfies,witness});
 }rows.push({name:row.name,status:row.proof.status,guard:row.proof.guard,samples});
}
const result={node:process.version,rows,apiCalls:calls,samples:rows.reduce((n,r)=>n+r.samples.length,0)};
fs.writeFileSync(path.join(dir,'results.json'),JSON.stringify(result,null,2));console.log(JSON.stringify({cases:rows.length,samples:result.samples,calls}));
