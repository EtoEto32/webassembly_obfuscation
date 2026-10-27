const fs=require('fs'),path=require('path'),assert=require('assert');
const root=process.argv[2],manifest=JSON.parse(fs.readFileSync(path.join(root,'manifest.json')));
let state=21102193;
function random(){state^=state<<13;state^=state>>>17;state^=state<<5;return state>>>0;}
const memory=Buffer.alloc(65536);for(let i=0;i<memory.length;i++)memory[i]=random()&255;
const rot=(x,k)=>((x<<k)|(x>>>(32-k)))>>>0;
function oracle(seed,ptr,n,k,mask){
 let y=seed>>>0;
 for(let i=0;i<n;i++){
  const a=(ptr+4*i)>>>0;if(a>65532)return {trap:true};
  y=(rot(y,k)^memory.readUInt32LE(a))>>>0;
 }
 return {trap:false,value:(y&mask)>>>0};
}
const inputs=[];
for(const s of [0,1,0xffffffff,0x80000000,0x7fffffff,0xaaaaaaaa,0x55555555])
 for(const ptr of [0,1,4,65528,65532,65533,65535,65536,0xfffffffc,0xffffffff])
  for(const n of [0,1,2,3,31,32,33,64])inputs.push([s,ptr,n]);
for(let i=0;i<512;i++)inputs.push([random(),random()%65540,random()%97]);
for(let j=0;j<32;j++)inputs.push([2**j,0,32]);
const records=[];
for(const row of manifest){
 const data=fs.readFileSync(path.join(root,row.file));assert(WebAssembly.validate(data));
 const e=new WebAssembly.Instance(new WebAssembly.Module(data)).exports;
 Buffer.from(e.memory.buffer).set(memory);
 let traps=0;
 for(const [seed,ptr,n] of inputs){
  const expected=oracle(seed,ptr,n,row.rotation,row.mask);let actual;
  try{actual={trap:false,value:e.run(seed,ptr,n)>>>0};}catch(err){if(!(err instanceof WebAssembly.RuntimeError))throw err;actual={trap:true};}
  assert.deepStrictEqual(actual,expected,row.file+' '+[seed,ptr,n]);
  assert(Buffer.from(e.memory.buffer).equals(memory),'memory changed');
  traps+=Number(actual.trap);
 }
 records.push({file:row.file,calls:inputs.length,traps,mismatches:0});
}
fs.writeFileSync(path.join(root,'correctness.json'),JSON.stringify({inputs,records,calls:inputs.length*records.length,node:process.version,v8:process.versions.v8},null,2));
console.log(JSON.stringify({binaries:records.length,calls:inputs.length*records.length,traps:records.reduce((n,r)=>n+r.traps,0),mismatches:0}));
