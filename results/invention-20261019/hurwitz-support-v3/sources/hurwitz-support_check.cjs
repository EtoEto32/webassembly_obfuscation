const fs=require('fs'),path=require('path'),folder=process.argv[2];
const m=JSON.parse(fs.readFileSync(path.join(folder,'manifest.json')));
function formula(t,x,y){const op=t[0];if(op==='v')return ((t[1]<32?x:y)>>>(t[1]%32))&1;if(op==='c')return t[1];if(op==='not')return 1^formula(t[1],x,y);const a=formula(t[1],x,y),b=formula(t[2],x,y);return op==='and'?a&b:op==='or'?a|b:a^b;}
function variables(t,out=new Set()){if(t[0]==='v')out.add(t[1]);else for(const q of t.slice(1))if(Array.isArray(q))variables(q,out);return [...out].sort((a,b)=>a-b);}
let seed=20261019;function rand(){seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed|0;}
let calls=0,traps=0;const rows=[];
for(const [model,t] of Object.entries(m.models)){
 const inputs=[],edge=[0,1,-1,0x7fffffff,-2147483648,0x55555555,0xaaaaaaaa,0xffff];
 for(const x of edge)for(const y of edge)inputs.push([x|0,y|0]);
 for(let j=0;j<32;j++)inputs.push([1<<j,0],[0,1<<j],[~(1<<j),-1],[-1,~(1<<j)]);
 for(let j=0;j<2048;j++)inputs.push([rand(),rand()]);
 const vs=variables(t);if(vs.length<=16)for(let k=0;k<(1<<vs.length);k++){let x=0,y=0;for(let j=0;j<vs.length;j++)if((k>>j)&1){const v=vs[j];if(v<32)x|=1<<v;else y|=1<<(v-32);}inputs.push([x,y]);}
 for(const row of m.files.filter(q=>q.model===model)){
  const bytes=fs.readFileSync(path.join(folder,row.path));if(!WebAssembly.validate(bytes))throw Error('validation '+row.path);
  const run=new WebAssembly.Instance(new WebAssembly.Module(bytes)).exports.run;
  for(const [x,y] of inputs){let actual;try{actual=run(x,y);}catch(e){traps++;throw e;}const expected=formula(t,x,y);if(actual!==expected)throw Error(JSON.stringify({row,x,y,expected,actual}));calls++;}
  rows.push({path:row.path,inputs:inputs.length});
 }
}
console.log(JSON.stringify({binaries:m.files.length,calls,traps,mismatches:0,rows}));
