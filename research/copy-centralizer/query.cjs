// Attack input: observed target binary and public read/write/copy ABI only.
const fs=require('fs');const t=process.hrtime.bigint(),bytes=fs.readFileSync(process.argv[2]);
const ex=new WebAssembly.Instance(new WebAssembly.Module(bytes)).exports,mem=new Uint8Array(ex.memory.buffer),n=32;
const initial=Buffer.from(mem),plain=Array.from({length:n},(_,i)=>ex.read(i)),columns=[];let calls=n;
for(let i=0;i<n;i++){
 ex.write(i,plain[i]^1);calls++;const col=[];
 for(let j=0;j<mem.length;j++){const d=mem[j]^initial[j];if(d!==0&&d!==1)throw Error('not byte-linear');if(j>=n&&d)throw Error('outside public window');if(j<n)col.push(d);}
 columns.push(col);ex.write(i,plain[i]);calls++;if(!Buffer.from(mem).equals(initial))throw Error('restore failed');
}
const matrix=Array.from({length:n},(_,j)=>columns.reduce((r,c,i)=>r|(c[j]<<i),0)>>>0);
function encode(x){return matrix.map(r=>{let v=0;for(let i=0;i<n;i++)if((r>>>i)&1)v^=x[i];return v;});}
const offset=encode(plain).map((v,i)=>v^initial[i]);
let state=211044,holdoutCalls=0;const logical=[...plain];
for(let k=0;k<128;k++){state=(Math.imul(state,1664525)+1013904223)>>>0;const i=(state>>>8)%n,v=(state>>>16)&255;ex.write(i,v);holdoutCalls++;logical[i]=v;const y=encode(logical);for(let j=0;j<n;j++)if((y[j]^offset[j])!==mem[j])throw Error('holdout mismatch');}
console.log(JSON.stringify({window:n,matrix,offset,plain,physicalInitial:[...initial.subarray(0,n)],zeroOutsideWindow:initial.subarray(n).every(x=>x===0),learningCalls:calls,directCloneReadCalls:n,holdoutCalls,elapsedMs:Number(process.hrtime.bigint()-t)/1e6}));
