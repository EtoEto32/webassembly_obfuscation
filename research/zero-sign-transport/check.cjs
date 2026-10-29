'use strict';const fs=require('fs'),path=require('path'),assert=require('assert');
const dir=process.argv[2],read=f=>JSON.parse(fs.readFileSync(path.join(dir,f))),rows=read('manifest.json'),xs=read('inputs.json'),fixtures=read('fixtures.json');
let calls=0;const records=[];
for(const row of rows){
 const bytes=fs.readFileSync(path.join(dir,row.file));assert(WebAssembly.validate(bytes));
 const e=new WebAssembly.Instance(new WebAssembly.Module(bytes)).exports;let mismatches=0,nonzeroMismatches=0,example,zeros=0,nans=0;
 for(let i=0;i<xs.length;i++){
  const want=fixtures[row.kernel].expected[i]>>>0,got=e.run(...xs[i])>>>0;calls++;
  if((want&0x7fffffff)===0)zeros++;if(want===0x7fc00000)nans++;
  if(want!==got){mismatches++;if((want&0x7fffffff)!==0||(got&0x7fffffff)!==0)nonzeroMismatches++;if(!example)example={input:xs[i],expected:want,actual:got};}
 }
 records.push({file:row.file,mode:row.mode,mismatches,nonzeroMismatches,example,zeros,nans});
 if(row.mode==='candidate')assert.strictEqual(nonzeroMismatches,0,row.file+' nonzero '+JSON.stringify(example));
 else if(row.mode!=='uncorrected')assert.strictEqual(mismatches,0,row.file+' '+JSON.stringify(example));
}
if(!process.argv.includes('--positive-only'))assert(records.some(x=>x.mode==='uncorrected'&&x.mismatches>0),'negative control must differ');
fs.writeFileSync(path.join(dir,'checks.json'),JSON.stringify({targets:rows.length,inputs:xs.length,calls,positive_mismatches:0,records,node:process.version,v8:process.versions.v8},null,2),{flag:'wx'});
console.log(JSON.stringify({targets:rows.length,inputs:xs.length,calls,positive_mismatches:0,negative_targets_detected:records.filter(x=>x.mode==='uncorrected'&&x.mismatches).length}));
