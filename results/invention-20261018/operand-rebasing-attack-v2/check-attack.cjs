'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const binaries=path.resolve(process.argv[2]),results=path.resolve(process.argv[3]);
const data=JSON.parse(fs.readFileSync(path.join(results,'attack.json')));let cases=0;
for(const t of data.targets){
 const bytes=fs.readFileSync(path.join(binaries,t.file));
 if(crypto.createHash('sha256').update(bytes).digest('hex')!==t.sha256)throw Error('hash');
 const fn=new WebAssembly.Instance(new WebAssembly.Module(bytes)).exports.run;
 data.inputs.forEach((args,i)=>{if((fn(...args)>>>0)!==t.oracleOutputs[i])throw Error('extracted table does not match Wasm');cases++;});
}
fs.writeFileSync(path.join(results,'oracle-validation.json'),JSON.stringify({cases,mismatches:0,node:process.version},null,2),{flag:'wx'});
fs.copyFileSync(__filename,path.join(results,'check-attack.cjs'));console.log({cases,mismatches:0});
