import json
import shutil
import subprocess
import sys
from pathlib import Path
import prototype as p

out=Path(sys.argv[1]).resolve();out.mkdir(parents=True,exist_ok=False)
rows=[];attacks=[]
for name,k,mask in [('wide',1,0x7fffffff),('byte',5,255),('half',16,65535),('bit',1,1)]:
    src=out/(name+'-source-raw.wasm');p.q.compile(p.source(k,mask),src)
    dst=out/(name+'-history-raw.wasm');info=p.transform(src,dst)
    for mode in ('source','history'):
        raw=out/f'{name}-{mode}-raw.wasm'
        for opt in ('raw','O3'):
            file=raw if opt=='raw' else out/f'{name}-{mode}-{opt}.wasm'
            if opt=='O3':p.q.tool('wasm-opt',[raw,'-O3','-o',file])
            p.q.w.tool('wasm-validate',[file])
            row=dict(name=name,rotation=k,mask=mask,mode=mode,opt=opt,file=file.name,bytes=file.stat().st_size,transform=info)
            rows.append(row)
            # Identical queries on source and transformed binary; no source data is an attack input.
            proc=subprocess.run(['node',str(Path(__file__).with_name('inspect.cjs')),str(file)],capture_output=True,text=True,timeout=30)
            (out/(file.stem+'-attack.log')).write_text(proc.stdout+proc.stderr,encoding='utf-8');proc.check_returncode()
            a=json.loads(proc.stdout);assert (a['rotation'],a['mask'])==(k,mask)
            attacks.append(dict(file=file.name,**a))
            if mode=='history':
                recovered=out/(file.stem+'-recovered.wasm');p.q.compile(p.source(a['rotation'],a['mask']),recovered)
                assert recovered.read_bytes()==src.read_bytes()
                rows.append(dict(row,mode='recovered',file=recovered.name,bytes=recovered.stat().st_size))
p.q.save(out/'manifest.json',rows);p.q.save(out/'attacks.json',attacks)
proc=subprocess.run(['node',str(Path(__file__).with_name('check.cjs')),str(out)],capture_output=True,text=True,timeout=90)
(out/'check.log').write_text(proc.stdout+proc.stderr,encoding='utf-8');proc.check_returncode()
# Input-dependent rotation has no uniform finite suffix-only realization.
dynamic=out/'dynamic.wasm';p.q.compile(p.source(0,0x7fffffff,True),dynamic)
p.q.tool('wasm-opt',[dynamic,'-O3','-o',out/'dynamic-O3.wasm'])
js='''const fs=require('fs'),assert=require('assert');let rows=[];
for(const file of process.argv.slice(1)){const e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(file))).exports;
for(const h of [1,2,8,32,128,1024]){let before=[],after=[];
for(const prefix of [0,0x80000000]){new Uint8Array(e.memory.buffer).fill(0);let v=new DataView(e.memory.buffer);v.setUint32(0,prefix,true);v.setUint32(4*(h+1),1,true);
let outputs=Array.from({length:h+2},(_,n)=>e.run(0,0,n)>>>0);before.push(outputs);after.push(e.run(0,0,h+2)>>>0);}
assert.deepStrictEqual(before[0],before[1]);assert.deepStrictEqual(after,[0,1]);rows.push({file,h,previous_outputs_equal:true,last_h_inputs_equal:true,next_outputs:after});}}
console.log(JSON.stringify(rows));'''
proc=subprocess.run(['node','-e',js,str(dynamic),str(out/'dynamic-O3.wasm')],capture_output=True,text=True,timeout=30)
proc.check_returncode();p.q.save(out/'dynamic-counterexamples.json',json.loads(proc.stdout))
for name in ['dynamic','changed-mask']:
    bad=dynamic
    if name=='changed-mask':
        bad=out/'changed-mask.wasm';p.q.compile(p.source(1,255).replace('(memory (export "memory") 1 1)','(memory (export "memory") 1 2)'),bad)
    try:p.transform(bad,out/('unexpected-'+name+'.wasm'))
    except p.q.Unsupported as e:p.q.save(out/('reject-'+name+'.json'),dict(rejected=True,reason=str(e)))
    else:raise AssertionError(name)
snap=out/'sources';snap.mkdir()
for f in Path(__file__).parent.iterdir():
    if f.suffix in ('.py','.cjs','.md'):shutil.copy2(f,snap/f.name)
p.q.save(out/'hashes.json',{str(f.relative_to(out)):p.q.digest(f) for f in out.rglob('*') if f.is_file()})
print(proc.stdout if False else (out/'check.log').read_text())
print(json.dumps(dict(recovered=len(attacks),queries_per_binary=64,dynamic_counterexamples=12)))
