'use strict';
const fs=require('node:fs'), path=require('node:path'), assert=require('node:assert/strict');
const dir=process.argv[2], read=f=>JSON.parse(fs.readFileSync(path.join(dir,f)));
const rows=read('manifest.json'), inputs=read('inputs.json'), fixtures=read('fixtures.json');
let calls=0; const records=[];
for(const row of rows){
  const bytes=fs.readFileSync(path.join(dir,row.file)); assert(WebAssembly.validate(bytes));
  const api=new WebAssembly.Instance(new WebAssembly.Module(bytes)).exports;
  let zeros=0,nans=0;
  for(let j=0;j<inputs.length;j++){
    const expected=fixtures[row.kernel].expected[j]>>>0, actual=api.run(...inputs[j])>>>0;
    assert.equal(actual,expected,row.file+' '+JSON.stringify(inputs[j])); calls++;
    if((expected&0x7fffffff)===0)zeros++; if(expected===0x7fc00000)nans++;
  }
  records.push({file:row.file,calls:inputs.length,zeros,nans,mismatches:0});
}
const scratch=new DataView(new ArrayBuffer(8));
function toBits(x){scratch.setFloat64(0,x,true);return scratch.getBigUint64(0,true);}
function toFloat(x){scratch.setBigUint64(0,x,true);return scratch.getFloat64(0,true);}
let state=21102191; function rand(){state^=state<<13;state^=state>>>17;state^=state<<5;return state>>>0;}
const quant=[];
for(const file of ['quant-raw.wasm','quant-O3.wasm']){
  const bytes=fs.readFileSync(path.join(dir,file));assert(WebAssembly.validate(bytes));
  const api=new WebAssembly.Instance(new WebAssembly.Module(bytes)).exports;let cases=0;
  for(const p of [-32,-17,-1,0,1,17,32]){
    let xs=[0n,1n,0x8000000000000000n,0x7ff0000000000000n,0xfff0000000000000n,0x7ff8000000000001n];
    for(const e of [-151,-150,-149,-127,-126,-125,0,126,127,128]){
      for(const frac of [0n,1n,0xfffffffn,0x10000000n,0x10000001n,0x1fffffffn,0xfffffffffffffn]){
        const bits=(BigInt(e+p+1023)<<52n)|frac;
        xs.push(bits,bits|0x8000000000000000n);
      }
    }
    for(let j=0;j<1024;j++)xs.push((BigInt(rand())<<32n)|BigInt(rand()));
    for(const bits of xs){
      const x=toFloat(bits), expected=Math.fround(x/2**p)*2**p;
      const actual=BigInt.asUintN(64,api.q(bits,p));
      if(Number.isNaN(expected))assert(Number.isNaN(toFloat(actual)));
      else assert.equal(actual,toBits(expected),file+' p='+p+' bits='+bits.toString(16));
      cases++;
    }
  }
  quant.push({file,cases,mismatches:0});
}
fs.writeFileSync(path.join(dir,'checks.json'),JSON.stringify({calls,records,quant,node:process.version,v8:process.versions.v8},null,2),{flag:'wx'});
console.log(JSON.stringify({binaries:rows.length+quant.length,calls,quantCases:quant.reduce((a,x)=>a+x.cases,0),mismatches:0}));
