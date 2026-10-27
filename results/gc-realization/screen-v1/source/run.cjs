const fs = require('fs');
const req=JSON.parse(fs.readFileSync(process.argv[2],'utf8')),rows=[];
for (const file of req.files) {
  let phase='validation';
  const t=performance.now();
  try {
    const bytes=fs.readFileSync(req.directory+'/'+file);
    if(!WebAssembly.validate(bytes))throw new Error('validation rejected');
    phase='compilation';const module=new WebAssembly.Module(bytes);
    phase='instantiation';const instance=new WebAssembly.Instance(module);
    phase='execution';const result=instance.exports.run();
    rows.push({file,status:'ok',result,ms:performance.now()-t});
  } catch(e) {rows.push({file,status:'error',phase,error:String(e)});}
}
console.log(JSON.stringify({version:process.version,v8:process.versions.v8,peakRSSKiB:process.resourceUsage().maxRSS,rows}));
