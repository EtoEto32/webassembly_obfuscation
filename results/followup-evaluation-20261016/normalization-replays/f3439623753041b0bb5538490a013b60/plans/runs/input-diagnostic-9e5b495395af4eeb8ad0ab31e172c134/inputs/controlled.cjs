'use strict';
const fs=require('fs'),crypto=require('crypto');
function read(file){const fd=fs.openSync(file,'r'),chunks=[];try{for(;;){const b=Buffer.alloc(4096),n=fs.readSync(fd,b,0,b.length);if(!n)break;chunks.push(b.subarray(0,n));}}finally{fs.closeSync(fd);}return Buffer.concat(chunks);}
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const raw=read('/inputs/plan.json'),plan=JSON.parse(raw);
if(sha(raw)!==process.env.PLAN_SHA256||process.version!==plan.intended_node||process.versions.v8!==plan.intended_v8||process.platform!=='linux')throw Error('Runtime/plan mismatch');
for(const a of plan.assets)if(sha(read('/inputs/'+a.name))!==a.sha256)throw Error('Asset mismatch');
const {load}=require('/inputs/glue-loader.cjs');
const report={status:'running',plan_sha256:sha(raw),started_utc:new Date().toISOString(),reference_public:[],additional_vectors:[],checks:[]};
function save(){const b=Buffer.from(JSON.stringify(report,null,2)+'\n'),file='/outputs/controlled-checks.json',fd=fs.openSync(file+'.tmp','w');try{for(let i=0;i<b.length;)i+=fs.writeSync(fd,b,i,Math.min(4096,b.length-i));}finally{fs.closeSync(fd);}fs.renameSync(file+'.tmp',file);}
async function prepare(artifact){
  if(artifact.family==='swamped'){
    const h=require('/inputs/host-original.cjs').load(read('/inputs/'+artifact.file));
    return {hash:v=>{if(Buffer.from(v.hex,'hex').length!==76)throw Error('Input contract');h.hash(v);return h.output();},close:()=>h.close()};
  }
  const h=await load(read('/inputs/'+artifact.glue).toString('utf8'),read('/inputs/'+artifact.file)),m=h.Module;
  if(artifact.family==='webminerpoolhashcn')return {
    hash:v=>Buffer.from(m.HEAPU8.buffer,m.ccall('hash_cn','number',['string','number','number','number'],[v.hex,0,0,0]),64).toString('ascii'),close:()=>{}};
  const ptr=h.context._malloc(4096);m._allocate_state();
  return {hash:v=>{const data=Buffer.from(v.hex,'hex');if(data[0]>=7||data.length!==76)throw Error('xmr cn/0 contract');m.HEAPU8.set(data,ptr);const q=m._hash(ptr,76,-1,-1,0);if(!Buffer.from(m.HEAPU8.buffer,ptr+39,4).equals(data.subarray(39,43)))throw Error('Nonce changed');return Buffer.from(m.HEAPU8.buffer,q,32).toString('hex');},close:()=>m._free_state()};
}
async function main(){
  const ref=await prepare({family:'webminerpoolhashcn',file:'webminerpoolhashcn.wasm',glue:'webminerpoolhashcn.js'});
  try{
    for(const v of plan.public_vectors){const actual=ref.hash(v);if(actual!==v.expected)throw Error('Reference public mismatch');report.reference_public.push({id:v.id,actual,expected:v.expected});}
    for(const v of plan.controlled.additional_vectors)report.additional_vectors.push({...v,expected:ref.hash(v),oracle:'Separately distributed webminerpoolhashcn cn/0; shared lineage, not a formal independent proof.'});
  }finally{ref.close();}save();
  for(const artifact of plan.controlled.artifacts){
    const vectors=[...plan.public_vectors,...report.additional_vectors].filter(v=>artifact.family!=='xmr-wasm'||Buffer.from(v.hex,'hex')[0]<7);
    for(const mode of ['fresh-each','forward','reverse']){
      let h=mode==='fresh-each'?null:await prepare(artifact);
      try{
        for(const v of mode==='reverse'?[...vectors].reverse():vectors){
          if(mode==='fresh-each')h=await prepare(artifact);
          try{const actual=h.hash(v);if(actual!==v.expected){report.failed_check={artifact_id:artifact.id,mode,vector_id:v.id,actual,expected:v.expected};throw Error('Controlled output mismatch');}
            report.checks.push({artifact_id:artifact.id,family:artifact.family,mode,vector_id:v.id,actual,expected:v.expected});
          }finally{if(mode==='fresh-each')h.close();}
        }
      }finally{if(mode!=='fresh-each')h.close();}
    }
    save();console.log(JSON.stringify({artifact_id:artifact.id,checked:report.checks.length}));
  }
  report.status='complete';report.finished_utc=new Date().toISOString();save();
}
main().catch(error=>{report.status='failed';report.error=String(error.stack||error);save();console.error(error);process.exitCode=1;});
