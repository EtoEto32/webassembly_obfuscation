import fs from 'node:fs';import path from 'node:path';
const out=process.argv[2],data=JSON.parse(fs.readFileSync(path.join(out,'manifest.json')));
let pairs=0;
for(const row of data.rows){
  const results=[];const bytes=fs.readFileSync(path.join(out,row.source));if(!WebAssembly.validate(bytes))throw Error('validation');
  for(let side=0;side<2;side++){
    let ex,trace=[],refs=[];
    const snap=()=>row.kind==='memory'?[...new Uint8Array(ex.resource.buffer,0,2)]:[0,1].map(n=>{const f=ex.resource.get(n);return f===null?256:({101:259,202:260})[f()];});
    const touch=()=>{trace.push({name:'touch'});for(let cell=0;cell<2;cell++)if(row.mask&(1<<cell)){if(row.kind==='memory')new Uint8Array(ex.resource.buffer)[cell]=[65,66,0][row.value];else ex.resource.set(cell,refs[row.value]);}};
    const observe=()=>trace.push({name:'observe',read:snap()});
    ex=(await WebAssembly.instantiate(bytes,{env:{touch,observe}})).instance.exports;refs=row.kind==='table'?[ex.resource.get(0),ex.resource.get(1),null]:[];ex[side?'release_b':'retire']();
    for(let cell=0;cell<2;cell++)if(row.kind==='memory')new Uint8Array(ex.resource.buffer)[cell]=[65,66][row.initial[cell]];else ex.resource.set(cell,refs[row.initial[cell]]);
    const result=[];for(const name of ['arm','finish']){trace=[];let outcome='return';try{ex[name]();}catch(e){if(!(e instanceof WebAssembly.RuntimeError))throw e;outcome='trap';}result.push({outcome,trace});}results.push(result);
  }
  if(JSON.stringify(results)!==JSON.stringify(row.results))throw Error('engine difference: '+JSON.stringify(row));pairs++;
}
console.log(JSON.stringify({pairs,entryCalls:4*pairs,preparationCalls:2*pairs,status:'pass',node:process.version}));
