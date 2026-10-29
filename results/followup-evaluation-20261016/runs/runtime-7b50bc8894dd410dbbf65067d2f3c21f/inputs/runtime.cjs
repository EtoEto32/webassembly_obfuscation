'use strict';
// Each timed block uses a fresh process; the parent preserves trace logs and raw records.
const fs=require('fs'),path=require('path'),os=require('os'),crypto=require('crypto'),cp=require('child_process');
const {performance}=require('perf_hooks');
function read(file){const fd=fs.openSync(file,'r'),chunks=[];try{for(;;){const b=Buffer.alloc(4096),n=fs.readSync(fd,b,0,b.length);if(!n)break;chunks.push(b.subarray(0,n));}}finally{fs.closeSync(fd);}return Buffer.concat(chunks);}
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const raw=read('/inputs/plan.json'),plan=JSON.parse(raw);
if(sha(raw)!==process.env.PLAN_SHA256||process.version!==plan.intended_node||process.versions.v8!==plan.intended_v8||process.platform!=='linux')throw Error('Runtime/plan mismatch');
for(const asset of plan.assets)if(sha(read('/inputs/'+asset.name))!==asset.sha256)throw Error('Asset digest mismatch');
function cgroup(){for(const file of ['/sys/fs/cgroup/cpu.stat','/sys/fs/cgroup/cpu/cpu.stat']){try{return {path:file,values:Object.fromEntries(read(file).toString().trim().split('\n').map(line=>{const [k,v]=line.split(/\s+/);return [k,Number(v)];}))};}catch{}}return null;}
function save(file,value){const data=Buffer.from(JSON.stringify(value,null,2)+'\n'),fd=fs.openSync(file+'.tmp','w');try{for(let i=0;i<data.length;)i+=fs.writeSync(fd,data,i,Math.min(4096,data.length-i));}finally{fs.closeSync(fd);}fs.renameSync(file+'.tmp',file);}
async function child(entry){
  const artifact=plan.runtime.artifacts.find(a=>a.id===entry.artifact_id),wasm=read('/inputs/'+artifact.file);
  let host,hash,output,close,nonce;
  const vectors=plan.public_vectors.filter(v=>artifact.family!=='xmr-wasm'||Buffer.from(v.hex,'hex')[0]<7);
  const initCpu=process.cpuUsage(),initStart=performance.now();
  if(artifact.family==='swamped'){
    host=require('/inputs/host-original.cjs').load(wasm);hash=v=>host.hash(v);output=()=>host.output();close=()=>host.close();nonce=()=>true;
  }else{
    host=await require('/inputs/glue-loader.cjs').load(read('/inputs/'+artifact.glue).toString('utf8'),wasm);
    const m=host.Module,ptr=host.context._malloc(4096);m._allocate_state();let q,last;
    hash=v=>{last=Buffer.from(v.hex,'hex');m.HEAPU8.set(last,ptr);q=m._hash(ptr,last.length,-1,-1,0);};
    output=()=>Buffer.from(m.HEAPU8.buffer,q,32).toString('hex');
    nonce=()=>Buffer.from(m.HEAPU8.buffer,ptr+39,4).equals(last.subarray(39,43));close=()=>m._free_state();
  }
  const initialization_ms=performance.now()-initStart,initialization_cpu_us=process.cpuUsage(initCpu);
  const check=()=>vectors.map(v=>{hash(v);const actual=output();if(actual!==v.expected||!nonce())throw Error('Expected output/nonce mismatch');return {id:v.id,actual,expected:v.expected,nonce_unchanged:nonce()};});
  try{
    const before=check();let n=0,t=performance.now();
    while(performance.now()-t<plan.runtime.warmup_seconds*1000)hash(vectors[n++%vectors.length]);
    const warmup_count=n,warmup_ms=performance.now()-t;
    const cpu0=process.cpuUsage(),stat0=cgroup(),began=new Date().toISOString();
    n=0;t=performance.now();const bins=[];let binStart=t,binCount=0,q;
    do{hash(vectors[n++%vectors.length]);const now=performance.now();if(now-binStart>=1000){bins.push({end_ms:now-t,count:n-binCount,elapsed_ms:now-binStart});binStart=now;binCount=n;}}
    while(performance.now()-t<plan.runtime.block_seconds*1000);
    const elapsed_ms=performance.now()-t,cpu=process.cpuUsage(cpu0),stat1=cgroup();
    const actual=output(),expected=vectors[(n-1)%vectors.length].expected,nonce_unchanged=nonce();
    if(actual!==expected||!nonce_unchanged)throw Error('Final measured output mismatch');
    const after=check();
    console.log('FOLLOWUP_RESULT '+JSON.stringify({...entry,sha256:artifact.sha256,family:artifact.family,
      flags:process.execArgv,initialization_ms,initialization_cpu_us,warmup_count,warmup_ms,
      count:n,elapsed_ms,hashes_per_second:n*1000/elapsed_ms,cpu_time_us:cpu,cgroup_before:stat0,cgroup_after:stat1,
      affinity_status:read('/proc/self/status').toString().split('\n').filter(l=>l.startsWith('Cpus_allowed_list:')),
      bins,started_utc:began,finished_utc:new Date().toISOString(),final_output:actual,final_expected:expected,
      final_nonce_unchanged:nonce_unchanged,pre_checks:before,post_checks:after}));
  }finally{close();}
}
async function parent(){
  const options=cp.spawnSync(process.execPath,['--v8-options'],{encoding:'utf8',timeout:10000});
  if(options.status!==0)throw Error('Cannot inspect V8 options');
  fs.writeFileSync('/outputs/v8-options.txt',options.stdout);
  for(const mode of plan.runtime.modes)for(const flag of mode.flags){const name=flag.replace(/^--no-/,'--');if(!options.stdout.includes(name))throw Error('Unsupported flag '+flag);}
  const report={status:'running',started_utc:new Date().toISOString(),node:process.version,v8:process.versions.v8,
    cpu_model:os.cpus()[0].model,plan_sha256:sha(raw),samples:[],
    scope:'Pilot of fresh-process, bracketed throughput and explicit compiler modes; not a powered equivalence study.'};
  const file='/outputs/runtime.json';save(file,report);
  try{
    for(const entry of plan.runtime.schedule){
      const mode=plan.runtime.modes.find(m=>m.id===entry.mode);
      const result=cp.spawnSync(process.execPath,[...mode.flags,'--trace-wasm-compilation-times',__filename,'--child',JSON.stringify(entry)],{encoding:'utf8',timeout:120000,maxBuffer:16*1024*1024});
      const prefix=String(entry.sequence).padStart(3,'0');fs.writeFileSync('/outputs/'+prefix+'-stdout.txt',result.stdout||'');fs.writeFileSync('/outputs/'+prefix+'-stderr.txt',result.stderr||'');
      if(result.error||result.status!==0)throw Error('Child failure '+entry.sequence+': '+String(result.error||result.stderr));
      const marker=result.stdout.split('\n').find(line=>line.startsWith('FOLLOWUP_RESULT '));if(!marker)throw Error('Missing child record');
      report.samples.push(JSON.parse(marker.slice('FOLLOWUP_RESULT '.length)));save(file,report);
      console.log(JSON.stringify({completed:report.samples.length,total:plan.runtime.schedule.length,mode:entry.mode,family:entry.family}));
    }
    report.status='complete';report.finished_utc=new Date().toISOString();save(file,report);
  }catch(error){report.status='failed';report.error=String(error.stack||error);save(file,report);throw error;}
}
(process.argv[2]==='--child'?child(JSON.parse(process.argv[3])):parent()).catch(error=>{console.error(error);process.exitCode=1;});
