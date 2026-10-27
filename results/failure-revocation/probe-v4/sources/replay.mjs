import fs from 'node:fs';
const spec=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const consumer=new WebAssembly.Module(fs.readFileSync(spec.consumer));
const rows=[];
for(const item of spec.cases) for(const mode of ['original','rollback','entry','address','refs']) {
  const table=new WebAssembly.Table({element:'anyfunc',initial:8});
  const memory=new WebAssembly.Memory({initial:1});
  const bias=new WebAssembly.Global({value:'i32',mutable:false},9);
  const out=new WebAssembly.Global({value:'anyfunc',mutable:true},null);
  const gate=new WebAssembly.Global({value:'i32',mutable:true},1);
  const held=[],during=[];
  const env={table,memory,bias,out,keep:f=>held.push(f),capture:()=>{
    if(['active','set','passive'].includes(item.route)) held.push(table.get(0));
    else if(item.route==='global') held.push(out.value);
    else if(item.route==='factory') held.push(table.get(1)());
    if(held.length!==1)throw new Error('capture failure');
    during.push(held[0](5));
  }, fail:()=>{throw new Error('controlled host failure')}};
  const binary=fs.readFileSync(item.binaries[mode==='rollback'?'original':mode]);
  let error=null,instance=null;
  try { instance=new WebAssembly.Instance(new WebAssembly.Module(binary),{env,__failure_gate:{alive:gate}}); }
  catch(e){
    if(e instanceof WebAssembly.RuntimeError)error='trap';
    else if(e.message==='controlled host failure')error='host-error';
    else throw e;
    gate.value=0;
    if(mode==='rollback') {for(let i=0;i<table.length;i++)table.set(i,null);out.value=null;}
  }
  const before=new DataView(memory.buffer).getUint32(0,true);
  const saved=new WebAssembly.Table({element:'anyfunc',initial:1});saved.set(0,held[0]);
  const c=new WebAssembly.Instance(consumer,{env:{table:saved}});
  const attempts=[];
  for(const [via,f] of [['host',held[0]],['wasm',c.exports.call]])for(const x of [-2147483648,-1,0,1,2147483647]) {
    let result;
    try {result={type:'return',value:f(x)}}catch(e){if(!(e instanceof WebAssembly.RuntimeError))throw e;result={type:'trap'}}
    attempts.push({via,x,result});
  }
  const after=new DataView(memory.buffer).getUint32(0,true);
  const identity=instance ? instance.exports.f===held[0] && instance.exports.factory()===held[0] : null;
  if(identity===false)throw new Error('identity mismatch');
  rows.push({name:item.name,mode,error,during,before,after,attempts,identity});
}
console.log(JSON.stringify({node:process.version,v8:process.versions.v8,rows}));
