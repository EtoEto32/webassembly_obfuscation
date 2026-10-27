const fs = require('node:fs');
const path = require('node:path');
const root = process.argv[2];
const manifest = JSON.parse(fs.readFileSync(path.join(root,'manifest.json')));
let seed = 20261022;
function random() { seed = (Math.imul(seed,1664525)+1013904223)|0; return seed; }
function rotl(x,k) { return (x<<k)|(x>>>(32-k)); }
function op(x,p) {
  if(p.kind===0) return rotl((x+p.a)|0,p.k)^p.b;
  if(p.kind===1) return (Math.imul(x^p.a,p.b)+rotl(x,p.k))|0;
  return (rotl(x^p.a,p.k) ^ (x>>>p.h) ^ p.b)|0;
}
function reference(f,x,s) { for(const j of f.orders[s&1]) x=op(x,f.ops[j]); return x|0; }
function instantiate(file) { const b=fs.readFileSync(path.join(root,file)); if(!WebAssembly.validate(b))throw Error('Node validation '+file); return new WebAssembly.Instance(new WebAssembly.Module(b)).exports; }
const boundary=[0,1,-1,-2147483648,2147483647,2147483646,0x55555555,0xaaaaaaaa|0,0xffff,0x10000,31,32,33];
const flags=[0,1,2,3,-1,-2147483648,2147483647,0xaaaaaaaa|0];
const rows=[]; for(const x of boundary)for(const s of flags)rows.push([x,s]);
for(let i=0;i<4096;i++)rows.push([random(),random()]);
const report={rows_per_target:rows.length,main:[],probes:[],negative:[],main_calls:0,probe_calls:0,mismatches:0};
for(const t of manifest.targets) {
  const f=manifest.fixtures[t.fixture]; const e=instantiate(t.file);
  for(const [x,s] of rows){const y=e.run(x,s)|0;if(y!==reference(f,x,s))throw Error('Mismatch '+t.file+' '+JSON.stringify([x,s,y]));report.main_calls++;}
  report.main.push({file:t.file,calls:rows.length});
  if(e.bench){
    for(const count of [0,1,17,255]){
      let x=123,s=987,sum=0;
      for(let k=0;k<count;k++){x=(Math.imul(x,1664525)+1013904223)|0;s=(Math.imul(s,1664525)+1013904223)|0;sum^=reference(f,x,s);}
      if((e.bench(count,123,987)|0)!==(sum|0))throw Error('Bench checksum mismatch '+t.file);
    }
  }
}
for(const t of manifest.probes) {
  const f=manifest.fixtures[t.fixture];const e=instantiate(t.file);const v=new Int32Array(e.memory.buffer);
  const original=new Uint8Array(e.memory.buffer).slice();
  for(let pattern=0;pattern<4;pattern++)for(const [x,s] of rows.slice(0,256)){
    for(let j=0;j<f.ops.length;j++)v[32768/4+j]=pattern===0?0:pattern===1?-1:pattern===2?0x55555555:random();
    const y=e.run(x,s)|0;if(y!==reference(f,x,s))throw Error('Initial state mismatch '+t.file);report.probe_calls++;
    const bytes=new Uint8Array(e.memory.buffer);
    if(!Buffer.from(bytes.subarray(0,32768)).equals(Buffer.from(original.subarray(0,32768))) || !Buffer.from(bytes.subarray(32768+4*f.ops.length)).equals(Buffer.from(original.subarray(32768+4*f.ops.length))))throw Error('Unexpected memory write');
  }
  report.probes.push({file:t.file,calls:1024,linear_memory_bytes:e.memory.buffer.byteLength});
}
for(const t of manifest.negative){
  const f=manifest.fixtures[t.fixture];const e=instantiate(t.file);let differences=0;
  for(const [x,s]of rows.slice(0,256))if((e.run(x,s)|0)!==reference(f,x,s))differences++;
  if(differences===0)throw Error('Negative control failed to expose missing update');
  report.negative.push({file:t.file,tested:256,differences});
}
report.environment={node:process.version,v8:process.versions.v8,platform:process.platform,arch:process.arch,cpu:require('node:os').cpus()[0].model};
fs.writeFileSync(path.join(root,'checks.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({main_calls:report.main_calls,probe_calls:report.probe_calls,negative:report.negative.length,mismatches:0}));
