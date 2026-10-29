import fs from 'node:fs';import path from 'node:path';import crypto from 'node:crypto';
const out=process.argv[2],cases=JSON.parse(fs.readFileSync(path.join(out,'controls.json'))).dynamic;
const hash=b=>crypto.createHash('sha256').update(new Uint8Array(b)).digest('hex');
let calls=0;
for(const row of cases){
  const bytes=fs.readFileSync(path.join(out,row.file));
  if(!WebAssembly.validate(bytes))throw Error(`validation failed: ${row.file}`);
  const outcomes=[];
  for(const drop of [false,true]){
    const ex=(await WebAssembly.instantiate(bytes)).instance.exports;
    if(drop)ex.retire();
    const initialMemory=hash(ex.memory.buffer);let outcome='return';
    try{ex.entry();}catch(e){if(!(e instanceof WebAssembly.RuntimeError))throw e;outcome='trap';}
    outcomes.push({outcome,memory:hash(ex.memory.buffer),initialMemory});calls++;
  }
  if(JSON.stringify(outcomes)!==JSON.stringify(row.outcomes))throw Error(`engine mismatch: ${row.file}`);
}
console.log(JSON.stringify({engine:process.version,v8:process.versions.v8,pairs:cases.length,entryCalls:calls,preparationCalls:cases.length,status:'pass'}));
