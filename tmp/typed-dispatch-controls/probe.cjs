'use strict';
// Direct binary generation: no assembler validation repair.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const u=n=>{const a=[];do{const b=n&127;n>>>=7;a.push(b|(n?128:0));}while(n);return a;};
const sec=(id,a)=>[id,...u(a.length),...a],sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const types=sec(1,[3,0x5f,1,0x7f,0,0x60,1,0x7f,1,0x7f,0x60,1,0x64,0,1,0x7f]);
const make=[0x20,0,0xfb,0,0],set=[0x21,1],read=[0x20,1,0xfb,2,0,0];
// Same state0 allocation and state1 read in every flattened condition.
const flat=[0x03,0x7f,0x20,2,0x45,0x04,0x40,...make,...set,0x41,1,0x21,2,0x0c,1,0x0b,...read,0x0b,0x0b];
const localDecl=nullable=>[2,1,nullable?0x63:0x64,0,1,0x7f];
const cases=[
 {name:'flat-nonnullable-invalid',valid:false,body:[...localDecl(false),...flat]},
 {name:'flat-nullable',valid:true,body:[...localDecl(true),...flat]},
 {name:'flat-nonnullable-global-sentinel',valid:true,global:true,body:[...localDecl(false),0x23,0,...set,...flat]},
 // The typed header must have a non-null payload even before real allocation.
 {name:'flat-typed-global-sentinel',valid:true,global:true,body:[...localDecl(false),0x23,0,0x03,2,...set,
   0x20,2,0x45,0x04,0x40,...make,...set,0x41,1,0x21,2,0x20,1,0x0c,1,0x0b,...read,0x0b,0x0b]},
 {name:'flat-typed-null-seed-invalid',valid:false,body:[...localDecl(false),0xd0,0,0x03,2,...set,
   0x20,2,0x45,0x04,0x40,...make,...set,0x41,1,0x21,2,0x20,1,0x0c,1,0x0b,...read,0x0b,0x0b]}
];
const out=path.join(__dirname,'artifacts');fs.mkdirSync(out,{recursive:true});
let seed=0x753be291;const inputs=[0,1,-1,2147483647,-2147483648];
for(let i=0;i<4096;i++){seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;inputs.push(seed|0);}
fs.writeFileSync(path.join(out,'inputs.json'),JSON.stringify(inputs));
const rows=[];
for(const c of cases){
 const global=c.global?sec(6,[1,0x64,0,0,0x41,0,0xfb,0,0,0x0b]):[];
 const bytes=Buffer.from([0,97,115,109,1,0,0,0,...types,...sec(3,[1,1]),...global,...sec(7,[1,3,114,117,110,0,0]),...sec(10,[1,...u(c.body.length),...c.body])]);
 fs.writeFileSync(path.join(out,c.name+'.wasm'),bytes);
 const row={name:c.name,bytes:bytes.length,sha256:sha(bytes),expected_valid:c.valid,valid:WebAssembly.validate(bytes)};
 assert.equal(row.valid,c.valid);
 if(row.valid){const m=new WebAssembly.Module(bytes);assert.deepEqual(WebAssembly.Module.imports(m),[]);const f=new WebAssembly.Instance(m,{}).exports.run;
 row.tests=inputs.length;row.mismatches=inputs.filter(x=>f(x)!==x).length;assert.equal(row.mismatches,0);
 }else{try{new WebAssembly.Module(bytes);}catch(e){row.error=e.message;}}
 rows.push(row);
}
const result={node:process.version,v8:process.versions.v8,seed:'0x753be291',script_sha256:sha(fs.readFileSync(__filename)),scope:'Validation and identity-output probes only, not a general transformer, benchmark, or resistance result.',rows};
fs.writeFileSync(path.join(out,'results.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result,null,2));
