const fs=require('node:fs');
const bytes=fs.readFileSync(process.argv[2]);
if(!WebAssembly.validate(bytes))throw Error('invalid Wasm');
const module_=new WebAssembly.Module(bytes);
const create=()=>new WebAssembly.Instance(module_).exports;
const e=create();
const samples=[];
if(process.argv[3]==='fresh'){
 const zero=create().step(0)>>>0,one=create().step(1)>>>0;
 const delta=(one-zero-1)>>>0;if(delta&1)throw Error('invalid square difference');
 const initialF=delta>>>1;
 for(let s=0;s<=4;s++){
  const a=create(),b=create();a.step((s-initialF)|0);b.step((s-initialF)|0);
  samples.push({s,zero:a.step(0)>>>0,one:b.step(1)>>>0});
 }
 console.log(JSON.stringify({samples,bootstrap:{zero,one,initialF},calls:{reset:0,step:22,total:22,instances:12}}));
}else{
for(let s=0;s<=4;s++){
  e.reset(s);const zero=e.step(0)>>>0;
  e.reset(s);const one=e.step(1)>>>0;
  samples.push({s,zero,one});
}
console.log(JSON.stringify({samples,calls:{reset:10,step:10,total:20}}));
}
