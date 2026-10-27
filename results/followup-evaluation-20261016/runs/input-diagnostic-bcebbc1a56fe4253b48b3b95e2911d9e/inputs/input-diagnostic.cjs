'use strict';
// Diagnosis of the existing fixed-width entry; original Wasm and host remain unchanged.
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const {performance}=require('perf_hooks');
function read(file){const fd=fs.openSync(file,'r'),chunks=[];try{for(;;){const b=Buffer.alloc(4096),n=fs.readSync(fd,b,0,b.length);if(!n)break;chunks.push(b.subarray(0,n));}}finally{fs.closeSync(fd);}return Buffer.concat(chunks);}
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const raw=read('/inputs/plan.json'),plan=JSON.parse(raw);
if(sha(raw)!==process.env.PLAN_SHA256 || process.platform!=='linux' || process.version!==plan.intended_node || process.versions.v8!==plan.intended_v8)throw Error('Plan/runtime mismatch');
for(const a of plan.assets)if(sha(read('/inputs/'+a.name))!==a.sha256)throw Error('Asset mismatch '+a.name);
const original=require('/inputs/host-original.cjs'),diagnostic=require('/inputs/host-diagnostic.cjs');
const report={started_utc:new Date().toISOString(),node:process.version,v8:process.versions.v8,
  plan_sha256:sha(raw),status:'running',public_checks:[],length_argument_checks:[],
  history_checks:[],tail_checks:[],boundary_checks:[],reference_checks:[]};
