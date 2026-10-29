'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),os=require('node:os');
const d=path.resolve(process.argv[2]);const read=n=>JSON.parse(fs.readFileSync(path.join(d,n),'utf8'));
const write=(n,v)=>{const p=path.join(d,n);if(fs.existsSync(p))throw Error('Refuse overwrite');fs.writeFileSync(p,JSON.stringify(v,null,2));};
const plan=read('plan.json'),manifest=read('manifest.json');let seed=plan.seed;
const rand=()=>{seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed>>>0;};
const mask=0xffffffffn;
function reference(x,n,N){let q=0;let a=BigInt(x>>>0);for(let i=0;i<(n&63);i++){
 const s=BigInt(q+1),k=(2654435761n*s)&mask;
 a^=k;a=((a<<s)|(a>>(32n-s)))&mask;
 a=(a*BigInt(3+2*q)+s*17n)&mask;q=(q+Number((a^(a>>11n))&BigInt(N-1)))&(N-1);
}return Number(BigInt.asIntN(32,a));}
const inputs=[];for(const x of [0,1,2,0x7fffffff,0x80000000,0xffffffff])for(const n of [0,1,2,31,63,64,65,0xffffffff])inputs.push([x,n]);
for(let i=0;i<plan.random_inputs;i++)inputs.push([rand(),rand()]);write('inputs.json',inputs);
const rows=[];
for(const a of manifest.artifacts){
 const bytes=fs.readFileSync(path.join(d,a.file));if(crypto.createHash('sha256').update(bytes).digest('hex')!==a.sha256)throw Error('Hash');
 const start=performance.now(),e=new WebAssembly.Instance(new WebAssembly.Module(bytes)).exports,initMilliseconds=performance.now()-start;
 let mismatches=0;const failures=[];
 // Reuse each instance across all inputs to detect missing per-call reset.
 for(const [x,n]of inputs){const expected=reference(x,n,a.N),got=e.run(x,n);if(got!==expected){mismatches++;if(failures.length<4)failures.push({x,n,expected,got});}}
 rows.push({N:a.N,mode:a.mode,level:a.level,cases:inputs.length,mismatches,failures,initMilliseconds});
}
write('checks.json',{node:process.version,v8:process.versions.v8,flags:process.execArgv,cpu:os.cpus()[0].model,rows,
 note:'No runtime performance claim: init timing is single-shot diagnostic. Three table sizes are one kernel family, not three applications. Tests do not prove whole-module equivalence.'});
fs.copyFileSync(__filename,path.join(d,'check.cjs'));
console.log(JSON.stringify({variants:rows.length,cases:rows.reduce((n,r)=>n+r.cases,0),mismatches:rows.reduce((n,r)=>n+r.mismatches,0)}));
if(rows.some(r=>r.mismatches))process.exitCode=1;
