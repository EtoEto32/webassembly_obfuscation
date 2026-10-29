'use strict';
const fs=require('fs'),path=require('path'),os=require('os');
const {performance}=require('perf_hooks');
function evalBig(t,x) {
  if(t[0]==='v')return BigInt(x[t[1]]);
  if(t[0]==='c')return BigInt(t[1]);
  const a=evalBig(t[1],x),b=evalBig(t[2],x);
  return (t[0]==='add'?a+b:a*b)&0xffffffffn;
}
function inputs(n){
  const cases=[],boundary=[0,1,2,2047,2048,2049,65535,65536,0x7fffffff,0x80000000,0xfffffffe,0xffffffff];
  for(const a of boundary)for(const b of boundary)cases.push(Array.from({length:n},(_,i)=>i%2?a:b));
  for(let i=0;i<n;i++)for(let bit=0;bit<32;bit++){
    const x=Array(n).fill(0xffffffff);x[i]=(2**bit)>>>0;cases.push(x);
  }
  let state=(0x52454749^n)>>>0;
  const next=()=>{state^=state<<13;state^=state>>>17;state^=state<<5;return state>>>0;};
  for(let i=0;i<4096;i++)cases.push(Array.from({length:n},next));
  return cases;
}
async function check(directory){
  const build=JSON.parse(fs.readFileSync(path.join(directory,'build.json')));
  if(build.status!=='built')throw new Error('Build incomplete');
  const fixtures=JSON.parse(fs.readFileSync(path.join(directory,'fixtures.json')));
  const cases=Object.fromEntries(Object.entries(fixtures).map(([k,f])=>[k,inputs(f.n)]));
  fs.writeFileSync(path.join(directory,'inputs.json'),JSON.stringify(cases),{flag:'wx'});
  const rows=[];let calls=0;
  for(const row of build.conditions)for(const kind of ['original','recovered']){
    const file=path.join(directory,kind==='original'?'':'recovered',row.file);
    if(!fs.existsSync(file)){rows.push({...row,kind,status:'missing'});continue;}
    const bytes=fs.readFileSync(file);if(!WebAssembly.validate(bytes))throw new Error('Invalid Wasm');
    const {instance}=await WebAssembly.instantiate(bytes);let count=0;
    for(const x of cases[row.kernel].concat(cases[row.kernel].slice(0,10).reverse())){
      const expected=Number(evalBig(fixtures[row.kernel].tree,x))>>>0;
      const actual=instance.exports.run(...x)>>>0;
      if(expected!==actual)throw new Error(JSON.stringify({file,x,expected,actual}));
      calls++;count++;
    }
    rows.push({file:row.file,kind,status:'passed',calls:count});
  }
  const {instance}=await WebAssembly.instantiate(fs.readFileSync(path.join(directory,'bad-width.wasm')));
  let detected=0;
  for(const x of cases.dot8)if((instance.exports.run(...x)>>>0)!==Number(evalBig(fixtures.dot8.tree,x)))detected++;
  if(!detected)throw new Error('Bad-width control not detected');
  const result={node:process.version,v8:process.versions.v8,cpu:os.cpus()[0].model,rows,calls,mismatches:0,bad_width_mismatches:detected};
  fs.writeFileSync(path.join(directory,'correctness.json'),JSON.stringify(result,null,2),{flag:'wx'});
  console.log(JSON.stringify({conditions:rows.length,calls,mismatches:0,bad_width_mismatches:detected}));
}
async function timing(file,n){
  const {instance}=await WebAssembly.instantiate(fs.readFileSync(file));
  const x=Array.from({length:n},(_,i)=>Math.imul(0x9e3779b1,i+1)|0);let checksum=0;
  for(let i=0;i<5000;i++){x[0]=(x[0]+1)|0;checksum^=instance.exports.run(...x);}
  const samples=[];
  for(let trial=0;trial<7;trial++){
    const start=performance.now();
    for(let i=0;i<10000;i++){x[0]=(x[0]+1)|0;checksum^=instance.exports.run(...x);}
    samples.push((performance.now()-start)*1e6/10000);
  }
  console.log(JSON.stringify({samples_ns:samples,checksum,warmup:5000,calls_per_trial:10000,
    max_rss_kib:process.resourceUsage().maxRSS,node:process.version,v8:process.versions.v8,cpu:os.cpus()[0].model}));
}
(process.argv[2]==='--timing'?timing(process.argv[3],Number(process.argv[4])):check(process.argv[2])).catch(e=>{console.error(e);process.exitCode=1;});
