const fs=require('fs'),path=require('path'),folder=process.argv[2];
if(process.argv[3]==='check'){
 let tests=0,referenceCalls=0;const m=JSON.parse(fs.readFileSync(path.join(folder,'manifest.json')));
 for(const row of m.files){
  const e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(folder,row.path)))).exports;
  for(const seed of [0,1,0x7fffffff,0xffffffff])for(const count of [0,1,2,17,31]){
   let x=seed|0,y=seed^0x9e3779b9,acc=0;
   for(let i=0;i<count;i++){x=(x+71717)|0;y=(y+13331)|0;acc=(((acc<<5)|(acc>>>27))+e.run(x,y))|0;referenceCalls++;}
   if(e.bench(seed,count)!==acc)throw Error(JSON.stringify({row,seed,count,acc}));tests++;
  }
 }
 console.log(JSON.stringify({harnesses:m.files.length,tests,referenceCalls,mismatches:0}));
}else{
 const e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(folder))).exports;
 let sink=0;for(let i=0;i<5;i++)sink^=e.bench(i*12345,20000);
 const samples=[];for(let i=0;i<11;i++){const t=process.hrtime.bigint();sink^=e.bench(i*12345+123,10000);samples.push(Number(process.hrtime.bigint()-t)/10000);}
 console.log(JSON.stringify({median_ns:[...samples].sort((a,b)=>a-b)[5],samples_ns:samples,maxRSS_KiB:process.resourceUsage().maxRSS,warmup_calls:100000,calls_per_sample:10000,repetitions:11,sink}));
}
