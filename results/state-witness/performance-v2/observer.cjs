'use strict';
// These functions never invoke a guest function except generated observers.
function call(fn,args=[]) {
  try { const x=fn(...args);return {value:typeof x==='bigint'?x.toString():x??null}; }
  catch(e) { if(e instanceof WebAssembly.RuntimeError)return {trap:true};throw e; }
}
function snapshot(instance,manifest,options={segments:true,bounds:true}) {
  const e=instance.exports, out={globals:[],segments:[]};
  if(manifest.memory) {
    out.pages=e.__sw_pages()>>>0;
    if(out.pages>256)throw Error('State outside research memory budget');
    if(options.bounds)out.memoryEnd=call(e.__sw_memory_end);
    if(e.__sw_memory)out.memory=Buffer.from(new Uint8Array(e.__sw_memory.buffer,0,out.pages*65536));
    else {out.memory=Buffer.alloc(out.pages*65536);for(let i=0;i<out.memory.length;i++)out.memory[i]=e.__sw_byte(i);}
  }
  if(manifest.table) {
    const refs=new Map();
    if(manifest.profile==='full')for(let i=0;i<manifest.functions;i++){
      const fn=e['__sw_func_'+i];if(!refs.has(fn))refs.set(fn,[]);refs.get(fn).push(i);
    }
    // Optimizers may make several original canonical exports refer to one function.
    // Keep the entire alias class rather than silently overwriting its identity.
    if(manifest.profile==='full')out.functionAliases=[...refs.values()].filter(x=>x.length>1);
    for(let t=0;t<(manifest.tableCount??1);t++){
      const suffix=t===0?'':'_'+t, len='length'+suffix,tab='table'+suffix;
      out[len]=e['__sw_length'+suffix]()>>>0;out[tab]=[];
      if(out[len]>4096)throw Error('State outside research table budget');
      if(options.bounds)out['tableEnd'+suffix]=call(e['__sw_table_end'+suffix]);
      for(let i=0;i<out[len];i++) {
        if(manifest.profile==='numeric')out[tab].push(e['__sw_null'+suffix](i)?null:'nonnull');
        else {const ref=e['__sw_ref'+suffix](i);if(ref!==null&&!refs.has(ref))throw Error('unmapped function reference');out[tab].push(ref===null?null:refs.get(ref));}
      }
    }
  }
  for(const g of manifest.globals)out.globals.push(call(e['__sw_global_'+g.index]));
  if(options.segments)for(const s of manifest.segments)out.segments.push(s.probe?call(e[s.probe]):{unobservable:true});
  return out;
}
function difference(a,b) {
  const diff=[];
  for(const key of new Set([...Object.keys(a),...Object.keys(b)])) {
    const same=key==='memory'?a[key]?.equals(b[key]):JSON.stringify(a[key])===JSON.stringify(b[key]);
    if(!same)diff.push(key);
  }
  return diff;
}
module.exports={call,snapshot,difference};
