const fs=require('fs'),path=require('path');
const root=process.argv[2],manifest=JSON.parse(fs.readFileSync(path.join(root,'manifest.json')));
const M=(1n<<64n)-1n,lo=x=>Number(x&0xffffffffn)>>>0;
const pair=(a,b)=>BigInt(a>>>0)|(BigInt(b>>>0)<<32n);
const fold=x=>(lo(x)^lo(x>>32n))>>>0;
const rol=(x,k)=>((x<<k)|(x>>>(32-k)))>>>0;
const rol64=(x,k)=>((x<<BigInt(k))|(x>>BigInt(64-k)))&M;
function oracle(name,x,y){
  if(name==='serial'){let a=(x^y)>>>0;for(let k=0;k<6;k++)a=rol(((a+17+2*k)^Math.imul(a,3+2*k)^y)>>>0,k+1);return a;}
  if(name==='branch'){let a=((x+y)^x^y)>>>0;if(y&2)a=Math.imul(a,1664525)>>>0;else a=fold((pair(a,x)*4294967311n)&M);return fold(rol64(pair(a,y),13));}
  if(name==='diamond'){let v=pair(x,y);for(let k=0;k<16;k++)if(x&(1<<k)){const a=(fold(v)+k*31+7)>>>0;v=rol64(v,k+1)^BigInt(a);}else v=((v+4294967311n+BigInt(k))*BigInt(3+2*k))&M;return fold(v);}
  throw Error(name);
}
const edges=[0,1,2,3,7,15,31,32,255,256,65535,65536,0x7fffffff,0x80000000,0xfffffffe,0xffffffff];
const inputs=edges.flatMap(x=>edges.map(y=>[x,y]));let s=20261022;
for(let i=0;i<4096;i++){s=(Math.imul(s,1664525)+1013904223)>>>0;const x=s;s=(Math.imul(s,1664525)+1013904223)>>>0;inputs.push([x,s]);}
// All low-16 branch patterns, one fixed companion, used only by diamond.
const result=[];
for(const row of manifest.targets){const bytes=fs.readFileSync(path.join(root,row.file));
  if(!WebAssembly.validate(bytes))throw Error('invalid '+row.file);
  const run=new WebAssembly.Instance(new WebAssembly.Module(bytes)).exports.run;
  const corpus=row.name==='diamond'?inputs.concat(Array.from({length:65536},(_,x)=>[x,0x9e3779b9])):inputs;
  let calls=0,traps=0,bad=null;
  for(const [x,y]of corpus){let got;try{got=run(x,y)>>>0;}catch(e){traps++;bad={x,y,error:String(e)};break;}
    const want=oracle(row.name,x,y);calls++;if(got!==want){bad={x,y,got,want};break;}}
  if(row.negative?!bad:bad)throw Error(JSON.stringify({file:row.file,unexpected:bad}));
  result.push({file:row.file,negative:!!row.negative,calls,traps,counterexample:bad});
}
console.log(JSON.stringify({node:process.version,v8:process.versions.v8,base_inputs:inputs.length,diamond_exhaustive_low16:65536,results:result}));
