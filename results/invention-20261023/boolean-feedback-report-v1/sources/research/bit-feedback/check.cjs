const fs=require('fs'),os=require('os'),{performance}=require('perf_hooks');
let seed=20261018; function rnd(){seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed>>>0;}
const manifest=JSON.parse(fs.readFileSync(process.argv[2])), rows=manifest.records;
const edge=[0,1,2,31,32,255,256,65535,65536,0x7fffffff,0x80000000,0xffffffff,0xaaaaaaaa,0x55555555];
const inputs=edge.flatMap(x=>edge.map(y=>[x,y]));for(let i=0;i<2048;i++)inputs.push([rnd(),rnd()]);
function load(path){let bytes=fs.readFileSync(path);if(!WebAssembly.validate(bytes))throw Error('validation '+path);return new WebAssembly.Instance(new WebAssembly.Module(bytes)).exports.run;}
const base={};for(const r of rows)if(r.variant==='plain'&&r.opt==='raw')base[r.kernel]=load(r.path);
const details=[];let calls=0,mismatches=0;
for(const r of rows){for(const path of [r.path,...manifest.attacks.filter(a=>a.path===r.path&&a.status==='ok').map(a=>a.recovered)]){
  const fn=load(path);let errors=0;for(const [a,b] of inputs){let expected=base[r.kernel](a,b),actual=fn(a,b);calls+=2;errors+=actual!==expected;}
  mismatches+=errors;details.push({path,inputs:inputs.length,mismatches:errors});}}
const result={calls,mismatches,inputs:inputs.length,conditions:details.length,details,environment:{node:process.version,v8:process.versions.v8,platform:os.platform(),arch:os.arch(),cpu:os.cpus()[0].model,linear_memory_bytes:0}};
fs.writeFileSync(require('path').join(require('path').dirname(process.argv[2]),'correctness.json'),JSON.stringify(result,null,2));
fs.writeFileSync(require('path').join(require('path').dirname(process.argv[2]),'inputs.json'),JSON.stringify(inputs));
console.log(JSON.stringify({calls,mismatches,conditions:details.length}));if(mismatches)process.exitCode=1;
