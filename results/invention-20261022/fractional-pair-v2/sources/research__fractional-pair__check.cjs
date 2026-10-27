const fs=require('fs'),path=require('path'),out=process.argv[2];
const manifest=JSON.parse(fs.readFileSync(path.join(out,'manifest.json'))),M=0xffffffffn;
let state=221027;
function rand(){state^=state<<13;state^=state>>>17;state^=state<<5;return state>>>0;}
function rot(x,k){return ((x<<BigInt(k))|(x>>BigInt(32-k)))&M;}
function oracle(name,xx,dd){let x=BigInt(xx),d=BigInt(dd),h=0n;
 if(name==='pair')return d===0n?null:(x/d<<32n)|(x%d);
 for(let i=0;i<(name==='chain'?16:64);i++){
  if(name==='euclid'&&d===0n)break;
  if(d===0n)return null;
  const q=x/d,r=x%d;h=(h*33n+q)&M;
  if(name==='chain'){x=rot(x,7)^r;d=((d+h)&M)|1n;}else{x=d;d=r;}
 }
 return (x<<32n)|h;
}
const boundary=[0,1,2,3,7,15,16,31,32,255,256,65535,65536,0x7fffffff,0x80000000,0xfffffffe,0xffffffff,1836311903,2971215073];
const inputs={};
for(const name of ['pair','chain','euclid']){
 const set=new Map();function add(x,d){set.set(x+','+d,[x,d]);}
 const n=name==='pair'?256:16;
 for(let x=0;x<n;x++)for(let d=0;d<n;d++)add(x,d);
 for(const x of boundary)for(const d of boundary)add(x,d);
 for(const {x,d} of JSON.parse(fs.readFileSync(path.join(out,'model.json'))).wide_counterexamples)add(x,d);
 for(let i=0;i<4096;i++)add(rand(),rand());
 inputs[name]=Array.from(set.values());
}
fs.writeFileSync(path.join(out,'inputs.json'),JSON.stringify(inputs));
const expected={};for(const name in inputs)expected[name]=inputs[name].map(([x,d])=>oracle(name,x,d));
const results=[];
for(const t of manifest.targets){
 const bytes=fs.readFileSync(path.join(out,t.file));if(!WebAssembly.validate(bytes))throw Error('validation '+t.file);
 const w=new WebAssembly.Instance(new WebAssembly.Module(bytes)).exports;
 let mismatches=0,traps=0;const examples=[];
 for(let i=0;i<inputs[t.name].length;i++){
  const [x,d]=inputs[t.name][i];let got;
  try{got=BigInt.asUintN(64,w.run(x,d));}catch(e){if(!(e instanceof WebAssembly.RuntimeError))throw e;got=null;traps++;}
  if(got!==expected[t.name][i]){mismatches++;if(examples.length<4)examples.push({x,d,got:String(got),expected:String(expected[t.name][i])});}
 }
 results.push({file:t.file,name:t.name,mode:t.mode,opt:t.opt,calls:inputs[t.name].length,traps,mismatches,examples});
}
const positive=results.filter(r=>r.mode!=='bad'),negative=results.filter(r=>r.mode==='bad');
const report={results,positiveCalls:positive.reduce((a,r)=>a+r.calls,0),positiveTraps:positive.reduce((a,r)=>a+r.traps,0),positiveMismatches:positive.reduce((a,r)=>a+r.mismatches,0),negativeDetected:negative.filter(r=>r.mismatches>0).length,node:process.version,v8:process.versions.v8,maxRssKiB:process.resourceUsage().maxRSS};
fs.writeFileSync(path.join(out,'checks.json'),JSON.stringify(report,null,2));
if(report.positiveMismatches||report.negativeDetected!==negative.length)throw Error('correctness/negative control failed');
console.log(JSON.stringify({positiveCalls:report.positiveCalls,positiveTraps:report.positiveTraps,negativeDetected:report.negativeDetected}));
