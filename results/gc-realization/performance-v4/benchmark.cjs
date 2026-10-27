const fs=require('fs');
const req=JSON.parse(fs.readFileSync(process.argv[2],'utf8')),cases=[];
for(const {file,observer,nodes} of req.files){
  const bytes=fs.readFileSync(req.directory+'/'+file);
  const instance=new WebAssembly.Instance(new WebAssembly.Module(bytes));
  const check=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(req.directory+'/'+observer))).exports.check;
  let previous=null;
  function run(){
    const raw=instance.exports.make(),refs=nodes===1?[raw]:raw;
    if(refs.length!==nodes||check(...refs)!==1)throw Error('graph mismatch');
    if(previous===refs[0])throw Error('fresh identity mismatch');
    previous=refs[0];
  }
  for(let i=0;i<200;i++)run();
  const samples=[];
  for(let b=0;b<7;b++){
    const start=process.hrtime.bigint();
    for(let i=0;i<500;i++)run();
    samples.push(Number(process.hrtime.bigint()-start)/500);
  }
  cases.push({file,samples_ns:samples,median_ns:[...samples].sort((a,b)=>a-b)[3]});
}
console.log(JSON.stringify({version:process.version,v8:process.versions.v8,peakRSSKiB:process.resourceUsage().maxRSS,cases}));
