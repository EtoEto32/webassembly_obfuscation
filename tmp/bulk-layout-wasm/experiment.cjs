'use strict';
const fs=require('node:fs'),path=require('node:path'),cp=require('node:child_process'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const root=process.env.WASM_TOOLS_ROOT || 'C:/Users/ettotto/Documents/webassembly_obfuscation/.tools';
const asm=path.join(root,'wabt-1.0.42/bin/wat2wasm.exe'),opt=path.join(root,'binaryen-version_133/bin/wasm-opt.exe');
const out=path.join(__dirname,'artifacts');fs.mkdirSync(out,{recursive:true});
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const addr=x=>`(i32.xor ${x} (i32.const 23040))`;
const bounds=`(if (i32.or (i64.gt_u (i64.add (i64.extend_i32_u (local.get $s)) (i64.extend_i32_u (local.get $n))) (i64.const 65536)) (i64.gt_u (i64.add (i64.extend_i32_u (local.get $d)) (i64.extend_i32_u (local.get $n))) (i64.const 65536))) (then unreachable)) (if (i32.eqz (local.get $n)) (then return))`;
const loop=`(if (i32.gt_u (local.get $d) (local.get $s))
 (then (local.set $i (local.get $n)) (loop $back
  (local.set $i (i32.sub (local.get $i) (i32.const 1)))
  (i32.store8 ${addr('(i32.add (local.get $d) (local.get $i))')} (i32.load8_u ${addr('(i32.add (local.get $s) (local.get $i))')}))
  (br_if $back (local.get $i))))
 (else (loop $forward
  (i32.store8 ${addr('(i32.add (local.get $d) (local.get $i))')} (i32.load8_u ${addr('(i32.add (local.get $s) (local.get $i))')}))
  (local.set $i (i32.add (local.get $i) (i32.const 1)))
  (br_if $forward (i32.lt_u (local.get $i) (local.get $n))))))`;
const fast=`(if (i32.and (i32.le_u (i32.add (i32.and (local.get $s) (i32.const 255)) (local.get $n)) (i32.const 256)) (i32.le_u (i32.add (i32.and (local.get $d) (i32.const 255)) (local.get $n)) (i32.const 256))) (then (memory.copy ${addr('(local.get $d)')} ${addr('(local.get $s)')} (local.get $n)) return))`;
const variants=['plain','mapped-loop','mapped-bulk'];const manifest=[];
for(const kind of variants){
 const body=kind==='plain'?'(memory.copy (local.get $d) (local.get $s) (local.get $n))':bounds+(kind==='mapped-bulk'?fast:'')+loop;
 const wat=`(module (memory (export "memory") 1 1)
 (func $copy (export "copy") (param $d i32) (param $s i32) (param $n i32) (local $i i32) ${body})
 (func (export "batch") (param $count i32) (param $d i32) (param $s i32) (param $n i32)
 (block $done (loop $again (br_if $done (i32.eqz (local.get $count)))
 (call $copy (local.get $d) (local.get $s) (local.get $n))
 (local.set $count (i32.sub (local.get $count) (i32.const 1))) (br $again)))))`;
 fs.writeFileSync(path.join(out,kind+'.wat'),wat);
 cp.execFileSync(asm,[path.join(out,kind+'.wat'),'-o',path.join(out,kind+'-raw.wasm')]);
 cp.execFileSync(opt,[path.join(out,kind+'-raw.wasm'),'-O2','--enable-bulk-memory','-o',path.join(out,kind+'-O2.wasm')]);
 for(const mode of ['raw','O2']){const file=kind+'-'+mode+'.wasm',bytes=fs.readFileSync(path.join(out,file));manifest.push({file,kind,mode,bytes:bytes.length,sha256:sha(bytes)});}
}
const points=[0,1,2,127,128,254,255,256,257,511,512,65279,65280,65534,65535,65536,65537,0x7fffffff,0xffffffff];
const cases=[];
for(const s of points)for(const n of [0,1,2,255,256,257,65536,0xffffffff]){cases.push({d:s,s,n});cases.push({d:(s+1)>>>0,s,n});cases.push({d:0,s,n});}
let seed=0x516abcd1;const rng=()=>{seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed>>>0;};
for(let i=0;i<128;i++)cases.push({s:rng()%65537,d:rng()%65537,n:rng()%513});
const unique=[...new Map(cases.map(c=>[JSON.stringify(c),c])).values()];
const initial=Buffer.alloc(65536);for(let i=0;i<initial.length;i++)initial[i]=rng()&255;
const encoded=Buffer.alloc(65536);for(let i=0;i<65536;i++)encoded[i^23040]=initial[i];
fs.writeFileSync(path.join(out,'initial.bin'),initial);fs.writeFileSync(path.join(out,'inputs.json'),JSON.stringify(unique));
const results=[];const instances=[];
for(const row of manifest){
 const m=new WebAssembly.Module(fs.readFileSync(path.join(out,row.file)));assert.deepEqual(WebAssembly.Module.imports(m),[]);
 const exp=new WebAssembly.Instance(m,{}).exports,mem=Buffer.from(exp.memory.buffer),mapped=row.kind!=='plain';
 instances.push({...row,exp,mem,mapped});
 for(const c of unique){
  mem.set(mapped?encoded:initial);const expected=Buffer.from(initial);
  const trap=BigInt(c.s)+BigInt(c.n)>65536n||BigInt(c.d)+BigInt(c.n)>65536n;
  if(!trap)expected.set(initial.subarray(c.s,c.s+c.n),c.d);
  let trapped=false;try{exp.copy(c.d,c.s,c.n);}catch(e){if(!(e instanceof WebAssembly.RuntimeError))throw e;trapped=true;}
  const decoded=mapped?Buffer.from(Array.from({length:65536},(_,i)=>mem[i^23040])):Buffer.from(mem);
  const same=expected.equals(decoded);results.push({file:row.file,...c,expected_trap:trap,trapped,memory_equal:same,memory_sha256:sha(decoded)});
  assert.equal(trapped,trap);assert(same,JSON.stringify({file:row.file,...c}));
 }
}
// Exploratory repeated timing; memory is reset outside the timed region.
const timings=[];const workloads=[{name:'inside-block',s:0,d:512,n:128},{name:'cross-block',s:128,d:1024,n:512},{name:'overlap',s:0,d:1,n:128}];
for(const w of workloads){for(const i of instances){i.mem.set(i.mapped?encoded:initial);for(let k=0;k<12;k++)i.exp.batch(4096,w.d,w.s,w.n);}
 for(let round=0;round<7;round++){const order=instances.slice();for(let k=order.length-1;k>0;k--){const j=rng()%(k+1);[order[k],order[j]]=[order[j],order[k]];}
  for(const i of order){i.mem.set(i.mapped?encoded:initial);const t=process.hrtime.bigint();i.exp.batch(16384,w.d,w.s,w.n);const ms=Number(process.hrtime.bigint()-t)/1e6;timings.push({file:i.file,workload:w.name,round,count:16384,ms});}
 }
}
const meta={node:process.version,v8:process.versions.v8,seed:'0x516abcd1',tool_versions:{asm:cp.execFileSync(asm,['--version'],{encoding:'utf8'}).trim(),opt:cp.execFileSync(opt,['--version'],{encoding:'utf8'}).trim()},script_sha256:sha(fs.readFileSync(__filename)),manifest,inputs:unique.length,comparisons:results.length,mismatches:results.filter(r=>r.expected_trap!==r.trapped||!r.memory_equal).length,trap_cases_per_binary:unique.filter(c=>BigInt(c.s)+BigInt(c.n)>65536n||BigInt(c.d)+BigInt(c.n)>65536n).length};
for(const [name,value] of Object.entries({meta,results,timings}))fs.writeFileSync(path.join(out,name+'.json'),JSON.stringify(value,null,2));
console.log(JSON.stringify(meta,null,2));
