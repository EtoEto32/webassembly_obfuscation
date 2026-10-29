const fs=require('fs'),path=require('path');
const root=process.argv[2],m=JSON.parse(fs.readFileSync(path.join(root,'manifest.json')));
let seed=20261019;function random(){seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed>>>0;}
const memory0=Buffer.alloc(65536);for(let i=0;i<memory0.length;i++)memory0[i]=random()&255;
function poly(a,x,u){let z=a[0]|0;const terms=[x,u,Math.imul(x,x),Math.imul(x,u),Math.imul(u,u)];for(let j=0;j<5;j++)z=(z+Math.imul(a[j+1],terms[j]))|0;return z;}
function ref(d,mem,p,n){let x=d.x0|0,y=d.y0|0;for(let i=0;i<(n>>>0);i++){const a=((p>>>0)+i)>>>0;if(a>=mem.length)return {trap:true};let u=mem[a],nx=(poly(d.P,x,u)+Math.imul(d.b,y))|0; y=(poly(d.Q,x,u)+Math.imul(poly(d.R,x,u),y))|0;x=nx;}return {trap:false,value:x};}
const cases=[];for(const p of [0,1,65520,65535,65536,0xffffffff,0xfffffffe])for(const n of [0,1,2,16,17,0xffffffff])cases.push([p,n]);
for(let i=0;i<1000;i++)cases.push([i%3===0?65500+random()%50:random()%4096,random()%65]);
let calls=0,traps=0,words=0;const records=[];
for(const f of m.files){const bytes=fs.readFileSync(path.join(root,f.path));if(!WebAssembly.validate(bytes))throw Error(f.path);const e=new WebAssembly.Instance(new WebAssembly.Module(bytes)).exports,mem=Buffer.from(e.memory.buffer),d=m.models[f.model];let localcalls=0,localtraps=0;
 function one(p,n){const expected=ref(d,mem,p,n),before=Buffer.from(mem);let actual;try{actual={trap:false,value:e.run(p,n)}}catch(err){if(!(err instanceof WebAssembly.RuntimeError))throw err;actual={trap:true};}calls++;localcalls++;if(actual.trap){traps++;localtraps++;}if(actual.trap!==expected.trap||(!actual.trap&&actual.value!==expected.value)||!mem.equals(before))throw Error(JSON.stringify({f,p,n,actual,expected,memoryEqual:mem.equals(before)}));}
 memory0.copy(mem);for(const [p,n] of cases)one(p,n);
 for(let n=0;n<=9;n++)for(let word=0;word<1<<n;word++){for(let i=0;i<n;i++)mem[i]=(word>>>i)&1;one(0,n);words++;}
 records.push({path:f.path,calls:localcalls,traps:localtraps});
}
console.log(JSON.stringify({binaries:m.files.length,calls,traps,mismatches:0,exhaustive_word_calls:words,boundary_cases:42,random_cases:1000,words_per_binary:1023,full_memory_bytes_checked_per_call:65536,seed:20261019,records}));
