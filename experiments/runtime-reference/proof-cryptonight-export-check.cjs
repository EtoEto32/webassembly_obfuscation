/* Prepared-only runner: requires confirmed permission and an isolated container.
 * One derivative per process; finite public vectors, no demo main or pool.
 */
'use strict';
const fs=require('fs'),path=require('path'),vm=require('vm'),os=require('os');
const {read,save,digest}=require('./proof-glue-controls.cjs');

function workspaceRelativePath(root,relative){
  // Manifests written on Windows may contain backslashes, even when the
  // experiment runs in Linux. Treat both separators as directory boundaries.
  if(typeof relative!=='string'||/^[\\/]/.test(relative)||/^[A-Za-z]:/.test(relative))
    throw Error('Expected a workspace-relative artifact path.');
  const parts=relative.split(/[\\/]/);
  if(parts.some(p=>!p||p==='.'||p==='..'))throw Error('Invalid artifact path component.');
  return path.join(root,...parts);
}

function requireExecutionConditions(){
  if(process.env.UNIVERSITY_HASH_EXECUTION_APPROVED!=='1')
    throw Error('Execution permission has not been confirmed; no Wasm was loaded.');
  if(process.platform!=='linux'||!fs.existsSync('/.dockerenv'))
    throw Error('An isolated Linux container is required.');
  if(typeof process.getuid!=='function'||process.getuid()===0)
    throw Error('Run as a non-root container user.');
  const external=Object.entries(os.networkInterfaces()).flatMap(([name,entries])=>
    entries.filter(e=>!e.internal).map(e=>name+':'+e.address));
  if(external.length)throw Error('Network isolation is missing: '+external.join(','));
}

async function loadOriginalGlue(glue,bytes){
  let captured;
  const logs=[],Module={noInitialRun:true,wasmBinary:bytes,
    print:x=>logs.push(String(x)),printErr:x=>logs.push(String(x)),
    instantiateWasm(imports,receive){
      const module=new WebAssembly.Module(bytes),instance=new WebAssembly.Instance(module,imports);
      captured=instance.exports;receive(instance,module);return instance.exports;
    }};
  const context=vm.createContext({Module,console,process,Buffer,require,module:{exports:{}},exports:{},
    __dirname:'/tmp',__filename:'/tmp/original-glue.js',setTimeout,clearTimeout,
    performance,TextDecoder,TextEncoder,WebAssembly});
  context.global=context;
  const listeners=process.listeners('uncaughtException');
  try{vm.runInContext(glue,context,{timeout:10000});}
  finally{for(const listener of process.listeners('uncaughtException'))
    if(!listeners.includes(listener))process.removeListener('uncaughtException',listener);}
  if(!captured||!Module.calledRun)throw Error('Original glue initialization incomplete.');
  return {exports:captured,logs};
}

