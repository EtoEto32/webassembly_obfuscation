'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict'),vm=require('node:vm'),os=require('node:os');
const root=__dirname,out=path.resolve(process.argv[2]||path.join(root,'artifacts'));
if(fs.existsSync(path.join(out,'verification.json')))throw Error('Refuse overwrite verification');
const plan=JSON.parse(fs.readFileSync(path.join(root,'plan.json')));
const manifest=JSON.parse(fs.readFileSync(path.join(out,'manifest.json')));
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
assert.equal(sha(fs.readFileSync(path.join(root,'plan.json'))),manifest.plan_sha256);
// Reviewed local modules, unchanged. Resolve their two external helpers to Node builtins.
function vendor(name){
 const file=name+'.js', bytes=fs.readFileSync(path.join(root,'vendor',file));
 assert.equal(sha(bytes),manifest.vendor[file]);
 const m={exports:{}};
 vm.runInThisContext('(function(require,module,exports){'+bytes.toString()+'\n})',{filename:file})(dep=>{
  if(dep==='safe-buffer')return {Buffer};
  if(dep==='inherits')return require('node:util').inherits;
  if(dep==='./hash')return vendor('hash');
  throw Error('Unexpected dependency '+dep);
 },m,m.exports);return m.exports;
}
const Sha256=vendor('sha256');
let rng=plan.input_seed>>>0;
function random(){rng^=rng<<13;rng^=rng>>>17;rng^=rng<<5;return rng>>>0;}
function bytes(n){const b=Buffer.alloc(n);for(let i=0;i<n;i++)b[i]=random()&255;return b;}
const cases=[];
function add(id,b,known){const expected=sha(b);if(known)assert.equal(expected,known);cases.push({id,bytes:b,expected,known:!!known});}
add('empty',Buffer.alloc(0),'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855');
add('abc',Buffer.from('abc'),'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad');
add('long-known',Buffer.from('abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq'),'248d6a61d20638b8e5c026930c3e6039a33ce45964ff2167f6ecedd419db06c1');
add('million-a',Buffer.alloc(1000000,97),'cdc76e5c9914fb9281a1c7e284d73e67f1809a48a497200e046d39ccc7112cd0');
for(let n=0;n<=256;n++)add('length-'+n,bytes(n));
for(const n of [511,512,513,1023,1024,1025,4095,4096,4097,65535,65536,65537,1048575,1048576])add('boundary-'+n,bytes(n));
for(let i=0;i<256;i++)add('random-'+i,bytes(random()%8193));
for(const test of cases)assert.equal(new Sha256().update(test.bytes).digest('hex'),test.expected,'reference '+test.id);
const bundle=Buffer.concat(cases.map(x=>x.bytes));fs.writeFileSync(path.join(out,'inputs.bin'),bundle);
let offset=0;const index=cases.map(t=>{const row={id:t.id,offset,length:t.bytes.length,expected:t.expected,known:t.known};offset+=t.bytes.length;return row;});
fs.writeFileSync(path.join(out,'inputs.json'),JSON.stringify({seed:plan.input_seed,bundle_sha256:sha(bundle),cases:index},null,2));
const instances=manifest.files.map(row=>{
 const b=fs.readFileSync(path.join(out,row.file));assert.equal(sha(b),row.sha256);
 return {row,api:new WebAssembly.Instance(new WebAssembly.Module(b)).exports};
});
const observed=[];
for(const {row,api} of instances){
 const mem=new Uint8Array(api.memory.buffer);const outputs=[];
 for(const t of cases){
  mem.set(t.bytes,1024);mem.fill(0xa5,1024+t.bytes.length,Math.min(mem.length,1024+t.bytes.length+64));
  const ptr=api.hash(t.bytes.length);assert.equal(ptr,512);
  const digest=Buffer.from(mem.slice(ptr,ptr+32)).toString('hex');assert.equal(digest,t.expected,row.file+' '+t.id);
  assert.equal(sha(mem.subarray(1024,1024+t.bytes.length)),t.expected,'input changed');
  assert.ok(mem.subarray(1024+t.bytes.length,1024+t.bytes.length+64).every(v=>v===0xa5),'post-input canary');
  outputs.push({id:t.id,digest});
 }
 const rejected=[];
 for(const n of [1048577,0x7fffffff,0x80000000,0xffffffff]){
  const before=sha(mem);assert.throws(()=>api.hash(n),WebAssembly.RuntimeError);assert.equal(sha(mem),before,'trap wrote memory');rejected.push(n);
 }
 // After rejected calls, valid repeated calls must still work.
 mem.set(Buffer.from('abc'),1024);api.hash(3);assert.equal(Buffer.from(mem.slice(512,544)).toString('hex'),cases[1].expected);
 observed.push({file:row.file,checks:cases.length,mismatches:0,rejected_lengths:rejected,outputs});
}
// Mutation control shows the verifier detects a bad round constant.
const control=instances[0].api, cmem=new Uint8Array(control.memory.buffer);
cmem.set(Buffer.from('abc'),1024);const saved=cmem[768];cmem[768]^=1;control.hash(3);
const mutated=Buffer.from(cmem.slice(512,544)).toString('hex');assert.notEqual(mutated,cases[1].expected);cmem[768]=saved;
const verification={node:process.version,openssl:process.versions.openssl,v8:process.versions.v8,script_sha256:sha(fs.readFileSync(__filename)),cases_per_binary:cases.length,binary_count:instances.length,total:cases.length*instances.length,reference_checks:cases.length,mutation_control:{round_constant_detected:true,mutated_digest:mutated},results:observed};
fs.writeFileSync(path.join(out,'verification.json'),JSON.stringify(verification,null,2));
console.log(JSON.stringify({cases:cases.length,binaries:instances.length,total:verification.total,mismatches:0}));
const timings=[];
for(const n of plan.performance.lengths){
 const input=bytes(n);
 for(const {api} of instances){new Uint8Array(api.memory.buffer).set(input,1024);for(let j=0;j<plan.performance.warmup_calls;j++)api.hash(n);}
 for(let trial=0;trial<plan.budget.benchmark_trials;trial++)for(let k=0;k<instances.length;k++){
  const {row,api}=instances[(k+trial)%instances.length];
  const begin=process.hrtime.bigint();for(let j=0;j<plan.budget.benchmark_calls_per_trial;j++)api.hash(n);
  const elapsed=Number(process.hrtime.bigint()-begin);
  assert.equal(Buffer.from(new Uint8Array(api.memory.buffer,512,32)).toString('hex'),sha(input));
  timings.push({file:row.file,length:n,trial,order:k,calls:plan.budget.benchmark_calls_per_trial,ns:elapsed});
 }
}
const summaries=[];
for(const row of manifest.files)for(const length of plan.performance.lengths){
 const times=timings.filter(x=>x.file===row.file&&x.length===length).map(x=>x.ns/x.calls).sort((a,b)=>a-b);
 summaries.push({file:row.file,length,median_ns:times[4],min_ns:times[0],max_ns:times.at(-1)});
}
fs.writeFileSync(path.join(out,'performance.json'),JSON.stringify({cpu:os.cpus()[0].model,platform:process.platform,arch:process.arch,node:process.version,v8:process.versions.v8,plan_sha256:manifest.plan_sha256,raw:timings,summaries},null,2));
console.log(JSON.stringify(summaries,null,2));
