'use strict';
// Exercise the owned runner using an in-memory host. No WebAssembly API is exposed.
const fs=require('fs'),path=require('path'),vm=require('vm'),crypto=require('crypto'),assert=require('assert');
const root=path.resolve(__dirname,'..');
const script=fs.readFileSync(path.join(root,'experiments/runtime-reference/countermeasure-benchmark.cjs'));
const digest=b=>crypto.createHash('sha256').update(b).digest('hex');
const hostBytes=Buffer.from('synthetic mock host; never a mining implementation');
const artifacts=[Buffer.from('inert fixture A'),Buffer.from('inert fixture B')];
const vectors=[{id:'input-a',hex:'010203'},{id:'input-b',hex:'ff00'}].map(v=>({...v,expected:digest(Buffer.from(v.hex,'hex'))}));
const extra=[{id:'extra',hex:'11223344',expected:null}];
const base={environment:{intended_node:process.version,intended_v8:process.versions.v8},
  host:{sha256:digest(hostBytes)},baseline_sha256:digest(artifacts[0]),public_vectors:vectors,
  additional_vectors:extra,artifacts:artifacts.map((b,i)=>({id:'fixture-'+i,sha256:digest(b)})),
  measurement:{warmup_seconds:.02,minimum_block_seconds:.025,
    schedule:[{artifact_id:'fixture-0',repetition:1,position:0},{artifact_id:'fixture-1',repetition:1,position:1}]}};

function exercise(options={}) {
  const plan=JSON.parse(JSON.stringify(base)),raw=Buffer.from(JSON.stringify(plan));
  const files=new Map([['/inputs/plan.json',raw],['/inputs/swamped-host.cjs',hostBytes],
    ['/inputs/runner.cjs',script],['/inputs/permission.json',Buffer.from(JSON.stringify({
      confirmed:true,plan_sha256:digest(raw),user_statement:'synthetic unit-test only; not real approval',confirmed_at:'fixture'}))]]);
  artifacts.forEach(b=>files.set('/inputs/'+digest(b)+'.wasm',b));
  if(options.corrupt) files.set('/inputs/'+digest(artifacts[1])+'.wasm',Buffer.from('corrupt'));
  if(options.invalidPermission) files.set('/inputs/permission.json',Buffer.from('{}'));
  const descriptors=new Map();let nextFd=1,clock=0,hostLoads=0,hashCalls=0,closes=0;
  const fakeFs={
    openSync(file,mode) {if(mode==='r'&&!files.has(file))throw Error('Missing fixture');
      if(mode==='w')files.set(file,Buffer.alloc(0));const fd=nextFd++;descriptors.set(fd,{file,offset:0});return fd;},
    readSync(fd,buffer,offset,length) {const d=descriptors.get(fd),data=files.get(d.file),n=Math.min(length,data.length-d.offset);
      data.copy(buffer,offset,d.offset,d.offset+n);d.offset+=n;return n;},
    writeSync(fd,buffer,offset,length) {const d=descriptors.get(fd);
      files.set(d.file,Buffer.concat([files.get(d.file),buffer.subarray(offset,offset+length)]));return length;},
    closeSync(fd) {descriptors.delete(fd);},
    renameSync(from,to) {files.set(to,files.get(from));files.delete(from);}
  };
  const fakeHost={load(bytes) {hostLoads++;let output='';
    return {layout:{mock:true},calls:{},hash(v) {hashCalls++;
      if(options.trap && bytes.equals(artifacts[1]))throw Error('synthetic trap');
      output=digest(Buffer.from(v.hex,'hex'));
      if(options.mismatch && bytes.equals(artifacts[1]))output='00'.repeat(32);
    },output(){return output;},close(){closes++;}};
  }};
  const fakeProcess={platform:'linux',version:process.version,versions:process.versions,
    argv:[options.validateOnly?'--validate-only':'--execute'],
    env:{PLAN_SHA256:digest(raw),EXPERIMENT_IMAGE_ID:'synthetic-fixture',
      PROFESSOR_PERMISSION_CONFIRMED:options.noPermission?'no':'yes'},
    exit(code){throw {fixtureExit:true,code};}};
  const context={Buffer,Date,Map,Error,process:fakeProcess,__filename:'/inputs/runner.cjs',console:{log(){}},
    require(name) {
      if(name==='fs')return fakeFs;
      if(name==='path')return path.posix;
      if(name==='crypto')return crypto;
      if(name==='os')return {cpus:()=>[{model:'synthetic CPU'}]};
      if(name==='perf_hooks')return {performance:{now(){clock+=10;return clock;}}};
      if(name==='/inputs/swamped-host.cjs')return fakeHost;
      throw Error('Unexpected require '+name);
    }};
  let error=null;
  try {vm.runInNewContext(script.toString('utf-8'),context,{timeout:1000});}
  catch(e){error=e;}
  const report=files.has('/outputs/measurement.json')?JSON.parse(files.get('/outputs/measurement.json')):null;
  assert.equal(descriptors.size,0);
  return {error,report,hostLoads,hashCalls,closes};
}
const checks=[];
let r=exercise({validateOnly:true});assert(r.error.fixtureExit&&r.error.code===0);assert.equal(r.hostLoads,0);checks.push('validate-only never loads host');
r=exercise({noPermission:true});assert.match(r.error.message,/not authorized/);assert.equal(r.hostLoads,0);checks.push('missing execution permission refuses before host');
r=exercise({invalidPermission:true});assert.match(r.error.message,/Permission evidence missing/);assert.equal(r.hostLoads,0);checks.push('invalid permission record refuses before host');
r=exercise({corrupt:true});assert.match(r.error.message,/Artifact mismatch/);assert.equal(r.hostLoads,0);checks.push('artifact mismatch refuses before host');
r=exercise();assert.equal(r.error,null);assert.equal(r.report.status,'complete');assert.equal(r.report.samples.length,2);
assert.equal(r.hostLoads,r.closes);assert.equal(r.report.additional_checks.length,4);
for(const sample of r.report.samples){assert(sample.count>0&&sample.elapsed_ms>=25);assert.equal(sample.hashes_per_second,sample.count*1000/sample.elapsed_ms);assert.equal(sample.pre_checks.length,2);assert.equal(sample.post_checks.length,2);}
checks.push('complete mock run preserves inputs, checks, count, elapsed and rates');
r=exercise({mismatch:true});assert.match(r.error.message,/Hash output mismatch/);assert.equal(r.report.status,'failed');assert.equal(r.report.samples.length,0);assert.equal(r.hostLoads,r.closes);assert.equal(r.report.failed_check.artifact_id,'fixture-1');assert.equal(r.report.failed_check.actual,'00'.repeat(32));assert.equal(r.report.failed_check.expected,digest(Buffer.from(extra[0].hex,'hex')));checks.push('wrong mock output stops before throughput and saves actual, expected and artifact context');
r=exercise({trap:true});assert.match(r.error.message,/synthetic trap/);assert.equal(r.report.status,'failed');assert.equal(r.report.samples.length,0);assert.equal(r.hostLoads,r.closes);checks.push('mock trap stops and saves partial failure');
const report={checks,runner_sha256:digest(script),test_sha256:digest(fs.readFileSync(__filename)),
  target_wasm_executed:false,webassembly_api_exposed:false,real_professor_permission_created:false,
  scope:'In-memory protocol/control-flow checks only; no real host, Wasm, runtime throughput or timeout proof.'};
fs.writeFileSync(path.join(root,'results/countermeasures/runtime-preparation/runner-mock-checks.json'),JSON.stringify(report,null,2));
console.log(JSON.stringify(report));
