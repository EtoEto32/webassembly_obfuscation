// Public exports only. Assumes the declared argument-byte writer family.
const fs=require('fs'),{performance}=require('perf_hooks');
const start=performance.now(),e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(process.argv[2]))).exports;
const setup=performance.now()-start,mem=new Uint8Array(e.memory.buffer),params=e.run.length;
if(params<2||params>32||mem.length!==65536)throw Error('Unsupported public API');
const args=Array(params).fill(0),labels={};
for(let p=1;p<params;p++)for(let b=0;b<4;b++){const label=(p-1)*4+b+1;args[p]|=label<<(8*b);labels[label]=[p,b];}
let queries=0;const frames=[],records=[],t=performance.now();
function probe(capacity){mem.fill(255);args[0]=mem.length-capacity;let trap=false;
 try{e.run(...args)}catch(error){if(!(error instanceof WebAssembly.RuntimeError))throw error;trap=true}
 queries++;const image={};for(let i=0;i<capacity;i++){const v=mem[args[0]+i];if(v===255)continue;if(!labels[v])throw Error('Outside byte-writer family');image[i]=labels[v];}
 records.push({capacity,trap,written_bytes:Object.keys(image).length});return {trap,image};
}
let got=probe(256);if(got.trap)throw Error('Unsupported footprint or trap');
while(Object.keys(got.image).length){const right=1+Math.max(...Object.keys(got.image).map(Number));frames.push({right,image:got.image});got=probe(right-1);
 if(!got.trap)throw Error('Nontrapping prefix outside declared family');if(queries>257)throw Error('No progress');}
frames.reverse();console.log(JSON.stringify({status:'success',params,queries,setup_ms:setup,analysis_ms:performance.now()-t,frames,records,
 scope:'Known copy-of-argument-bytes family; no code inspection, original model, or transformation seed'}));
