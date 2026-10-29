// Small rejection experiment; not a general Wasm transformer.
const fs = require('node:fs');
const path = require('node:path');
const cp = require('node:child_process');
const crypto = require('node:crypto');
const root = __dirname;
const output = path.join(root, 'artifacts');
if (fs.existsSync(output)) throw new Error('Preserve existing results');
fs.mkdirSync(output);
const tools = process.env.WASM_TOOLS_ROOT;
if (!tools) throw new Error('Set WASM_TOOLS_ROOT');
const compiler = path.join(tools, 'wabt-1.0.42/bin/wat2wasm.exe');
const optimizer = path.join(tools, 'binaryen-version_133/bin/wasm-opt.exe');
const variants = {
  strict: '(drop (i32.div_u (local.get $x) (local.get $y)))',
  naive: '',
  checked: '(if (i32.eqz (local.get $y)) (then unreachable))',
};
const inputs=[];
const boundary=[0,1,2,3,0x7fffffff,0x80000000,0xfffffffe,0xffffffff];
for (const x of boundary) for(const y of boundary) for(const k of [0,1,2,7,16,31,32,33]) inputs.push([x,y,k]);
// BigInt independent reference: observable trap and global at termination.
function reference(x,y,k,previous) {
  if (y===0) return {trap:true,stage:0,value:previous};
  const mask=(1n<<BigInt(k%32))-1n;
  return {trap:false,stage:1,value:Number((BigInt(x)*BigInt(x))&mask)};
}
function invoke(exports, args) {
  try { return {trap:false,stage:(exports.run(...args),exports.stage.value),value:exports.result.value>>>0}; }
  catch (error) {if (!(error instanceof WebAssembly.RuntimeError)) throw error; return {trap:true,stage:exports.stage.value,value:exports.result.value>>>0};}
}
async function main() {
  const rows=[];
  for(const [variant,effect] of Object.entries(variants)) {
    const wat=`(module
      (global $stage (export "stage") (mut i32) (i32.const 0))
      (global $result (export "result") (mut i32) (i32.const 0))
      (func (export "run") (param $x i32) (param $y i32) (param $k i32)
        (global.set $stage (i32.const 0))
        ${effect}
        (global.set $stage (i32.const 1))
        (global.set $result (i32.and
          (i32.mul (local.get $x) (local.get $x))
          (i32.sub (i32.shl (i32.const 1) (local.get $k)) (i32.const 1))))))`;
    const base=path.join(output,variant);
    fs.writeFileSync(base+'.wat',wat);
    cp.execFileSync(compiler,[base+'.wat','-o',base+'.wasm']);
    cp.execFileSync(optimizer,[base+'.wasm','-O2','-o',base+'.O2.wasm']);
    for(const suffix of ['', '.O2']) {
      const file=base+suffix+'.wasm';
      const bytes=fs.readFileSync(file);
      const {instance}=await WebAssembly.instantiate(bytes);
      let mismatches=0,traps=0,previous=0;
      const failures=[];
      for(const input of inputs) {
        const actual=invoke(instance.exports,input),expected=reference(...input,previous);
        previous=expected.value;
        traps+=actual.trap;
        if(JSON.stringify(actual)!==JSON.stringify(expected)) {mismatches++;failures.push({input,actual,expected});}
      }
      rows.push({variant,optimized:!!suffix,inputCount:inputs.length,mismatches,traps,
        bytes:bytes.length,sha256:crypto.createHash('sha256').update(bytes).digest('hex'),failures});
    }
  }
  const result={node:process.version,v8:process.versions.v8,
    wabt:cp.execFileSync(compiler,['--version'],{encoding:'utf8'}).trim(),
    binaryen:cp.execFileSync(optimizer,['--version'],{encoding:'utf8'}).trim(),inputs,rows};
  fs.writeFileSync(path.join(output,'results.json'),JSON.stringify(result,null,2));
  console.log(JSON.stringify(rows.map(({failures,...r})=>r),null,2));
  if(rows.some(r=>r.variant==='naive'?r.mismatches!==64:r.mismatches!==0)) throw new Error('Unexpected outcome');
}
main().catch(e=>{console.error(e);process.exitCode=1;});
