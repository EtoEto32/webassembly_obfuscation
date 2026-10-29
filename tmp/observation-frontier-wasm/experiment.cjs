const fs=require('node:fs');
const path=require('node:path');
const cp=require('node:child_process');
const crypto=require('node:crypto');
const root=__dirname;
const tools=process.env.WASM_TOOLS_ROOT||'C:/Users/ettotto/Documents/webassembly_obfuscation/.tools';
const wat2wasm=path.join(tools,'wabt-1.0.42/bin/wat2wasm.exe');
const wasm2wat=path.join(tools,'wabt-1.0.42/bin/wasm2wat.exe');
const opt=path.join(tools,'binaryen-version_133/bin/wasm-opt.exe');
function run(exe,args){return cp.execFileSync(exe,args,{encoding:'utf8',timeout:30000}).trim();}
function sha(file){return crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');}
const expressions={P:'(i32.add (i32.add (local.get $a) (local.get $b)) (local.get $c))',Q:'(i32.add (local.get $a) (i32.add (local.get $b) (local.get $c)))'};
function prepare(){
 const out=path.join(root,'artifacts'); if(fs.existsSync(out))throw Error('Refuse overwrite artifacts'); fs.mkdirSync(out);
 const variants=[];
 for(const [name,expr] of Object.entries(expressions))for(const context of [false,true]){
  const label=name+(context?'_context':'');
  const body=context?`(i32.add ${expr} (i32.mul (local.get $c) (local.get $c)))`:expr;
  const source=path.join(out,label+'.wat');fs.writeFileSync(source,`(module (func $eval (export "eval") (param $a i32) (param $b i32) (param $c i32) (result i32) ${body}))\n`);
  const raw=path.join(out,label+'_raw.wasm'); run(wat2wasm,[source,'-o',raw]);
  const optimized=path.join(out,label+'_O2.wasm');run(opt,[raw,'-O2','-o',optimized]);
  for(const [mode,binary] of [['raw',raw],['O2',optimized]]){
   const dis=path.join(out,label+'_'+mode+'.dis.wat');run(wasm2wat,[binary,'--generate-names','-o',dis]);
   variants.push({name:label+'_'+mode,context,binary,dis,sha256:sha(binary),bytes:fs.statSync(binary).size});
  }
 }
 fs.writeFileSync(path.join(out,'variants.json'),JSON.stringify({versions:{wabt:run(wat2wasm,['--version']),binaryen:run(opt,['--version']),node:process.version,v8:process.versions.v8},variants},null,2));
 return variants;
}
if(require.main===module)prepare();
module.exports={prepare,run,sha,root,wat2wasm,wasm2wat};
