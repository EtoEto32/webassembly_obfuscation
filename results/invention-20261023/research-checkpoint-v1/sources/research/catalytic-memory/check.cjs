const fs=require('fs'),path=require('path'),assert=require('assert');
const folder=process.argv[2],m=JSON.parse(fs.readFileSync(path.join(folder,'manifest.json')));
let seed=0x7f4a7c15;
function random(){seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed>>>0;}
function expected(name,a){if(name==='and')return (a[0]&a[1])>>>0;const p=Math.imul(a[0],a[1])>>>0;return name==='div'?(a[2]===0?'trap':Math.floor(p/a[2])>>>0):p;}
(async()=>{
 const report={targets:[],calls:0,expected_traps:0,mismatches:0,negative:[],node:process.version,v8:process.versions.v8};
 const edges=[0,1,0xffffffff,0x80000000,0x7fffffff,0x55555555,0xaaaaaaaa];
 for(const t of m.targets){
  const {instance}=await WebAssembly.instantiate(fs.readFileSync(path.join(folder,t.file)));
  const bytes=new Uint8Array(instance.exports.memory.buffer),word=new DataView(bytes.buffer);
  const initial=new Uint8Array(bytes.length);for(let j=0;j<bytes.length;j++)initial[j]=random()&255;
  bytes.set(initial);let calls=0,traps=0;
  const rows=[];for(const x of edges)for(const y of edges)for(const z of (t.n===3?edges:[1]))rows.push([x,y,z]);
  for(let j=0;j<4096;j++)rows.push([random(),random(),t.n===3&&j%8===0?0:random()]);
  for(const a of rows){
   const dirty=random();word.setUint32(0,dirty,true);let got;
   try{got=instance.exports.run(...a.slice(0,t.n))>>>0;}catch(e){if(!(e instanceof WebAssembly.RuntimeError))throw e;got='trap';}
   assert.strictEqual(got,expected(t.fixture,a),t.file+' value');
   assert.strictEqual(word.getUint32(0,true),dirty,t.file+' scratch');
   if(got==='trap')traps++;calls++;
  }
  assert.deepStrictEqual(bytes.slice(4),initial.slice(4),t.file+' other memory');
  report.targets.push({...t,calls,traps});report.calls+=calls;report.expected_traps+=traps;
 }
 for(const t of m.negative){
  const {instance}=await WebAssembly.instantiate(fs.readFileSync(path.join(folder,t.file)));
  const mem=new DataView(instance.exports.memory.buffer);mem.setUint32(0,0x12345678,true);let trapped=false;
  try{instance.exports.run(7,9,0);}catch(e){if(!(e instanceof WebAssembly.RuntimeError))throw e;trapped=true;}
  assert(trapped);assert.strictEqual(mem.getUint32(0,true),0x1234567f);
  report.negative.push({file:t.file,trapped,before:0x12345678,after:mem.getUint32(0,true),corruption_detected:true});
 }
 fs.writeFileSync(path.join(folder,'checks.json'),JSON.stringify(report,null,2));
 console.log(JSON.stringify({targets:report.targets.length,calls:report.calls,expected_traps:report.expected_traps,mismatches:report.mismatches,negative:report.negative}));
})().catch(e=>{console.error(e);process.exitCode=1;});
