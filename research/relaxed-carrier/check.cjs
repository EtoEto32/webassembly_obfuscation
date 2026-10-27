const fs=require('fs'),path=require('path');
const root=process.argv[2], manifest=JSON.parse(fs.readFileSync(path.join(root,'manifest.json')));
const rot=(x,k)=>(x<<k)|(x>>>(32-k));
function reference(model,a,b,c){
  if(model==='majority')return (a&b)|(c&(a|b));
  let t=0,acc=0;
  for(let r=0;r<Number(model.slice(3));r++){
    t=((a&b)^rot(c,(r*7+3)&31)^(Math.imul(r+1,0x9e3779b9)|0)^acc)|0;
    a=(b^(t>>>(r%5+1)))|0;b=(c|(t<<(r%3+1)))|0;c=(t^rot(a,(r*3+5)&31))|0;acc=t>>>7;
  }
  return (a^b^c)|0;
}
const bounds=[0,1,2,15,16,31,32,127,255,0x7fffffff,-2147483648,-1,0x55555555],inputs=[];
for(const a of bounds)for(const b of bounds)for(const c of bounds)inputs.push([a,b,c]);
let seed=20261019;function rng(){seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed|0;}
for(let i=0;i<3000;i++)inputs.push([rng(),rng(),rng()]);
let calls=0,traps=0;const records=[];
for(const item of manifest.files){
  const bytes=fs.readFileSync(path.join(root,item.path));
  if(!WebAssembly.validate(bytes))throw Error('validation: '+item.path);
  const e=new WebAssembly.Instance(new WebAssembly.Module(bytes)).exports;
  for(const input of inputs){let got;try{got=e.run(...input);calls++;}catch(err){traps++;throw err;}
    const expected=reference(item.model,...input);if(got!==expected)throw Error(JSON.stringify({item,input,got,expected}));}
  records.push({path:item.path,calls:inputs.length});
}
console.log(JSON.stringify({calls,traps,mismatches:0,inputs_per_binary:inputs.length,boundary_inputs:bounds.length**3,random_inputs:3000,seed:20261019,records,node:process.version,v8:process.versions.v8}));
