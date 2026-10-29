const fs=require('node:fs'),path=require('node:path'),os=require('node:os');
const m=JSON.parse(fs.readFileSync(path.join(__dirname,'manifest.json')));
const inputs=JSON.parse(fs.readFileSync(path.join(__dirname,'inputs.json'))).slice(-256);
const variants=m.binaries.filter(b=>b.file.includes('.O2.')).map(b=>({...b,run:new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(__dirname,b.file)))).exports.run}));
let sink=0;
function batch(v,n){const start=process.hrtime.bigint();let sum=0;for(let i=0;i<n;i++){const a=inputs[i&255];sum=(sum+v.run(a[0],a[1],a[2]))|0;}sink^=sum;return Number(process.hrtime.bigint()-start)/1e6;}
for(const v of variants)batch(v,16384);
const calls=65536,rows=[];
for(let round=0;round<9;round++)for(let j=0;j<variants.length;j++){const v=variants[(j+round)%variants.length];rows.push({round,file:v.file,ms:batch(v,calls)});}
const summary=variants.map(v=>{const a=rows.filter(r=>r.file===v.file).map(r=>r.ms).sort((a,b)=>a-b);return {file:v.file,bytes:v.bytes,min:a[0],median:a[4],max:a[8]};});
const report={node:process.version,v8:process.versions.v8,cpu:os.cpus()[0].model,calls,rounds:9,sink,scope:'Single host; JS-Wasm boundary included; no CPU affinity; fixed calls; normal timings short and ratios exploratory only.',rows,summary};
fs.writeFileSync(path.join(__dirname,'timings.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(summary,null,2));
