const fs=require('node:fs'),path=require('node:path');const dir=process.argv[2];
const rows=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json'))),cases=JSON.parse(fs.readFileSync(path.join(dir,'cases.json')));
function model(t,x){return t[0]==='bit'?((x>>>t[1])&1)^t[2]:t[0]==='and'?model(t[1],x)&model(t[2],x):model(t[1],x)|model(t[2],x);}
let seed=0x12362139;function rand(){seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed>>>0;}
const specs={};for(const [name,c] of Object.entries(cases)){const xs=Array.from({length:1<<c.bits},(_,i)=>i);xs.push(0xffffffff,0x80000000,0x7fffffff,0);for(let i=0;i<512;i++)xs.push(rand());specs[name]=xs;}
const report={positive:[],negative:[],calls:0,traps:0,mismatches:0,node:process.version,v8:process.versions.v8};
for(const row of rows){
 const bytes=fs.readFileSync(path.join(dir,row.file));if(!WebAssembly.validate(bytes))throw Error('validation');
 const e=new WebAssembly.Instance(new WebAssembly.Module(bytes)).exports;
 let errors=0,traps=0,witness=null;
 for(const x of specs[row.name]){const expected=model(cases[row.name].tree,x);let actual,trap=null;try{actual=e.run(x);}catch(err){if(!(err instanceof WebAssembly.RuntimeError))throw err;trap=String(err);traps++;}
  if(trap||actual!==expected){errors++;witness??={x,expected,actual,trap};}}
 const item={file:row.file,calls:specs[row.name].length,mismatches:errors,traps,witness};
 if(row.negative){if(!errors)throw Error('negative without witness '+row.file);report.negative.push(item);}
 else {if(errors)throw Error(JSON.stringify(item));report.positive.push(item);report.calls+=item.calls;report.mismatches+=errors;report.traps+=traps;}
}
console.log(JSON.stringify(report));
