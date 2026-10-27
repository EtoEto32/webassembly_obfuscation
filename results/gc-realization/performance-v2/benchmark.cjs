const fs=require('fs');
const req=JSON.parse(fs.readFileSync(process.argv[2],'utf8')),cases=[];
for(const file of req.files){
  const bytes=fs.readFileSync(req.directory+'/'+file);
  const instance=new WebAssembly.Instance(new WebAssembly.Module(bytes));
  for(let i=0;i<200;i++)if(instance.exports.run()!==1)throw Error('warmup mismatch');
  const samples=[];
  for(let b=0;b<7;b++){
    const start=process.hrtime.bigint();
    for(let i=0;i<500;i++)if(instance.exports.run()!==1)throw Error('measurement mismatch');
    samples.push(Number(process.hrtime.bigint()-start)/500);
  }
  cases.push({file,samples_ns:samples,median_ns:[...samples].sort((a,b)=>a-b)[3]});
}
console.log(JSON.stringify({version:process.version,v8:process.versions.v8,peakRSSKiB:process.resourceUsage().maxRSS,cases}));