async function main(){
  requireExecutionConditions(); // Before reading/instantiating glue or Wasm.
  const [root,originalSha,out,mode]=process.argv.slice(2);
  if(!root||!out||!/^[0-9a-f]{64}$/.test(originalSha||''))
    throw Error('Usage: runner ROOT ORIGINAL_SHA OUTPUT_JSON [--throughput-block]');
  if(mode!==undefined&&mode!=='--throughput-block')throw Error('Unknown execution mode.');
  if(fs.existsSync(out))throw Error('Output exists; select a fresh result path.');
  const manifestBytes=read(path.join(root,'results/runtime-mining/cross-dataset/proof-of-theft/cryptonight-export-only-manifest.json'));
  const spec=JSON.parse(manifestBytes),item=spec.modules.find(r=>r.original_sha256===originalSha);
  if(!item)throw Error('Original SHA not in the reviewed derivative manifest.');
  const vectorBytes=read(path.join(root,'results/runtime-mining/cross-dataset/proof-of-theft/glue-control-input.json'));
  const vectors=JSON.parse(vectorBytes);
  const original=read(workspaceRelativePath(root,item.original_object)),bytes=read(workspaceRelativePath(root,item.derivative_object));
  const glue=read(workspaceRelativePath(root,item.original_glue));
  if(digest(original)!==item.original_sha256||digest(bytes)!==item.derivative_sha256||digest(glue)!==item.original_glue_sha256)
    throw Error('Artifact digest mismatch.');
  const report={status:'started',started_utc:new Date().toISOString(),method:item.method,
    original_sha256:item.original_sha256,derivative_sha256:item.derivative_sha256,
    glue_sha256:item.original_glue_sha256,manifest_sha256:digest(manifestBytes),
    vector_manifest_sha256:digest(vectorBytes),reference_sha256:vectors.reference_sha256,
    reference_url:vectors.reference_url,script_sha256:digest(read(__filename)),
    file_helpers_sha256:digest(read(require.resolve('./proof-glue-controls.cjs'))),
    node:process.version,v8:process.versions.v8,image_id:process.env.EXPERIMENT_IMAGE_ID,
    algorithm:'cn/0 candidate; verify against independent outputs',results:[],
    runtime:'Original glue, noInitialRun=true, export-only derivative, one module per process, network disabled',
    limitations:['Export visibility can affect compilation; this is not the unchanged published binary.',
      'Five finite vectors do not prove all-input correctness or full source/binary equivalence.',
      'Per-call diagnostic durations are not warmed repeated throughput results.',
      'Optional throughput is one block per fresh process; three rotated rounds across matched artifacts are required for comparison.',
      'Throughput includes JavaScript input copies and loop timing, and uses the same finite public inputs repeatedly.'],
    requested_mode:mode||'public-vector-check'};
  save(out,report);
  try{
    const host=await loadOriginalGlue(glue.toString('utf8'),bytes),e=host.exports;
    report.glue_logs=host.logs;
    if(!(e.memory instanceof WebAssembly.Memory)||typeof e[item.added_export]!=='function')
      throw Error('Reviewed memory/hash interface unavailable.');
    const stackSave=e.stackSave||e.emscripten_stack_get_current;
    const stackAlloc=e.stackAlloc||e._emscripten_stack_alloc;
    const stackRestore=e.stackRestore||e._emscripten_stack_restore;
    if(!stackSave||!stackAlloc||!stackRestore)throw Error('Reviewed stack interface unavailable.');
    const saved=stackSave(),input=stackAlloc(128),output=stackAlloc(64);
    try{
      for(const vector of vectors.vectors){
        const blob=Buffer.from(vector.hex,'hex');
        if(blob.length>128||vector.variant!==0||vector.lite!==0)throw Error('Unexpected public vector domain.');
        let heap=new Uint8Array(e.memory.buffer);
        if(input<0||output<0||input+128>heap.length||output+64>heap.length)throw Error('Stack allocation outside memory.');
        heap.fill(0,input,input+128);heap.set(blob,input);heap.fill(0xa5,output,output+64);
        const start=performance.now();e[item.added_export](input,output,blob.length);
        const diagnosticElapsed=performance.now()-start;
        heap=new Uint8Array(e.memory.buffer);
        const actual=Buffer.from(heap.subarray(output,output+32)).toString('hex');
        const inputUnchanged=Buffer.from(heap.subarray(input,input+blob.length)).equals(blob);
        const guardUnchanged=heap.subarray(output+32,output+64).every(b=>b===0xa5);
        report.results.push({vector_id:vector.id,expected:vector.expected,actual,
          matches:actual===vector.expected,input_unchanged:inputUnchanged,
          output_guard_unchanged:guardUnchanged,diagnostic_elapsed_ms:diagnosticElapsed});
        save(out,report);
        if(actual!==vector.expected||!inputUnchanged||!guardUnchanged)
          throw Error('Vector output/input/guard check failed; do not benchmark this candidate.');
      }
      if(mode==='--throughput-block'){
        const prepared=vectors.vectors.map(v=>({...v,blob:Buffer.from(v.hex,'hex')}));
        const hash=index=>{
          const v=prepared[index%prepared.length];
          new Uint8Array(e.memory.buffer).set(v.blob,input);
          e[item.added_export](input,output,v.blob.length);
          return v;
        };
        // No main, nonce search, pool, or network request is used. An external
        // process timeout must bound a possible stuck synchronous Wasm call.
        let warmCount=0,warmStart=performance.now();
        do{hash(warmCount++);}while(performance.now()-warmStart<3000);
        const warmElapsed=performance.now()-warmStart;
        let count=0,last;
        const startedUtc=new Date().toISOString(),start=performance.now();
        do{last=hash(count++);}while(performance.now()-start<30000);
        const elapsed=performance.now()-start,finishedUtc=new Date().toISOString();
        const heap=new Uint8Array(e.memory.buffer);
        const actual=Buffer.from(heap.subarray(output,output+32)).toString('hex');
        const inputUnchanged=Buffer.from(heap.subarray(input,input+last.blob.length)).equals(last.blob);
        const guardUnchanged=heap.subarray(output+32,output+64).every(b=>b===0xa5);
        report.throughput_block={warmup_count:warmCount,warmup_elapsed_ms:warmElapsed,
          target_warmup_ms:3000,target_elapsed_ms:30000,count,elapsed_ms:elapsed,
          hashes_per_second:count*1000/elapsed,started_utc:startedUtc,finished_utc:finishedUtc,
          last_vector_id:last.id,expected:last.expected,actual,matches:actual===last.expected,
          input_unchanged:inputUnchanged,output_guard_unchanged:guardUnchanged};
        save(out,report);
        if(actual!==last.expected||!inputUnchanged||!guardUnchanged)
          throw Error('Timed block final output/input/guard check failed; exclude its rate.');
      }
    }finally{stackRestore(saved);}
    report.status='all five public vectors and checked guards matched';
    if(mode==='--throughput-block')report.status='public vectors and one timed block final check matched';
  }catch(error){report.status='failed';report.error=String(error.stack||error);process.exitCode=1;}
  report.finished_utc=new Date().toISOString();save(out,report);
  console.log(JSON.stringify({status:report.status,checked:report.results.length,method:item.method}));
}
if(require.main===module)main().catch(error=>{console.error(String(error));process.exitCode=1;});
module.exports={requireExecutionConditions,workspaceRelativePath};
