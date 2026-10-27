import prototype as p
import json,sys,subprocess
out=p.ROOT/sys.argv[1];out.mkdir(parents=True,exist_ok=False)
table='(v128.const i8x16 '+' '.join(str(i+1) for i in range(16))+')'
mask='(v128.const i8x16 '+' '.join(['15']*16)+')'
results=[]
for safe in (False,True):
    idx='(i32x4.splat (local.get 0))'
    if safe:idx='(v128.and '+idx+' '+mask+')'
    wat='(module (func (export "run") (param i32) (result i32) (i32x4.extract_lane 0 (i8x16.swizzle '+table+' '+idx+'))))'
    src=out/('safe.wasm' if safe else 'unsafe.wasm');p.q.compile(wat,src)
    dst=src.with_name(src.stem+'-lowered.wasm');r=p.lower(src,dst)
    assert r['changed']==int(safe)
    code="const fs=require('fs');const a=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(process.argv[1]))).exports.run;const b=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(process.argv[2]))).exports.run;for(let i=0;i<256;i++){const x=Math.imul(i,0x01010101);if(a(x)!==b(x))throw Error('mismatch');}console.log(256);"
    v=subprocess.check_output(['node','-e',code,str(src),str(dst)],text=True)
    results.append(dict(safe=safe,changed=r['changed'],input_cases=int(v),wasm_calls=int(v)*2))
# Both specified relaxed-swizzle interpretations agree for every index in [0,15].
# 16 is a concrete counterexample outside the accepted domain: zero vs table[0].
model=[]
for i in range(256):
    strict=i+1 if i<16 else 0
    relaxed_x86=(i%16)+1 if i<128 else 0
    if i<16:assert strict==relaxed_x86
    if strict!=relaxed_x86:model.append(i)
assert model==list(range(16,128))
(out/'checks.json').write_text(json.dumps(dict(controls=results,model_disagreement_indices=model),indent=2),encoding='utf-8')
print(json.dumps(results))
