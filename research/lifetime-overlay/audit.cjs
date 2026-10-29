const fs=require('fs'),path=require('path');const root=process.argv[2];
const targets=JSON.parse(fs.readFileSync(path.join(root,'controls.json')));const rows=[];
const input=[0,1,17,0x7fffffff,0x80000000,0xffffffff];
for(const t of targets.regressions){const a=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(root,t.source)))).exports.run;
const b=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(root,t.recovered)))).exports.run;
let count=0;for(const x of input)for(const y of input){let want;
if(t.name==='tee-order')want=(x+17)>>>0;
if(t.name==='load-before-branch-store')want=(x+((y&1)?7:11))>>>0;
if(t.name==='signed-load')want=x&0x80000000?0xffffffff:0;
if(t.name==='condition-write')want=y?((y+7)>>>0):11;
const av=a(x,y)>>>0,bv=b(x,y)>>>0;if(av!==want||bv!==want)throw Error(JSON.stringify({t,x,y,av,bv,want}));count+=2;}
rows.push({name:t.name,calls:count});}
console.log(JSON.stringify({rows}));
