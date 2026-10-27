'use strict';const fs=require('fs'),path=require('path'),d=process.argv[2],load=f=>JSON.parse(fs.readFileSync(path.join(d,f)));
const get=f=>new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(d,f)))).exports;
const rot=(x,r)=>((x<<r)|(x>>>(32-r)))>>>0;
function reference(r,args){const [T,x,y,z]=args;if((T>>>0)>16384)return 'trap';const a=Uint32Array.from(r.coeff,(_,i)=>((x^Math.imul(i+1,0x10204081))+y)>>>0);
for(let t=0;t<T;t++){let b=(rot((z+Math.imul(t,0x9e3779b9))>>>0,11)^y)>>>0;for(let i=0;i<a.length;i++){const u=a[i],c=r.coeff[i];a[i]=r.kind===0?rot((Math.imul(u,c)+b)>>>0,r.r):r.kind===1?(Math.imul(u^b,c)+rot(u,r.r))>>>0:(rot((u+b)>>>0,r.r)^Math.imul(u,c))>>>0;b=a[i];}}
let ret=0;for(const v of a)ret^=v;return {words:a,ret};}
let seed=3719;const rnd=()=>{seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed|0;};const cases=[];
for(const T of [0,1,2,3,4,7,8,15,16,17,31,128,16384,16385,-1,0x7fffffff])for(const x of [0,-1,0x7fffffff,-2147483648])cases.push([T,x,x^0x5a5a5a5a,x^0x12345678]);
for(let i=0;i<128;i++)cases.push([rnd()&127,rnd(),rnd(),rnd()]);
const call=(e,args)=>{try{return e.run(...args)}catch(x){if(x instanceof WebAssembly.RuntimeError)return 'trap';throw x;}};
const records=[];let calls=0,traps=0;
for(const r of load('manifest.json')){const inst=[get(r.source_probe),get(r.probe)];if(r.recovered)inst.push(get(r.recovered_probe));const memory=new Uint32Array(16384);
for(const args of cases){const want=reference(r,args);if(want!=='trap')memory.set(want.words);for(const e of inst){const got=call(e,args);calls++;if(got==='trap')traps++;if(got!==(want==='trap'?'trap':want.ret))throw Error('return '+r.file+' '+JSON.stringify(args));const actual=new Uint32Array(e.memory.buffer);for(let j=0;j<actual.length;j++)if(actual[j]!==memory[j])throw Error('memory '+r.file+' '+j);}}
records.push({file:r.file,cases:cases.length,instances:inst.length,status:'pass'});}
const negative=[];for(const r of load('negative-manifest.json')){const e=get(r.probe);let witness=null;for(const args of cases){const want=reference(r,args),got=call(e,args);if(want!=='trap'&&(got!==want.ret||want.words.some((v,i)=>v!==new Uint32Array(e.memory.buffer)[i]))){witness={args,expected:want.ret,got};break;}}if(!witness)throw Error('missing negative');negative.push({file:r.file,witness});}
fs.writeFileSync(path.join(d,'inputs.json'),JSON.stringify(cases));fs.writeFileSync(path.join(d,'negative.json'),JSON.stringify(negative,null,2));fs.writeFileSync(path.join(d,'checks.json'),JSON.stringify({wasm_calls:calls,traps,mismatches:0,cases_per_target:cases.length,negative_witnesses:negative.length,records},null,2));
