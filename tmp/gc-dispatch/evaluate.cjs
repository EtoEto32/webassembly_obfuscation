'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict'),os=require('node:os');
const out=path.join(__dirname,'artifacts'),manifest=JSON.parse(fs.readFileSync(path.join(out,'manifest.json')));
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
// Separate BigInt implementation; does not read WAT, generator or its expressions.
const U=x=>BigInt.asUintN(32,x),rot=(x,n)=>U((x<<n)|(x>>(32n-n)));
function reference(kernel,a,b,count){let x=U(BigInt(a)),y=U(BigInt(b)),n=Number(BigInt(count)&63n);let left=0,right=0;
  while(n>0){
    if(kernel==='gcd') {if(x===0n||y===0n)break;if(x>=y){x-=y;left++;}else{y-=x;right++;}}
    else if(x&1n){x=U(rot(x^y,5n)+BigInt(n)*73244475n);y=U(y^(x*33n));left++;}
    else{x=U(x*x+y);y=U(rot(y,7n)+x);right++;} n--;
  }
  return {value:x|(y<<32n),left,right};
}
let randomState=0x19d07c35;
function random(){randomState^=randomState<<13;randomState^=randomState>>>17;randomState^=randomState<<5;return randomState>>>0;}
const edges=[0,1,2,3,0x7fffffff,0x80000000,0xfffffffe,0xffffffff];
const inputs=[];for(const x of edges)for(const y of edges)for(const n of [0,1,2,31,63,64,65,0xffffffff])inputs.push([x,y,n]);
for(let i=0;i<4096;i++)inputs.push([random(),random(),random()]);
const refs={},coverage={};
for(const k of ['mix','gcd']){let left=0,right=0;refs[k]=inputs.map(a=>{const r=reference(k,...a);left+=r.left;right+=r.right;return r.value;});coverage[k]={reference_left_steps:left,reference_right_steps:right};assert(left>0&&right>0);}
const modules=manifest.files.map(f=>{const bytes=fs.readFileSync(path.join(out,f.file));assert.equal(sha(bytes),f.sha256);
  const start=process.hrtime.bigint(),m=new WebAssembly.Module(bytes);assert.deepEqual(WebAssembly.Module.imports(m),[]);
  const instance=new WebAssembly.Instance(m,{});return {f,run:instance.exports.run,batch:instance.exports.batch,compile_and_instantiate_ns:Number(process.hrtime.bigint()-start)};});
const checks=[];
for(const m of modules){let mismatches=0,first;
  inputs.forEach((args,i)=>{const actual=BigInt.asUintN(64,m.run(...args));if(actual!==refs[m.f.kernel][i]){mismatches++;first??={args,expected:refs[m.f.kernel][i].toString(),actual:actual.toString()};}});
  let expectedBatch=0n;
  for(let i=0;i<257;i++){const seed=123456;expectedBatch^=reference(m.f.kernel,(seed+Math.imul(i,1664525))>>>0,(seed^Math.imul(i,1013904223))>>>0,(i&31)+16).value;}
  const batchPassed=BigInt.asUintN(64,m.batch(257,123456))===expectedBatch;
  checks.push({name:m.f.name,input_cases:inputs.length,mismatches,first,batchPassed,compile_and_instantiate_ns:m.compile_and_instantiate_ns});
}
const report={node:process.version,v8:process.versions.v8,platform:process.platform,arch:process.arch,cpu:os.cpus()[0]?.model,
  script_sha256:sha(fs.readFileSync(__filename)),input_seed:'0x19d07c35',input_cases:inputs.length,
  input_sha256:sha(JSON.stringify(inputs)),coverage,checks,
  scope:'Finite output comparisons with independent BigInt reference; branch counts are reference counts, not dynamic coverage of transformed binaries.'};
fs.writeFileSync(path.join(out,'correctness.json'),JSON.stringify(report,null,2)+'\n');
assert(checks.every(r=>r.mismatches===0&&r.batchPassed),'correctness failed');
for(const m of modules)for(let i=0;i<20;i++)m.batch(65536,123456+i);
const times=[],count=65536,rounds=7;
for(let round=0;round<rounds;round++){
  const order=[...modules];for(let i=order.length-1;i>0;i--){const j=random()%(i+1);[order[i],order[j]]=[order[j],order[i]];}
  const seed=random()|0,checksum=new Map();
  for(let position=0;position<order.length;position++){
    const m=order[position],start=process.hrtime.bigint(),value=m.batch(count,seed),elapsed=Number(process.hrtime.bigint()-start);
    const key=m.f.kernel;if(checksum.has(key))assert.equal(value,checksum.get(key));else checksum.set(key,value);
    times.push({round,position,name:m.f.name,kernel:m.f.kernel,mode:m.f.mode,optimization:m.f.optimization,count,seed,elapsed_ns:elapsed,ns_per_run:elapsed/count,checksum:value.toString()});
  }
}
fs.writeFileSync(path.join(out,'timing.json'),JSON.stringify({node:process.version,v8:process.versions.v8,cpu:os.cpus()[0]?.model,warmup:{batches:20,count:65536},rounds,count,
  order:'Seeded Fisher-Yates; every condition once each round; same seed in round',times},null,2)+'\n');
const median=xs=>[...xs].sort((a,b)=>a-b)[Math.floor(xs.length/2)];
const summary=modules.map(({f})=>{const rows=times.filter(t=>t.name===f.name),values=rows.map(t=>t.ns_per_run);
  const paired=rows.map(t=>t.ns_per_run/times.find(b=>b.round===t.round&&b.kernel===f.kernel&&b.optimization===f.optimization&&b.mode==='structured').ns_per_run);
  return {name:f.name,bytes:f.bytes,median_ns:median(values),min_ns:Math.min(...values),max_ns:Math.max(...values),median_paired_ratio:median(paired)};});
fs.writeFileSync(path.join(out,'summary.json'),JSON.stringify(summary,null,2)+'\n');
console.log(JSON.stringify({modules:checks.length,comparisons:checks.length*inputs.length,mismatches:0,batch_checks:checks.length,timing_observations:times.length,summary},null,2));
