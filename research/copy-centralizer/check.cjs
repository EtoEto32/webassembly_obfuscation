const fs=require('fs'),path=require('path');
const root=process.argv[2],rows=JSON.parse(fs.readFileSync(path.join(root,'manifest.json'))),fixtures=JSON.parse(fs.readFileSync(path.join(root,'fixtures.json')));
let state=211043,calls=0,traps=0,comparisons=0;
function rnd(){state=(Math.imul(state,1664525)+1013904223)>>>0;return state;}
function instantiate(file){const bytes=fs.readFileSync(path.join(root,file));if(!WebAssembly.validate(bytes))throw Error('validation '+file);return new WebAssembly.Instance(new WebAssembly.Module(bytes)).exports;}
function apply(rows,data){return rows.map(r=>{let v=0;for(let i=0;i<rows.length;i++)if((r>>>i)&1)v^=data[i];return v;});}
const reports=[];
for(const row of rows){
 const ex=instantiate(row.observed),fixture=fixtures.find(x=>x.name===row.kernel),ref=Buffer.alloc(65536);Buffer.from(fixture.data).copy(ref);const raw=new Uint8Array(ex.memory.buffer);let localCalls=0,localTraps=0;
 function check(){const logical=Buffer.from(raw);if(['native','conjugate'].includes(row.mode))Buffer.from(apply(row.inverse,logical)).copy(logical);else if(row.mode==='uniform')for(let i=0;i<row.n;i++)logical[i]^=173;if(!logical.equals(ref))throw Error('memory '+row.file+' '+localCalls);comparisons++;}
 function read(i){calls++;localCalls++;let value,err=false;try{value=ex.read(i);}catch(e){if(!(e instanceof WebAssembly.RuntimeError))throw e;err=true;traps++;localTraps++;}if(err!==(i>>>0>=65536)||!err&&value!==ref[i>>>0])throw Error('read '+row.file+' '+i);}
 function write(i,v){calls++;localCalls++;let err=false;try{ex.write(i,v);}catch(e){if(!(e instanceof WebAssembly.RuntimeError))throw e;err=true;traps++;localTraps++;}if(err!==(i>>>0>=65536))throw Error('write trap');if(!err)ref[i>>>0]=v;check();}
 check();
 for(let i=0;i<row.n;i++)for(const v of [0,1,127,128,255,256,0x80000000,0xffffffff]){write(i,v);read(i);}
 for(const i of [row.n-1,row.n,31,32,65535,65536,0x80000000,0xffffffff]){read(i);write(i,0x12345678);}
 for(let step=0;step<512;step++){
  const kind=rnd()%3;if(kind===0)write(rnd()%32,rnd());else if(kind===1)read(rnd()%65536);else {const j=rnd()%fixture.copies.length,[d,s,l]=fixture.copies[j];ex['copy'+j]();calls++;localCalls++;Buffer.from(ref.subarray(s,s+l)).copy(ref,d);check();}
 }
 reports.push({file:row.file,calls:localCalls,traps:localTraps});
}
const result={targets:rows.length,calls,traps,fullMemoryComparisons:comparisons,mismatches:0,reports,node:process.version,v8:process.versions.v8};fs.writeFileSync(path.join(root,'checks.json'),JSON.stringify(result,null,2));console.log(JSON.stringify({targets:rows.length,calls,traps,comparisons,mismatches:0}));
