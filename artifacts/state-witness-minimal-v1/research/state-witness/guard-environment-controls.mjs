import fs from 'node:fs';import path from 'node:path';import assert from 'node:assert/strict';
const dir=process.argv[2],manifest=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json'))),expected=JSON.parse(fs.readFileSync(path.join(dir,'wasmtime.json')));
const foreign=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(dir,'foreign.wasm')))).exports.foreign;
let apiCalls=0,preparationApiCalls=0,cellWrites=0,pureReferenceTagCalls=0;const rows=[];
for(const row of manifest.rows){
 if(row.execution!=='run'){rows.push({name:row.name,status:row.execution});continue;}
 const mod=new WebAssembly.Module(fs.readFileSync(path.join(dir,row.source))),traces=[];
 for(const word of row.words){
  const pair=[new WebAssembly.Instance(mod).exports,new WebAssembly.Instance(mod).exports];pair[0].retire();pair[1].release_b();preparationApiCalls+=2;
  const trace=[];let difference=null;
  for(let index=0;index<word.length;index++){
   const step=word[index];let outcomes=[];
   if(step.kind==='write'){
    for(const [cell,value] of step.cells)for(const ex of pair){if(row.kind==='memory')new Uint8Array(ex.resource.buffer)[cell]=value;else ex.resource.set(cell%2**32,value===256?null:foreign);cellWrites++;}
    outcomes=[['write'],['write']];
   }else for(const ex of pair){try{outcomes.push(['return',ex[step.name](...step.args)??null]);}catch(err){if(!(err instanceof WebAssembly.RuntimeError))throw err;outcomes.push(['trap']);}apiCalls++;}
   const snapshots=[];
   if(row.proof.contract!=='returns'&&row.mode!=='private')for(const ex of pair){
    if(row.kind==='memory')snapshots.push(Buffer.from(ex.resource.buffer).toString('hex'));
    else {const ref=ex.resource.get(0);snapshots.push(ref===null?null:ref());if(ref!==null)pureReferenceTagCalls++;}
   }
   const storeEqual=!snapshots.length||snapshots[0]===snapshots[1];
   trace.push({kind:step.kind,outcomes,storeEqual,first:!snapshots.length?[]:row.kind==='memory'?snapshots.map(x=>parseInt(x.slice(0,2),16)):snapshots});
   if(JSON.stringify(outcomes[0])!==JSON.stringify(outcomes[1])||!storeEqual){difference=index+1;break;}
   if(row.proof.protocol==='terminal'&&outcomes[0][0]==='trap')break;
  }
  assert.equal(difference,row.witness?word.length:null,row.name);traces.push({difference,trace});
 }
 rows.push({name:row.name,status:'matched',traces});
}
const result={rows,apiCalls,preparationApiCalls,pureReferenceTagCalls,cellWrites};assert.deepEqual(result,expected);
fs.writeFileSync(path.join(dir,'results.json'),JSON.stringify({...result,node:process.version},null,2));
console.log(JSON.stringify({contracts:rows.length,executed:rows.filter(x=>x.status==='matched').length,apiCalls,preparationApiCalls,cellWrites,pureReferenceTagCalls}));
