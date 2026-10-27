const fs=require('fs'),path=require('path');
const dir=process.argv[2],manifest=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json')));
let total=0,mismatches=0,trapTotal=0;const rows=[];
function invoke(f,x){try{return {kind:'value',value:f(x)>>>0};}catch(e){
  if(!(e instanceof WebAssembly.RuntimeError))throw e;
  if(!/memory access out of bounds/i.test(e.message))throw e;
  return {kind:'memory_oob'};
}}
for(const r of manifest.rows){
  const b=fs.readFileSync(path.join(dir,r.wasm));if(!WebAssembly.validate(b))throw Error('Invalid '+r.wasm);
  const f=new WebAssembly.Instance(new WebAssembly.Module(b)).exports.run;
  const data=Buffer.from(manifest.truth[r.fixture],'hex'),S=2**r.shift;
  const limit=Math.floor(65534/S),inputs=Array.from({length:limit+1},(_,i)=>i);
  if(r.shift)for(let i=0;i<=limit;i++)inputs.push(i+2**(32-r.shift));
  inputs.push(0,1,limit,limit+1,65534,65535,65536,0x7fffffff,0x80000000,0xfffffffe,0xffffffff);
  let state=0x20261018;
  for(let i=0;i<256;i++){state^=state<<13;state^=state>>>17;state^=state<<5;inputs.push(state>>>0);}
  let bad=0,traps=0;
  for(const x of inputs){
    const address=Number((BigInt(x>>>0)*(1n<<BigInt(r.shift)))&0xffffffffn);
    const expected=address+1>=65536?{kind:'memory_oob'}:
      {kind:'value',value:(data[address]??0)^(data[address+1]??0)};
    const actual=invoke(f,x);if(actual.kind==='memory_oob')traps++;
    if(actual.kind!==expected.kind||actual.value!==expected.value)bad++;
  }
  rows.push({wasm:r.wasm,inputs:inputs.length,mismatches:bad,traps});
  total+=inputs.length;mismatches+=bad;trapTotal+=traps;
}
const result={node:process.version,v8:process.versions.v8,conditions:rows.length,executions:total,
              mismatches,traps:trapTotal,rows};
fs.writeFileSync(path.join(dir,'checks.json'),JSON.stringify(result,null,2));
console.log(JSON.stringify({conditions:rows.length,executions:total,mismatches,traps:trapTotal}));
if(mismatches)process.exitCode=1;
