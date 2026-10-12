const fs=require('node:fs'),path=require('node:path');
const {root,run,sha,wat2wasm}=require('./experiment.cjs');
const out=path.join(root,'artifacts');
const manifest=JSON.parse(fs.readFileSync(path.join(out,'variants.json')));
const MASK=0xffffffffn;
function truth(a,b,c,context){return Number((BigInt(a)+BigInt(b)+BigInt(c)+(context?BigInt(c)*BigInt(c):0n))&MASK);}
function target(a,b,c){return Number(((BigInt(a)+BigInt(b))*BigInt(c)*BigInt(c))&MASK);}
function symbolic(wat){
 const stack=[],intermediates=[];
 for(const raw of wat.split('\n')){
  const line=raw.trim();const get=/^local\.get \$p([012])/.exec(line);
  if(get){stack.push(['a','b','c'][Number(get[1])]);continue;}
  const match=/^i32\.(add|sub|mul|xor|and|or)\b/.exec(line);
  if(match){const right=stack.pop(),left=stack.pop();if(left===undefined||right===undefined)throw Error('Symbolic underflow');const t=[match[1],left,right];stack.push(t);intermediates.push(t);continue;}
  if(/^(?:local\.|i32\.|call|if|block|loop|br|select|drop)/.test(line))throw Error('Unsupported instruction '+line);
 }
 if(stack.length!==1)throw Error('Unexpected stack');return {output:stack[0],intermediates};
}
const OPS={add:(x,y)=>(x+y)>>>0,sub:(x,y)=>(x-y)>>>0,mul:(x,y)=>Math.imul(x,y)>>>0,xor:(x,y)=>(x^y)>>>0,and:(x,y)=>(x&y)>>>0,or:(x,y)=>(x|y)>>>0};
function evaldecoder(d,atoms){return d[0]==='atom'?atoms[d[1]]:d[0]==='not'?(~atoms[d[1]])>>>0:OPS[d[0]](atoms[d[1]],atoms[d[2]]);}
async function main(){
 if(fs.existsSync(path.join(out,'results.json')))throw Error('Refuse overwrite results');
 const inputs=[],keys=new Set();function push(a,b,c){const key=[a,b,c].join(',');if(!keys.has(key)){keys.add(key);inputs.push([a,b,c]);}}
 for(let a=0;a<8;a++)for(let b=0;b<8;b++)for(let c=0;c<8;c++)push(a,b,c);
 const trainingCount=inputs.length,bounds=[0,1,7,8,0x7fffffff,0x80000000,0xfffffffe,0xffffffff];
 for(const a of bounds)for(const b of bounds)for(const c of bounds)push(a,b,c);
 let state=0x4f425357;function rand(){state^=state<<13;state^=state>>>17;state^=state<<5;return state>>>0;}
 for(let i=0;i<512;i++)push(rand(),rand(),rand());
 fs.writeFileSync(path.join(out,'inputs.json'),JSON.stringify({seed:0x4f425357,trainingCount,inputs}));
 const results=[];
 for(const variant of manifest.variants){
  const wat=fs.readFileSync(variant.dis,'utf8').replace(/\r\n/g,'\n');const sym=symbolic(wat);
  const transformed=wat.replace(/\n  \(func \$eval/, '\n  (import "trace" "value" (func $trace (param i32) (result i32)))\n  (func $eval').replace(/\bi32\.(add|sub|mul|xor|and|or)\b/g,match=>match+'\n    call $trace');
  const instWat=path.join(out,variant.name+'.observed.wat'),instWasm=path.join(out,variant.name+'.observed.wasm');fs.writeFileSync(instWat,transformed);run(wat2wasm,[instWat,'-o',instWasm]);
  let trace=[];
  const observed=(await WebAssembly.instantiate(fs.readFileSync(instWasm),{trace:{value:v=>{trace.push(v>>>0);return v;}}})).instance.exports.eval;
  const plain=(await WebAssembly.instantiate(fs.readFileSync(variant.binary))).instance.exports.eval;
  const records=[];let failures=0;
  for(const args of inputs){trace=[];const actual=observed(...args)>>>0,unobserved=plain(...args)>>>0,expected=truth(...args,variant.context);if(actual!==expected||unobserved!==expected)failures++;if(trace.length!==sym.intermediates.length)throw Error('Trace length mismatch');records.push({args,actual,unobserved,expected,target:target(...args),atoms:[...args,0,1,...trace]});}
  const candidates=[],n=records[0].atoms.length;
  for(let i=0;i<n;i++){candidates.push(['atom',i],['not',i]);for(let j=0;j<n;j++)for(const op of Object.keys(OPS))candidates.push([op,i,j]);}
  const fits=candidates.filter(d=>records.slice(0,trainingCount).every(r=>evaldecoder(d,r.atoms)===r.target));
  const verified=fits.map(d=>({decoder:d,heldoutFailures:records.slice(trainingCount).filter(r=>evaldecoder(d,r.atoms)!==r.target).length}));
  fs.writeFileSync(path.join(out,variant.name+'.observations.json'),JSON.stringify(records));
  results.push({...variant,arithmeticInstructions:sym.intermediates.length,observedSha256:sha(instWasm),tests:inputs.length,failures,atomExpressions:['a','b','c',0,1,...sym.intermediates],outputExpression:sym.output,decoderCandidates:candidates.length,trainingFits:fits.length,verified});
 }
 const report={versions:manifest.versions,trainingCount,heldoutCount:inputs.length-trainingCount,results,limitations:['Post-Binaryen instrumentation changes the JIT input; native JIT traces are not measured.','Fixed-position arithmetic values and one-operation decoder only.','The target is an illustrative expression, not a demonstrated indispensable program secret.']};
 fs.writeFileSync(path.join(out,'results.json'),JSON.stringify(report,null,2));
 console.log(JSON.stringify({trainingCount,heldoutCount:report.heldoutCount,results:results.map(r=>({name:r.name,bytes:r.bytes,sha:r.sha256,tests:r.tests,failures:r.failures,trainingFits:r.trainingFits,heldoutFailures:r.verified.map(x=>x.heldoutFailures)}))}));
 if(results.some(r=>r.failures))throw Error('Semantic mismatch');
}
main().catch(e=>{console.error(e);process.exitCode=1;});
