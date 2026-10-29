"""Reproducible generation, semantic attacks and native differential checks."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import random
import shutil
import subprocess
import sys
import time
import prototype as p
import attack as a

HERE=Path(__file__).resolve().parent
sys.setrecursionlimit(20000)
def save(path,data):path.write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding='utf-8')
def command(args,timeout=120):
    r=subprocess.run(list(map(str,args)),capture_output=True,text=True,timeout=timeout)
    if r.returncode:raise RuntimeError(json.dumps(dict(command=list(map(str,args)),stdout=r.stdout,stderr=r.stderr)))
    return json.loads(r.stdout)

def models():
    bits=[0,31,32,63,5,37,17,49,9,41,23,55,3,35,29,61]
    def tree(leaves,rng):
        if len(leaves)==1:return ('not',leaves[0]) if rng.randrange(4)==0 else leaves[0]
        m=len(leaves)//2
        return (rng.choice(['and','or']),tree(leaves[:m],rng),tree(leaves[m:],rng))
    v=[('v',i) for i in bits]
    mux=lambda s,x,y:('or',('and',s,x),('and',('not',s),y))
    return {
        'alternating8':tree(v[:8],random.Random(101)),
        'mux7':mux(v[0],mux(v[1],v[3],v[4]),mux(v[2],v[5],v[6])),
        'repeated8':tree([v[i] for i in [0,1,2,0,3,4,1,5,6,2,3,7,4,0,6,7]],random.Random(202)),
        'balanced16':tree(v,random.Random(303)),
        'repeated16':tree([v[(i*7+i//3)%16] for i in range(32)],random.Random(404))}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);ap.add_argument('--compare',type=Path);ap.add_argument('--quick',action='store_true');opt=ap.parse_args();out=opt.output;out.mkdir(parents=True,exist_ok=False);(out/'sources').mkdir()
    hashes={}
    for path in [HERE/'prototype.py',HERE/'attack.py',HERE/'run.py',HERE/'check.cjs',p.ROOT/'research/lane-demand/prototype.py',p.ROOT/'research/output-recurrence/prototype.py',p.ROOT/'research/connectivity-elimination/prototype.py']:
        name=path.parent.name+'_'+path.name;shutil.copyfile(path,out/'sources'/name);hashes[name]=hashlib.sha256(path.read_bytes()).hexdigest()
    env=dict(date='2026-10-19',platform=platform.platform(),python=sys.version,node=command(['node','-e','console.log(JSON.stringify({node:process.version,v8:process.versions.v8}))']),wabt=p.w.tool('wat2wasm',['--version']).strip(),binaryen=p.w.tool('wasm-opt',['--version']).strip(),sources=hashes)
    save(out/'environment.json',env);fs=[];attacks=[];transforms=[];ms=models()
    if opt.quick:ms=dict(list(ms.items())[:2])
    def record(name,mode,level,path,**kw):
        fs.append(dict(model=name,mode=mode,opt=level,path=path.name,bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),**kw))
    for name,t in ms.items():
        src=out/f'{name}.source.raw.wasm';p.c.compile_wat('(module (func (export "run") (param i32 i32) (result i32) '+p.formula_wat(t)+'))',src)
        for mode in ('source','base','basis','fused','braid'):
            raw=out/f'{name}.{mode}.raw.wasm'
            if mode!='source':transforms.append(dict(model=name,**p.transform(src,raw,mode)))
            for level in ('raw','O3'):
                path=raw if level=='raw' else out/f'{name}.{mode}.{level}.wasm'
                if level=='O3':p.w.tool('wasm-opt',[raw,'-O3','--all-features','-o',path]);p.w.tool('wasm-validate',[path])
                record(name,mode,level,path)
                if mode!='source':
                    for reduce in (False,True) if mode=='braid' else (False,):
                        target=out/f'{name}.{mode}.{level}.{"reduced" if reduce else "recovered"}.wasm'
                        try:
                            data=a.recover(path,target,reduce)
                            record(name,mode+'.'+('reduced' if reduce else 'recovered'),level,target)
                        except ValueError as ex:data=dict(status='unsupported',error=str(ex))
                        except MemoryError as ex:data=dict(status='resource_limit',error=str(ex))
                        except TimeoutError as ex:data=dict(status='timeout',error=str(ex))
                        except Exception as ex:data=dict(status='error',error=repr(ex))
                        attacks.append(dict(model=name,mode=mode,opt=level,reduce=reduce,**data))
            print(name+' '+mode,flush=True)
        save(out/'manifest.json',dict(models=ms,files=fs));save(out/'attacks.json',attacks);save(out/'transforms.json',transforms)
    save(out/'correctness.json',command(['node',HERE/'check.cjs',out]))
    if opt.compare:
        prior=json.loads((opt.compare/'manifest.json').read_text());old={q['path']:q['sha256'] for q in prior['files']};same=[q['path'] for q in fs if old.get(q['path'])==q['sha256']];different=[q['path'] for q in fs if old.get(q['path'])!=q['sha256']];save(out/'replay.json',dict(same=same,different=different))
    save(out/'summary.json',dict(status='completed',binaries=len(fs),recovered=sum(x['status']=='recovered' for x in attacks),attack_statuses={s:sum(x['status']==s for x in attacks) for s in sorted(set(x['status'] for x in attacks))}))
    print((out/'summary.json').read_text())

if __name__=='__main__':main()
