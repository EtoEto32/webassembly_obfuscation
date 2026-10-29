const fs=require('fs'),path=require('path'),dir=process.argv[2];
const manifest=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json'),'utf8'));
let rng=20261018;function random(){rng^=rng<<13;rng^=rng>>>17;rng^=rng<<5;return rng>>>0;}
const initial=Buffer.alloc(65536);for(let i=0;i<initial.length;i++)initial[i]=random()&255;
function evalpoly(poly,x){let y=0;for(const term of poly){let v=term.coefficient|0;for(const i of term.monomial)v=Math.imul(v,x[i]);y=(y+v)|0;}return y;}
function reference(f,p,n){let state=[0,0,0,0];for(let i=0;i<(n>>>0);i++){
 const addr=((p>>>0)+i)>>>0;if(addr>=initial.length)return {trap:true};const x=state.concat(initial[addr]);state=f.map(poly=>evalpoly(poly,x));}
 return {trap:false,value:state[0]};}
const cases=[];for(const p of [0,1,65520,65535,65536,0xffffffff,0xfffffffe])for(const n of [0,1,2,16,17,0xffffffff])cases.push([p,n]);
for(let i=0;i<1000;i++)cases.push([i%3===0?65500+random()%50:random()%4096,random()%65]);
const expected={};for(const [name,f] of Object.entries(manifest.models))expected[name]=cases.map(args=>reference(f,...args));
let calls=0,traps=0,mismatches=0;const details=[];
for(const f of manifest.files){const bytes=fs.readFileSync(path.join(dir,f.path));if(!WebAssembly.validate(bytes))throw Error('Invalid '+f.path);
 const e=new WebAssembly.Instance(new WebAssembly.Module(bytes)).exports,mem=Buffer.from(e.memory.buffer);initial.copy(mem);
 for(let i=0;i<cases.length;i++){let actual;try{actual={trap:false,value:e.run(...cases[i])}}catch(error){if(!(error instanceof WebAssembly.RuntimeError))throw error;actual={trap:true};}
  const wanted=expected[f.model][i];calls++;if(actual.trap)traps++;
  if(actual.trap!==wanted.trap||(!actual.trap&&actual.value!==wanted.value)||!mem.equals(initial)){mismatches++;if(details.length<5)details.push({path:f.path,args:cases[i],actual,wanted});}
 }}
console.log(JSON.stringify({binaries:manifest.files.length,calls,traps,mismatches,details,cases_per_binary:cases.length,boundary_cases:42,random_cases:1000,
 memory_bytes_compared_per_call:65536,node:process.version,v8:process.versions.v8}));if(mismatches)process.exitCode=1;
