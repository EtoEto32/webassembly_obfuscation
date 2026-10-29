const fs=require('fs'),path=require('path');const dir=process.argv[2];
const rows=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json'))),edge=[0,1,2,3,7,255,65535,0x7fffffff,0x80000000,0xffffffff];
const inputs=[],seen=new Set();function put(a){let k=a.join(',');if(!seen.has(k)){seen.add(k);inputs.push(a);}}
for(const x of edge)for(const y of edge)for(const z of edge)put([x,y,z]);
let seed=221050;function next(){seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed>>>0;}
for(let i=0;i<2048;i++)put([next(),next(),next()]);
function oracle(name,a){let [x,y,z]=a.map(BigInt),q;
 if(name==='arith'){const s=BigInt.asUintN(32,x+y);q=(s^z)*s;}
 else if(name==='blend')q=BigInt.asUintN(32,(x&y)+z)^y;
 else q=BigInt.asUintN(32,x*y+y)|z;
 return Number(BigInt.asUintN(32,q));}
const results=[];
for(const row of rows){let b=fs.readFileSync(path.join(dir,row.file));if(!WebAssembly.validate(b))throw Error('invalid');
 let ex=new WebAssembly.Instance(new WebAssembly.Module(b)).exports;
 let mismatch=0,traps=0,first=null;
 for(const a of inputs){let got;try{got=ex.run(...a)>>>0;}catch(e){traps++;continue;}
 let expected=oracle(row.name,a);if(got!==expected){mismatch++;if(!first)first={a,got,expected};}}
 const item={...row,calls:inputs.length,mismatch,traps,first};results.push(item);
 if(traps||(!row.negative&&mismatch)||(row.negative&&!mismatch))throw Error(JSON.stringify(item));}
const report={seed:221050,inputs:inputs.length,node:process.version,v8:process.versions.v8,positiveConditions:results.filter(x=>!x.negative).length,positiveCalls:results.filter(x=>!x.negative).reduce((s,x)=>s+x.calls,0),negativeConditions:results.filter(x=>x.negative).length,results};
fs.writeFileSync(path.join(dir,'checks.json'),JSON.stringify(report,null,2));fs.writeFileSync(path.join(dir,'inputs.json'),JSON.stringify(inputs));
console.log(JSON.stringify({inputs:inputs.length,positiveConditions:report.positiveConditions,positiveCalls:report.positiveCalls,negativeConditions:report.negativeConditions}));
