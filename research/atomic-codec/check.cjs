'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const out=path.resolve(process.argv[2]),rows=JSON.parse(fs.readFileSync(path.join(out,'manifest.json')));
const dest=path.join(out,'checks.json');if(fs.existsSync(dest))throw Error('refuse overwrite');
let rng=211021;function random(){rng^=rng<<13;rng^=rng>>>17;rng^=rng<<5;return rng>>>0;}
function update(op,x,y,z){switch(op){case'load':return[x,x];case'store':return[undefined,y];case'add':return[x,(x+y)>>>0];case'sub':return[x,(x-y)>>>0];case'and':return[x,(x&y)>>>0];case'or':return[x,(x|y)>>>0];case'xor':return[x,(x^y)>>>0];case'xchg':return[x,y];case'cmpxchg':return[x,x===y?z:x];default:throw Error(op);}}
const init=Array.from({length:16384},random),values=[0,1,0x7fffffff,0x80000000,0xfffffffe,0xffffffff];
const pointers=[0,1,2,3,4,8,65528,65532,65533,65535,65536,0xfffffffc,0xffffffff];
const result=[];
for(const row of rows){
 const file=path.join(out,row.file),bytes=fs.readFileSync(file);assert.equal(crypto.createHash('sha256').update(bytes).digest('hex'),row.sha256);assert(WebAssembly.validate(bytes));
 const memory=new WebAssembly.Memory({initial:1,maximum:1,shared:true}),physical=new Uint32Array(memory.buffer),logical=Uint32Array.from(init);
 const encode=x=>(Math.imul(x,row.a)+row.b)>>>0;for(let i=0;i<physical.length;i++)physical[i]=encode(logical[i]);
 const expected=physical.slice(),api=new WebAssembly.Instance(new WebAssembly.Module(bytes),{env:{memory}}).exports;
 const names=Object.keys(api).filter(n=>n!=='bench');let tests=[];
 for(const name of names)for(const p of pointers)for(const v of values.slice(0,3))tests.push({name,p,y:v,z:0x89abcdef});
 let local=0x12345678;function rand(){local^=local<<13;local^=local>>>17;local^=local<<5;return local>>>0;}
 for(let i=0;i<512;i++)tests.push({name:names[rand()%names.length],p:4*(rand()%16384),y:rand(),z:rand()});
 let calls=0,traps=0,witness=null;
 for(const t of tests){
  const off=t.name.startsWith('offset')?Number(t.name.slice(6)):0,addr=(t.p>>>0)+off,op=off?'add':t.name;
  const shouldTrap=addr%4!==0||addr+4>65536;let actual,trap=false;
  try{actual=api[t.name](t.p,t.y,t.z);if(actual!==undefined)actual>>>=0;}catch(e){assert(e instanceof WebAssembly.RuntimeError);trap=true;}
  calls++;if(shouldTrap)traps++;
  let want;
  if(!shouldTrap){const [old,next]=update(op,logical[addr/4],t.y,t.z);want=old;logical[addr/4]=next;expected[addr/4]=encode(next);}
  let difference=-1;for(let i=0;i<physical.length;i++)if(physical[i]!==expected[i]){difference=i;break;}
  if(trap!==shouldTrap||(!trap&&actual!==want)||difference>=0){witness={test:t,trap,shouldTrap,actual,want,difference};break;}
 }
 if(row.mode==='bad-and')assert(witness,'wrong AND must be detected');else assert.equal(witness,null,JSON.stringify({row,witness}));
 // The observed module and public store identify an affine memory representation.
 // No original module, generator coefficients, or expected memory is passed here.
 const start=performance.now();const attack=infer(file);const attackMs=performance.now()-start;
 const recovered=[];for(let i=0;i<physical.length;i++)recovered.push(attack.decode(physical[i]));
 if(!witness)assert.deepEqual(recovered,Array.from(logical));
 result.push({file:row.file,negative:row.negative,calls,traps,witness,inferred:{a:attack.a.toString(),b:attack.b.toString()},identificationStores:2,identificationMsIncludingInstantiation:attackMs,memoryRecovered:!witness});
}
function infer(file){
 const memory=new WebAssembly.Memory({initial:1,maximum:1,shared:true}),words=new Uint32Array(memory.buffer);
 const api=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(file)),{env:{memory}}).exports;
 api.store(0,0);const b=BigInt(words[0]);api.store(0,1);const mask=0xffffffffn,a=(BigInt(words[0])-b)&mask;
 assert(a&1n);let inverse=1n;for(let i=0;i<5;i++)inverse=(inverse*(2n-a*inverse))&mask;
 return{a,b,decode:x=>Number(((BigInt(x)-b)*inverse)&mask)};
}
fs.writeFileSync(dest,JSON.stringify({seed:211021,node:process.version,v8:process.versions.v8,results:result},null,2));
console.log(JSON.stringify({conditions:result.length,positive:result.filter(x=>!x.negative).length,calls:result.reduce((s,x)=>s+x.calls,0),negativeWitnesses:result.filter(x=>x.witness).length}));
module.exports={update};
