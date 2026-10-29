import itertools
import json
from pathlib import Path
import random
import subprocess
import sys
import time
import word
from shared import h

FIXTURES={
 'muladd':[('mul',('p',0),('p',1)),('add',('n',0),('p',2)),('mul',('n',1),('n',0))],
 'square':[('mul',('p',0),('p',0)),('sub',('n',0),('p',1)),('mul',('n',1),('p',2))],
 'mixcarry':[('add',('p',0),('p',1)),('xor',('n',0),('p',2)),('mul',('n',1),('p',1))]
}


def source_wat(nodes):
    def ref(r):return f'(local.get {r[1] if r[0]=="p" else 3+r[1]})'
    body=''.join(f'(local.set {3+i} (i32.{op} {ref(a)} {ref(b)}))' for i,(op,a,b) in enumerate(nodes))
    return f'(module (func (export "run") (param i32 i32 i32) (result i32) (local i32 i32 i32) {body} (local.get 5)))'


def models():
    rng=random.Random(20261023);rows=[];start=time.perf_counter()
    for name,nodes in FIXTURES.items():
        for width in (2,3,4,8,32):
            mask=(1<<width)-1
            if width==2:cases=itertools.product(itertools.product(range(4),repeat=3),repeat=2)
            else:cases=(([rng.randrange(mask+1) for _ in range(3)],[rng.randrange(mask+1) for _ in range(3)]) for _ in range(2048))
            count=0;worst=0
            for params,initial in cases:
                desired=[]
                for node in nodes:desired.append(word.front.calc(node,desired,params,width))
                state=list(initial)
                for t in range(4*width+1):
                    if state==desired:worst=max(worst,t);break
                    state=word.step(nodes,params,state,width)
                else:raise AssertionError((name,width,params,initial,state,desired))
                assert word.step(nodes,params,desired,width)==desired
                count+=1
            rows.append({'name':name,'width':width,'cases':count,'worst_observed_rounds':worst,'bound':4*width})
    return {'cases':rows,'elapsed_ms':1000*(time.perf_counter()-start)}


def main(out):
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False);records=[]
    for name,nodes in FIXTURES.items():
        src=out/(name+'-plain.wasm');h.save(source_wat(nodes),src);h.w.tool('wasm-opt',[src,'-O3','-o',src.with_name(src.stem+'-O3.wasm')])
        for mode in ('pipeline','feedback'):
            for j,initial in enumerate(((0,0,0),(0xffffffff,0x80000000,1),(0x12345678,0x76543210,0xaaaaaaaa))):
                dest=out/(name+'-'+mode+'-'+str(j)+'.wasm');meta=word.transform(src,dest,mode,initial);h.w.tool('wasm-opt',[dest,'-O3','-o',dest.with_name(dest.stem+'-O3.wasm')]);h.w.tool('wasm-validate',[dest.with_name(dest.stem+'-O3.wasm')]);records.append({'name':name,'file':dest.name,**meta})
    (out/'manifest.json').write_text(json.dumps(records,indent=2));m=models();(out/'models.json').write_text(json.dumps(m,indent=2));print(json.dumps({'models':sum(r['cases'] for r in m['cases']),'worst':[(r['name'],r['width'],r['worst_observed_rounds']) for r in m['cases']]}),flush=True)
    r=subprocess.run(['node',str(h.HERE.parent/'boolean-feedback/word-check.cjs'),str(out)],capture_output=True,text=True,timeout=180);(out/'check.stdout.log').write_text(r.stdout);(out/'check.stderr.log').write_text(r.stderr)
    if r.returncode:raise RuntimeError(r.stderr)
    print(r.stdout)

if __name__=='__main__':main(sys.argv[1])
