const fs = require('fs'), path = require('path');
const dir=process.argv[2], manifest=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json')));
let rng=20261018; function rand(){rng^=rng<<13;rng^=rng>>>17;rng^=rng<<5;return rng>>>0;}
const words=[];
for(let n=0;n<=10;n++)for(let v=0;v<(1<<n);v++)words.push(Uint8Array.from({length:n},(_,i)=>(v>>>i)&1));
for(let k=0;k<256;k++)words.push(Uint8Array.from({length:rand()%1025},()=>rand()&255));
function ref(model, bytes){let s=0;for(const a of bytes)s=model.delta[a&1][s];return (model.final>>>s)&1;}
const records=[];let calls=0,mismatches=0,memoryMismatches=0;
for(const f of manifest.files){
  const bytes=fs.readFileSync(path.join(dir,f.path));
  if(!WebAssembly.validate(bytes))throw Error('Validation: '+f.path);
  const e=new WebAssembly.Instance(new WebAssembly.Module(bytes)).exports;
  const mem=Buffer.from(e.memory.buffer), saved=Buffer.alloc(mem.length);
  for(let i=0;i<mem.length;i++)mem[i]=(i*131+17)&255;
  let bad=0,mbad=0,normal=0,traps=0;
  const model=manifest.models[f.benchmark];
  for(const word of words){
    mem.set(word,17);mem.copy(saved);
    const actual=e.run(17,word.length),expected=ref(model,word);
    bad+=actual!==expected;mbad+=Buffer.compare(mem,saved)!==0;normal++;calls++;
  }
  const edges=[[0,0],[65536,0],[0xffffffff,0],[65535,1],[65536,1],
               [0xffffffff,1],[65535,2],[0xfffffffe,3],[0xffffffff,2],[65528,8]];
  for(const [p,n] of edges){
    mem.copy(saved);let outcome,expected;
    try{outcome={value:e.run(p,n)};}catch(x){if(!(x instanceof WebAssembly.RuntimeError))throw x;outcome={trap:true,reason:x.message};traps++;}
    const addresses=Array.from({length:n},(_,i)=>(p+i)>>>0);
    expected=addresses.some(i=>i>=mem.length)?{trap:true}:{value:ref(model,addresses.map(i=>mem[i]))};
    bad+=(!!outcome.trap!==!!expected.trap)||(!expected.trap&&outcome.value!==expected.value);
    mbad+=Buffer.compare(mem,saved)!==0;normal++;calls++;
  }
  records.push({path:f.path,calls:normal,mismatches:bad,memory_mismatches:mbad,traps});
  mismatches+=bad;memoryMismatches+=mbad;
}
const wrong=manifest.negative_control;
const e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(dir,wrong.path)))).exports;
const mem=new Uint8Array(e.memory.buffer);let wrongMismatches=0;
for(const word of words){mem.set(word);wrongMismatches+=e.run(0,word.length)!==ref(manifest.models[wrong.benchmark],word);}
const report={node:process.version,v8:process.versions.v8,words_per_file:words.length,edges_per_file:10,
              files:records.length,calls,mismatches,memory_mismatches:memoryMismatches,
              negative_control:{path:wrong.path,calls:words.length,mismatches:wrongMismatches},records};
fs.writeFileSync(path.join(dir,'checks.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({files:records.length,calls,mismatches,memoryMismatches,wrongMismatches}));
if(mismatches||memoryMismatches||!wrongMismatches)process.exitCode=1;
