'use strict';
const assert=require('node:assert/strict');const {call}=require('./observer.cjs');
function snapshot(e,m){
  const out={globals:[],segments:[],tables:[]},refs=new Map();
  for(let i=0;i<m.functions;i++){
    const ref=e.__sw_directory.get(i);assert.equal(typeof ref,'function');
    if(!refs.has(ref))refs.set(ref,[]);refs.get(ref).push(i);
  }
  out.aliases=[...refs.values()].filter(x=>x.length>1);
  if(m.memory){
    out.pages=e.__sw_pages()>>>0;if(out.pages>256)throw Error('Logical memory exceeds 256-page profile');
    out.memory=Buffer.from(new Uint8Array(e.__sw_memory.buffer,0,out.pages*65536));
    out.memoryEnd=call(e.__sw_memory_end);
  }
  for(let t=0;t<m.tableCount;t++){
    const suffix=t?'_'+t:'',n=e['__sw_length'+suffix]()>>>0,table=[];
    if(n>4096)throw Error('Logical table exceeds 4096-entry profile');
    for(let i=0;i<n;i++){
      const ref=e['__sw_table'+suffix].get(i);
      if(ref!==null&&!refs.has(ref))throw Error('Unmapped function reference');
      table.push(ref===null?null:refs.get(ref));
    }
    out.tables.push({length:n,values:table,end:call(e['__sw_table_end'+suffix])});
  }
  for(const g of m.globals)out.globals.push(call(e['__sw_global_'+g.index]));
  for(const s of m.segments)out.segments.push(s.probe?call(e[s.probe]):{unobservable:true});
  return out;
}
module.exports={snapshot};
