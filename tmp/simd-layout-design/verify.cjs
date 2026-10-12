// Independent scalar reference: no import of generator, no SIMD model reuse.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
let state = 0x4a821d39;
function random32() { state ^= state << 13; state ^= state >>> 17; state ^= state << 5; return state >>> 0; }
function reference(words) {
  const bytes=[];
  for (const w of words.slice(0,4)) for(let b=0;b<4;b++) bytes.push((w >>> (8*b)) & 255);
  const v=[];
  for(let i=0;i<8;i++) { const sum=bytes[2*i]+bytes[2*i+1]; v.push((sum*sum+37)%65536); }
  return [0,1,2,3].map(i=>v[2*i]+v[2*i+1]);
}
const patterns=[
 [0,0,0,0], [0xffffffff,0xffffffff,0xffffffff,0xffffffff],
 [0x03020100,0x07060504,0x0b0a0908,0x0f0e0d0c],
 [0x00ff00ff,0xff00ff00,0x7f807f80,0x807f807f],
 [0x80000000,0x7fffffff,1,0xfffffffe]
];
// Every layout combination is exercised; input patterns and seed recorded.
const inputs=[];
for(let u=0;u<512;u++) {
 for(const words of patterns) inputs.push([...words.map(x=>x>>>0),u]);
 inputs.push([random32(),random32(),random32(),random32(),u]);
}
for(let i=0;i<1024;i++) inputs.push([random32(),random32(),random32(),random32(),random32()]);
fs.writeFileSync(path.join(__dirname,'inputs.json'),JSON.stringify(inputs));
const manifest=JSON.parse(fs.readFileSync(path.join(__dirname,'manifest.json')));
const results=[];
for(const b of manifest.binaries) {
 const bytes=fs.readFileSync(path.join(__dirname,b.file));
 if(crypto.createHash('sha256').update(bytes).digest('hex')!==b.sha256) throw Error('binary changed');
 const mod=new WebAssembly.Module(bytes);
 if(WebAssembly.Module.imports(mod).length) throw Error('unexpected imports');
 const run=new WebAssembly.Instance(mod).exports.run;
 let digest=crypto.createHash('sha256');
 for(let i=0;i<inputs.length;i++) {
   const out=run(...inputs[i]).map(x=>x>>>0), expected=reference(inputs[i]);
   if(JSON.stringify(out)!==JSON.stringify(expected)) throw Error(JSON.stringify({file:b.file,i,input:inputs[i],out,expected}));
   digest.update(JSON.stringify(out)+'\n');
 }
 results.push({file:b.file,cases:inputs.length,failures:0,outputSha256:digest.digest('hex')});
}
const report={node:process.version,v8:process.versions.v8,seed:'0x4a821d39',layoutCombinations:512,
  casesPerBinary:inputs.length,totalComparisons:inputs.length*results.length,results};
fs.writeFileSync(path.join(__dirname,'results.json'),JSON.stringify(report,null,2));
console.log(JSON.stringify(report,null,2));
