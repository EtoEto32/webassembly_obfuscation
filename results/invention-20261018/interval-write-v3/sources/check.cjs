const fs=require('fs'),path=require('path');
const dir=process.argv[2], manifest=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json')));
let seed=20261018;function rand(){seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed>>>0;}
function ref(t,a){if(t[0]==='lt')return +((a[t[1]]&255)<(a[t[2]]&255));if(t[0]==='const')return t[1];
 const x=ref(t[1],a),y=ref(t[2],a);return t[0]==='and'?x&y:t[0]==='or'?x|y:x^y;}
const cases={};
for(const [name,m] of Object.entries(manifest.models)){
 const a=[];
 if(m.n===2)for(let x=0;x<256;x++)for(let y=0;y<256;y++)a.push([x,y]);
 const edges=[0,1,127,128,254,255,256,65535,0x80000000,0xffffffff];
 for(const x of edges)for(const y of edges)a.push(Array.from({length:m.n},(_,i)=>i%2?y:x));
 for(let i=0;i<4096;i++)a.push(Array.from({length:m.n},()=>rand()));
 cases[name]=a;
}
let calls=0,bad=0,mbad=0;const rows=[];
for(const item of manifest.files){
 const binary=fs.readFileSync(path.join(dir,item.path));if(!WebAssembly.validate(binary))throw Error(item.path);
 const e=new WebAssembly.Instance(new WebAssembly.Module(binary)).exports;
 const mem=Buffer.from(e.memory.buffer);for(let i=0;i<mem.length;i++)mem[i]=(i*131+17)&255;
 const before=Buffer.from(mem);let mismatches=0,memory=0;
 for(const a of cases[item.model]){
  const got=e.run(...a),expected=ref(manifest.models[item.model].tree,a);
  mismatches+=got!==expected;memory+=Buffer.compare(before,mem)!==0;calls++;
 }
 bad+=mismatches;mbad+=memory;
 rows.push({path:item.path,calls:cases[item.model].length,mismatches,memory_mismatches:memory});
}
const negatives=[];
for(const item of manifest.negative){
 const e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(dir,item.path)))).exports;
 const inputs=item.kind==='missing_reset'?[[0,255],[0,0]]:cases.pair2;
 let errors=0;for(const a of inputs)errors+=e.run(...a)!==ref(manifest.models.pair2.tree,a);
 if(!errors)throw Error('Negative control failed '+item.kind);
 negatives.push({kind:item.kind,calls:inputs.length,mismatches:errors});
}
const result={files:rows.length,calls,mismatches:bad,memory_mismatches:mbad,rows,negative_controls:negatives};
fs.writeFileSync(path.join(dir,'checks.json'),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify({files:rows.length,calls,mismatches:bad,memory_mismatches:mbad,negative_controls:negatives}));
if(bad||mbad)process.exitCode=1;
