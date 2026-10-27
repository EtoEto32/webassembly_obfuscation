'use strict';
const fs=require('node:fs'),path=require('node:path');const h=require('./harness.cjs');
async function main(dir){
 const rows=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json'))),ins=h.inputs(),results=[];
 let total=0,mismatches=0;
 for(const row of rows){
  const src=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(dir,row.source)))).exports.run;
  const expected=ins.map(a=>src(...a));total+=ins.length;
  for(const file of [row.file,...(row.recovered?[row.recovered]:[])]){
   const vm=file===row.file&&row.mode!=='scalar';
   const memory=vm?new WebAssembly.Memory({initial:1,maximum:1,shared:true}):null;
   const inst=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(dir,file))),vm?{env:{memory}}:{});
   let bad=0;for(let i=0;i<ins.length;i++){if(inst.exports.run(...ins[i])!==expected[i])bad++;total++;}
   mismatches+=bad;results.push({file,workers:0,inputs:ins.length,mismatches:bad});
  }
  if(row.mode==='atomic')for(const workers of [1,2,4]){
   const p=await h.pool(path.join(dir,row.file),workers);let bad=0,multi=0,counts={};
   try {for(let i=0;i<ins.length;i++){
    const got=await p.run(ins[i]);if(got!==expected[i])bad++;total++;
    const owners=h.owners(p.heap);if(Object.keys(owners).length>1)multi++;
    for(const [id,n] of Object.entries(owners))counts[id]=(counts[id]||0)+n;
    if(p.heap[16]!==p.heap[3])throw new Error('operation counter mismatch');
   }} finally{await p.close();}
   mismatches+=bad;results.push({file:row.file,workers,inputs:ins.length,mismatches:bad,multi_worker_inputs:multi,owner_counts:counts});
  }
  console.log(row.file);
 }
 fs.writeFileSync(path.join(dir,'correctness.json'),JSON.stringify({seed:20261019,boundary:512,random:256,inputs:ins.length,total_calls:total,mismatches,results},null,2));
 if(mismatches)throw new Error('differential failure');
}
main(process.argv[2]).catch(e=>{console.error(e);process.exitCode=1;});
