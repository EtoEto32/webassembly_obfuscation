const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=__dirname,base=path.resolve(root,'../../tmp/settling-carry');
const output=path.join(root,'artifacts/verification.json');
if(fs.existsSync(output))throw Error('existing verification');
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const manifestBytes=fs.readFileSync(path.join(base,'manifest.json'));
const inputBytes=fs.readFileSync(path.join(base,'inputs.json'));
const manifest=JSON.parse(manifestBytes),inputs=JSON.parse(inputBytes),mask=0xffffffffn;
// Independent BigInt DAG interpretation, reused from the original verifier.
function reference(nodes,x,y){
 const state=[],env={x:BigInt(x),y:BigInt(y)};
 const val=q=>typeof q==='number'?state[q]:env[q];
 for(const [op,...args] of nodes){
  const a=val(args[0]);let z;
  if(op==='rotl'){const k=BigInt(args[1]);z=(a<<k)|(a>>(32n-k));}
  else if(op==='select')z=val(args[2])!==0n?a:val(args[1]);
  else {const b=val(args[1]);z=op==='add'?a+b:op==='mul'?a*b:op==='xor'?a^b:op==='lt'?(a<b?1n:0n):undefined;}
  if(z===undefined)throw Error('unknown operation');state.push(z&mask);
 }
 return Number(state.at(-1));
}
const reports=[];
for(const name of ['mixed','cross','select']){
 const dir=path.join(root,'artifacts',name),cert=JSON.parse(fs.readFileSync(path.join(dir,'certificate.json')));
 const source=fs.readFileSync(path.join(base,name+'.carry.wasm')),recovered=fs.readFileSync(path.join(dir,'recovered.wasm'));
 const recorded=manifest.binaries.find(x=>x.file===name+'.carry.wasm');
 if(hash(source)!==cert.input_sha256||hash(source)!==recorded.sha256||hash(recovered)!==cert.output_sha256)throw Error('hash mismatch');
 const run=b=>new WebAssembly.Instance(new WebAssembly.Module(b)).exports.run;
 const originalRun=run(source),recoveredRun=run(recovered),observations=[];
 for(const input of inputs){
  const a=originalRun(...input)>>>0,b=recoveredRun(...input)>>>0,expected=reference(manifest.programs[name],...input);
  if(a!==expected||b!==expected)throw Error(JSON.stringify({name,input,a,b,expected}));
  observations.push([a,b,expected]);
 }
 reports.push({name,cases:inputs.length,mismatches:0,observations});
}
const report={node:process.version,v8:process.versions.v8,input_sha256:hash(inputBytes),manifest_sha256:hash(manifestBytes),reports,
 totalInputTriples:inputs.length*reports.length,totalWasmOracleComparisons:2*inputs.length*reports.length};
fs.writeFileSync(output,JSON.stringify(report,null,2));
console.log(JSON.stringify({...report,reports:reports.map(({observations,...x})=>x)},null,2));
