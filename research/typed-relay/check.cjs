const fs=require('fs'),path=require('path');
const dir=process.argv[2],randomCount=+process.argv[3];
const files=JSON.parse(fs.readFileSync(path.join(dir,'files.json'),'utf8'));
let rng=20261018;function random(){rng^=rng<<13;rng^=rng>>>17;rng^=rng<<5;return rng>>>0;}
function rotl(x,k){return (x<<k)|(x>>>(32-k));}
function rotr(x,k){return (x>>>k)|(x<<(32-k));}
function reference(model,mem,p,n,seed){
 let a=seed|0,b=(seed^19088743)|0;
 for(let i=0;i<(n>>>0);i++){
  const addr=((p>>>0)+i)>>>0;if(addr>=mem.length)return {trap:true};const x=mem[addr];
  if(model==='rolling')a=(Math.imul(rotl(a,5)^x,33)+i)|0;
  else if(model==='dual'){a=(a+Math.imul(x,i+1))|0;b=(rotr(b,3)^((a-x)|0))|0;}
  else{a=(rotl(a,7)+x)|0;if(x&1)mem[addr]=(x^a)&255;b=(b^Math.imul(a,17))|0;}
 }return {trap:false,value:(a^b)|0};
}
let calls=0,mismatches=0,traps=0;const details=[],cases=[];
for(const p of [0,1,65520,65535,65536,0xffffffff,0xfffffffe])for(const n of [0,1,2,16,17])for(const seed of [0,1,-1,0x80000000])cases.push([p,n,seed]);
for(let i=0;i<randomCount;i++)cases.push([i%3===0?65500+(random()%50):random()%4096,random()%65,random()]);
const initial=Buffer.alloc(65536);for(let i=0;i<initial.length;i++)initial[i]=random()&255;
for(const f of files){
 const bytes=fs.readFileSync(path.join(dir,f.path));if(!WebAssembly.validate(bytes))throw Error('invalid '+f.path);
 const e=new WebAssembly.Instance(new WebAssembly.Module(bytes)).exports;const memory=Buffer.from(e.memory.buffer);
 let errors=0,trapCount=0;
 for(const args of cases){
  initial.copy(memory);const expectedMem=Buffer.from(initial);const expect=reference(f.model,expectedMem,...args);
  let actual;try{actual={trap:false,value:e.run(...args)}}catch(err){if(!(err instanceof WebAssembly.RuntimeError))throw err;actual={trap:true};}
  calls++;if(actual.trap){traps++;trapCount++;}
  if(actual.trap!==expect.trap||(!actual.trap&&actual.value!==expect.value)||!memory.equals(expectedMem)){errors++;if(errors<3)details.push({file:f.path,args,actual,expect,memoryEqual:memory.equals(expectedMem)});}
 }
 mismatches+=errors;
}
console.log(JSON.stringify({calls,traps,mismatches,details,cases_per_binary:cases.length,binaries:files.length,random_count:randomCount,
 full_memory_bytes_compared_per_call:65536,node:process.version,v8:process.versions.v8}));
