const fs=require('node:fs'),path=require('node:path'),d=process.argv[2],rows=JSON.parse(fs.readFileSync(path.join(d,'manifest.json'))),cases=JSON.parse(fs.readFileSync(path.join(d,'cases.json')));
let seed=0x21309817;function random(){seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed>>>0;}
const edge=[0,1,0xffffffff,0x80000000];
const seqs=Array.from({length:64},(_,i)=>[edge[i%4],...Array.from({length:255},random)]);
fs.writeFileSync(path.join(d,'inputs.json'),JSON.stringify(seqs));
function poly(a,x){let v=0;for(let i=a.length-1;i>=0;i--)v=(Math.imul(v,x)+a[i])|0;return v;}
const result={rows:[],conditions:rows.length,instances:0,step_calls:0,mismatches:0,traps:0};
for(const row of rows){
 const module_=new WebAssembly.Module(fs.readFileSync(path.join(d,row.file)));
 for(const inputs of seqs){const e=new WebAssembly.Instance(module_).exports;if(Object.keys(e).join()!=='step')throw Error('unexpected API');let x=0;result.instances++;
  for(const u of inputs){x=(poly(cases[row.name],x)+u)|0;const got=e.step(u)|0,expected=Math.imul(x,x);result.step_calls++;if(got!==expected)throw Error(JSON.stringify({file:row.file,u,got,expected}));}}
 result.rows.push({file:row.file,instances:seqs.length,step_calls:seqs.length*seqs[0].length,mismatches:0});
}
console.log(JSON.stringify(result));
