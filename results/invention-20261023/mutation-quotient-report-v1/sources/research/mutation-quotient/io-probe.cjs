// This process receives only the delivered Wasm and public array size.
const fs=require('node:fs');
const e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(process.argv[2]))).exports,n=Number(process.argv[3]);
e.reset();const start=process.hrtime.bigint();
const diffs=Array.from({length:n-1},(_,i)=>e.run(0,i+1,0,0)>>>0);
const scale=e.run(3,0,1,0)>>>0;
console.log(JSON.stringify({diffs,scale,queries:n,reset_calls:1,query_ms:Number(process.hrtime.bigint()-start)/1e6}));
