'use strict';
const fs=require('node:fs'),path=require('node:path'),h=require('./harness.cjs');
async function main(main,out){
 const extra=JSON.parse(fs.readFileSync(path.join(out,'extra.json')));let rows=[],calls=0;
 const base=h.inputs();
 for(const row of extra){
  const src=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(out,row.source)))).exports.run;
  const recovered=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(out,row.recovered)))).exports.run;
  const p=await h.pool(path.join(out,row.target),4);let bad=0;
  const inputs=base.map((x,i)=>row.arity===3?x:Array.from({length:16},(_,j)=>Math.imul(x[j%3]^j,17+j)|0));
  try {for(let i=0;i<inputs.length;i++){
   const a=inputs[i],want=src(...a),serial=p.instance.exports.run(...a),rec=recovered(...a);calls+=3;
   if(want!==serial||rec!==want)bad++;
   if(i%16===0){const got=await p.run(a);calls++;if(got!==want)bad++;}
  }}finally{await p.close();}
  rows.push({target:row.target,inputs:inputs.length,parallel_inputs:inputs.filter((_,i)=>i%16===0).length,mismatches:bad});
 }
 const negSrc=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(out,'negative-source.wasm')))).exports.run;
 const memory=new WebAssembly.Memory({initial:1,maximum:1,shared:true}),heap=new Int32Array(memory.buffer);
 const wrong=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(out,'negative-no-dependency.wasm'))),{env:{memory}}).exports;
 let differences=0,counterexample=null;
 for(const a of base){wrong.init(...a);wrong.attempt(heap[2],0);wrong.work(0);const got=wrong.result(),want=negSrc(...a);if(got!==want){differences++;counterexample??={input:a,expected:want,actual:got};}}
 const manifest=JSON.parse(fs.readFileSync(path.join(main,'manifest.json'))),expected=[];
 for(const row of manifest)for(const file of [row.file,...(row.recovered?[row.recovered]:[])]){
  const vm=file===row.file&&row.mode!=='scalar';const input=[[0,0,0],[1,-1,32],[-2147483648,0x7fffffff,31],[0x55555555,-1,-2147483648]];
  const src=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(main,row.source)))).exports.run;
  expected.push({path:path.resolve(main,file),inputs:input.map(a=>vm?[...a,...Array(13).fill(0)]:a),expected:input.map(a=>src(...a))});
 }
 fs.writeFileSync(path.join(out,'native.json'),JSON.stringify({rows,total_calls:calls,mismatches:rows.reduce((a,x)=>a+x.mismatches,0),negative:{inputs:base.length,differences,counterexample}},null,2));
 fs.writeFileSync(path.join(out,'wabt-expected.json'),JSON.stringify(expected,null,2));
 if(rows.some(x=>x.mismatches)||!differences)throw new Error('verification failed');
}
main(process.argv[2],process.argv[3]).catch(e=>{console.error(e);process.exitCode=1});
