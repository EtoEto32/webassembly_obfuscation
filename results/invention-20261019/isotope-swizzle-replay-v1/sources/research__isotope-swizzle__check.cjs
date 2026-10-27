'use strict';const fs=require('fs'),path=require('path'),d=process.argv[2];
const load=n=>JSON.parse(fs.readFileSync(path.join(d,n)));const models=load('models.json');
const get=f=>new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(d,f)))).exports.run;
function byte(t,x){if(Number.isInteger(t))return x[t]&15;const a=byte(t[1],x),b=byte(t[2],x);return (t[0]==='add'?a+b:t[0]==='sub'?a-b:a^b)&15;}
function reference(t,args){let r=0;for(let k=0;k<4;k++)r|=byte(t,args.map(x=>(x>>>(8*k))&255))<<(8*k);return r|0;}
const spread=x=>((x)|(((x*3+1)&15)<<8)|(((x*5+7)&15)<<16)|(((x*7+11)&15)<<24))|0;
const cases=[];for(let x=0;x<16;x++)for(let y=0;y<16;y++)for(let z=0;z<16;z++)cases.push([spread(x),spread(y),spread(z)]);
const edges=[0,1,15,16,127,128,255,0x0f0f0f0f,0xf0f0f0f0,0xffffffff,0x7fffffff,0x80000000];
for(const x of edges)for(const y of edges)for(const z of edges)cases.push([x,y,z]);
let seed=20261019;const rnd=()=>{seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed|0;};for(let i=0;i<2048;i++)cases.push([rnd(),rnd(),rnd()]);
let calls=0;const records=[];
for(const row of load('manifest.json')){
 const fns=[get(row.source),get(row.file),get(row.recovered)];let mismatches=0;
 for(const args of cases){const expected=reference(models[row.kernel],args);for(const f of fns){calls++;if(f(...args)!==expected)mismatches++;}}
 records.push({file:row.file,mismatches});if(mismatches)throw Error('mismatch '+row.file);
}
fs.writeFileSync(path.join(d,'inputs.json'),JSON.stringify(cases));fs.writeFileSync(path.join(d,'checks.json'),JSON.stringify({cases:cases.length,wasm_calls:calls,mismatches:0,unexpected_traps:0,records},null,2));
