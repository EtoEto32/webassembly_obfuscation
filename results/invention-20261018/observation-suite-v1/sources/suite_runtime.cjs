'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),os=require('node:os'),cp=require('node:child_process');
const dir=path.resolve(process.argv[2]),command=process.argv[3]||'run';
const read=f=>JSON.parse(fs.readFileSync(path.join(dir,f),'utf8'));
const write=(f,x)=>{const p=path.join(dir,f);if(fs.existsSync(p))throw Error('Refuse overwrite '+p);fs.writeFileSync(p,JSON.stringify(x,null,2));};
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const plan=read('plan.json'),manifest=read('manifest.json');
if(sha(fs.readFileSync(path.join(dir,'plan.json')))!==manifest.planSHA256)throw Error('Plan hash');
const mask=0xffffffffn;
function ref(t,row){if(typeof t==='number')return BigInt(t)&mask;if(typeof t==='string')return BigInt(row[Number(t.slice(1))]>>>0);const a=ref(t[1],row),b=ref(t[2],row);return ({add:()=>a+b,sub:()=>a-b,mul:()=>a*b})[t[0]]()&mask;}
const nextFactory=seed=>()=>{seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed>>>0;};
async function instance(a,probe=false,observer=()=>{}){
 const file=path.join(dir,probe?a.probe:a.file),bytes=fs.readFileSync(file);
 if(!probe&&sha(bytes)!==a.sha256)throw Error('Artifact hash '+a.id);
 return (await WebAssembly.instantiate(bytes,probe?{probe:{observe:(id,x)=>{observer(id,x);return x;}}}:{})).instance.exports;
}
function apply(op,x,y){switch(op){case'add':return (x+y)|0;case'sub':return (x-y)|0;case'mul':return Math.imul(x,y);case'xor':return x^y;case'and':return x&y;case'or':return x|y;}}
async function run(){
 const random=nextFactory(plan.seed),inputs=[];
 const boundary=[0,1,2,0x7fffffff,0x80000000,0xffffffff];
 for(const a of boundary)for(const b of boundary)for(const c of boundary)inputs.push([a,b,c]);
 for(let i=0;i<plan.correctness_random;i++)inputs.push([random(),random(),random()]);
 write('correctness-inputs.json',inputs);
 const train=Array.from({length:plan.training},()=>[random(),random(),random()]);
 const holdout=Array.from({length:plan.holdout},()=>[random(),random(),random()]);
 const attackInputs=[...train,...holdout];write('attack-inputs.json',{training:plan.training,inputs:attackInputs});
 const initial=Buffer.alloc(65536);for(let i=0;i<65536;i++)initial[i]=random()&255;
 fs.writeFileSync(path.join(dir,'initial-memory.bin'),initial);
 const rows=[];
 for(const name of Object.keys(plan.programs)){
  const artifacts=manifest.artifacts.filter(a=>a.program===name),runtimes=[];
  for(const a of artifacts){
   const e=await instance(a),trace=[];const pe=await instance(a,true,(id,x)=>trace.push([id,x]));
   let runBad=0,probeBad=0,memoryBad=0,traps=0;const failures=[];
   for(let i=0;i<inputs.length;i++){
    const input=inputs[i],expect=Number(BigInt.asIntN(32,ref(plan.programs[name],input)));
    if(e.run(...input)!==expect)runBad++;
    trace.length=0;if(pe.run(...input)!==expect)probeBad++;
    // Independent reference for writes and traps; preserve all 64KiB bytes.
    const addresses=[0,1,15,16,17,65532,65533,65535,65536,0xffffffff];
    const p=i<addresses.length?addresses[i]:(i%2?input[0]:input[0]%65536);
    new Uint8Array(e.memory.buffer).set(initial);const expectedMemory=Buffer.from(initial);expectedMemory.writeUInt32LE(p>>>0,16);
    const expectTrap=(p>>>0)>65532;let got=null,trap=false;
    try{got=e.checked(p,...input);}catch(err){if(!(err instanceof WebAssembly.RuntimeError))throw err;trap=/memory access out of bounds/.test(err.message);if(!trap)throw err;}
    if(trap)traps++;
    const expectValue=expectTrap?null:(expect+expectedMemory.readInt32LE(p>>>0))|0;
    if(trap!==expectTrap||got!==expectValue||!Buffer.from(e.memory.buffer).equals(expectedMemory)){
     memoryBad++;if(failures.length<3)failures.push({input,p,got,expectValue,trap,expectTrap});
    }
   }
   // Probe inputs differ from correctness inputs. Positional identity is fixed.
   const sampleRows=[];
   for(const input of attackInputs){trace.length=0;const output=pe.run(...input);sampleRows.push({output,trace:[...trace]});}
   const target=plan.targets[name];
   write(a.id+'-samples.json',{id:a.id,training:plan.training,inputs:attackInputs,
     targetValues:target?attackInputs.map(row=>Number(BigInt.asIntN(32,ref(target,row)))):null,rows:sampleRows});
   const row={id:a.id,checks:inputs.length,runMismatches:runBad,probeMismatches:probeBad,memoryMismatches:memoryBad,traps,failures,
     memoryBytes:e.memory.buffer.byteLength,nsPerCall:[],batchOutputs:[]};
   rows.push(row);runtimes.push({a,e,row});
  }
  const n=plan.timing.calls_per_batch;
  // Check an independent host implementation on a small batch before timing.
  for(const {e,row} of runtimes){let s=plan.seed,acc=0;for(let i=0;i<64;i++){s=(Math.imul(s,1664525)+1013904223)|0;const z=(s<<7)|(s>>>25);acc^=Number(BigInt.asIntN(32,ref(plan.programs[name],[s,s^123456789,z])));}if(e.batch(64,plan.seed)!==acc)throw Error('Batch reference mismatch '+row.id);}
  for(const {e}of runtimes)for(let j=0;j<plan.timing.warmup_batches;j++)e.batch(n,plan.seed+j);
  console.log('TIMING-BEGIN '+name);
  const order=[];
  for(let block=0;block<plan.timing.blocks;block++){
   let expected=null;const used=[];
   for(let position=0;position<runtimes.length;position++){
    const index=(block+position)%runtimes.length,{a,e,row}=runtimes[index];used.push(a.id);
    const t=performance.now(),v=e.batch(n,plan.seed+block),elapsed=performance.now()-t;
    row.nsPerCall.push(elapsed*1e6/n);row.batchOutputs.push(v);
    if(expected===null)expected=v;else if(expected!==v)throw Error('Timed batch differs');
   }order.push(used);
  }
  console.log('TIMING-END '+name);
  write(name+'/timing-order.json',order);
  console.log('verified and timed '+name);
 }
 const meta={node:process.version,v8:process.versions.v8,execArgv:process.execArgv,cpu:os.cpus()[0].model,platform:process.platform,
   resourceUsage:process.resourceUsage(),memoryUsage:process.memoryUsage(),rows,
   notes:['Measurements are exploratory on one host; no CPU isolation.',
    'Each 15-block Latin cycle puts each of 15 variants in each order position once.',
    'Instrumentation follows Binaryen optimization and covers run only; JIT may optimize probe and normal code differently.',
    'Aggregate process memory is not per-variant memory; separate fresh processes are measured by the memory command.']};
 write('runtime.json',meta);
 if(rows.some(r=>r.runMismatches+r.probeMismatches+r.memoryMismatches))throw Error('Correctness mismatch; see runtime.json');
}
function fingerprint(v,n){return v.slice(0,n).join(',');}
function attack(s){
 if(!s.targetValues)return {status:'no_target'};
 const train=s.training,N=s.inputs.length,target=s.targetValues,bank=[],seen=new Set();let attempts=0;
 const add=(values,term)=>{const k=fingerprint(values,train);if(!seen.has(k)){seen.add(k);bank.push({values,term});}};
 for(let j=0;j<3;j++)add(s.inputs.map(x=>x[j]|0),['input',j]);
 for(const c of [0,1])add(Array(N).fill(c),['const',c]);
 const ids=s.rows[0].trace.map(x=>x[0]);
 for(let i=0;i<s.rows.length;i++)if(s.rows[i].trace.length!==ids.length||s.rows[i].trace.some((x,j)=>x[0]!==ids[j]))return {status:'unsupported_dynamic_trace'};
 for(let j=0;j<ids.length;j++)add(s.rows.map(r=>r.trace[j][1]),['event',ids[j]]);
 add(s.rows.map(r=>r.output),['output']);
 const match=values=>values.every((v,i)=>v===target[i]);
 for(const a of bank)if(match(a.values))return {status:'sample_validated',cost:0,term:a.term,attempts,atoms:bank.length};
 const one=[],seenOne=new Set();let falseCandidates=0;
 function candidate(op,a,b,cost){
  attempts++;if(attempts>plan.attack.max_attempts)return {status:'budget',attempts};
  const values=[];for(let i=0;i<train;i++)values.push(apply(op,a.values[i],b.values[i]));
  let targetTraining=true;for(let i=0;i<train;i++)if(values[i]!==target[i]){targetTraining=false;break;}
  if(targetTraining){for(let i=train;i<N;i++)values.push(apply(op,a.values[i],b.values[i]));if(match(values))return {status:'sample_validated',cost,term:[op,a.term,b.term],attempts,atoms:bank.length,falseCandidates};falseCandidates++;}
  if(cost===1){const k=fingerprint(values,train);if(!seen.has(k)&&!seenOne.has(k)){seenOne.add(k);for(let i=values.length;i<N;i++)values.push(apply(op,a.values[i],b.values[i]));one.push({values,term:[op,a.term,b.term]});}}
  return null;
 }
 for(const a of bank)for(const b of bank)for(const op of plan.attack.operations){const r=candidate(op,a,b,1);if(r)return r;}
 for(const a of one)for(const b of bank)for(const op of plan.attack.operations){let r=candidate(op,a,b,2);if(r)return r;r=candidate(op,b,a,2);if(r)return r;}
 return {status:'not_found_within_budget',attempts,atoms:bank.length,one:one.length,falseCandidates};
}
function attacks(){const results=[];for(const a of manifest.artifacts){const s=read(a.id+'-samples.json'),t=performance.now(),r=attack(s);results.push({id:a.id,...r,milliseconds:performance.now()-t});console.log(a.id+' '+r.status+' '+r.cost);}write('attacks.json',{training:plan.training,holdout:plan.holdout,results,limits:'Target-value oracle supplied; training-signature pruning can discard hypotheses. Failure is not a lower bound. All successes need independent symbolic verification.'});}
async function memoryWorker(){const a=manifest.artifacts.find(a=>a.id===process.argv[4]);if(!a)throw Error('Missing ID');const before=process.memoryUsage();const e=await instance(a);for(let i=0;i<12;i++)e.batch(plan.timing.calls_per_batch,plan.seed+i);console.log(JSON.stringify({id:a.id,before,after:process.memoryUsage(),resourceUsage:process.resourceUsage(),linearMemory:e.memory.buffer.byteLength}));}
function memories(){const result=[];for(const a of manifest.artifacts){const stdout=cp.execFileSync(process.execPath,['--no-liftoff','--no-wasm-tier-up','--no-wasm-lazy-compilation',__filename,dir,'memory-worker',a.id],{encoding:'utf8',timeout:30000});result.push(JSON.parse(stdout));}write('memory.json',{unitMaxRSS:'KiB (Node process.resourceUsage)',result,note:'One fresh process per artifact; whole-process peak includes Node/compiler startup, not just Wasm. Sequential single trials.'});}
if(command==='run')run().catch(e=>{console.error(e);process.exitCode=1;});else if(command==='attack')attacks();else if(command==='memory')memories();else if(command==='memory-worker')memoryWorker().catch(e=>{console.error(e);process.exitCode=1;});else throw Error('command');
