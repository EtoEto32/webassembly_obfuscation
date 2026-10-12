'use strict';
// Direct binary feasibility check: prevent an assembler from repairing local types.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const u=n=>{const a=[];do{const b=n&127;n>>>=7;a.push(b|(n?128:0));}while(n);return a;};
const sec=(id,a)=>[id,...u(a.length),...a],sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const prefix=[0,97,115,109,1,0,0,0,
  ...sec(1,[3,0x5f,1,0x7f,0, 0x60,1,0x7f,1,0x7f, 0x60,1,0x64,0,1,0x7f]),
  ...sec(3,[1,1]),...sec(7,[1,3,114,117,110,0,0])];
const make=[0x20,0,0xfb,0,0],setRef=[0x21,1],read=[0x20,1,0xfb,2,0,0];
const flatTail=[0x03,0x7f, // loop result i32
  0x20,2,0x45,0x04,0x40, // if pc==0
  ...make,...setRef,0x41,1,0x21,2,0x0c,1,0x0b,
  ...read,0x0b,0x0b];
const cases=[
  {name:'initialize-before-loop',expected_valid:true,body:[1,1,0x64,0,...make,...setRef,0x03,0x7f,...read,0x0b,0x0b]},
  {name:'flat-nonnullable',expected_valid:false,body:[2,1,0x64,0,1,0x7f,...flatTail]},
  {name:'flat-nullable',expected_valid:true,body:[2,1,0x63,0,1,0x7f,...flatTail]},
  {name:'typed-loop-payload',expected_valid:true,body:[1,1,0x64,0,...make,0x03,2,...setRef,...read,0x0b,0x0b]}
];
const out=path.join(__dirname,'artifacts');fs.mkdirSync(out,{recursive:true});
const results=[];
for(const c of cases){
  const bytes=Buffer.from([...prefix,...sec(10,[1,...u(c.body.length),...c.body])]);fs.writeFileSync(path.join(out,c.name+'.wasm'),bytes);
  const row={name:c.name,sha256:sha(bytes),bytes:bytes.length,expected_valid:c.expected_valid,valid:WebAssembly.validate(bytes)};
  try{const m=new WebAssembly.Module(bytes);assert.deepEqual(WebAssembly.Module.imports(m),[]);const f=new WebAssembly.Instance(m,{}).exports.run;
    row.outputs=[0,1,-1,2147483647,-2147483648].map(input=>({input,output:f(input)}));assert(row.outputs.every(p=>p.input===p.output));
  }catch(e){row.error=e.message;if(!(e instanceof WebAssembly.CompileError))throw e;}
  assert.equal(row.valid,row.expected_valid);results.push(row);
}
fs.writeFileSync(path.join(out,'results.json'),JSON.stringify({node:process.version,v8:process.versions.v8,script_sha256:sha(fs.readFileSync(__filename)),
 scope:'Four validation probes only; typed-loop-payload is not a full flattening algorithm or performance result.',results},null,2)+'\n');
console.log(JSON.stringify(results,null,2));
