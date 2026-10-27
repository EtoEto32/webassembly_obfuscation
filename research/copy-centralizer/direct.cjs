// Stronger task-specific attack: no matrix learning is needed for this public ABI.
const fs=require('fs');const t=process.hrtime.bigint();
const ex=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(process.argv[2]))).exports;
const plain=Array.from({length:32},(_,i)=>ex.read(i));
console.log(JSON.stringify({window:32,plain,logicalReadCalls:32,logicalWriteCalls:0,zeroPhysicalOutsideWindow:new Uint8Array(ex.memory.buffer).subarray(32).every(x=>x===0),elapsedMs:Number(process.hrtime.bigint()-t)/1e6}));
