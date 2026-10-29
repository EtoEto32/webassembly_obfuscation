const fs=require('fs'),path=require('path');const dir=process.argv[2];
const oracle={muladd:(x,y,z)=>{const a=Math.imul(x,y),b=(a+z)|0;return Math.imul(b,a);},square:(x,y,z)=>Math.imul((Math.imul(x,x)-y)|0,z),mixcarry:(x,y,z)=>Math.imul(((x+y)|0)^z,y)};
let seed=0x48151623;const rng=()=>{seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed|0;};
const edge=[0,1,-1,0x80000000|0,0x7fffffff,0x55555555,0xaaaaaaaa|0],cases=[];
for(const x of edge)for(const y of edge)for(const z of edge)cases.push([x,y,z]);
for(let b=0;b<32;b++)for(let p=0;p<3;p++){let a=[0,0,0];a[p]=1<<b;cases.push(a);a=[-1,-1,-1];a[p]=~(1<<b);cases.push(a);}
for(let i=0;i<4096;i++)cases.push([rng(),rng(),rng()]);
const rows=[];for(const file of fs.readdirSync(dir).filter(f=>f.endsWith('.wasm'))){const name=file.split('-')[0];if(!oracle[name])continue;const e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(dir,file)))).exports;
for(const args of cases)if(e.run(...args)!==(oracle[name](...args)|0))throw Error(JSON.stringify({file,args,expected:oracle[name](...args),actual:e.run(...args)}));rows.push({file,calls:cases.length,mismatches:0});}
const result={node:process.version,v8:process.versions.v8,seed:'0x48151623',boundary:535,random:4096,records:rows,calls:rows.length*cases.length,mismatches:0};fs.writeFileSync(path.join(dir,'correctness.json'),JSON.stringify(result,null,2));console.log(JSON.stringify({targets:rows.length,calls:result.calls,mismatches:0}));
