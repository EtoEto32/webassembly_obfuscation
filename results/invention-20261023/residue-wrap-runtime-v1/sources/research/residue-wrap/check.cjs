const fs=require('node:fs'),path=require('node:path');
const dir=process.argv[2],cases=JSON.parse(fs.readFileSync(path.join(dir,'cases.json'))),manifest=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json')));
const mask=0xffffffffn;
function model(t,args){if(t[0]==='p')return BigInt(args[t[1]]);if(t[0]==='c')return BigInt(t[1]);const a=model(t[1],args),b=model(t[2],args);return ({add:()=>a+b,sub:()=>a-b,mul:()=>a*b}[t[0]]())&mask;}
let seed=0x53251409;function rand(){seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed>>>0;}
const special=[0,1,2,65535,65536,65537,65539,0x7fffffff,0x80000000,0xfffffffe,0xffffffff];
const inputs=special.flatMap(a=>special.map(b=>[a,b]));for(let i=0;i<4096;i++)inputs.push([rand(),rand()]);
const result={calls:0,traps:0,mismatches:0,rows:[],negative:[],node:process.version,v8:process.versions.v8};
for(const row of manifest){
  const e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(dir,row.file)))).exports;
  let errors=0,traps=0,witness=null;
  for(const args of inputs){const expected=Number(model(cases[row.name],args))>>>0;let actual,trap=false;
    try{actual=e.run(...args)>>>0;}catch(err){if(!(err instanceof WebAssembly.RuntimeError))throw err;trap=true;traps++;}
    if(trap||actual!==expected){errors++;if(!witness)witness={args,expected,actual,trap};}
  }
  const item={file:row.file,calls:inputs.length,traps,mismatches:errors};
  if(row.negative){if(!errors)throw Error('negative without counterexample');result.negative.push({...item,witness});}
  else{if(errors)throw Error(JSON.stringify({row,witness}));result.calls+=inputs.length;result.traps+=traps;result.mismatches+=errors;result.rows.push(item);}
}
console.log(JSON.stringify(result));
