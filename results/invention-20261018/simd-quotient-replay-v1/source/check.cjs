const fs=require('fs'),path=require('path');const dir=process.argv[2],m=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json')));
let seed=0x20261018;function rnd(){seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed>>>0;}
const inputs=[];for(let x=0;x<256;x++)for(let y=0;y<256;y++)inputs.push([...Array(4).fill(Math.imul(x,0x01010101)),...Array(4).fill(Math.imul(y,0x01010101))]);
for(let i=0;i<2048;i++)inputs.push(Array.from({length:8},rnd));
function ref(kind,args){let mask=0;for(let i=0;i<16;i++){const x=(args[i>>2]>>((i&3)*8))&255,y=(args[4+(i>>2)]>>((i&3)*8))&255;let b;
 if(kind==='range')b=(x>23&&x<201&&!(y<7))||x===y;
 if(kind==='pair')b=(x>y)!==(x>=71&&y<=99);
 if(kind==='filter')b=(x<64&&y>200)||(x!==17&&(y>x||y===127));
 if(b)mask|=1<<i;}return mask;}
const expected={};for(const k of ['range','pair','filter'])expected[k]=inputs.map(a=>ref(k,a));
const details=[];let calls=0,errors=0;
for(const a of m.attacks){for(const file of [a.path,...(a.status==='ok'?[a.recovered]:[])]){const bytes=fs.readFileSync(file);if(!WebAssembly.validate(bytes))throw Error('validation');const fn=new WebAssembly.Instance(new WebAssembly.Module(bytes)).exports.run;let mismatches=0;
 for(let i=0;i<inputs.length;i++){const z=inputs[i];const actual=fn(z[0],z[1],z[2],z[3],z[4],z[5],z[6],z[7]);calls++;if(actual!==expected[a.kernel][i])mismatches++;}
 details.push({file,inputs:inputs.length,mismatches});errors+=mismatches;}}
fs.writeFileSync(path.join(dir,'correctness.json'),JSON.stringify({calls,mismatches:errors,conditions:details.length,inputs:inputs.length,details},null,2));
fs.writeFileSync(path.join(dir,'random-inputs.json'),JSON.stringify(inputs.slice(65536)));
fs.writeFileSync(path.join(dir,'interpreter-inputs.json'),JSON.stringify([0,255,65280,32712].map(i=>inputs[i]).map(a=>({args:a,expected:Object.fromEntries(['range','pair','filter'].map(k=>[k,ref(k,a)]))})),null,2));
console.log(JSON.stringify({calls,mismatches:errors,conditions:details.length}));if(errors)process.exitCode=1;
