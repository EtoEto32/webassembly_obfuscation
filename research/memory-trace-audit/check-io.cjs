'use strict';
const fs=require('fs'),path=require('path'),crypto=require('crypto'),cp=require('child_process');
const {recoverIO}=require('./attack-io.cjs');
const input=path.resolve(process.argv[2]),out=path.resolve(process.argv[3]);
fs.mkdirSync(out,{recursive:false});
fs.mkdirSync(path.join(out,'source'));
for(const name of ['attack-io.cjs','check-io.cjs'])fs.copyFileSync(path.join(__dirname,name),path.join(out,'source',name));
const root=path.resolve(__dirname,'../..'),tools=process.env.WASM_TOOLS_ROOT||path.join(root,'.tools');
const wabt=(name,args)=>cp.execFileSync(path.join(tools,'wabt-1.0.42/bin',name+'.exe'),args,{encoding:'utf8',timeout:30000});
const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const m=JSON.parse(fs.readFileSync(path.join(input,'manifest.json')));

// Construct a fresh implementation from learned public-index relationships.
// It does not reuse the original binary, its physical addresses, or its layout.
function emitClone(r,stem){
  const data=Buffer.alloc(r.nodes*8);
  for(let i=0;i<r.nodes;i++){data.writeUInt32LE(r.next[i]+1,i*8);data.writeUInt32LE(r.values[i],i*8+4);}
  const escaped=[...data].map(x=>'\\'+x.toString(16).padStart(2,'0')).join('');
  const wat=`(module (memory 1) (data (i32.const 8) "${escaped}")
    (func (export "run") (param $start i32) (param $limit i32) (result i32)
      (local $q i32) (local $left i32) (local $acc i32)
      (if (i32.ge_u (local.get $start) (i32.const ${r.nodes})) (then unreachable))
      (local.set $q (i32.add (local.get $start) (i32.const 1)))
      (local.set $left (i32.and (local.get $limit) (i32.const 255)))
      (block $done (loop $loop
        (br_if $done (i32.eqz (local.get $q)))
        (br_if $done (i32.eqz (local.get $left)))
        (local.set $acc (i32.xor (i32.rotl (local.get $acc) (i32.const 5))
          (i32.load offset=4 (i32.shl (local.get $q) (i32.const 3)))))
        (local.set $q (i32.load (i32.shl (local.get $q) (i32.const 3))))
        (local.set $left (i32.sub (local.get $left) (i32.const 1))) (br $loop)))
      (local.get $acc)))`;
  const wp=path.join(out,stem+'-clone.wat'),bp=path.join(out,stem+'-clone.wasm');
  fs.writeFileSync(wp,wat);wabt('wat2wasm',[wp,'-o',bp]);wabt('wasm-validate',[bp]);
  return {path:bp,sha256:hash(bp),bytes:fs.statSync(bp).size};
}

const rows=[];
let failures=0,totalValidation=0;
for(const row of m.rows){
  const p=path.join(input,row.wasm);if(hash(p)!==row.sha256)throw Error('Hash mismatch');
  const oracle=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(p))).exports.run;
  const t0=process.hrtime.bigint();
  const learned=recoverIO(oracle);
  const elapsed_ns=Number(process.hrtime.bigint()-t0);
  // Attack already returned. Only now consult truth for scoring.
  const truth=m.truth[row.family];
  const expectedNext=truth.next.map(x=>x===0?-1:(x-256)/16);
  const valueCorrect=learned.values?.filter((x,i)=>x===truth.values[i]).length||0;
  const exactNext=learned.next?.filter((x,i)=>x===expectedNext[i]).length||0;
  const allCandidatesContainTruth=learned.candidates?.every((xs,i)=>xs.includes(expectedNext[i]))||false;
  const reportName=row.wasm.replace('.wasm','-io.json');
  fs.writeFileSync(path.join(out,reportName),JSON.stringify(learned,null,2));
  let clone=null,checks=0,bad=0,traps=0;
  if(learned.status==='unique'){
    clone=emitClone(learned,row.wasm.replace('.wasm',''));
    const f=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(clone.path))).exports.run;
    for(let start=0;start<truth.nodes;start++)for(let k=0;k<256;k++){
      checks++;if((oracle(start,k)>>>0)!==(f(start,k)>>>0))bad++;
    }
    for(const start of [truth.nodes,truth.nodes+1,0x7fffffff,0xffffffff])for(const k of [0,1,255,256,0xffffffff]){
      const outcome=g=>{try{return {value:g(start,k)}}catch(e){if(!(e instanceof WebAssembly.RuntimeError))throw e;return {trap:e.message}}};
      const a=outcome(oracle),b=outcome(f);checks++;if(a.trap)traps++;
      if(JSON.stringify(a)!==JSON.stringify(b))bad++;
    }
    // High limit bits are also tested rather than silently assuming wrapping.
    for(const start of [0,truth.nodes-1])for(const k of [256,257,0x7fffffff,0xffffffff]){
      checks++;if((oracle(start,k)>>>0)!==(f(start,k)>>>0))bad++;
    }
  }
  if(valueCorrect!==truth.nodes||exactNext!==truth.nodes||bad||!allCandidatesContainTruth)failures++;
  totalValidation+=checks;
  rows.push({...row,status:learned.status,nodes:learned.nodes,queries:learned.queries.length,
    max_queried_length:Math.max(...learned.queries.map(q=>q.length)),phases:learned.phases,
    value_correct:valueCorrect,successor_correct_including_null:exactNext,allCandidatesContainTruth,
    elapsed_ns,report:reportName,clone,validation_inputs:checks,validation_mismatches:bad,validation_traps:traps});
}
// Identical zero-valued nodes give the same output for many different graphs.
// The learner MUST report ambiguity; choosing any one graph is not recovery.
const zeroOracle=(i,k)=>{if((i>>>0)>=3)throw new WebAssembly.RuntimeError('unreachable');return 0;};
const zero=recoverIO(zeroOracle,{maxLength:5});
const negativeControl=zero.status==='ambiguous'&&zero.next===null&&zero.candidates.every(xs=>xs.length===4);
fs.writeFileSync(path.join(out,'ambiguous-control.json'),JSON.stringify(zero,null,2));
const result={node:process.version,v8:process.versions.v8,
  input_manifest_sha256:hash(path.join(input,'manifest.json')),
  source_sha256:Object.fromEntries(['attack-io.cjs','check-io.cjs'].map(n=>[n,hash(path.join(__dirname,n))])),
  conditions:rows.length,failed_conditions:failures,validation_inputs:totalValidation,
  validation_executions:2*totalValidation,ambiguity_control_passed:negativeControl,rows,
  scope:'Known public API contract; query-only graph recovery. No internal memory or trace supplied to learner.',
  cost_scope:'Single measurement including attack oracle calls, excluding compilation/clone checking; not a benchmark claim.'};
fs.writeFileSync(path.join(out,'results.json'),JSON.stringify(result,null,2));
console.log(JSON.stringify({conditions:rows.length,failed_conditions:failures,
  queries:[...new Set(rows.map(x=>x.queries))],validation_inputs:totalValidation,
  validation_executions:2*totalValidation,ambiguity_control_passed:negativeControl}));
if(failures||!negativeControl)process.exitCode=1;
