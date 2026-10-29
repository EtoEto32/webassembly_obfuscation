// Exact public-I/O learning for the documented bit-independent family.
// Only binary path, public arity, and output file are supplied.
const fs=require('node:fs');
const binary=process.argv[2],n=Number(process.argv[3]),file=process.argv[4];
if(n<5||n>24)throw Error('Exhaustive learner supports 5..24 variables');
if(fs.existsSync(file))throw Error('Refuse overwrite');
const begin=process.hrtime.bigint();
const e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(binary))).exports;
if(e.run.length!==n)throw Error('Arity mismatch');
const compileMs=Number(process.hrtime.bigint()-begin)/1e6;
const a=Array(n).fill(0),patterns=[0xaaaaaaaa,0xcccccccc,0xf0f0f0f0,0xff00ff00,0xffff0000];
for(let k=0;k<5;k++)a[n-1-k]=patterns[k]|0;
for(let k=0;k<1024;k++)e.run(...a);
const count=2**(n-5),buffer=Buffer.alloc(count*4),start=process.hrtime.bigint();
for(let b=0;b<count;b++){
 for(let j=0;j<n-5;j++)a[j]=-((b>>>(n-6-j))&1);
 buffer.writeInt32LE(e.run(...a)|0,4*b);
}
const queryMs=Number(process.hrtime.bigint()-start)/1e6;
fs.writeFileSync(file,buffer);
console.log(JSON.stringify({queries:count,boolean_assignments:2**n,warmup:1024,compile_ms:compileMs,query_ms:queryMs,table_bytes:buffer.length,max_rss_kib:process.resourceUsage().maxRSS,node:process.version,v8:process.versions.v8}));
