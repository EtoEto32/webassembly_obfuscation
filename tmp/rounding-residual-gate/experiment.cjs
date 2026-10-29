const fs=require('node:fs'),path=require('node:path'),cp=require('node:child_process'),crypto=require('node:crypto');
const root=__dirname, out=path.join(root,'artifacts');
if(fs.existsSync(out))throw Error('Refuse overwrite artifacts');
fs.mkdirSync(out);
const toolRoot=process.env.WASM_TOOLS_ROOT || 'C:/Users/ettotto/Documents/webassembly_obfuscation/.tools';
const wat2wasm=path.join(toolRoot,'wabt-1.0.42/bin/wat2wasm.exe');
const opt=path.join(toolRoot,'binaryen-version_133/bin/wasm-opt.exe');
const run=(exe,args)=>cp.execFileSync(exe,args,{encoding:'utf8'}).trim();
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const exponents=[52,53,60,70,83,84,85], inputs=new Set([0,1,2,3,0xffffffff]);
for(let j=0;j<=32;j++)for(let d=-3;d<=3;d++){
  const n=2**j+d;if(n>=0&&n<=0xffffffff)inputs.add(n);
}
let rng=0x52455349;
for(let i=0;i<4096;i++){rng=(Math.imul(rng,1664525)+1013904223)>>>0;inputs.add(rng);}
const xs=[...inputs];fs.writeFileSync(path.join(out,'inputs.json'),JSON.stringify({seed:0x52455349,inputs:xs}));
const result={node:process.version,v8:process.versions.v8,wabt:run(wat2wasm,['--version']),binaryen:run(opt,['--version']),inputs:xs.length,variants:[]};
function expected(x,k){
 const X=BigInt(x), B=1n<<BigInt(k), step=1n<<BigInt(k-52);
 let q=X/step;const rem=X%step;
 if(2n*rem>step||(2n*rem===step&&(q&1n)))q++;
 const rounded=q*step;
 return {hi:B+rounded,lo:X-rounded};
}
function hex(f){const b=Buffer.alloc(8);b.writeDoubleLE(f);return b.toString('hex');}
for(const k of exponents){
 const stem=path.join(out,'k'+k);
 const wat=`(module
 (func (export "encode") (param $x i32) (result f64 f64) (local $h f64)
  (local.set $h (f64.add (f64.const 0x1p${k}) (f64.convert_i32_u (local.get $x))))
  (local.get $h)
  (f64.sub (f64.convert_i32_u (local.get $x)) (f64.sub (local.get $h) (f64.const 0x1p${k}))))
 (func (export "recover") (param $h f64) (param $l f64) (result i32)
  (i32.trunc_f64_u (f64.add (f64.sub (local.get $h) (f64.const 0x1p${k})) (local.get $l)))))`;
 fs.writeFileSync(stem+'.wat',wat);run(wat2wasm,[stem+'.wat','-o',stem+'.wasm']);
 run(opt,[stem+'.wasm','-O2','--enable-multivalue','-o',stem+'.opt.wasm']);
 for(const variant of ['raw','O2']){
  const file=stem+(variant==='raw'?'.wasm':'.opt.wasm'), bytes=fs.readFileSync(file);
  const api=new WebAssembly.Instance(new WebAssembly.Module(bytes)).exports;
  let errors=0,loIsX=0;const observations=[];
  for(const x of xs){
   const [h,l]=api.encode(x), y=api.recover(h,l)>>>0, exact=expected(x,k);
   if(BigInt(h)!==exact.hi||BigInt(l)!==exact.lo||y!==x)errors++;
   if(l===x)loIsX++;
   observations.push([hex(h),hex(l),y]);
  }
  fs.writeFileSync(stem+'.'+variant+'.observations.json',JSON.stringify(observations));
  const row={k,variant,file:path.basename(file),sha256:sha(bytes),bytes:bytes.length,checks:xs.length,errors,loIsX};
  result.variants.push(row);console.log(JSON.stringify(row));if(errors)throw Error('Mismatch');
 }
}
fs.writeFileSync(path.join(out,'results.json'),JSON.stringify(result,null,2));
