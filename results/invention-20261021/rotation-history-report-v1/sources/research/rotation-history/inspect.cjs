// Recovery uses only the binary's public run/memory API and the known family.
const fs=require('fs'),{performance}=require('perf_hooks');
const filename=process.argv[2];
const t0=performance.now();
const bytes=fs.readFileSync(filename);
if(!WebAssembly.validate(bytes))throw Error('invalid Wasm');
const e=new WebAssembly.Instance(new WebAssembly.Module(bytes)).exports;
new Uint8Array(e.memory.buffer).fill(0);
const prepared=performance.now();
let calls=0;
function query(seed,len){calls++;return e.run(seed,0,len)>>>0;}
const zero=Array.from({length:32},(_,j)=>query(2**j,0));
let mask=0;for(let j=0;j<32;j++){if(zero[j]!==0&&zero[j]!==2**j)throw Error('mask projection required');mask=(mask|zero[j])>>>0;}
if(!mask)throw Error('empty observation');
const one=Array.from({length:32},(_,j)=>query(2**j,1));
const rotate=(x,k)=>((x<<k)|(x>>>(32-k)))>>>0;
const ks=Array.from({length:32},(_,j)=>j).filter(k=>one.every((v,j)=>v===((rotate(2**j,k)&mask)>>>0)));
if(ks.length!==1)throw Error('not a uniquely identified rotation');
const elapsed=performance.now();
console.log(JSON.stringify({rotation:ks[0],mask,queries:calls,prepare_ms:prepared-t0,recovery_ms:elapsed-prepared,
  limitation:'family identification from finite queries, not a general equivalence proof'}));
