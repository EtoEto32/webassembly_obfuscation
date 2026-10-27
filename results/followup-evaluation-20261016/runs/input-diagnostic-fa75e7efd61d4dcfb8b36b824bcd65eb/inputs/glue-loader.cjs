/* Load only reviewed, unchanged Emscripten glue in a network-disabled container.
 * noInitialRun prevents xmr-wasm's infinite demo main from running.
 */
'use strict';
const fs = require('fs'), vm = require('vm'), path = require('path'), crypto = require('crypto');
function read(file) {
  const fd=fs.openSync(file,'r'),chunks=[];
  try {for (;;) {const b=Buffer.alloc(4096),n=fs.readSync(fd,b,0,4096,null);
    if(!n)break;chunks.push(b.subarray(0,n));}}finally{fs.closeSync(fd);}
  return Buffer.concat(chunks);
}
const digest = b => crypto.createHash('sha256').update(b).digest('hex');
function save(file, value) {
  const b=Buffer.from(JSON.stringify(value,null,2)+'\n'),temp=file+'.tmp',fd=fs.openSync(temp,'w');
  try {for(let i=0;i<b.length;){i+=fs.writeSync(fd,b,i,Math.min(4096,b.length-i));}}finally{fs.closeSync(fd);}
  fs.renameSync(temp,file);
}
async function load(glue, bytes) {
  const logs=[], Module={noInitialRun:true,wasmBinary:bytes,
    print:x=>logs.push(String(x)),printErr:x=>logs.push(String(x)),
    instantiateWasm(imports, receive) {
      const module=new WebAssembly.Module(bytes),instance=new WebAssembly.Instance(module,imports);
      receive(instance,module);return instance.exports;
    }};
  const context=vm.createContext({Module,console,process,Buffer,require,module:{exports:{}},exports:{},
    __dirname:'/tmp',__filename:'/tmp/original-glue.js',setTimeout,clearTimeout,
    performance,TextDecoder,TextEncoder,WebAssembly});
  context.global=context;
  const originalListeners=process.listeners('uncaughtException');
  vm.runInContext(glue,context,{timeout:10000});
  for(const listener of process.listeners('uncaughtException')) {
    if(!originalListeners.includes(listener))process.removeListener('uncaughtException',listener);
  }
  if (!Module.calledRun) throw Error('Original glue runtime initialization did not complete');
  return {Module,logs,context};
}
async function main() {
  const root=process.argv[2],file=process.argv[3];
  const spec=JSON.parse(read(path.join(root,'results/runtime-mining/cross-dataset/proof-of-theft/glue-control-input.json')));
  const report={started_utc:new Date().toISOString(),node:process.version,v8:process.versions.v8,
    image_id:process.env.EXPERIMENT_IMAGE_ID,script_sha256:digest(read(__filename)),
    reference_url:spec.reference_url,reference_sha256:spec.reference_sha256,results:[]};
  for(const item of spec.modules) {
    const row={...item,outputs:[]};report.results.push(row);
    try {
      const bytes=read(path.join(root,item.object)),glue=read(path.join(root,item.glue));
      if(digest(bytes)!==item.sha256||digest(glue)!==item.glue_sha256)throw Error('Digest mismatch');
      const {Module:m,logs,context}=await load(glue.toString('utf8'),bytes);row.glue_logs=logs;
      if(item.family==='cryptonight-hash') {
        // Check the real exported interface, not just a generated JS wrapper.
        if(!item.exports.includes('cryptonight_hash'))throw Error('Published module has no cryptonight_hash export');
      }
      let input;
      if(item.family==='xmr-wasm') {input=context._malloc(4096);m._allocate_state();}
      for(const vector of spec.vectors) {
        let actual,nonce_unchanged=true;
        if(item.family==='webminerpoolhashcn') {
          const ptr=m.ccall('hash_cn','number',['string','number','number','number'],[vector.hex,0,0,0]);
          actual=Buffer.from(m.HEAPU8.buffer,ptr,64).toString('ascii');
        } else if(item.family==='xmr-wasm') {
          // Its public wrapper selects the CN variant from blob[0].
          if(Buffer.from(vector.hex,'hex')[0]>=7)continue;
          const blob=Buffer.from(vector.hex,'hex');m.HEAPU8.set(blob,input);
          const ptr=m._hash(input,blob.length,-1,-1,0);
          actual=Buffer.from(m.HEAPU8.buffer,ptr,32).toString('hex');
          nonce_unchanged=Buffer.from(m.HEAPU8.buffer,input+39,4).equals(blob.subarray(39,43));
        } else throw Error('Unsupported reviewed ABI');
        row.outputs.push({vector_id:vector.id,actual,expected:vector.expected,
          matches:actual===vector.expected,nonce_unchanged});
      }
      if(item.family==='xmr-wasm')m._free_state();
      row.status=row.outputs.length&&row.outputs.every(x=>x.matches&&x.nonce_unchanged)?'all applicable public vectors matched':'mismatch';
    }catch(e){row.status='failed';row.error=String(e.stack||e);}
    save(file,report);console.log(JSON.stringify({family:item.family,method:item.method,status:row.status,checked:row.outputs.length,error:row.error?.split('\n')[0]}));
  }
  report.finished_utc=new Date().toISOString();save(file,report);
}
module.exports={read,save,digest,load};
if(require.main===module)main().catch(e=>{console.error(e);process.exitCode=1;});
