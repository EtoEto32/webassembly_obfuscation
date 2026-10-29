const fs=require('fs'),path=require('path');
const dir=process.argv[2],manifest=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json')));
let seed=221030;function rand(){seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed>>>0;}
const mask=0xffffffffn,mod=x=>x&mask;
function rot(x,n){n=BigInt(n&31);return mod((x<<n)|(x>>((32n-n)&31n)));}
function oracle(n,x,y,pars){
  let [c1,c2,r]=pars.map(BigInt),stack=[];n=n&31;x=BigInt(x>>>0);y=BigInt(y>>>0);
  for(let d=n;d>0;--d){stack.push(BigInt(d));[x,y]=[y,mod(x^mod(rot(y,Number(r))+BigInt(d)*c1))];}
  x=mod(x^c1);y=mod(y+c2);
  for(const d of stack.reverse()){x=mod(x+d*c2);y=mod(y^rot(d,5));}
  return BigInt.asIntN(64,x|(y<<32n));
}
const edge=[0,1,2,31,32,255,65535,0x7fffffff,0x80000000,0xffffffff];
const inputs=[];
for(let n=0;n<32;n++)for(const x of edge)for(const y of edge)inputs.push([n,x,y]);
for(const n of edge)for(const x of edge)inputs.push([n,x,0xffffffff-x]);
for(let j=0;j<4096;j++)inputs.push([rand(),rand(),rand()]);
const cases=[...new Map(inputs.map(x=>[x.join(','),x])).values()];
const expected=new Map();for(const fixture of manifest.fixtures)expected.set(fixture.name,cases.map(x=>oracle(...x,fixture.parameters)));
let rows=[];
for(const b of manifest.binaries){
  const bytes=fs.readFileSync(path.join(dir,b.file));if(!WebAssembly.validate(bytes))throw Error('invalid '+b.file);
  const w=new WebAssembly.Instance(new WebAssembly.Module(bytes)).exports;let mismatch=0,traps=0,first=null;
  const ref=expected.get(b.name);
  for(let i=0;i<cases.length;i++){
    try {const got=w.run(...cases[i]);if(got!==ref[i]){mismatch++;first??={input:cases[i],got:String(got),expected:String(ref[i])};}}
    catch(e){traps++;first??={input:cases[i],error:String(e)};}
  }
  rows.push({file:b.file,name:b.name,mode:b.mode,opt:b.opt,negative:b.negative,calls:cases.length,mismatch,unexpectedTraps:traps,first});
}
const result={node:process.version,v8:process.versions.v8,seed:221030,uniqueInputs:cases.length,rows,
 positiveCalls:rows.filter(x=>!x.negative).reduce((n,x)=>n+x.calls,0),
 positiveMismatches:rows.filter(x=>!x.negative).reduce((n,x)=>n+x.mismatch,0),
 unexpectedTraps:rows.reduce((n,x)=>n+x.unexpectedTraps,0),negativeDetected:rows.filter(x=>x.negative&&x.mismatch>0).length};
fs.writeFileSync(path.join(dir,'checks.json'),JSON.stringify(result,null,2));
console.log(JSON.stringify({uniqueInputs:result.uniqueInputs,conditions:rows.length,positiveCalls:result.positiveCalls,mismatch:result.positiveMismatches,traps:result.unexpectedTraps,negativeDetected:result.negativeDetected}));
if(result.positiveMismatches||result.unexpectedTraps||rows.some(x=>x.negative&&x.mismatch===0))process.exitCode=1;
