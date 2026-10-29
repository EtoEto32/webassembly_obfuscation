var req=JSON.parse(read(scriptArgs[0])),rows=[];
for(var file of req.files){
  var phase='validation';var start=Date.now();
  try{
    var bytes=read(req.directory+'/'+file,'binary');
    if(!WebAssembly.validate(bytes))throw new Error('validation rejected');
    phase='compilation';var module=new WebAssembly.Module(bytes);
    phase='instantiation';var instance=new WebAssembly.Instance(module);
    phase='execution';var result=instance.exports.run();
    rows.push({file,status:'ok',result,ms:Date.now()-start});
  }catch(e){rows.push({file,status:'error',phase,error:String(e)});}
}
print(JSON.stringify({rows}));
