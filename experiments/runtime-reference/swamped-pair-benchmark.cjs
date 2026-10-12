'use strict';
const path=require('path'),os=require('os'),{performance}=require('perf_hooks');
const {read,save,digest}=require('./proof-glue-controls.cjs');
const {load}=require('./swamped-host.cjs');
const root='/work',dir=path.join(root,'results/runtime-mining/cross-dataset/swamped');
const manifest=read(path.join(dir,'controlled-pair-manifest.json')),spec=JSON.parse(manifest);
const input=read(path.join(root,'results/runtime-mining/cross-dataset/proof-of-theft/glue-control-input.json'));
const vectors=JSON.parse(input).vectors;
const checkOnly=process.argv.includes('--check-only');
const out=path.join(dir,checkOnly?'controlled-pair-public-vector-check.json':'controlled-pair-repeated-throughput.json');
const report={started_utc:new Date().toISOString(),algorithm:'cn/0',node:process.version,v8:process.versions.v8,
 cpu_model:os.cpus()[0].model,image_id:process.env.EXPERIMENT_IMAGE_ID,
 script_sha256:digest(read(__filename)),host_sha256:digest(read(require.resolve('./swamped-host.cjs'))),
 manifest_sha256:digest(manifest),vector_manifest_sha256:digest(input),
 clock_for_context_initialization_ms:1700000000500,network:'disabled',workers:1,
 warmup_seconds:3,seconds_per_block:30,repetitions:3,checks:[],samples:[],
 limits:['One sampled transformation realization per method.','Other host workloads not fully controlled.',
 'Locally generated variants, not the complete published transformed corpus.']};
const check=(host)=>vectors.map(v=>{host.hash(v);return {id:v.id,matches:host.output()===v.expected};});
try{
 for(const item of spec.cases){
  const bytes=read(path.join(root,item.object));if(digest(bytes)!==item.sha256)throw Error('Digest mismatch');
  const host=load(bytes),checks=check(host);host.close();
  report.checks.push({name:item.name,sha256:item.sha256,checks});
  if(!checks.every(c=>c.matches))throw Error('Public vector mismatch');
 }
 save(out,report);
 if(!checkOnly)for(let rep=0;rep<3;rep++){
  const order=spec.cases.slice(rep).concat(spec.cases.slice(0,rep));
  for(const item of order){
   const bytes=read(path.join(root,item.object));if(digest(bytes)!==item.sha256)throw Error('Digest mismatch');
   const host=load(bytes);if(!check(host).every(c=>c.matches))throw Error('Pre-block mismatch');
   let n=0,t=performance.now();while(performance.now()-t<3000)host.hash(vectors[n++%vectors.length]);
   n=0;t=performance.now();do{host.hash(vectors[n++%vectors.length]);}while(performance.now()-t<30000);
   const elapsed=performance.now()-t,last=vectors[(n-1)%vectors.length];
   const valid=host.output()===last.expected,post=check(host);
   const row={name:item.name,sha256:item.sha256,repetition:rep+1,count:n,elapsed_ms:elapsed,
    hashes_per_second:n*1000/elapsed,final_output_matches:valid,post_block_checks:post,
    memory_layout:host.layout,host_calls:host.calls,finished_utc:new Date().toISOString()};
   host.close();report.samples.push(row);save(out,report);console.log(JSON.stringify(row));
   if(!valid||!post.every(c=>c.matches))throw Error('Measured output mismatch');
  }
 }
 report.status='complete';report.finished_utc=new Date().toISOString();save(out,report);
 console.log(JSON.stringify({status:report.status,blocks:report.samples.length,checked_modules:report.checks.length}));
}catch(e){report.status='failed';report.error=String(e.stack||e);save(out,report);console.error(report.error);process.exitCode=1;}
