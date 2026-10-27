'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),os=require('node:os');
const dir=path.resolve(process.argv[2]),m=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json')));
function evalRef(e,args){if(e[0]==='var')return args[e[1]]&65535;if(e[0]==='const')return e[1];
 const a=evalRef(e[1],args),b=evalRef(e[2],args);return e[0]==='min'?Math.min(a,b):Math.min(65535,a+b);}
let seed=20261018;const rnd=()=>{seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed>>>0;};
const inputs={};for(const r of m.artifacts){if(inputs[r.kernel])continue;
 const cases=[],n=r.inputs,boundary=[0,1,2,32767,32768,65534,65535,65536,0x7fffffff,0x80000000,0xffffffff];
 for(const v of boundary)cases.push(Array(n).fill(v));
 for(let j=0;j<n;j++)for(const v of boundary){const a=Array(n).fill(0);a[j]=v;cases.push(a);const b=Array(n).fill(65535);b[j]=v;cases.push(b);}
 for(let i=0;i<4096;i++)cases.push(Array.from({length:n},()=>rnd()));
 // Small inputs exercise non-saturated paths, which uniform u16 tests under-sample.
 for(let i=0;i<4096;i++)cases.push(Array.from({length:n},()=>rnd()%1024));
 inputs[r.kernel]=cases;
}
const rows=[];let sink=0;
for(const r of m.artifacts){const bytes=fs.readFileSync(path.join(dir,r.file));if(crypto.createHash('sha256').update(bytes).digest('hex')!==r.sha256)throw Error('hash');
 if(!WebAssembly.validate(bytes))throw Error('validation');const fn=new WebAssembly.Instance(new WebAssembly.Module(bytes)).exports.run;
 let mismatches=0,traps=0;for(const args of inputs[r.kernel]){let actual;try{actual=fn(...args);}catch(e){traps++;continue;}if(actual!==evalRef(m.referenceExpressions[r.kernel],args))mismatches++;}
 const batch=()=>{let s=0;for(let i=0;i<20000;i++)s=(Math.imul(s,33)^fn(...inputs[r.kernel][i%inputs[r.kernel].length]))|0;return s;};
 sink^=batch();const times=[],checks=[];for(let k=0;k<9;k++){const begin=process.hrtime.bigint();const check=batch();times.push(Number(process.hrtime.bigint()-begin)/20000);checks.push(check);sink^=check;}times.sort((a,b)=>a-b);
 rows.push({...r,cases:inputs[r.kernel].length,mismatches,traps,medianNs:times[4],sortedNs:times,checks});
}
const result={node:process.version,v8:process.versions.v8,cpu:os.cpus()[0].model,rows,inputs,sink,warmup:20000,repetitions:9,iterations:20000,
 memory:'No Wasm linear memory. Process/JIT allocation not measured.',performanceLimit:'Fixed artifact order; JS spread/call and input-array lookup included; pilot measurement only.'};
fs.writeFileSync(path.join(dir,'checks.json'),JSON.stringify(result,null,2),{flag:'wx'});fs.copyFileSync(__filename,path.join(dir,'check.cjs'));
console.log(JSON.stringify(rows.map(r=>({file:r.file,cases:r.cases,mismatches:r.mismatches,traps:r.traps,medianNs:r.medianNs}))));
if(rows.some(r=>r.mismatches||r.traps))process.exitCode=1;
