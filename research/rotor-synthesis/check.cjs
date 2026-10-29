const fs=require('node:fs'),path=require('node:path');
const base=process.argv[2], manifest=JSON.parse(fs.readFileSync(path.join(base,'manifest.json')));
const masks=[0,1,2,0x7fffffff,0x80000000,0xffffffff,0xaaaaaaaa,0x55555555,0x01010101];
const inputs=[];for(const a of masks)for(const b of masks)for(const c of masks)inputs.push([a,b,c]);
for(let v=0;v<8;v++)inputs.push([v&1?-1:0,v&2?-1:0,v&4?-1:0]);
let seed=20261023;const rand=()=>seed=(Math.imul(seed,1664525)+1013904223)|0;
for(let i=0;i<4096;i++)inputs.push([rand(),rand(),rand()]);
const oracle={and3:(a,b,c)=>a&b&c,majority3:(a,b,c)=>(a&b)|(a&c)|(b&c),mux3:(a,b,c)=>(a&b)|(~a&c)};
let calls=0,mismatches=0;const cases=[];
for(const t of manifest){
 const bytes=fs.readFileSync(path.join(base,t.file));if(!WebAssembly.validate(bytes))throw Error('invalid '+t.file);
 const e=new WebAssembly.Instance(new WebAssembly.Module(bytes)).exports;let errors=0;
 for(const args of inputs){if((e.run(...args)|0)!==(oracle[t.name](...args)|0))errors++;calls++;}
 cases.push({file:t.file,calls:inputs.length,mismatches:errors});mismatches+=errors;
}
const result={binaries:manifest.length,inputs_per_binary:inputs.length,calls,mismatches,cases};
fs.writeFileSync(path.join(base,'correctness.json'),JSON.stringify(result,null,2));
if(mismatches)throw Error(JSON.stringify(result));console.log(JSON.stringify({binaries:manifest.length,inputs_per_binary:inputs.length,calls,mismatches}));
