const fs=require('node:fs');
const bytes=fs.readFileSync(process.argv[2]);
if(!WebAssembly.validate(bytes))throw Error('invalid Wasm');
const e=new WebAssembly.Instance(new WebAssembly.Module(bytes)).exports;
const samples=[];
for(let s=0;s<=4;s++){
  e.reset(s);const zero=e.step(0)>>>0;
  e.reset(s);const one=e.step(1)>>>0;
  samples.push({s,zero,one});
}
console.log(JSON.stringify({samples,calls:{reset:10,step:10,total:20}}));
