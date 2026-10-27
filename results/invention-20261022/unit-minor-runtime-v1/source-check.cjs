const fs=require('fs'),path=require('path');
const dir=process.argv[2], rows=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json')));
const edge=[0,1,2,3,7,255,65535,0x7fffffff,0x80000000,0xffffffff];
const inputs=[],seen=new Set();
function put(a){const k=a.join(',');if(!seen.has(k)){seen.add(k);inputs.push(a);}}
for(const x of edge)for(const y of edge)for(const z of edge)put([x,y,z]);
let seed=221041;function next(){seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed>>>0;}
for(let i=0;i<4096;i++)put([next(),next(),next()]);
function oracle(name,a){const [x,y,z]=a.map(BigInt);let n;
 if(name==='bilinear')n=(x+y)*(z+7n)-x*z;
 else if(name==='horner')n=((3n*x+y)*x+z)*x+17n;
 else if(name==='product')n=(x+y+3n)*(y+z+5n)*(z+x+7n);
 else throw Error(name);
 return Number(BigInt.asUintN(32,n));
}
const results=[];
for(const row of rows){const b=fs.readFileSync(path.join(dir,row.file));
 if(!WebAssembly.validate(b))throw Error('validation '+row.file);
 const ex=new WebAssembly.Instance(new WebAssembly.Module(b)).exports;
 if(Object.keys(ex).join(',')!=='run')throw Error('unexpected export');
 let mismatch=0,traps=0,first=null;
 for(const a of inputs){let got;try{got=ex.run(...a)>>>0;}catch(e){traps++;if(!first)first={a,trap:String(e)};continue;}
 const expected=oracle(row.name,a);if(got!==expected){mismatch++;if(!first)first={a,got,expected};}}
 results.push({...row,calls:inputs.length,mismatch,traps,first});
 if(traps||(!row.negative&&mismatch)||(row.negative&&!mismatch))throw Error(JSON.stringify(results.at(-1)));
}
const report={seed:221041,inputs:inputs.length,node:process.version,v8:process.versions.v8,results,
 positiveCalls:results.filter(x=>!x.negative).reduce((s,x)=>s+x.calls,0),
 positiveConditions:results.filter(x=>!x.negative).length,negativeConditions:results.filter(x=>x.negative).length};
fs.writeFileSync(path.join(dir,'checks.json'),JSON.stringify(report,null,2));
fs.writeFileSync(path.join(dir,'inputs.json'),JSON.stringify(inputs));
console.log(JSON.stringify({positiveCalls:report.positiveCalls,positiveConditions:report.positiveConditions,negativeConditions:report.negativeConditions,inputs:inputs.length}));
