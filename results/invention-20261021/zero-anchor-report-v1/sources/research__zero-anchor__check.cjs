'use strict';
const fs=require('fs'),path=require('path'),d=process.argv[2];
const load=n=>JSON.parse(fs.readFileSync(path.join(d,n)));const models=load('models.json');
const cases=[];const spread=x=>(x|((x^85)<<8)|((x^170)<<16)|((x^255)<<24))|0;
// Exhaust the two byte arguments; z is a distinct deterministic lane pattern.
for(let a=0;a<256;a++)for(let b=0;b<256;b++)cases.push([spread(a),spread(b),spread((a*73+b*19)&255)]);
const edge=[0,1,15,16,127,128,255,-1,0x7fffffff,0x80000000,0x0f0f0f0f,0xf0f0f0f0];
for(const a of edge)for(const b of edge)for(const c of edge)cases.push([a,b,c]);
let seed=20261021;const rnd=()=>{seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed|0;};
for(let i=0;i<4096;i++)cases.push([rnd(),rnd(),rnd()]);
function oracle(steps,args){let v=0;for(let k=0;k<4;k++){let x=(args[0]>>>(8*k))&15;for(const [op,param,shift] of steps){const b=(args[param]>>>(8*k+shift))&1;x=(op==='add'?x+b:op==='sub'?x-b:x^b)&15;}v|=x<<(8*k);}return v|0;}
const expected={};for(const [name,steps] of Object.entries(models))expected[name]=cases.map(x=>oracle(steps,x));
let calls=0;const records=[];
for(const row of load('manifest.json')){
  const f=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(d,row.file)))).exports.run;
  let mismatches=0;for(let i=0;i<cases.length;i++){calls++;if(f(...cases[i])!==expected[row.kernel][i])mismatches++;}
  records.push({file:row.file,calls:cases.length,mismatches});if(mismatches)throw Error('mismatch '+row.file);
}
fs.writeFileSync(path.join(d,'inputs.json'),JSON.stringify(cases));
fs.writeFileSync(path.join(d,'checks.json'),JSON.stringify({cases:cases.length,wasm_calls:calls,mismatches:0,unexpected_traps:0,records},null,2));
