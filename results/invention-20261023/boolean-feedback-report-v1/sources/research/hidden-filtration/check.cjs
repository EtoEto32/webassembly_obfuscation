const fs=require('fs'),path=require('path');
const folder=process.argv[2];
const rot=(x,r)=>(x<<r)|(x>>>(32-r));
const oracle={
  mix8:(x,y)=>{let a=rot(x,3),b=rot(y,27),c=a&b,d=c^x,e=rot(d,5),f=d^y;return (e&f)^x;},
  select10:(x,y)=>{let a=rot(x,11),b=x^y,c=a&b,d=c|y,e=rot(d,7),f=e^a,g=f&d,h=rot(g,13),i=h^b;return i|x;},
  chain12:(x,y)=>{let a=rot(x,3),b=rot(y,17),c=a^b,d=c&x,e=rot(d,9),f=e^y,g=f|d,h=g&c,i=rot(h,23),j=i^e,k=j&g;return k^a;}
};
let seed=0x19480317;function rng(){seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed|0;}
const edge=[0,-1,1,-2147483648,2147483647,0x55555555,0xaaaaaaaa|0];
const cases=[];for(const a of edge)for(const b of edge)cases.push([a,b]);
for(let i=0;i<32;i++){cases.push([1<<i,0],[0,1<<i],[~(1<<i),-1],[-1,~(1<<i)]);}
for(let i=0;i<4096;i++)cases.push([rng(),rng()]);
const records=[];
for(const file of fs.readdirSync(folder).filter(f=>f.endsWith('.wasm')&&!f.includes('diagnostic'))){
  const name=file.split('-')[0];if(!oracle[name])continue;
  const bytes=fs.readFileSync(path.join(folder,file));if(!WebAssembly.validate(bytes))throw Error(file+' invalid');
  const run=new WebAssembly.Instance(new WebAssembly.Module(bytes)).exports.run;
  for(const args of cases){const expected=oracle[name](...args)|0,actual=run(...args)|0;if(actual!==expected)throw Error(JSON.stringify({file,args,actual,expected}));}
  records.push({file,calls:cases.length,mismatches:0});
}
const result={node:process.version,v8:process.versions.v8,seed:'0x19480317',random_cases:4096,boundary_cases:177,records,total_calls:records.length*cases.length,mismatches:0};
fs.writeFileSync(path.join(folder,'correctness.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result));
