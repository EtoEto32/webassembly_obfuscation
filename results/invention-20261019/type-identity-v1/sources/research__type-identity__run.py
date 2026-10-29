import argparse,json,platform,random,shutil,subprocess
from pathlib import Path
import prototype as q
HERE=Path(__file__).resolve().parent
def kernels():
    rows=[];pat='10110'
    for i in range(len(pat)+1):
        row=[]
        for b in '01':
            if i==len(pat):row.append(i);continue
            s=pat[:i]+b;row.append(max(j for j in range(len(pat)+1) if s.endswith(pat[:j])))
        rows.append(row+[int(i==len(pat))])
    r=random.Random(1926)
    return {'mod5':[[2*i%5,(2*i+1)%5,int(i==0)] for i in range(5)],'pattern':rows,'random16':[[r.randrange(16),r.randrange(16),r.randrange(2)] for _ in range(16)]}
MODES=[('plain',0,0),('branch',0,0),('gc',1,0),('groups',2,0),('groups',8,0),('groups',2,32),('groups',8,32)]
def main(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=False);snap=out/'sources';snap.mkdir();ss=[]
    deps=['exception-packet/prototype.py','connectivity-elimination/prototype.py','stack-cycle/transform.py']
    for f in [*HERE.glob('*.py'),*HERE.glob('*.cjs'),HERE/'plan.md',*[q.ROOT/'research'/x for x in deps]]:
        rel=str(f.relative_to(q.ROOT));n=rel.replace('\\','__').replace('/','__');shutil.copyfile(f,snap/n);ss.append(dict(path=rel,snapshot=n,sha256=q.digest(f)))
    q.save(out/'sources.json',ss);q.save(out/'environment.json',dict(python=platform.python_version(),os=platform.platform(),node=subprocess.check_output(['node','--version'],text=True).strip(),binaryen=q.tool('wasm-opt',['--version']).strip(),wabt=q.p.w.tool('wat2wasm',['--version']).strip()))
    rows=[];models=kernels();q.save(out/'models.json',models)
    for kernel,model in models.items():
        src=out/(kernel+'-source.wasm');q.p.compile(q.packed(model),src)
        for mode,g,d in MODES:
            label=f'{kernel}-{mode}-g{g}-d{d}';raw=out/(label+'-raw.wasm');info=q.transform(src,raw,mode,g,d)
            for opt in ('raw','O3'):
                f=raw if opt=='raw' else out/(label+'-O3.wasm')
                if opt=='O3':q.tool('wasm-opt',[raw,*q.FEATURES,'-O3','-o',f])
                rec=out/(f.stem+'-lower.wasm');a=q.lower(f,rec);a.pop('output')
                rows.append(dict(info,kernel=kernel,opt=opt,source=src.name,file=f.name,recovered=rec.name,bytes=f.stat().st_size,sha256=q.digest(f),recovered_sha256=q.digest(rec),recovered_bytes=rec.stat().st_size,analysis=a))
    q.save(out/'manifest.json',rows)
    subprocess.run(['node',str(HERE/'check.cjs'),str(out)],check=True,timeout=120)
    # Changing an unused sibling breaks the identity of the whole clone group.
    neg=[]
    for kernel,model in models.items():
        f=out/(kernel+'-broken-group.wasm');f.write_bytes(q.gc_binary(model,2,32,broken=True));neg.append(dict(kernel=kernel,file=f.name))
    q.save(out/'negative-manifest.json',neg)
    subprocess.run(['node',str(HERE/'check.cjs'),str(out),'negative'],check=True,timeout=30)
    q.save(out/'summary.json',dict(targets=len(rows),recovered=len(rows),checks=json.loads((out/'checks.json').read_text()),negative=json.loads((out/'negative.json').read_text())))
    print(json.dumps(json.loads((out/'summary.json').read_text())))
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('output');main(a.parse_args().output)
