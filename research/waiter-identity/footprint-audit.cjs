'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert'),crypto=require('crypto');
const out=process.argv[2],cases=JSON.parse(fs.readFileSync(path.join(out,'cases.json'))),rows=[];
for(const item of cases){
  const bytes=fs.readFileSync(path.join(out,item.name+'.wasm'));assert(WebAssembly.validate(bytes));
  assert.strictEqual(crypto.createHash('sha256').update(bytes).digest('hex'),item.certificate.sha256);
  const memory=new WebAssembly.Memory({initial:1,maximum:4,shared:true}),expected=new Uint8Array(65536);let expectedTrap=false;
  // This runtime oracle uses the generation recipe, not the checker's ranges.
  for(const address of item.addresses){if(address+4>expected.length){expectedTrap=true;break;}new DataView(expected.buffer).setUint32(address,305419896,true);}
  let trapped=false;const inst=new WebAssembly.Instance(new WebAssembly.Module(bytes),{env:{memory}});
  try{inst.exports.run(0);}catch(e){if(!(e instanceof WebAssembly.RuntimeError))throw e;trapped=true;}
  assert.strictEqual(trapped,expectedTrap);assert.deepStrictEqual(new Uint8Array(memory.buffer),expected);
  const cell=item.certificate.stableOffset;if(cell!==null)assert.strictEqual(Atomics.load(new Int32Array(memory.buffer),cell/4),0);
  rows.push({name:item.name,trapped,wholeMemoryMatches:true,stableOffset:cell,stableCellUnchanged:cell!==null});
}
fs.writeFileSync(path.join(out,'results.json'),JSON.stringify({node:process.version,checks:rows.length,rows,scope:'Generated constant and unknown-address cases, not a proof for arbitrary Wasm.'},null,2));
console.log(JSON.stringify({checks:rows.length,traps:rows.filter(r=>r.trapped).length,stableCells:rows.filter(r=>r.stableOffset!==null).length}));
