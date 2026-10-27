'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert');
const folder=process.argv[2],read=n=>JSON.parse(fs.readFileSync(path.join(folder,n))),rows=read('manifest.json'),inputs=read('inputs.json'),fixtures=read('fixtures.json');
const mask=0xffffffffn,records=[];
for(const row of rows){
 const bytes=fs.readFileSync(path.join(folder,row.file));assert(WebAssembly.validate(bytes));const e=new WebAssembly.Instance(new WebAssembly.Module(bytes)).exports;
 let wrong=0,traps=0,example;
 for(const x of inputs){
  let y=BigInt(x);for(const [a,b] of fixtures[row.kernel])y=(y*BigInt(a)+BigInt(b))&mask;const want=Number(y);
  try{const got=e.run(x)>>>0;if(got!==want){wrong++;if(!example)example={input:x,expected:want,actual:got};}}
  catch(err){if(!(err instanceof WebAssembly.RuntimeError))throw err;traps++;if(!example)example={input:x,expected:want,trap:String(err)};}
 }
 if(row.mode!=='decoder')assert.strictEqual(wrong+traps,0,row.file+' '+JSON.stringify(example));
 records.push({file:row.file,kernel:row.kernel,mode:row.mode,inputs:inputs.length,wrong_results:wrong,watchdog_traps:traps,example});
}
assert(records.filter(x=>x.mode==='decoder').every(x=>x.wrong_results+x.watchdog_traps>0));
const r={targets:rows.length,inputs:inputs.length,calls:rows.length*inputs.length,positive_targets:records.filter(x=>x.mode!=='decoder').length,records,node:process.version,v8:process.versions.v8};
fs.writeFileSync(path.join(folder,'checks.json'),JSON.stringify(r,null,2),{flag:'wx'});console.log(JSON.stringify({targets:r.targets,calls:r.calls,positive_targets:r.positive_targets}));
