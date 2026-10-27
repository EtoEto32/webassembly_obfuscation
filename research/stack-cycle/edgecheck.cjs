'use strict';
const fs=require('fs'),path=require('path'),root=path.resolve(process.argv[2]);
const rows=JSON.parse(fs.readFileSync(path.join(root,'edge-manifest.json'),'utf8'));
let seed=13171;function rnd(){seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed>>>0;}
const xs=[0,1,-1,-2147483648,2147483647,0x7f800000,0xff800000|0,0x7fc01234,0x7f801234];
const longs=[0n,1n,-1n,0x7ff0000000000000n,0x7ff8123456789abcn,0x7ff0000000000001n,-0x8000000000000000n,0x7fffffffffffffffn];
for(let i=0;i<1024;i++){xs.push(rnd()|0);longs.push(BigInt.asIntN(64,(BigInt(rnd())<<32n)|BigInt(rnd())));}
function oracle(name,a){
  if(name==='f32bits')return a[0]^(-2147483648);
  if(name==='f64bits')return BigInt.asIntN(64,a[0]^0x8000000000000000n);
  if(name==='i64'){let x=BigInt.asUintN(64,a[0]);for(let i=0;i<17;i++){x=BigInt.asUintN(64,x*3n);x=BigInt.asUintN(64,(x<<7n)|(x>>57n));}return BigInt.asIntN(64,x);}
  if(name==='multiresult'){let x=a[1];for(let i=0;i<17;i++)x=BigInt.asIntN(64,3n*x+7n);return [a[0],x];}
  let x=a[0];for(let i=0;i<17;i++)x=((a[2]?x:a[1])+7)|0;return x;
}
const report=[];let total=0,bad=0;
for(const row of rows){
  const inst=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(root,row.file))));
  let errors=0;
  for(let i=0;i<xs.length;i++){
    const args=row.name==='f32bits'?[xs[i]]:['i64','f64bits'].includes(row.name)?[longs[i%longs.length]]:row.name==='multiresult'?[xs[i],longs[i%longs.length]]:[xs[i],xs[(i+1)%xs.length],i%3-1];
    const expected=oracle(row.name,args),actual=inst.exports.run(...args);total++;
    const ok=Array.isArray(expected)?expected.every((x,j)=>x===actual[j]):expected===actual;
    if(!ok)errors++;
  }
  bad+=errors;report.push({...row,calls:xs.length,mismatches:errors});
}
fs.writeFileSync(path.join(root,'edge-correctness.json'),JSON.stringify({conditions:rows.length,calls:total,mismatches:bad,rows:report},null,2));
console.log(JSON.stringify({conditions:rows.length,calls:total,mismatches:bad}));if(bad)process.exitCode=1;
