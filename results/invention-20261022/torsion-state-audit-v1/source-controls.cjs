const fs=require('fs'),path=require('path');const root=process.argv[2],m=JSON.parse(fs.readFileSync(path.join(root,'controls.json')));
function instance(file){return new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(root,file)))).exports;}
const rows=[];
for(const row of m.outside){const a=instance(row.file),b=instance(row.recovered);a.reset();b.reset();const prefix=[];
for(let i=0;i<16;i++){const u=i?0:1,av=a.step(u)>>>0,bv=b.step(u)>>>0;if(av!==bv)throw Error('prefix mismatch');prefix.push(av);}
let witness;if(row.name==='input-exception'){a.reset();b.reset();witness={input:0xdeadbeef,source:a.step(0xdeadbeef)>>>0,recovered:b.step(0xdeadbeef)>>>0};}
else witness={input:0,source:a.step(0)>>>0,recovered:b.step(0)>>>0,step:17};
if(witness.source===witness.recovered)throw Error('expected witness');rows.push({name:row.name,prefix,witness});}
const a=instance(m.delay.file),b=instance(m.delay.recovered);a.reset();b.reset();let s=1,calls=0;
for(let i=0;i<2048;i++){s=(Math.imul(s,1664525)+1013904223)>>>0;if((a.step(s)>>>0)!==(b.step(s)>>>0))throw Error('delay corrected bound');calls+=2;}
console.log(JSON.stringify({outside:rows,corrected_delay_calls:calls}));
