'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),os=require('node:os');
const d=path.resolve(process.argv[2]),m=JSON.parse(fs.readFileSync(path.join(d,'manifest.json'),'utf8'));
const save=(n,v)=>fs.writeFileSync(path.join(d,n),JSON.stringify(v,null,2),{flag:'wx'});
function ref(k,args,bits=32){const [a,b,c,d]=args.map(BigInt);let r;
 if(k==='add-xor')r=(a+b)^(c+d);
 else if(k==='xor-add')r=(a^b)+(c^d);
 else if(k==='nested')r=((a+b)^c)-d;
 else if(k==='reused-anchor')r=(a+(b^c))^(d+a);
 else throw Error(k);
 return Number(BigInt.asUintN(bits,r));
}
const inputs=[],boundary=[0,1,2,0x7fffffff,0x80000000,0xffffffff];
for(const a of boundary)for(const b of boundary)for(const c of boundary)for(const d of boundary)inputs.push([a,b,c,d]);
let seed=20261018;const rnd=()=>{seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed>>>0;};
for(let i=0;i<2048;i++)inputs.push([rnd(),rnd(),rnd(),rnd()]);save('inputs.json',inputs);
const rows=[];
for(const a of m.artifacts){
 const bytes=fs.readFileSync(path.join(d,a.file));if(crypto.createHash('sha256').update(bytes).digest('hex')!==a.sha256)throw Error('hash');
 if(!WebAssembly.validate(bytes))throw Error('validation');
 const e=new WebAssembly.Instance(new WebAssembly.Module(bytes)).exports;let mismatches=0,traps=0;const failures=[];
 for(const args of inputs){const expected=ref(a.kernel,args);let actual;try{actual=e.run(...args)>>>0;}catch(err){traps++;continue;}
  if(expected!==actual){mismatches++;if(failures.length<4)failures.push({args,expected,actual});}}
 rows.push({kernel:a.kernel,mode:a.mode,level:a.level||'raw',cases:inputs.length,mismatches,traps,failures});
}
const supports=[];
for(const kernel of [...new Set(m.artifacts.map(a=>a.kernel))]){
 const frequencies=new Uint32Array(256);
 for(let a=0;a<16;a++)for(let b=0;b<16;b++)for(let c=0;c<16;c++)for(let d=0;d<16;d++){
  const residue=(ref(kernel,[a,b,c,d],4)-a)&15;frequencies[a*16+residue]++;
 }
 supports.push({kernel,bits:4,inputs:65536,payloads:frequencies.length,minFrequency:Math.min(...frequencies),maxFrequency:Math.max(...frequencies)});
}
save('checks.json',{node:process.version,v8:process.versions.v8,cpu:os.cpus()[0].model,rows,supports,
 note:'Construction tests only. Equal local payload distributions are not a white-box resistance claim. Full word-level inverse-compilation attack not run yet.'});
fs.copyFileSync(__filename,path.join(d,'check.cjs'));
console.log(JSON.stringify({variants:rows.length,cases:rows.reduce((n,r)=>n+r.cases,0),mismatches:rows.reduce((n,r)=>n+r.mismatches,0),traps:rows.reduce((n,r)=>n+r.traps,0),supports}));
if(rows.some(r=>r.mismatches||r.traps)||supports.some(r=>r.minFrequency!==256||r.maxFrequency!==256))process.exitCode=1;
