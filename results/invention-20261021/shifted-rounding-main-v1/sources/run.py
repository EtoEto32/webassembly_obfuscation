"""Actual-binary transform and independent integer-oracle validation."""
import importlib.util
import itertools
import json
import random
import shutil
import subprocess
import sys
from pathlib import Path
import prototype as p

spec=importlib.util.spec_from_file_location('independent_f32',p.ROOT/'research/zero-sign-transport/model.py')
model=importlib.util.module_from_spec(spec);spec.loader.exec_module(model)


def fixture(name):
    nodes=[('input',i) for i in range(3)]
    def op(tag,a,b):nodes.append((tag,a,b));return len(nodes)-1
    if name=='multiply-add':root=op('add',op('mul',0,1),2)
    elif name=='horner6':
        root=2
        for i in range(6):root=op('sub' if i%2 else 'add',op('mul',root,0),1)
    elif name=='butterfly4':
        a,b=0,1
        for i in range(4):a,b=op('sub',op('mul',a,2),b),op('add',op('mul',b,2),a)
        root=op('mul',a,b)
    elif name=='cancellation':root=op('add',op('mul',op('sub',0,0),1),op('sub',2,2))
    else:raise ValueError(name)
    return nodes,root


def main():
    out=Path(sys.argv[1]).resolve();out.mkdir(parents=True,exist_ok=False)
    save=lambda name,obj:p.q.save(out/name,obj)
    snap=out/'sources';snap.mkdir()
    for f in Path(__file__).parent.iterdir():
        if f.suffix in ('.py','.cjs','.md'):shutil.copy2(f,snap/f.name)
    edge=[0,0x80000000,1,0x80000001,0x007fffff,0x00800000,0x3f000000,0x3f800000,
          0xbf800000,0x3f800001,0x7f7fffff,0xff7fffff,0x7f800000,0xff800000,0x7fc00000,0x7f800001]
    inputs=[list(x) for x in itertools.product(edge,repeat=3)];rng=random.Random(21102191)
    inputs += [[rng.getrandbits(32) for _ in range(3)] for j in range(2048)]
    for _ in range(256):
        a=rng.getrandbits(32);inputs.append([a,a^0x80000000,rng.getrandbits(32)])
    save('inputs.json',inputs);rows=[];fixtures={}
    for name in ('multiply-add','horner6','butterfly4','cancellation'):
        nodes,root=fixture(name)
        fixtures[name]=dict(nodes=nodes,root=root,expected=[model.evaluate(nodes,root,x) for x in inputs])
        src=out/(name+'-source.wasm');p.q.compile(p.generate(3,nodes,root,'plain',0)[0],src)
        for mode in ('plain','eager','grid0','shifted'):
            raw=out/f'{name}-{mode}-raw.wasm';info=p.transform(src,raw,mode,37)
            for opt in ('raw','O3'):
                f=raw if opt=='raw' else raw.with_name(raw.name.replace('-raw.','-O3.'))
                if opt=='O3':p.q.tool('wasm-opt',[raw,'-O3','-o',f])
                p.q.w.tool('wasm-validate',[f])
                rows.append(dict(kernel=name,mode=mode,opt=opt,file=f.name,bytes=f.stat().st_size,
                                 transform=info,linear_memory_bytes=0,sha256=p.q.digest(f)))
        print(name,flush=True)
    save('manifest.json',rows);save('fixtures.json',fixtures)
    qt='(module '+p.quantizer()+''' (func (export "q") (param i64 i32) (result i64)
      (i64.reinterpret_f64 (call $quant (f64.reinterpret_i64 (local.get 0)) (local.get 1)))))'''
    p.q.compile(qt,out/'quant-raw.wasm')
    p.q.tool('wasm-opt',[out/'quant-raw.wasm','-O3','-o',out/'quant-O3.wasm'])
    proc=subprocess.run(['node',str(Path(__file__).with_name('check.cjs')),str(out)],capture_output=True,text=True,timeout=90)
    (out/'check-stdout.txt').write_text(proc.stdout,encoding='utf-8');(out/'check-stderr.txt').write_text(proc.stderr,encoding='utf-8')
    proc.check_returncode()
    save('hashes.json',{str(f.relative_to(out)):p.q.digest(f) for f in out.rglob('*') if f.is_file()})
    print(proc.stdout,flush=True)


if __name__=='__main__':main()
