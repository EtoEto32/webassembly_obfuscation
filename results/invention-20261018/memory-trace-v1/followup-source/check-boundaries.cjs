'use strict';
// Validate the instrumentation itself at actual load traps, including memarg
// offsets whose addition MUST NOT wrap to i32 before the load.
const fs = require('fs');
const path = require('path');
const cp = require('child_process');
const crypto = require('crypto');
const root = path.resolve(__dirname, '../..');
const tools = process.env.WASM_TOOLS_ROOT || path.join(root,'.tools');
const out = path.resolve(process.argv[2]);
const python = process.argv[3] || 'python';
fs.mkdirSync(out, {recursive: false});
const run = (exe,args) => cp.execFileSync(exe,args,{encoding:'utf8',timeout:30000});
const wabt = (name,args) => run(path.join(tools,'wabt-1.0.42/bin',name+'.exe'), args);
const hash = p => crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const bytes = new Uint8Array(65536);
const samples = [255,128,1,127,0,254,33,89,101,201,17,222,77,155,64,3];
bytes.set(samples,0); bytes.set(samples,65520);
const escaped = samples.map(x=>'\\'+x.toString(16).padStart(2,'0')).join('');
const cases = [0,1,2,3,15,16,65519,65520,65528,65531,65532,65533,65534,65535,65536,65537,0x7fffffff,0xffffffff];
const rows = [];
const outcomes = f => {try{return {value:f()};}catch(e){if(!(e instanceof WebAssembly.RuntimeError))throw e;return {trap:e.message};}};
const same = (a,b) => JSON.stringify(a)===JSON.stringify(b);
for (const [op,width,signed] of [['i32.load',4,true],['i32.load8_s',1,true],['i32.load8_u',1,false],['i32.load16_s',2,true],['i32.load16_u',2,false]]) {
  for (const offset of [0,65535,0xffffffff]) {
    const stem = op.replace('.','-')+'-'+offset;
    const wat = path.join(out,stem+'.wat'), wasm = path.join(out,stem+'.wasm'), trace = path.join(out,stem+'-traced.wasm');
    // Calling through an existing helper also checks preservation of function
    // references when two function imports are inserted.
    fs.writeFileSync(wat,`(module (memory 1)
      (data (i32.const 0) "${escaped}") (data (i32.const 65520) "${escaped}")
      (func $read (param i32) (result i32) (${op} offset=${offset} (local.get 0)))
      (func (export "run") (param i32) (result i32) (call $read (local.get 0))))`);
    wabt('wat2wasm',[wat,'-o',wasm]);
    run(python,[path.join(__dirname,'instrument.py'),wasm,trace]);
    const normal = new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(wasm))).exports.run;
    let before=[],after=[];
    const audited = new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(trace)),{audit:{
      before(s,a,o){before.push((a>>>0)+(o>>>0));return a;},
      after(s,a,o,v){after.push((a>>>0)+(o>>>0));return v;}
    }}).exports.run;
    const checks=[];
    for(const p of cases){
      before=[];after=[];
      const address=(p>>>0)+offset;
      let want;
      if(address+width>65536) want={trap:'memory access out of bounds'};
      else {const dv=new DataView(bytes.buffer);want={value:width===4?dv.getInt32(address,true):width===2?(signed?dv.getInt16(address,true):dv.getUint16(address,true)):(signed?dv.getInt8(address):dv.getUint8(address))};}
      const a=outcomes(()=>normal(p)),b=outcomes(()=>audited(p));
      checks.push({p,address,want,normal:a,audited:b,before:[...before],after:[...after],
        equal:same(want,a)&&same(want,b)&&before.length===1&&before[0]===address&&after.length===(want.trap?0:1)});
    }
    rows.push({op,offset,width,signed,wasm:path.basename(wasm),traced:path.basename(trace),sha256:hash(wasm),traced_sha256:hash(trace),checks});
  }
}
const total=rows.reduce((n,r)=>n+r.checks.length*2,0);
const bad=rows.reduce((n,r)=>n+r.checks.filter(x=>!x.equal).length,0);
const result={node:process.version,v8:process.versions.v8,script_sha256:hash(__filename),
  instrumenter_sha256:hash(path.join(__dirname,'instrument.py')),total_executions:total,mismatched_input_conditions:bad,rows};
fs.writeFileSync(path.join(out,'checks.json'),JSON.stringify(result,null,2));
console.log(JSON.stringify({total_executions:total,mismatched_input_conditions:bad}));
if(bad)process.exitCode=1;
