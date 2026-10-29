'use strict';
const fs=require('node:fs'),assert=require('node:assert/strict');
const targets=JSON.parse(fs.readFileSync(process.argv[2]));if(fs.existsSync(process.argv[3]))throw Error('Refuse overwrite');
let seed=211061;const random=()=>seed=(Math.imul(seed,1664525)+1013904223)>>>0;
const cases=[[0,0,0,0],[1,0,1,0],[0x80000000,0,1,0],[0xffffffff,0,1,0],[0xffffffff,1,0,1],[0,1,0,0xffffffff]];
for(let i=0;i<128;i++)cases.push(Array.from({length:4},random));
const ref=x=>Math.imul((x[0]+x[1])|0,(x[2]-x[3])|0)>>>0;
function load(f){const b=fs.readFileSync(f);assert(WebAssembly.validate(b));return new WebAssembly.Instance(new WebAssembly.Module(b)).exports;}
const rows=[];
for(const t of targets){
 const e=load(t.path);assert.deepEqual(Object.keys(e),['run']);let matches=0,mismatches=0;
 for(const x of cases){if((e.run(...x)>>>0)===ref(x))matches++;else mismatches++;}
 if(t.length%2)assert.equal(mismatches,0);else assert(mismatches>0);
 let recovered=0;if(t.recovered){const r=load(t.recovered);for(const x of cases)assert.equal(r.run(...x)>>>0,ref(x));recovered=cases.length;}
 let trace=0,alias=null;if(t.probe){const p=load(t.probe);for(const x of cases)assert.equal(p.trace(...x)>>>0,Math.imul(t.length,ref(x))>>>0);trace=cases.length;
  if(t.length%2===0){const a=[0,0,1,0],b=[0x80000000,0,1,0];assert.notEqual(ref(a),ref(b));assert.equal(p.trace(...a),p.trace(...b));alias={inputs:[a,b],outputs:[ref(a),ref(b)],trace:p.trace(...a)>>>0};}
 }
 rows.push({length:t.length,opt:t.opt,cases:cases.length,matches,mismatches,recovered,trace,alias});
}
const r={node:process.version,v8:process.versions.v8,seed:211061,inputs:cases,rows,odd_correct:rows.filter(x=>x.length%2).reduce((s,x)=>s+x.matches,0),recovered_correct:rows.reduce((s,x)=>s+x.recovered,0),trace_checks:rows.reduce((s,x)=>s+x.trace,0),even_negative_conditions:rows.filter(x=>x.length%2===0&&x.mismatches>0).length};
fs.writeFileSync(process.argv[3],JSON.stringify(r,null,2));console.log(JSON.stringify({odd_correct:r.odd_correct,recovered_correct:r.recovered_correct,trace_checks:r.trace_checks,even_negative_conditions:r.even_negative_conditions}));
