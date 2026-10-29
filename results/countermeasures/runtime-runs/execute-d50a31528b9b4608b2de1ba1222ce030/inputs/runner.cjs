'use strict';
// Validation exits before importing the host or constructing any Wasm module.
const fs = require('fs'), path = require('path'), crypto = require('crypto'), os = require('os');
const {performance} = require('perf_hooks');
// Fixed chunks match the existing harness and avoid Docker bind-mount bulk-read errors.
function read(file) {
  const fd=fs.openSync(file,'r'),chunks=[];
  try {
    for (;;) {
      const b=Buffer.alloc(4096),n=fs.readSync(fd,b,0,b.length,null);
      if (!n) break;
      chunks.push(b.subarray(0,n));
    }
  } finally {fs.closeSync(fd);}
  return Buffer.concat(chunks);
}
const digest = b => crypto.createHash('sha256').update(b).digest('hex');
const input = '/inputs', output = '/outputs';
const raw = read(path.join(input, 'plan.json'));
const plan = JSON.parse(raw);
if (digest(raw) !== process.env.PLAN_SHA256) throw Error('Plan digest mismatch');
if (process.platform !== 'linux' || process.version !== plan.environment.intended_node ||
    process.versions.v8 !== plan.environment.intended_v8) throw Error('Runtime mismatch');
const artifacts = new Map(plan.artifacts.map(a => [a.id, a]));
for (const a of artifacts.values()) {
  if (digest(read(path.join(input, a.sha256+'.wasm'))) !== a.sha256) throw Error('Artifact mismatch');
}
const hostFile = path.join(input, 'swamped-host.cjs');
if (digest(read(hostFile)) !== plan.host.sha256) throw Error('Host digest mismatch');
const environment = {node:process.version,v8:process.versions.v8,platform:process.platform,
  cpu_model:os.cpus()[0].model,image_id:process.env.EXPERIMENT_IMAGE_ID,
  plan_sha256:digest(raw),runner_sha256:digest(read(__filename)),host_sha256:plan.host.sha256};
if (process.argv.includes('--validate-only')) {
  console.log(JSON.stringify({...environment,status:'validated-without-wasm-execution',artifacts:artifacts.size}));
  process.exit(0);
}
if (!process.argv.includes('--execute') || process.env.PROFESSOR_PERMISSION_CONFIRMED !== 'yes')
  throw Error('Execution not authorized');
const permission = JSON.parse(read(path.join(input,'permission.json')));
if (permission.confirmed !== true || permission.plan_sha256 !== digest(raw) ||
    !permission.user_statement || !permission.confirmed_at) throw Error('Permission evidence missing');
// Only reachable after validation and the explicit execution gate.
const {load} = require(hostFile);
const report = {...environment,status:'running',started_utc:new Date().toISOString(),
  permission_sha256:digest(read(path.join(input,'permission.json'))),
  public_checks:[],additional_checks:[],samples:[],additional_oracle:'unmodified baseline differential only'};
const save = () => {
  const target=path.join(output,'measurement.json');
  const data=Buffer.from(JSON.stringify(report,null,2)),fd=fs.openSync(target+'.tmp','w');
  try {
    for (let offset=0;offset<data.length;) {
      const n=fs.writeSync(fd,data,offset,Math.min(4096,data.length-offset));
      if (!n) throw Error('Incomplete log write');
      offset+=n;
    }
  } finally {fs.closeSync(fd);}
  fs.renameSync(target+'.tmp',target);
};
const bytes = a => {
  const data=read(path.join(input,a.sha256+'.wasm'));
  if (digest(data)!==a.sha256) throw Error('Artifact changed before execution');
  return data;
};
const check = (host,vectors,expected) => vectors.map(v => {
  host.hash(v);const actual=host.output(),wanted=expected ? expected[v.id] : v.expected;
  if (actual!==wanted) {
    report.failed_check={...report.current_context,id:v.id,actual,expected:wanted};
    throw Error('Hash output mismatch: '+v.id);
  }
  return {id:v.id,actual,expected:wanted,matches:true};
});
try {
  const baseline = [...artifacts.values()].find(a=>a.sha256===plan.baseline_sha256);
  report.current_context={phase:'baseline-oracle',artifact_id:baseline.id};
  const oracleHost=load(bytes(baseline)), oracle={};
  try {
    const publicCheck=check(oracleHost,plan.public_vectors);
    for (const v of plan.additional_vectors) {oracleHost.hash(v);oracle[v.id]=oracleHost.output();}
    report.baseline_oracle={public_checks:publicCheck,additional_outputs:oracle};save();
  } finally {oracleHost.close();}
  for (const a of artifacts.values()) {
    for (const reverse of [false,true]) {
      report.current_context={phase:'public-and-additional-checks',artifact_id:a.id,reverse};
      const host=load(bytes(a));
      try {
        const pub=check(host,plan.public_vectors);
        const vectors=reverse ? [...plan.additional_vectors].reverse() : plan.additional_vectors;
        const extra=check(host,vectors,oracle);
        report.public_checks.push({artifact_id:a.id,reverse,checks:pub});
        report.additional_checks.push({artifact_id:a.id,reverse,checks:extra});save();
      } finally {host.close();}
    }
  }
  for (const entry of plan.measurement.schedule) {
    report.current_context={phase:'throughput',...entry};
    const a=artifacts.get(entry.artifact_id), host=load(bytes(a));
    try {
      const before=check(host,plan.public_vectors);
      let n=0,t=performance.now();
      while(performance.now()-t < plan.measurement.warmup_seconds*1000)
        host.hash(plan.public_vectors[n++%plan.public_vectors.length]);
      const warmupCount=n,warmupElapsed=performance.now()-t;
      n=0;const blockStarted=new Date().toISOString();t=performance.now();
      do {host.hash(plan.public_vectors[n++%plan.public_vectors.length]);}
      while(performance.now()-t < plan.measurement.minimum_block_seconds*1000);
      const elapsed=performance.now()-t,last=plan.public_vectors[(n-1)%plan.public_vectors.length];
      const actual=host.output();if(actual!==last.expected) {
        report.failed_check={...report.current_context,id:last.id,actual,expected:last.expected,count:n,elapsed_ms:elapsed};
        throw Error('Final output mismatch');
      }
      const after=check(host,plan.public_vectors);
      report.samples.push({...entry,count:n,elapsed_ms:elapsed,hashes_per_second:n*1000/elapsed,
        warmup_count:warmupCount,warmup_elapsed_ms:warmupElapsed,
        final_output:actual,final_expected:last.expected,pre_checks:before,post_checks:after,
        layout:host.layout,host_calls:host.calls,started_utc:blockStarted,finished_utc:new Date().toISOString()});
      save();console.log(JSON.stringify({completed_blocks:report.samples.length,total_blocks:plan.measurement.schedule.length}));
    } finally {host.close();}
  }
  report.status='complete';report.finished_utc=new Date().toISOString();save();
} catch (error) {
  report.status='failed';report.error=String(error.stack||error);save();throw error;
}
