'use strict';
const fs=require('fs'),path=require('path'),os=require('os'),cp=require('child_process'),crypto=require('crypto');
const rot=(x,n)=>((x<<n)|(x>>>(32-n)))|0;
const refs={mix:(x,y)=>((x^y)+rot(x,7))|0,carry:(x,y)=>((x+y)^rot(y,13))|0,
  mask:(x,y)=>((x&rot(y,3))+(y^1831565813))|0};
const instantiate=p=>{const b=fs.readFileSync(p);if(!WebAssembly.validate(b))throw Error('Validation: '+p);
 return new WebAssembly.Instance(new WebAssembly.Module(b)).exports.run;};
if(process.argv[2]==='--worker'){
  const before=process.resourceUsage().maxRSS,f=instantiate(process.argv[3]);let sink=0;
  const initial=process.resourceUsage().maxRSS;
  for(let i=0;i<4000;i++)sink^=f(i,Math.imul(i,0x9e3779b1));
  if(global.gc)global.gc();
  const samples=[];
  for(let r=0;r<11;r++){
    const a=process.hrtime.bigint();
    for(let i=0;i<2000;i++)sink^=f(i+r,Math.imul(i,0x9e3779b1));
    samples.push(Number(process.hrtime.bigint()-a)/2000);
  }
  console.log(JSON.stringify({ns_per_call:samples,maxrss_kib:process.resourceUsage().maxRSS,
    before_load_maxrss_kib:before,after_load_maxrss_kib:initial,heap_after_timed_calls:process.memoryUsage().heapUsed,sink}));
  process.exit(0);
}
const dir=path.resolve(process.argv[2]),dest=path.join(dir,'checks.json');
if(fs.existsSync(dest))throw Error('Refuse overwrite');
const m=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json')));
const edge=[0,1,-1,0x7fffffff,-2147483648,0x55555555,0xaaaaaaaa,0xffff];
const inputs=[];for(const x of edge)for(const y of edge)inputs.push([x|0,y|0]);
for(let i=0;i<32;i++)for(const pair of [[1<<i,0],[0,1<<i],[1<<i,-1],[-1,1<<i]])inputs.push(pair);
let rng=0x4e26b18;const next=()=>{rng^=rng<<13;rng^=rng>>>17;rng^=rng<<5;return rng|0;};
for(let i=0;i<4096;i++)inputs.push([next(),next()]);
const rows=[];let total=0,bad=0;
for(const row of m.rows){
  for(const [kind,file] of [['original',row.wasm],...(row.recovered?[['recovered',row.recovered]]:[])]){
    const p=path.join(dir,file),f=instantiate(p);let mismatch=0;
    if(kind==='original'&&crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex')!==row.sha256)throw Error('Hash');
    for(const [a,b] of inputs){total++;if(f(a,b)!==refs[row.family](a,b))mismatch++;}
    bad+=mismatch;rows.push({family:row.family,optimization:row.optimization,
      mode:kind==='recovered'?'recovered':row.mode,wasm:file,inputs:inputs.length,mismatches:mismatch,
      bytes:fs.statSync(p).size});
  }
}
const performance=[];
// Independently launched child processes: no preceding condition's heap or JIT state.
// Reverse orders on alternating repetitions; no superiority significance claim.
for(let rep=0;rep<3;rep++){
  const order=rep%2?[...rows].reverse():rows;
  for(const row of order){
    const p=path.join(dir,row.wasm);
    const run=JSON.parse(cp.execFileSync(process.execPath,['--expose-gc',__filename,'--worker',p],{encoding:'utf8',timeout:30000}));
    performance.push({rep,family:row.family,mode:row.mode,optimization:row.optimization,...run});
  }
}
const result={node:process.version,v8:process.versions.v8,cpu:os.cpus()[0].model,
  platform:process.platform,arch:process.arch,inputs_per_condition:inputs.length,conditions:rows.length,
  executions:total,mismatches:bad,rows,performance,
  method:'4000 warmups; 11 x 2000 timed calls; 3 fresh processes/condition; host-call overhead included.',
  memory_scope:'Process high-water RSS in KiB includes Node, JIT, GC, harness. No linear memory in modules.',
  proof_scope:'Finite differential tests against independent JS. Not whole-domain formal equivalence.'};
fs.writeFileSync(dest,JSON.stringify(result,null,2));
console.log(JSON.stringify({conditions:rows.length,executions:total,mismatches:bad,performance_processes:performance.length}));
if(bad)process.exitCode=1;
