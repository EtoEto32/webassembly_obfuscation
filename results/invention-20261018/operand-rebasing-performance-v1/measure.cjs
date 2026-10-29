'use strict';
const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),crypto=require('node:crypto');
const dir=path.resolve(process.argv[2]),out=path.resolve(process.argv[3]);
fs.mkdirSync(out);
const manifest=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json')));
const rows=[],iterations=20000,warmup=20000,repeats=9;
let sink=0;
for(const a of manifest.artifacts){
 const bytes=fs.readFileSync(path.join(dir,a.file));
 if(crypto.createHash('sha256').update(bytes).digest('hex')!==a.sha256)throw Error('hash mismatch');
 const fn=new WebAssembly.Instance(new WebAssembly.Module(bytes)).exports.run;
 function batch(n){let s=0;for(let i=0;i<n;i++)s=(Math.imul(s,33)^fn(i,(i*7919)|0,(i^0x98765432)|0,(i*97)|0))|0;return s;}
 sink^=batch(warmup);const ns=[],checks=[];
 for(let r=0;r<repeats;r++){const begin=process.hrtime.bigint();const check=batch(iterations);ns.push(Number(process.hrtime.bigint()-begin)/iterations);checks.push(check);sink^=check;}
 ns.sort((a,b)=>a-b);rows.push({file:a.file,kernel:a.kernel,mode:a.mode,level:a.level||'raw',bytes:bytes.length,
  medianNs:ns[4],minNs:ns[0],maxNs:ns[8],sortedNs:ns,checks,
  declaredLinearMemoryBytes:['fused','unminimized'].includes(a.mode)?65536:0});
}
fs.writeFileSync(path.join(out,'performance.json'),JSON.stringify({node:process.version,v8:process.versions.v8,cpu:os.cpus()[0].model,
 platform:os.platform(),iterations,warmup,repeats,sink,rows,
 limitations:'Sequential microbenchmarks include JS-to-Wasm call cost. Memory is declared linear memory, not RSS or JIT allocation. No statistical significance claim.'},null,2),{flag:'wx'});
fs.copyFileSync(__filename,path.join(out,'measure.cjs'));
console.log(JSON.stringify(rows.filter(x=>x.level==='O3').map(x=>({kernel:x.kernel,mode:x.mode,ns:x.medianNs,bytes:x.bytes}))));
