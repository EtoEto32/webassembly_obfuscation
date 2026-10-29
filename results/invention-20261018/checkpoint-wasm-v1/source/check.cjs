const fs=require('fs'),path=require('path');
const dir=process.argv[1],m=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json')));
let s=0x162918;const next=()=>{s^=s<<13;s^=s>>>17;s^=s<<5;return s>>>0;};
const inputs=[0,1,2,3,0x7fffffff,0x80000000,0xfffffffe,0xffffffff,...Array.from({length:256},next)];
let total=0,bad=0;const rows=[];
for(const row of m.rows){const b=fs.readFileSync(path.join(dir,row.wasm));if(!WebAssembly.validate(b))throw Error('validate');
 const f=new WebAssembly.Instance(new WebAssembly.Module(b)).exports.run;
 const [c,d,a]=row.source.map(BigInt);const ref=x=>BigInt.asUintN(32,a*x*x+d*x+c);let mismatch=0;
 for(const x of inputs){total++;if(BigInt(f(x)>>>0)!==ref(ref(BigInt(x))))mismatch++;}bad+=mismatch;
 rows.push({wasm:row.wasm,inputs:inputs.length,mismatch});}
const r={node:process.version,v8:process.versions.v8,conditions:rows.length,executions:total,mismatches:bad,rows};
fs.writeFileSync(path.join(dir,'checks.json'),JSON.stringify(r,null,2));console.log(JSON.stringify({conditions:r.conditions,executions:total,mismatches:bad}));if(bad)process.exitCode=1;