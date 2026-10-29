'use strict';
// Reads only .wasm bytes. Supports the seven tiny direct-gc probes, not general GC.
const fs=require('node:fs'), path=require('node:path'), assert=require('node:assert/strict'), crypto=require('node:crypto');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
function reader(bytes) {
  let p=0;
  return {byte(){assert(p<bytes.length,'truncated');return bytes[p++];},
    uint(){let n=0,s=0,b; do {b=this.byte();assert(s<35,'oversized LEB');n+=(b&127)*2**s;s+=7;}while(b&128); return n;},
    take(n){assert(p+n<=bytes.length,'truncated');const v=bytes.subarray(p,p+n);p+=n;return v;},
    get remaining(){return bytes.length-p;}};
}
function predict(binary) {
  const r=reader(binary);assert.deepEqual([...r.take(8)],[0,97,115,109,1,0,0,0]);
  const sections=new Map();while(r.remaining){const id=r.byte(),v=r.take(r.uint());assert(!sections.has(id));sections.set(id,v);}
  assert.deepEqual([...sections.keys()],[1,3,7,10],'unsupported sections');
  const t=reader(sections.get(1)), types=[];
  function composite(op) {
    if(op===0x60){assert.equal(t.uint(),0);assert.equal(t.uint(),1);assert.equal(t.byte(),0x7f);return 'func:()->i32';}
    assert.equal(op,0x5f,'unsupported composite');const fields=[];
    for(let n=t.uint();n--;){const val=t.byte(),mut=t.byte();assert([0x7f,0x7e].includes(val));assert.equal(mut,0);fields.push(val);}
    return JSON.stringify(['struct',fields]);
  }
  for(let n=t.uint();n--;){const op=t.byte();let group;
    if(op===0x4e){group=[];for(let k=t.uint();k--;)group.push(composite(t.byte()));}
    else group=[composite(op)];
    // This subset has no type references: canonical key is group content + position.
    for(let i=0;i<group.length;i++)types.push(JSON.stringify([group,i]));
  }
  assert.equal(t.remaining,0);
  const c=reader(sections.get(10));assert.equal(c.uint(),1);const body=reader(c.take(c.uint()));assert.equal(c.remaining,0);
  assert.equal(body.uint(),0);assert.equal(body.byte(),0x41);assert.equal(body.byte(),7);
  assert.equal(body.byte(),0xfb);assert.equal(body.uint(),0);const source=body.uint();
  assert.equal(body.byte(),0xfb);assert.equal(body.uint(),0x14);const target=body.uint();
  assert.equal(body.byte(),0x0b);assert.equal(body.remaining,0);assert(source<types.length&&target<types.length);
  return {source,target,predicted:Number(types[source]===types[target]),types:types.length};
}
const dir=path.join(__dirname,'results','direct-gc');
const predictions=fs.readdirSync(dir).filter(x=>x.endsWith('.wasm')).sort().map(name=>{
  const bytes=fs.readFileSync(path.join(dir,name));return {name,sha256:sha(bytes),...predict(bytes)};
});
// Freeze predictions before invoking the engine. No oracle results feed predict().
const results=predictions.map(p=>{
  const bytes=fs.readFileSync(path.join(dir,p.name));assert.equal(sha(bytes),p.sha256);
  const actual=new WebAssembly.Instance(new WebAssembly.Module(bytes),{}).exports.run();
  return {...p,actual,matched:p.predicted===actual};
});
const report={script_sha256:sha(fs.readFileSync(__filename)),node:process.version,v8:process.versions.v8,
  oracle_queries_for_prediction:0,results,
  limitation:'Static reconstruction of constant ref.test result for seven restricted modules; not source recovery, general recursive-type analysis, or an obfuscation benchmark.'};
fs.writeFileSync(path.join(__dirname,'results','gc-recovery.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({modules:results.length,matched:results.filter(r=>r.matched).length,oracle_queries_for_prediction:0}));
assert(results.every(r=>r.matched));
