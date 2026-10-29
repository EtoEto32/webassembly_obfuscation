'use strict';
const fs=require('fs'),crypto=require('crypto');
function read(file){const fd=fs.openSync(file,'r'),chunks=[];try{for(;;){const b=Buffer.alloc(4096),n=fs.readSync(fd,b,0,b.length);if(!n)break;chunks.push(b.subarray(0,n));}}finally{fs.closeSync(fd);}return Buffer.concat(chunks);}
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const raw=read('/inputs/plan.json'),plan=JSON.parse(raw);
if(sha(raw)!==process.env.PLAN_SHA256||process.platform!=='linux'||process.version!==plan.intended_node||process.versions.v8!==plan.intended_v8)throw Error('Plan/runtime mismatch');
for(const asset of plan.assets)if(sha(read('/inputs/'+asset.name))!==asset.sha256)throw Error('Asset mismatch');
const {load}=require('/inputs/glue-loader.cjs');
const report={status:'running',started_utc:new Date().toISOString(),plan_sha256:sha(raw),node:process.version,v8:process.versions.v8,counts:[],ablations:[]};
function save(){const b=Buffer.from(JSON.stringify(report,null,2)+'\n'),file='/outputs/paths.json',fd=fs.openSync(file+'.tmp','w');try{for(let i=0;i<b.length;)i+=fs.writeSync(fd,b,i,Math.min(4096,b.length-i));}finally{fs.closeSync(fd);}fs.renameSync(file+'.tmp',file);}
async function main(){
  for(const artifact of [...plan.path_diagnostic.artifacts,...plan.path_diagnostic.ablations]){
    for(const vector of plan.path_diagnostic.vectors){
      const host=await load(read('/inputs/'+artifact.glue).toString('utf8'),read('/inputs/'+artifact.wasm));
      const m=host.Module,wasm=m.asm;
      const counts=()=>Object.fromEntries((artifact.counters||[]).map(name=>[name,String(wasm['followup_count_'+name].value)]));
      const zero=counts(),ptr=host.context._malloc(4096);m._allocate_state();const allocated=counts();
      m.HEAPU8.set(Buffer.from(vector.hex,'hex'),ptr);const q=m._hash(ptr,Buffer.from(vector.hex,'hex').length,-1,-1,0);
      const actual=Buffer.from(m.HEAPU8.buffer,q,32).toString('hex');const hashed=counts();
      if(actual!==vector.expected)throw Error('Output mismatch '+artifact.id+'/'+vector.id);
      if(!Buffer.from(m.HEAPU8.buffer,ptr+39,4).equals(Buffer.from(vector.hex,'hex').subarray(39,43)))throw Error('Nonce changed');
      m._free_state();const freed=counts();
      const row={id:artifact.id,vector_id:vector.id,actual,expected:vector.expected,nonce_unchanged:true};
      if(artifact.counters){row.snapshots={before_allocate:zero,after_allocate:allocated,after_hash:hashed,after_free:freed};row.hash_deltas=Object.fromEntries(artifact.counters.map(name=>[name,String(BigInt(hashed[name])-BigInt(allocated[name]))]));report.counts.push(row);}
      else report.ablations.push(row);
      save();
    }
  }
  report.status='complete';report.finished_utc=new Date().toISOString();save();console.log(JSON.stringify({status:report.status,counts:report.counts.length,ablations:report.ablations.length}));
}
main().catch(error=>{report.status='failed';report.error=String(error.stack||error);save();console.error(error);process.exitCode=1;});
