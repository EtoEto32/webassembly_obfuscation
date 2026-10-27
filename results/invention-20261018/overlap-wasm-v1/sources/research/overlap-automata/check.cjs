const fs=require('fs'),path=require('path');
const dir=process.argv[2],manifest=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json'),'utf8'));
let rng=20261018;function random(){rng^=rng<<13;rng^=rng>>>17;rng^=rng<<5;return rng>>>0;}
const memory0=Buffer.alloc(65536);for(let i=0;i<memory0.length;i++)memory0[i]=random()&255;
const cases=[];
for(const p of [0,1,65520,65535,65536,0xffffffff,0xfffffffe])for(const n of [0,1,2,16,17,0xffffffff])cases.push([p,n]);
for(let i=0;i<1000;i++)cases.push([i%3===0?65500+random()%50:random()%4096,random()%65]);
let calls=0,traps=0,mismatches=0,wordCases=0;const details=[];
function ref(d,mem,p,n){let q=d.start;for(let i=0;i<(n>>>0);i++){let a=((p>>>0)+i)>>>0;if(a>=mem.length)return {trap:true};q=d.trans[q][mem[a]&1];}return {trap:false,value:(d.final>>>q)&1};}
for(const f of manifest.files){
 const bin=fs.readFileSync(path.join(dir,f.path));if(!WebAssembly.validate(bin))throw Error('Invalid '+f.path);
 const e=new WebAssembly.Instance(new WebAssembly.Module(bin)).exports,mem=Buffer.from(e.memory.buffer),d=manifest.models[f.model];
 function one(p,n){const expected=ref(d,mem,p,n),before=Buffer.from(mem);let actual;
  try{actual={trap:false,value:e.run(p,n)}}catch(error){if(!(error instanceof WebAssembly.RuntimeError))throw error;actual={trap:true};}
  calls++;if(actual.trap)traps++;
  if(expected.trap!==actual.trap||(!actual.trap&&expected.value!==actual.value)||!mem.equals(before)){
   mismatches++;if(details.length<5)details.push({path:f.path,p,n,expected,actual,memoryEqual:mem.equals(before)});}}
 memory0.copy(mem);for(const [p,n] of cases)one(p,n);
 // Every binary word of length <= 9, independent of random-byte coverage.
 for(let n=0;n<=9;n++)for(let word=0;word<(1<<n);word++){
  for(let i=0;i<n;i++)mem[i]=(word>>>i)&1;one(0,n);wordCases++;}
}
const result={binaries:manifest.files.length,calls,traps,mismatches,details,boundary_cases:42,random_cases:1000,
 exhaustive_words_per_binary:1023,exhaustive_word_calls:wordCases,full_memory_bytes_checked_per_call:65536,node:process.version,v8:process.versions.v8};
console.log(JSON.stringify(result));if(mismatches)process.exitCode=1;
