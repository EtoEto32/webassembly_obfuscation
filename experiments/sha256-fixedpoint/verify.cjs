'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const out=path.resolve(process.argv[2]||path.join(__dirname,'artifacts'));
if(fs.existsSync(path.join(out,'verification.json')))throw Error('Refuse overwrite verification');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const manifest=JSON.parse(fs.readFileSync(path.join(out,'manifest.json')));
const corpus=path.join(__dirname,'../sha256-research-baseline/artifacts');
const indexBytes=fs.readFileSync(path.join(corpus,'inputs.json')),index=JSON.parse(indexBytes),bundle=fs.readFileSync(path.join(corpus,'inputs.bin'));
assert.equal(sha(indexBytes),'1d145223c7b8e865a9dfd6f1fc2fc398f2593aa1d6a994d9681e7fcb6e572514');assert.equal(sha(bundle),index.bundle_sha256);
assert.equal(sha(bundle),'1dc2bec61d8ed8c2263c33cf28c67493759b7e6ce029a518d333cc7bec8ffa23');
for(const n of [0,1,55,56,63,64,65,1048576])assert.ok(index.cases.some(t=>t.length===n));
const circuitBytes=fs.readFileSync(path.join(out,'circuit.json'));assert.equal(sha(circuitBytes),manifest.circuit_sha256);const circuit=JSON.parse(circuitBytes);
function instance(mode){const row=manifest.files.find(r=>r.mode===mode),b=fs.readFileSync(path.join(out,row.file));assert.equal(sha(b),row.sha256);return new WebAssembly.Instance(new WebAssembly.Module(b)).exports;}
const plain=instance('plain'),fixed=instance('fixedpoint'),bad=instance('bad-odd-mixing');
const rotr=(x,n)=>(x>>>n)|(x<<(32-n));
function t2(a,b,c){return ((rotr(a,2)^rotr(a,13)^rotr(a,22))+((a&b)^(a&c)^(b&c)))>>>0;}
let rng=2026101206;function random(){rng^=rng<<13;rng^=rng>>>17;rng^=rng<<5;return rng>>>0;}
const triples=[[0,0,0],[0xffffffff,0xffffffff,0xffffffff],[1,0,0],[0x80000000,1,0xffffffff]];
for(let i=0;i<32;i++)triples.push([random(),random(),random()]);
const locals=[];for(const xyz of triples){
 const actual=fixed.t2(...xyz)>>>0,expected=t2(...xyz);assert.equal(actual,expected);
 const values=xyz.flatMap(x=>Array.from({length:32},(_,i)=>(x>>>i)&1)).concat([0,1]);
 for(const g of circuit.gates){const a=values[g.a],b=values[g.b];values.push(g.op==='xor'?a^b:g.op==='and'?a&b:a|b);}
 const settled=new Uint32Array(fixed.memory.buffer,manifest.scratch.v,manifest.gates);assert.deepEqual(Array.from(settled),values.slice(98));
 locals.push({input:xyz,expected,actual,all_coordinates_equal_boolean_reference:true});
}
const rows=[],rejections=[];
for(const test of index.cases){
 const input=bundle.subarray(test.offset,test.offset+test.length),expected=sha(input);assert.equal(expected,test.expected);
 const digests={};for(const [mode,api] of [['plain',plain],['fixedpoint',fixed]]){
  const mem=new Uint8Array(api.memory.buffer);mem.set(input,1024);mem.fill(0xa5,1024+input.length,1024+input.length+64);
  const before=api.evaluations?.value;const ptr=api.hash(input.length);assert.equal(ptr,512);
  const digest=Buffer.from(mem.slice(ptr,ptr+32)).toString('hex');assert.equal(digest,expected,mode+' '+test.id);digests[mode]=digest;
  assert.equal(sha(mem.subarray(1024,1024+input.length)),expected,'input mutation');assert.ok(mem.subarray(1024+input.length,1024+input.length+64).every(x=>x===0xa5));
  if(mode==='fixedpoint'){
   assert.equal(api.evaluations.value-before,1,'transformed T2 must execute exactly once');
   assert.ok(new Uint32Array(api.memory.buffer,manifest.scratch.v,manifest.gates).every(x=>x===0||x===1),'unsettled coordinate');
  }
 }
 rows.push({id:test.id,length:test.length,expected,...digests});
}
for(const [mode,api] of [['plain',plain],['fixedpoint',fixed]]){
 const mem=new Uint8Array(api.memory.buffer);for(const n of [1048577,0x7fffffff,0x80000000,0xffffffff]){
  const before=sha(mem),calls=api.evaluations?.value;assert.throws(()=>api.hash(n),WebAssembly.RuntimeError);assert.equal(sha(mem),before);assert.equal(api.evaluations?.value,calls);rejections.push({mode,length:n});
 }
 mem.set(Buffer.from('abc'),1024);api.hash(3);assert.equal(Buffer.from(mem.slice(512,544)).toString('hex'),sha(Buffer.from('abc')));
}
const mutation=[];for(const text of ['', 'abc']){const b=Buffer.from(text),mem=new Uint8Array(bad.memory.buffer);mem.set(b,1024);bad.hash(b.length);const actual=Buffer.from(mem.slice(512,544)).toString('hex'),expected=sha(b);mutation.push({input:text,expected,actual,detected:actual!==expected});}
assert.ok(mutation.some(r=>r.detected),'negative control failed to discriminate');
const report={status:'correctness experiment; novelty unresolved',node:process.version,v8:process.versions.v8,openssl:process.versions.openssl,verify_sha256:sha(fs.readFileSync(__filename)),manifest_sha256:sha(fs.readFileSync(path.join(out,'manifest.json'))),corpus_sha256:sha(indexBytes),seed:2026101206,local_cases:locals.length,full_hash_cases:index.cases.length,full_hash_comparisons:2*rows.length,mismatches:0,locals,rows,rejections,mutation};
fs.writeFileSync(path.join(out,'verification.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({local_cases:locals.length,full_hash_cases:rows.length,comparisons:2*rows.length,mismatches:0,mutation},null,2));
