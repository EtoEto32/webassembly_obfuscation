const fs=require('fs'),assert=require('assert/strict');
const api=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(process.argv[1]))).exports;
const p=4294967291n,edge=[0n,1n,2n,p/2n,p-2n,p-1n],mem=new Uint32Array(api.memory.buffer);let cases=0;
function check(a,x,c){mem[1024]=Number(c);mem[1025]=Number(a);assert.equal(api.eval(4096,2,x),(a*x+c)%p);cases++;}
for(const a of edge)for(const x of edge)for(const c of edge)check(a,x,c);
let seed=271021;function word(){seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return BigInt(seed>>>0)%p;}
for(let i=0;i<4096;i++)check(word(),word(),word());console.log(JSON.stringify({cases,mismatches:0,seed:271021}));