const fs=require('node:fs');
const [binary,specfile]=process.argv.slice(2),spec=JSON.parse(fs.readFileSync(specfile));
const instance=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(binary)));
const result={calls:0,mismatches:0,traps:0,witnesses:[],node:process.version,v8:process.versions.v8};
for(const {args,expected} of spec.tests){
  result.calls++;let actual,trap=null;
  try{actual=instance.exports[spec.export](...args)>>>0;}
  catch(e){if(!(e instanceof WebAssembly.RuntimeError))throw e;trap=String(e);result.traps++;}
  if(trap||actual!==(expected>>>0)){
    result.mismatches++;
    if(result.witnesses.length<3)result.witnesses.push({args,expected:expected>>>0,actual,trap});
  }
}
console.log(JSON.stringify(result));