function save(){const data=Buffer.from(JSON.stringify(report,null,2)+'\n');const file='/outputs/input-diagnostic.json';const fd=fs.openSync(file+'.tmp','w');try{for(let i=0;i<data.length;){i+=fs.writeSync(fd,data,i,Math.min(4096,data.length-i));}}finally{fs.closeSync(fd);}fs.renameSync(file+'.tmp',file);}
function requireEqual(actual,expected,context){if(actual!==expected){report.failed_check={context,actual,expected};throw Error('Mismatch '+context);}}
const canonical=new Map();
function effectiveHash(bytes,prefix){const h=diagnostic.load(bytes);try{h.hash({hex:prefix.toString('hex')});return h.output();}finally{h.close();}}
async function main(){
  const baseline=read('/inputs/'+plan.cases[0].file);
  for(const c of plan.cases){
    const bytes=read('/inputs/'+c.file);
    for(const v of plan.public_vectors){
      const h=original.load(bytes);try{h.hash(v);requireEqual(h.output(),v.expected,c.id+'/'+v.id);report.public_checks.push({case_id:c.id,id:v.id,actual:h.output(),expected:v.expected});}finally{h.close();}
    }
    for(const length of plan.input_diagnostic.length_arguments){
      const h=diagnostic.load(bytes),v=plan.public_vectors[0];
      try{const d=h.diagnostic;new Uint8Array(d.memory.buffer).set(Buffer.from(v.hex,'hex'),d.input);
        d.exports._cryptonight_hash_variant_0(d.ctx,d.input,d.output,length);
        requireEqual(h.output(),v.expected,c.id+'/length-argument/'+length);
        report.length_argument_checks.push({case_id:c.id,argument:length,actual:h.output(),matches_public_76:true});
      }finally{h.close();}
    }
    for(const length of plan.input_diagnostic.short_lengths){
      const v=plan.additional_vectors.find(v=>v.id==='differential-length-'+length);
      for(const history of ['fresh','public0','public1']){
        for(const fill of ['retain','zero','ff']){
          const h=diagnostic.load(bytes);
          try{if(history!=='fresh')h.hash(plan.public_vectors[history==='public0'?0:1]);
            const d=h.diagnostic,heap=new Uint8Array(d.memory.buffer);
            if(fill!=='retain')heap.fill(fill==='zero'?0:255,d.input,d.input+256);
            heap.set(Buffer.from(v.hex,'hex'),d.input);
            const prefix=Buffer.from(d.memory.buffer,d.input,76).toString('hex');
            h.hash(v);const actual=h.output(),expected=effectiveHash(baseline,Buffer.from(prefix,'hex'));
            requireEqual(actual,expected,c.id+'/history/'+length+'/'+history+'/'+fill);
            canonical.set(prefix,expected);
            report.history_checks.push({case_id:c.id,length,history,fill,effective_input_76_hex:prefix,actual,canonical_expected:expected});
          }finally{h.close();}
        }
      }
    }
    for(const fill of [0,255]){
      const h=diagnostic.load(bytes),v=plan.public_vectors[0];
      try{const d=h.diagnostic;new Uint8Array(d.memory.buffer).fill(fill,d.input+76,d.input+256);
        h.hash(v);requireEqual(h.output(),v.expected,c.id+'/tail/'+fill);
        report.tail_checks.push({case_id:c.id,tail_fill:fill,actual:h.output(),matches_public:true});
      }finally{h.close();}
    }
    for(const index of [75,76]){
      const h=diagnostic.load(bytes),v=plan.public_vectors[0],data=Buffer.alloc(77);
      Buffer.from(v.hex,'hex').copy(data);data[index]^=1;
      try{h.hash({hex:data.toString('hex')});const output=h.output();
        if((output===v.expected)!==(index===76))throw Error('Unexpected input boundary '+index);
        canonical.set(data.subarray(0,76).toString('hex'),output);
        report.boundary_checks.push({case_id:c.id,changed_byte:index,actual:output,matches_original:output===v.expected});
      }finally{h.close();}
    }
    save();console.log(JSON.stringify({case_id:c.id,phase:'input-diagnostic-complete'}));
  }
  const {load}=require('/inputs/glue-loader.cjs');
  for(const ref of plan.references){
    const host=await load(read('/inputs/'+ref.glue).toString('utf8'),read('/inputs/'+ref.wasm));
    const m=host.Module;let ptr;
    if(ref.family==='xmr-wasm'){ptr=host.context._malloc(4096);m._allocate_state();}
    try{
      // Verify both reference implementations before using arbitrary effective buffers.
      for(const v of plan.public_vectors){
        if(ref.family==='xmr-wasm'&&Buffer.from(v.hex,'hex')[0]>=7)continue;
        const actual=ref.family==='webminerpoolhashcn'
          ?Buffer.from(m.HEAPU8.buffer,m.ccall('hash_cn','number',['string','number','number','number'],[v.hex,0,0,0]),64).toString('ascii')
          :(()=>{m.HEAPU8.set(Buffer.from(v.hex,'hex'),ptr);const q=m._hash(ptr,76,-1,-1,0);return Buffer.from(m.HEAPU8.buffer,q,32).toString('hex');})();
        requireEqual(actual,v.expected,ref.family+'/public/'+v.id);
        report.reference_checks.push({family:ref.family,kind:'public',id:v.id,actual,expected:v.expected});
      }
      for(const [hex,expected] of canonical){
        if(ref.family==='xmr-wasm'&&Buffer.from(hex,'hex')[0]>=7)continue;
        const actual=ref.family==='webminerpoolhashcn'
          ?Buffer.from(m.HEAPU8.buffer,m.ccall('hash_cn','number',['string','number','number','number'],[hex,0,0,0]),64).toString('ascii')
          :(()=>{m.HEAPU8.set(Buffer.from(hex,'hex'),ptr);const q=m._hash(ptr,76,-1,-1,0);return Buffer.from(m.HEAPU8.buffer,q,32).toString('hex');})();
        requireEqual(actual,expected,ref.family+'/effective-buffer');
        report.reference_checks.push({family:ref.family,kind:'effective-76-byte-buffer',hex,actual,expected});
      }
    }finally{if(ref.family==='xmr-wasm')m._free_state();}
    save();
  }
  report.unique_effective_buffers=canonical.size;report.status='complete';report.finished_utc=new Date().toISOString();save();
  console.log(JSON.stringify({status:report.status,public:report.public_checks.length,history:report.history_checks.length,references:report.reference_checks.length}));
}
main().catch(error=>{report.status='failed';report.error=String(error.stack||error);save();console.error(error);process.exitCode=1;});
