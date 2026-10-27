import fs from 'node:fs';import path from 'node:path';
const out=process.argv[2],data=JSON.parse(fs.readFileSync(path.join(out,'manifest.json')));
let calls=0;
for(const row of data.rows){
  const results=[],bytes=fs.readFileSync(path.join(out,row.source));
  for(let side=0;side<2;side++){
    let ex,trace=[],current=new Map(),block=0,refs=new Map();
    const reference=value=>{if(!refs.has(value)){const body=[0x00,0x41];let n=BigInt(value);while(true){let b=Number(n&127n);n>>=7n;const end=(n===0n&&(b&64)===0)||(n===-1n&&(b&64)!==0);body.push(b|(end?0:128));if(end)break;}body.push(0x0b);const wasm=Uint8Array.from([0,97,115,109,1,0,0,0,1,5,1,96,0,1,127,3,2,1,0,7,5,1,1,102,0,0,10,body.length+2,1,body.length,...body]);refs.set(value,new WebAssembly.Instance(new WebAssembly.Module(wasm)).exports.f);}return refs.get(value);};
    const snapshot=()=>row.kind==='memory'?[...new Uint8Array(ex.resource.buffer,0,2)]:[0,1].map(n=>{const f=ex.resource.get(n);if(f===null)return 256;const v=f();return ({101:259,202:260})[v]??v;});
    const touch=()=>{trace.push({name:'touch'});for(const [cell,value]of current.get(block)??[]){if(row.kind==='memory')new Uint8Array(ex.resource.buffer)[cell]=value;else ex.resource.set(cell%2**32,reference(value));}block++;};
    const observe=()=>{trace.push({name:'observe',read:snapshot()});block++;};
    ex=(await WebAssembly.instantiate(bytes,{env:{touch,observe}})).instance.exports;
    if(row.kind==='table')refs=new Map([[256,null],[259,ex.resource.get(0)],[260,ex.resource.get(1)]]);
    ex[side?'release_b':'retire']();
    for(const [cell,value]of row.values)if(row.kind==='memory')new Uint8Array(ex.resource.buffer)[cell]=value;else ex.resource.set(cell%2**32,reference(value));
    const output=[];for(const call of row.witness.calls){trace=[];block=0;current=new Map(call.writes.map(r=>[r.block,r.cells]));let outcome='return';try{ex[call.name]();}catch(e){if(!(e instanceof WebAssembly.RuntimeError))throw e;outcome='trap';}output.push({outcome,trace});calls++;}results.push(output);
  }
  if(JSON.stringify(results)!==JSON.stringify(row.results))throw Error('engine difference: '+JSON.stringify(row));
}
console.log(JSON.stringify({pairs:data.rows.length,apiCalls:calls,preparationCalls:2*data.rows.length,status:'pass',node:process.version}));
