const fs=require('node:fs'), path=require('node:path');
const dir=process.argv[2], manifest=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json')));
let seed=0x6221011;
function next(){seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed>>>0;}
function expected(d,a,w,n){if((n>>>0)>32)return null;let s=0;for(let i=0;i<n;i++)s=d[s][(w>>>i)&1];return (a>>>s)&1;}
const tests=[];
for(let len=0;len<=10;len++)for(let word=0;word<2**len;word++)tests.push([word,len]);
for(let len=0;len<=32;len++)for(const word of [0,1,0x7fffffff,0x80000000,0xffffffff,0xaaaaaaaa,0x55555555])tests.push([word,len]);
for(let i=0;i<2048;i++)tests.push([next(),next()%33]);
for(const len of [33,64,255,0xffffffff,0x80000000])for(const word of [0,1,0x80000000,0xffffffff])tests.push([word,len]);
const rows=[],negative=[];
for(const target of manifest.targets){
 const bytes=fs.readFileSync(path.join(dir,target.file));if(!WebAssembly.validate(bytes))throw Error('invalid');
 const e=new WebAssembly.Instance(new WebAssembly.Module(bytes)).exports;
 const f=manifest.fixtures[target.name];let calls=0,traps=0,mismatches=0,first=null,ones=0;
 for(const [word,len]of tests){
  let value=null,trapped=false;try{value=e.run(word,len);}catch(err){if(!(err instanceof WebAssembly.RuntimeError))throw err;trapped=true;}
  const want=expected(f.delta,f.accept,word,len);calls++;traps+=Number(trapped);ones+=Number(value===1);
  if(trapped!==(want===null)||(!trapped&&value!==want)){
   mismatches++;if(!first)first={word,len,want,value,trapped};
   if(target.mode!=='bad')throw Error(JSON.stringify({file:target.file,first}));
  }
 }
 const row={file:target.file,calls,traps,ones,mismatches,first};
 if(target.mode==='bad'){if(!mismatches)throw Error('negative missing counterexample');negative.push(row);}else rows.push(row);
}
const result={node:process.version,v8:process.versions.v8,inputCases:tests.length,exhaustiveShortWords:2047,
 randomWords:2048,seed:'0x6221011',rows,negative,calls:rows.reduce((a,r)=>a+r.calls,0),traps:rows.reduce((a,r)=>a+r.traps,0)};
fs.writeFileSync(path.join(dir,'checks.json'),JSON.stringify(result,null,2));
console.log(JSON.stringify({positive:rows.length,calls:result.calls,traps:result.traps,negative:negative.length}));
