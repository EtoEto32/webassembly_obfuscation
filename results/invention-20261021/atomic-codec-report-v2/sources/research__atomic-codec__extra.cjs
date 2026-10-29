'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const out=path.resolve(process.argv[2]),dest=path.join(out,'checks.json');if(fs.existsSync(dest))throw Error('refuse overwrite');
const rows=JSON.parse(fs.readFileSync(path.join(out,'manifest.json'))),source=new WebAssembly.Module(fs.readFileSync(path.join(out,'source.wasm'))),results=[];
const edges=[0,1,3,4,8,65532,65533,65536,0x80000000,0xffffffff],vals=[0,1,0x7fffffff,0x80000000,0xffffffff];
for(const r of rows){
 const m1=new WebAssembly.Memory({initial:1,maximum:1,shared:true}),m2=new WebAssembly.Memory({initial:1,maximum:1,shared:true}),a=new Uint32Array(m1.buffer),b=new Uint32Array(m2.buffer);b.fill(r.b);
 const x=new WebAssembly.Instance(source,{env:{memory:m1}}).exports,y=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(out,r.file))),{env:{memory:m2}}).exports;
 const encode=v=>Number((BigInt(v)*BigInt(r.a)+BigInt(r.b))&0xffffffffn);let calls=0,traps=0;
 function call(api,name,args){try{return{value:api[name](...args)>>>0,trap:false};}catch(e){assert(e instanceof WebAssembly.RuntimeError);return{trap:true};}}
 for(const name of Object.keys(x))for(const p of edges)for(const v of vals){
  const args=[p,v,(~v)>>>0],rx=call(x,name,args),ry=call(y,name,args);assert.deepEqual(rx,ry);calls+=2;if(rx.trap)traps+=2;
  for(let i=0;i<a.length;i++){const want=a[i]===0?r.b:encode(a[i]);if(b[i]!==want)assert.equal(b[i],want,JSON.stringify({file:r.file,name,args,index:i}));}
 }
 results.push({file:r.file,calls,traps,match:true});
}
fs.writeFileSync(dest,JSON.stringify(results,null,2));console.log(JSON.stringify({conditions:results.length,calls:results.reduce((s,x)=>s+x.calls,0),traps:results.reduce((s,x)=>s+x.traps,0)}));
