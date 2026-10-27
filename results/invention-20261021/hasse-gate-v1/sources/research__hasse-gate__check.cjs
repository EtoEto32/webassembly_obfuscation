const fs = require('node:fs');
const path = require('node:path');
const dir = process.argv[2];
const manifest = JSON.parse(fs.readFileSync(path.join(dir,'manifest.json')));
let state=0x621021a7;
function next(){ state^=state<<13; state^=state>>>17; state^=state<<5; return state>>>0; }
const edges=[0,1,2,3,15,16,31,32,0x7fffffff,0x80000000,0x80000001,0xfffffffe,0xffffffff,65535,65536,16777216];
const inputs=[];
for(const x of edges)for(const y of edges)inputs.push([x,y]);
for(let i=0;i<1024;i++)inputs.push([next(),next()]);
function reference(c,x,y){
 const values=c.nodes.map(n=>{
   if(n[0]==='x')return BigInt(n[1]===0?x:y);
   if(n[0]==='c')return BigInt(n[1]);
   return null;
 });
 for(let i=0;i<c.nodes.length;i++)if(values[i]===null){
   const [op,a,b]=c.nodes[i];
   values[i]=BigInt.asUintN(32,op==='add'?values[a]+values[b]:op==='sub'?values[a]-values[b]:values[a]*values[b]);
 }
 return Number(values[c.root]);
}
function instantiate(file){const b=fs.readFileSync(path.join(dir,file));if(!WebAssembly.validate(b))throw Error('invalid '+file);return new WebAssembly.Instance(new WebAssembly.Module(b)).exports.run;}
const rows=[];
for(const target of manifest.targets){
 const c=manifest.cases.find(c=>c.name===target.name);
 for(const file of [target.file,target.recovered].filter(Boolean)){
  const fn=instantiate(file);let mismatches=0;
  for(const [x,y] of inputs)if((fn(x,y)>>>0)!==reference(c,x,y))mismatches++;
  rows.push({file,calls:inputs.length,mismatches});if(mismatches)throw Error(JSON.stringify(rows.at(-1)));
 }
}
const zero=instantiate('control-zero.wasm'), nul=instantiate('control-null-polynomial.wasm'), derivative=instantiate('control-null-derivative.wasm');
let nullEqual=0,derivativeDifferent=0;
for(const [x,y] of inputs){if((zero(x,y)>>>0)===(nul(x,y)>>>0))nullEqual++;if((derivative(x,y)>>>0)===0x80000000)derivativeDifferent++;}
if(nullEqual!==inputs.length||derivativeDifferent!==inputs.length)throw Error('null function counterexample');
const result={node:process.version,v8:process.versions.v8,inputs:inputs.length,seed:'0x621021a7',rows,calls:rows.reduce((a,b)=>a+b.calls,0),
 controls:{calls:inputs.length*3,nullEqual,derivativeDifferent},memory:'no module has linear memory',trap:'supported arithmetic is total; no trap claims'};
fs.writeFileSync(path.join(dir,'checks.json'),JSON.stringify(result,null,2));console.log(JSON.stringify({calls:result.calls,mismatches:0,controls:result.controls}));
