const fs=require('node:fs'),path=require('node:path'),dir=process.argv[2];
const rows=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json'))),cases=JSON.parse(fs.readFileSync(path.join(dir,'cases.json')));
let seed=0x23cb1239;function random(){seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed>>>0;}
const edge=[0,1,2,0x7fffffff,0x80000000,0xfffffffe,0xffffffff,0x12345678];
const starts=[...edge,...Array.from({length:512},random)];
const seqs=starts.map(s=>({s,us:[...edge,...Array.from({length:16},random)]}));
fs.writeFileSync(path.join(dir,'inputs.json'),JSON.stringify(seqs));
function poly(a,x){let y=0;for(let i=a.length-1;i>=0;i--)y=(Math.imul(y,x)+a[i])|0;return y;}
const result={positive:[],negative:[],steps:0,peeks:0,resets:0,mismatches:0,traps:0,node:process.version,v8:process.versions.v8};
for(const row of rows){
 const bytes=fs.readFileSync(path.join(dir,row.file));if(!WebAssembly.validate(bytes))throw Error('validate');
 const e=new WebAssembly.Instance(new WebAssembly.Module(bytes)).exports;
 const item={file:row.file,steps:0,peeks:0,resets:0,mismatches:0,traps:0,witness:null};
 let x=0;
 function check(actual,expected,at){if((actual>>>0)!==(expected>>>0)){item.mismatches++;item.witness??={at,actual:actual>>>0,expected:expected>>>0};}}
 function peek(at){check(e.peek(),Math.imul(x,x),at);item.peeks++;}
 function step(u,at){x=(poly(cases[row.name],x)+u)|0;check(e.step(u),Math.imul(x,x),at);item.steps++;peek(at+' peek');}
 try{
  peek('initial');step(0,'initial step');
  for(let i=0;i<seqs.length;i++){const seq=seqs[i];e.reset(seq.s);item.resets++;x=seq.s|0;peek('reset '+i);for(let k=0;k<seq.us.length;k++)step(seq.us[k],`${i}:${k}`);}
 }catch(err){if(!(err instanceof WebAssembly.RuntimeError))throw err;item.traps++;item.witness??={trap:String(err)};}
 if(row.negative){if(!item.mismatches)throw Error('negative without witness');result.negative.push(item);}
 else {if(item.mismatches||item.traps)throw Error(JSON.stringify(item));result.positive.push(item);for(const k of ['steps','peeks','resets','mismatches','traps'])result[k]+=item[k];}
}
result.total_calls=result.steps+result.peeks+result.resets;
console.log(JSON.stringify(result));
