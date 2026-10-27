'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),os=require('node:os');
const d=path.resolve(process.argv[2]),read=n=>JSON.parse(fs.readFileSync(path.join(d,n),'utf8'));
const write=(n,v)=>fs.writeFileSync(path.join(d,n),JSON.stringify(v,null,2),{flag:'wx'});
const plan=read('plan.json'),manifest=read('manifest.json');let seed=plan.seed;
const rand=()=>{seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed>>>0;};
const mask=0xffffffffn;
function reference(a,b,n,k){let x=BigInt(a>>>0),y=BigInt(b>>>0);for(let i=0;i<(n&63);i++){
 let u,v;
 if(k==='quadratic'){u=x*x+3n*y+5n;v=y*y+3n*x+5n;}
 else if(k==='cubic'){u=x*x*x+2n*x*y+y+7n;v=y*y*y+2n*x*y+x+7n;}
 else if(k==='coupled'){u=x*x*y+3n*x+y*y+11n;v=y*y*x+3n*y+x*x+11n;}
 else throw Error('unknown kernel');x=u&mask;y=v&mask;
}return Number(BigInt.asIntN(32,x+y+7n*x*y));}
const inputs=[];
for(const x of [0,1,2,0x7fffffff,0x80000000,0xffffffff])for(const y of [0,1,2,0x7fffffff,0x80000000,0xffffffff])for(const n of [0,1,2,31,63,64,65,0xffffffff])inputs.push([x,y,n]);
for(let i=0;i<plan.random_inputs;i++)inputs.push([rand(),rand(),rand()]);write('inputs.json',inputs);
const rows=[];
for(const a of manifest.artifacts){
 const bytes=fs.readFileSync(path.join(d,a.file));if(crypto.createHash('sha256').update(bytes).digest('hex')!==a.sha256)throw Error('hash mismatch');
 const valid=WebAssembly.validate(bytes);if(!valid)throw Error('engine validation');
 const e=new WebAssembly.Instance(new WebAssembly.Module(bytes)).exports;
 let mismatches=0,unexpectedTraps=0;const failures=[];
 for(const [x,y,n]of inputs){const expected=reference(x,y,n,a.kernel);let got;
  try{got=e.run(x,y,n);}catch(err){unexpectedTraps++;if(failures.length<4)failures.push({x,y,n,error:String(err)});continue;}
  if(got!==expected){mismatches++;if(failures.length<4)failures.push({x,y,n,expected,got});}
 }
 rows.push({kernel:a.kernel,mode:a.mode,level:a.level,cases:inputs.length,mismatches,unexpectedTraps,failures,validated:valid});
}
write('checks.json',{node:process.version,v8:process.versions.v8,flags:process.execArgv,cpu:os.cpus()[0].model,rows,
 note:'Artificial kernels. BigInt reference. Finite test, not a whole-program proof. No performance measurement.'});
fs.copyFileSync(__filename,path.join(d,'check.cjs'));
console.log(JSON.stringify({variants:rows.length,cases:rows.reduce((n,r)=>n+r.cases,0),mismatches:rows.reduce((n,r)=>n+r.mismatches,0),traps:rows.reduce((n,r)=>n+r.unexpectedTraps,0)}));
if(rows.some(r=>r.mismatches||r.unexpectedTraps))process.exitCode=1;
