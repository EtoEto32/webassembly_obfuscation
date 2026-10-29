const fs=require('fs'),path=require('path'),d=process.argv[2],cases=JSON.parse(fs.readFileSync(path.join(d,'cases.json'))),rows=JSON.parse(fs.readFileSync(path.join(d,'manifest.json')));
const rot=(x,n)=>(x<<n)|(x>>>(32-n));
function oracle(x,y,cs){let z=x|0;for(const [a,b,c,e]of cs){z=rot(z,5)^y;z=(z+Math.imul(y,(z&1)?a:c)+((z&1)?b:e))|0;y^=rot(z,13);}return (z^y)|0;}
let seed=231301;function rand(){seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed;}
const edges=[0,1,2,3,0xffffffff,0x80000000,0x7fffffff,0x55555555],inputs=[];
for(const x of edges)for(const y of edges)inputs.push([x,y]);
for(let i=0;i<32;i++)inputs.push([1<<i,~(1<<i)], [~(1<<i),1<<i]);
for(let i=0;i<1024;i++)inputs.push([rand(),rand()]);
const report={positive:[],negative:[],calls:0,mismatches:0,traps:0,inputs_per_condition:inputs.length,node:process.version,v8:process.versions.v8};
for(const row of rows){const bytes=fs.readFileSync(path.join(d,row.file));if(!WebAssembly.validate(bytes))throw Error('invalid '+row.file);const e=new WebAssembly.Instance(new WebAssembly.Module(bytes)).exports;let count=0,witness=null,traps=0;
 for(const [x,y]of inputs){const expected=oracle(x,y,cases[row.name].coefficients);let actual;try{actual=e.run(x,y);}catch(err){traps++;actual=String(err);}if(actual!==expected){count++;witness??={x:x>>>0,y:y>>>0,expected,actual};}}
 const item={file:row.file,calls:inputs.length,mismatches:count,traps,witness};
 if(row.negative){if(!count)throw Error('negative had no witness');report.negative.push(item);}else{if(count)throw Error(JSON.stringify(item));report.positive.push(item);report.calls+=inputs.length;report.mismatches+=count;report.traps+=traps;}}
console.log(JSON.stringify(report));
