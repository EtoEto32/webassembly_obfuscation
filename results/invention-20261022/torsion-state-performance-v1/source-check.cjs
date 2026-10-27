const fs=require('fs'),path=require('path');const root=process.argv[2],m=JSON.parse(fs.readFileSync(path.join(root,'manifest.json')));
const mask=(1n<<32n)-1n;
const edge=[0,1,2,3,7,255,256,65535,65536,0x7fffffff,0x80000000,0xfffffffe,0xffffffff];
const actions=[];
for(const x of edge){actions.push(null,x,...Array(32).fill(0));}
for(let j=0;j<64;j++){actions.push(null);for(let k=0;k<64;k++)actions.push(edge[(j+k)%edge.length]);}
let rng=20261022;for(let i=0;i<8192;i++){rng=(Math.imul(rng,1664525)+1013904223)>>>0;if(i%127===0)actions.push(null);actions.push(rng);}
// Long zero-input tail tests persistence beyond the sampled impulse prefix.
actions.push(...Array(4096).fill(0));const rows=[];
for(const t of m.targets){const bytes=fs.readFileSync(path.join(root,t.file));if(!WebAssembly.validate(bytes))throw Error('invalid');
const e=new WebAssembly.Instance(new WebAssembly.Module(bytes)).exports;
const model=m.models[t.name],a=model.a.map(r=>r.map(BigInt)),b=model.b.map(BigInt),c=model.c.map(BigInt);
let state=c.map(()=>0n),calls=0,resets=0,traps=0,bad=null;
for(let i=0;i<actions.length;i++){const u=actions[i];if(u===null){e.reset();state=state.map(()=>0n);resets++;continue;}
const old=state;state=a.map((row,k)=>(row.reduce((s,v,j)=>s+v*old[j],0n)+b[k]*BigInt(u))&mask);
const want=Number(c.reduce((s,v,j)=>s+v*state[j],0n)&mask)>>>0;let got;
try{got=e.step(u)>>>0;}catch(err){traps++;bad={i,u,error:String(err)};break;}
calls++;if(got!==want){bad={i,u,got,want};break;}}
if(t.negative?!bad:bad)throw Error(JSON.stringify({file:t.file,bad}));
rows.push({file:t.file,negative:!!t.negative,calls,resets,traps,counterexample:bad});}
console.log(JSON.stringify({node:process.version,v8:process.versions.v8,input_steps:actions.filter(x=>x!==null).length,reset_actions:actions.filter(x=>x===null).length,rows}));
