'use strict';
const fs=require('fs'),path=require('path'),os=require('os');
const root=path.resolve(process.argv[2]);
const mode=process.argv[3]||'check';
let seed=20261018;
function rnd(){seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed>>>0;}
const bounds=[0,1,-1,-2147483648,2147483647,0x55555555,0xaaaaaaaa|0,65535,65536,65537,123456789];
const floats=[0,-0,1,-1,Number.MIN_VALUE,Number.MAX_VALUE,Infinity,-Infinity,Math.PI];
function enc(v){if(typeof v==='bigint')return {$i64:v.toString()};if(Object.is(v,-0))return {$f64:'-0'};if(!Number.isFinite(v))return {$f64:v>0?'Infinity':'-Infinity'};return v;}
function dec(v){if(v&&typeof v==='object'){if(v.$i64!==undefined)return BigInt(v.$i64);return v.$f64==='-0'?-0:Number(v.$f64);}return v;}
function cases(kernel){
  const a=[];
  if(kernel==='xorshift16')for(const x of bounds)a.push({args:[x]});
  if(kernel==='crc32word')for(const x of bounds)for(const y of bounds)a.push({args:[x,y]});
  if(kernel==='mixed4')for(let i=0;i<bounds.length;i++)for(const f of floats)a.push({args:[bounds[i],BigInt(bounds[i])*0x100000001n,f,bounds[(i+3)%bounds.length]]});
  if(kernel==='memory16'){
    for(const p of [-1,0,1,2,3,4,65520,65524,65528,65532,65533,65535,65536,0x7fffffff])
      for(const x of bounds)for(const d of [0,1,-1,2,-2,-2147483648])a.push({args:[p,x,d]});
    a.push({args:[0,-2147483648,-1],memory:'zero'});
    a.push({args:[128,42,1],memory:'data'});
  }
  for(let i=0;i<(kernel==='memory16'?1024:4096);i++){
    const x=rnd()|0,y=rnd()|0;
    if(kernel==='xorshift16')a.push({args:[x]});
    if(kernel==='crc32word')a.push({args:[x,y]});
    if(kernel==='mixed4')a.push({args:[x,BigInt.asIntN(64,(BigInt(rnd())<<32n)|BigInt(rnd())),y/8,rnd()|0]});
    if(kernel==='memory16')a.push({args:[i%5===0?rnd()|0:rnd()%65536,x,i%16===0?0:y]});
  }
  return a;
}
function xs(x,n){for(let i=0;i<n;i++){x^=x<<13;x^=x>>>17;x^=x<<5;}return x|0;}
const bits=new DataView(new ArrayBuffer(8));
function f64bits(f){bits.setFloat64(0,f,true);return bits.getBigUint64(0,true);}
const initial=Buffer.alloc(65536);for(let i=0;i<initial.length;i++)initial[i]=(i*13+7)&255;
function init(kind){if(kind==='zero')return Buffer.alloc(65536);if(kind==='data'){const b=Buffer.alloc(65536);b.write('stack-cycle',128);return b;}return Buffer.from(initial);}
function oracle(kernel,args,mem){
  if(kernel==='xorshift16')return {value:xs(args[0],16),trap:null};
  if(kernel==='crc32word'){let x=(args[0]^args[1])>>>0;for(let i=0;i<32;i++)x=((x>>>1)^((x&1)?0xedb88320:0))>>>0;return {value:x|0,trap:null};}
  if(kernel==='mixed4')return {value:args[0]^Number(BigInt.asIntN(32,BigInt.asUintN(64,args[1])^f64bits(args[2])))^xs(args[3],8),trap:null};
  let x=BigInt(args[1]|0),d=BigInt(args[2]|0);
  for(let i=0;i<16;i++){
    const p=(args[0]>>>0)+4*i;
    if(p+4>mem.length)return {trap:'bounds'};
    x=BigInt.asIntN(32,(x+BigInt(mem.readInt32LE(p)))*BigInt(2*i+3));mem.writeInt32LE(Number(x),p);
    if(i===0||i===7){if(d===0n)return {trap:'zero'};if(x===-2147483648n&&d===-1n)return {trap:'overflow'};x/=d;}
  }
  return {value:Number(x),trap:null};
}
function run(instance,args){try{return {value:instance.exports.run(...args),trap:null};}catch(e){
  if(!(e instanceof WebAssembly.RuntimeError))throw e;
  return {trap:/divide by zero/.test(e.message)?'zero':/unrepresentable/.test(e.message)?'overflow':/out of bounds/.test(e.message)?'bounds':'other:'+e.message};
}}
function instance(file){const b=fs.readFileSync(path.join(root,file));if(!WebAssembly.validate(b))throw Error('V8 rejected '+file);return new WebAssembly.Instance(new WebAssembly.Module(b));}
function equal(a,b){return a.trap===b.trap&&(a.trap!==null||a.value===b.value);}
function check(){
  const manifest=JSON.parse(fs.readFileSync(path.join(root,'manifest.json'),'utf8'));
  const inputs={};for(const k of ['xorshift16','mixed4','crc32word','memory16'])inputs[k]=cases(k);
  fs.writeFileSync(path.join(root,'inputs.json'),JSON.stringify(inputs,(k,v)=>typeof v==='bigint'?enc(v):typeof v==='number'?enc(v):v,2));
  const rows=[];let calls=0,mismatches=0;
  for(const entry of manifest){
    for(const kind of ['original','recovered']){
      const file=kind==='original'?entry.path:entry.recovered_path;if(!file)continue;
      const inst=instance(file),mem=inst.exports.memory?Buffer.from(inst.exports.memory.buffer):null;
      let bad=0,count=0;const traps={};let examples=[];
      for(const c of inputs[entry.kernel]){
        const expectedMem=mem?init(c.memory):null;if(mem)expectedMem.copy(mem);
        const expected=oracle(entry.kernel,c.args,expectedMem),actual=run(inst,c.args);
        count++;calls++;if(actual.trap)traps[actual.trap]=(traps[actual.trap]||0)+1;
        if(!equal(expected,actual)||(mem&&!mem.equals(expectedMem))){bad++;if(examples.length<3)examples.push({args:c.args.map(enc),expected,actual});}
      }
      // State persists across these calls, including after a trap.
      if(mem){
        const expectedMem=init();expectedMem.copy(mem);
        for(let i=0;i<96;i++){
          const c={args:[i%11===0?65532:(i%16)*4,(i*7919)|0,i%7===0?0:3]};
          const expected=oracle(entry.kernel,c.args,expectedMem),actual=run(inst,c.args);calls++;count++;
          if(actual.trap)traps[actual.trap]=(traps[actual.trap]||0)+1;
          if(!equal(expected,actual)||!mem.equals(expectedMem)){bad++;if(examples.length<3)examples.push({phase:'stateful',i,expected,actual});}
        }
      }
      mismatches+=bad;rows.push({kernel:entry.kernel,variant:entry.variant,opt:entry.opt,kind,file,calls:count,mismatches:bad,traps,examples});
    }
  }
  const wrong=instance('wrong-next.wasm');let detected=0;
  for(const c of inputs.xorshift16)if(!equal(oracle('xorshift16',c.args),run(wrong,c.args)))detected++;
  const report={conditions:rows.length,calls,mismatches,wrong_next:{inputs:inputs.xorshift16.length,detected},rows};
  fs.writeFileSync(path.join(root,'correctness.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify({conditions:rows.length,calls,mismatches,wrong_next_detected:detected}));
  if(mismatches||!detected||rows.length!==manifest.length*2)process.exitCode=1;
}
function performance(){
  const file=process.argv[4],kernel=process.argv[5],inst=instance(file);
  // Fixed pre-generated varying inputs, timed JS loop/argument spreading included.
  const inputs=cases(kernel).slice(-1024).map(c=>c.args);
  if(kernel==='memory16')for(let i=0;i<inputs.length;i++)inputs[i]=[(i%256)*4,inputs[i][1],3];
  let sink=0;
  for(let i=0;i<10000;i++)sink^=inst.exports.run(...inputs[i%inputs.length]);
  const samples=[];
  for(let rep=0;rep<9;rep++){
    const start=process.hrtime.bigint();
    for(let i=0;i<30000;i++)sink^=inst.exports.run(...inputs[i%inputs.length]);
    samples.push(Number(process.hrtime.bigint()-start)/30000);
  }
  const sorted=[...samples].sort((a,b)=>a-b);
  console.log(JSON.stringify({file,kernel,warmup:10000,batches:9,calls_per_batch:30000,ns:samples,median_ns:sorted[4],min_ns:sorted[0],max_ns:sorted[8],linear_memory_bytes:inst.exports.memory?.buffer.byteLength||0,max_rss_kib:process.resourceUsage().maxRSS,sink,node:process.version,v8:process.versions.v8,cpu:os.cpus()[0].model}));
}
if(mode==='check')check();else if(mode==='performance')performance();else throw Error('Unknown mode');
