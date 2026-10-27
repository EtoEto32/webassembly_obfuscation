import fs from 'node:fs';import path from 'node:path';import assert from 'node:assert/strict';
const dir=process.argv[2],m=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json')));let apiCalls=0,preparationApiCalls=0,cellWrites=0;const rows=[];
for(const row of m.rows){const mod=new WebAssembly.Module(fs.readFileSync(path.join(dir,row.source))),pair=[new WebAssembly.Instance(mod).exports,new WebAssembly.Instance(mod).exports];
 pair[0].retire_left();pair[1].retire_right();preparationApiCalls+=2;let difference=null;const trace=[];
 for(let i=0;i<row.word.length;i++){const step=row.word[i],outcomes=pair.map(e=>{if(step.kind==='write'){e.public.set(0,null);cellWrites++;return ['write'];}
  apiCalls++;try{return ['return',e[step.name]()??null];}catch(err){if(!(err instanceof WebAssembly.RuntimeError))throw err;return ['trap'];}});
  const publicValues=pair.map(e=>e.public.get(0)?.()??null);trace.push({kind:step.kind,outcomes,public:publicValues});
  if(publicValues[0]!==publicValues[1]||JSON.stringify(outcomes[0])!==JSON.stringify(outcomes[1])){difference=i+1;break;}
  if(row.proof.protocol==='terminal'&&outcomes[0][0]==='trap')break;
 }
 assert.equal(difference,row.difference);assert.deepEqual(trace,row.trace);rows.push({name:row.name,difference,trace});
}
assert.equal(apiCalls,m.apiCalls);assert.equal(preparationApiCalls,m.preparationApiCalls);assert.equal(cellWrites,m.cellWrites);
const result={node:process.version,rows,apiCalls,preparationApiCalls,cellWrites};fs.writeFileSync(path.join(dir,'results.json'),JSON.stringify(result,null,2));console.log(JSON.stringify({contracts:rows.length,apiCalls,preparationApiCalls,cellWrites}));
