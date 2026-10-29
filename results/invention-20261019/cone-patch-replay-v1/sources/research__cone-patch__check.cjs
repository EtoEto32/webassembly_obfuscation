'use strict';const fs=require('fs'),path=require('path'),d=process.argv[2];const load=f=>JSON.parse(fs.readFileSync(path.join(d,f)));const rows=load('manifest.json');
const get=f=>new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(d,f)))).exports;
const rotate=(x,r)=>((x<<r)|(x>>>(32-r)))>>>0;
function encode(words,n,coeff,inverse=false){const a=Uint32Array.from(words);let gates=[];for(let k=0;k<coeff.length;k++)for(let t=k%2;t<n;t+=2)gates.push([k,t]);if(inverse)gates.reverse();for(let base=0;base<a.length;base+=4*n)for(const [k,t]of gates)for(let l=0;l<4;l++){const v=(Math.imul(a[base+4*((t+n-1)%n)+l],coeff[k])+a[base+4*((t+1)%n)+l])>>>0;a[base+4*t+l]^=rotate(v,(7+5*k)%31+1);}return a;}
function update(a,n,which,r,x,y){if((r>>>0)>=4)return 'trap';const b=r*4*n;let u,v,z;if(which==='peek')return a[b+8]|0;if(which==='bump'){u=(a[b]+x)>>>0;v=(a[b+1]^y)>>>0;a[b]=u;a[b+1]=v;return (u^v)|0;}if(which==='coupled'){u=a[b];v=a[b+4];z=a[b+8];a[b]=(u+Math.imul(y,v))>>>0;a[b+4]=(v^rotate(z,x&31))>>>0;return (u^v^z)|0;}u=a[b];v=a[b+2*n];z=a[b+4*n-4];v=(v+Math.imul(x,z))>>>0;a[b+2*n]=v;a[b+4*n-4]=(z^u)>>>0;return (v+u)|0;}
const call=(e,k,a)=>{try{return e[k](...a)}catch(x){if(x instanceof WebAssembly.RuntimeError)return 'trap';throw x;}};
const names=['bump','coupled','spread','peek'];let seed=191026;const rnd=()=>{seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed|0;};const cases=[];
for(const r of [0,3,4,5,-1,0x7fffffff])for(const x of [0,1,-1,0x7fffffff,-2147483648,0x55555555])for(const name of names)cases.push([name,r,x,x^0x12345678]);
for(let i=0;i<192;i++)cases.push([names[i%3],rnd()&3,rnd(),rnd()]);
let calls=0,traps=0,snapshots=0;const records=[];
for(const row of rows){const orig=get(row.source_probe),e=get(row.probe);const ref=Uint32Array.from(load(row.initial));let comparisons=0;
 for(const [name,r,x,y]of cases){const expected=update(ref,row.n,name,r,x,y);for(const inst of [orig,e]){const got=call(inst,name,[r,x,y]);calls++;if(got==='trap')traps++;if(got!==expected)throw Error('return '+row.file);}
  const want=row.mode==='plain'?ref:encode(ref,row.n,row.coeff),actual=new Uint32Array(e.memory.buffer),plain=new Uint32Array(orig.memory.buffer);
  for(let j=0;j<actual.length;j++){if(actual[j]!==((j<want.length)?want[j]:0)||plain[j]!==((j<ref.length)?ref[j]:0))throw Error('state '+row.file+' '+j);comparisons++;}
 }
 if(row.mode!=='plain'){const recovered=encode(new Uint32Array(e.memory.buffer).slice(0,ref.length),row.n,row.attack.coeff,true);for(let j=0;j<ref.length;j++)if(ref[j]!==recovered[j])throw Error('attack '+row.file);snapshots++;}
 records.push({file:row.file,cases:cases.length,word_comparisons:comparisons,status:'pass'});
}
const negatives=[];for(const row of load('negative-manifest.json')){const e=get(row.probe),ref=Uint32Array.from(load(row.initial));let witness=null;for(const [name,r,x,y]of cases){const expected=update(ref,row.n,name,r,x,y),got=call(e,name,[r,x,y]);const want=encode(ref,row.n,row.coeff),actual=new Uint32Array(e.memory.buffer);let at=-1;for(let j=0;j<want.length;j++)if(actual[j]!==want[j]){at=j;break;}if(got!==expected||at>=0){witness={name,args:[r,x,y],expected,got,word:at};break;}}if(!witness)throw Error('negative lacks witness');negatives.push({file:row.file,witness});}
fs.writeFileSync(path.join(d,'inputs.json'),JSON.stringify(cases));fs.writeFileSync(path.join(d,'checks.json'),JSON.stringify({wasm_calls:calls,traps,mismatches:0,cases_per_target:cases.length,attack_snapshots:snapshots,records},null,2));fs.writeFileSync(path.join(d,'negative.json'),JSON.stringify(negatives,null,2));
