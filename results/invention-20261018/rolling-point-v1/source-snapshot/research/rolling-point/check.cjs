'use strict';
const fs = require('fs');
const path = require('path');
const assert = require('assert/strict');
const crypto = require('crypto');
const os = require('os');
const dir = path.resolve(process.argv[2]);
const manifest = JSON.parse(fs.readFileSync(path.join(dir, 'manifest.json')));
const p = BigInt(manifest.prime_hex), R = 1n << 2048n;
const mod = (x, n) => (x % n + n) % n;
function pow(a, b, n) {let r=1n;for(;b;b>>=1n,a=a*a%n)if(b&1n)r=r*a%n;return r;}
const ri=pow(R%p,p-2n,p);
let state=0x18442739;
function rnd(){state^=state<<13;state^=state>>>17;state^=state<<5;return state>>>0;}
function bytes(n){return Buffer.from(Array.from({length:n},()=>rnd()&255));}
function big(n=256){return BigInt('0x'+bytes(n).toString('hex'));}
function put(mem,off,x){for(let i=0;i<256;i++,x>>=8n)mem[off+i]=Number(x&255n);}
function get(mem,off){let x=0n;for(let i=255;i>=0;i--)x=(x<<8n)|BigInt(mem[off+i]);return x;}
async function main(){
 const audit = await WebAssembly.instantiate(fs.readFileSync(path.join(dir,'arithmetic-audit.wasm')));
 const work=new Uint8Array(audit.instance.exports.work.buffer);
 const at=manifest.audit_layout.h;
 // Keep arithmetic inputs outside the constant/table region and scratch.
 const aa=140000,bb=140256,cc=140512;
 const extremes=[0n,1n,2n,p-1n,p-2n,1n<<1024n,(1n<<2016n)-1n];
 let arithmetic=0;
 const pairs=[];for(const a of extremes)for(const b of extremes)pairs.push([a,b]);
 for(let i=0;i<600;i++)pairs.push([big()%p,big()%p]);
 for(const [a,b] of pairs){
  for(const output of [cc,aa,bb]){
   put(work,aa,a);put(work,bb,b);audit.instance.exports.mont(aa,bb,output);
   assert.equal(get(work,output),a*b*ri%p);arithmetic++;
  }
 }
 const checks=[];let calls=0,traps=0;
 for(const e of manifest.entries){
  const buf=fs.readFileSync(path.join(dir,e.file));
  assert.equal(crypto.createHash('sha256').update(buf).digest('hex'),e.sha256);
  assert.equal(WebAssembly.validate(buf),true);
  const {instance}=await WebAssembly.instantiate(buf);
  assert.equal(instance.exports.memory.buffer.byteLength,65536);assert.equal(instance.exports.memory.grow(0),1);
  // grow(0) can detach the previous ArrayBuffer even when its size is unchanged.
  const mem=new Uint8Array(instance.exports.memory.buffer);
  assert.deepEqual(Object.keys(instance.exports).sort(),['memory','run']);
  const pattern=Buffer.from(JSON.parse(fs.readFileSync(path.join(dir,`l${e.length}-truth.json`))).pattern,'hex');
  const inputs=[Buffer.alloc(0),bytes(e.length-1),pattern,bytes(e.length),Buffer.alloc(e.length+2),Buffer.alloc(e.length+2,255)];
  for(const offset of [1,3,8]) inputs.push(Buffer.concat([bytes(offset),pattern,bytes(3)]));
  for(const j of [0,e.length>>1,e.length-1]){const x=Buffer.from(pattern);x[j]^=1;inputs.push(x);}
  for(let j=0;j<5;j++)inputs.push(bytes(e.length+(rnd()%5)));
  // Every case is re-run on the same instance to catch stale private state.
  let total=0;
  for(const text of inputs){
   for(const ptr of [0,65536-text.length]){
    mem.fill(0xa5);mem.set(text,ptr);const before=Buffer.from(mem);
    const expected=text.indexOf(pattern);
    assert.equal(instance.exports.run(ptr,text.length),expected,e.file);
    assert.equal(instance.exports.run(ptr,text.length),expected,e.file+' repeated');
    assert.deepEqual(Buffer.from(mem),before,e.file+' memory');
    calls+=2;total+=2;
   }
  }
  for(const [ptr,len,trap] of [[65536,0,false],[65537,0,true],[65535,2,true],[-1,1,true],[0,-1,true],[-1,-1,true]]){
   const before=Buffer.from(mem);
   if(trap){assert.throws(()=>instance.exports.run(ptr,len),x=>x instanceof WebAssembly.RuntimeError && /memory access out of bounds/i.test(x.message));traps++;}
   else assert.equal(instance.exports.run(ptr,len),-1);
   assert.deepEqual(Buffer.from(mem),before);calls++;total++;
  }
  checks.push({file:e.file,calls:total,status:'passed'});
 }
 const result={arithmetic_comparisons:arithmetic,wasm_calls:calls,memory_traps:traps,mismatches:0,checks,
  environment:{node:process.version,v8:process.versions.v8,platform:os.platform(),release:os.release(),arch:os.arch(),cpu:os.cpus()[0].model}};
 fs.writeFileSync(path.join(dir,'checks.json'),JSON.stringify(result,null,2));
 console.log(JSON.stringify({arithmetic,calls,traps,mismatches:0}));
}
main().catch(e=>{console.error(e);process.exitCode=1;});
