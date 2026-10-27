'use strict';const fs=require('fs'),path=require('path'),d=process.argv[2];
const load=n=>JSON.parse(fs.readFileSync(path.join(d,n)));const models=load('models.json');
const get=f=>new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(d,f)))).exports.run;
function ref(rows,x,n){let q=0;for(let i=0;i<(n&31);i++)q=rows[q][(x>>>i)&1];return rows[q][2];}
if(process.argv[3]==='negative'){
 const results=[];for(const row of load('negative-manifest.json')){
  const run=get(row.file);let witness=null;
  for(let n=1;n<5&&!witness;n++)for(let x=0;x<16&&!witness;x++){
   let got;try{got=run(x,n)}catch(e){if(!(e instanceof WebAssembly.RuntimeError))throw e;got='trap';}
   const expected=ref(models[row.kernel],x,n);if(got!==expected)witness={x,n,got,expected};
  }if(!witness)throw Error('negative not detected');results.push({...row,witness});
 }fs.writeFileSync(path.join(d,'negative.json'),JSON.stringify(results,null,2));process.exit(0);
}
const cases=[];for(let n=0;n<=9;n++)for(let x=0;x<2**n;x++)cases.push([x,n]);
for(const x of [0,1,2,0x7fffffff,0x80000000,0xffffffff,0x55555555,0xaaaaaaaa])for(const n of [0,1,2,15,30,31,32,33,0x7fffffff,0xffffffff])cases.push([x,n]);
let seed=20261019;const rnd=()=>{seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed>>>0;};for(let i=0;i<512;i++)cases.push([rnd(),rnd()]);
let calls=0;const results=[];for(const row of load('manifest.json')){
 const original=get(row.source),target=get(row.file),recovered=get(row.recovered);let mismatches=0;
 for(const [x,n] of cases){const expected=ref(models[row.kernel],x,n);for(const f of [original,target,recovered]){calls++;if(f(x,n)!==expected)mismatches++;}}
 results.push({file:row.file,mismatches});if(mismatches)throw Error('mismatch '+row.file);
}
fs.writeFileSync(path.join(d,'inputs.json'),JSON.stringify(cases));fs.writeFileSync(path.join(d,'checks.json'),JSON.stringify({cases:cases.length,wasm_calls:calls,mismatches:0,unexpected_traps:0,rows:results},null,2));
