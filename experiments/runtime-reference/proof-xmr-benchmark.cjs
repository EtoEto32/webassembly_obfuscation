/* Recorded public vectors; reviewed xmr-wasm wrapper, no demo main or network. */
'use strict';
const path=require('path'),os=require('os');
const {read,save,digest,load}=require('./proof-glue-controls.cjs');
async function main(){
 const root=process.argv[2],out=process.argv[3];
 const manifest=read(path.join(root,'results/runtime-mining/cross-dataset/proof-of-theft/glue-control-input.json'));
 const spec=JSON.parse(manifest),vectors=spec.vectors.filter(v=>Buffer.from(v.hex,'hex')[0]<7);
 const modules=spec.modules.filter(m=>m.family==='xmr-wasm');
 const report={started_utc:new Date().toISOString(),node:process.version,v8:process.versions.v8,
  image_id:process.env.EXPERIMENT_IMAGE_ID,cpu_model:os.cpus()[0].model,algorithm:'cn/0',
  runtime:'Original generated glue; synchronous single worker; network disabled',
  script_sha256:digest(read(__filename)),host_loader_sha256:digest(read(require.resolve('./proof-glue-controls.cjs'))),
  manifest_sha256:digest(manifest),seconds_per_block:30,warmup_seconds:3,repetitions:3,
  reference_url:spec.reference_url,reference_sha256:spec.reference_sha256,samples:[],
  limitations:['Node.js, not browser pool runtime.','Distributed build settings are recorded, not freshly controlled.',
  'Other host workloads are not fully controlled.','Public wrapper uses a maximum target; confirm nonce unchanged in checked outputs.']};
 for(let rep=0;rep<3;rep++){
  const order=modules.slice(rep).concat(modules.slice(0,rep));
  for(const item of order){
   const wasm=read(path.join(root,item.object)),glue=read(path.join(root,item.glue));
   if(digest(wasm)!==item.sha256||digest(glue)!==item.glue_sha256)throw Error('Digest mismatch');
   const host=await load(glue.toString('utf8'),wasm),m=host.Module;
   const ptr=host.context._malloc(4096);m._allocate_state();
   const hash=v=>{const b=Buffer.from(v.hex,'hex');m.HEAPU8.set(b,ptr);return m._hash(ptr,b.length,-1,-1,0);};
   for(const v of vectors){const q=hash(v);if(Buffer.from(m.HEAPU8.buffer,q,32).toString('hex')!==v.expected)throw Error('Reference mismatch');}
   let n=0,t=performance.now();while(performance.now()-t<3000)hash(vectors[n++%vectors.length]);
   n=0;const start=performance.now();let q;
   do{q=hash(vectors[n++%vectors.length]);}while(performance.now()-start<30000);
   const elapsed=performance.now()-start,last=vectors[(n-1)%vectors.length];
   const valid=Buffer.from(m.HEAPU8.buffer,q,32).toString('hex')===last.expected;
   const nonce=Buffer.from(m.HEAPU8.buffer,ptr+39,4).equals(Buffer.from(last.hex,'hex').subarray(39,43));
   report.samples.push({method:item.method,sha256:item.sha256,glue_sha256:item.glue_sha256,
    repetition:rep+1,count:n,elapsed_ms:elapsed,hashes_per_second:n*1000/elapsed,
    final_output_matches:valid,final_nonce_unchanged:nonce,finished_utc:new Date().toISOString()});
   save(out,report);console.log(JSON.stringify(report.samples.at(-1)));
   m._free_state();if(!valid||!nonce)throw Error('Measured output mismatch');
  }
 }
 report.finished_utc=new Date().toISOString();save(out,report);
}
main().catch(e=>{console.error(e);process.exitCode=1;});
