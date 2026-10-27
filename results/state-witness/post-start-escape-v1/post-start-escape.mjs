import fs from 'node:fs';import path from 'node:path';import crypto from 'node:crypto';
const out=process.argv[2],data=JSON.parse(fs.readFileSync(path.join(out,'manifest.json')));
for(const row of data.rows){
  const bytes=fs.readFileSync(path.join(out,row.source)),results=[];if(!WebAssembly.validate(bytes))throw Error('validation');
  for(const drop of [false,true]){
    let captured;const ex=(await WebAssembly.instantiate(bytes,{env:{capture:f=>captured=f}})).instance.exports;
    if(drop)ex.retire();const beforeSha256=crypto.createHash('sha256').update(new Uint8Array(ex.memory.buffer)).digest('hex');
    const f=row.kind==='start-import'?captured:row.kind==='global'?ex.handle.value:ex.handle.get(0);let outcome='return';
    try{f();}catch(e){if(!(e instanceof WebAssembly.RuntimeError))throw e;outcome='trap';}
    results.push({outcome,beforeSha256,firstByte:new Uint8Array(ex.memory.buffer)[0]});
  }
  if(JSON.stringify(results)!==JSON.stringify(row.results))throw Error(row.kind);
}
console.log(JSON.stringify({pairs:data.rows.length,referenceCalls:2*data.rows.length,preparationCalls:data.rows.length,status:'pass'}));
