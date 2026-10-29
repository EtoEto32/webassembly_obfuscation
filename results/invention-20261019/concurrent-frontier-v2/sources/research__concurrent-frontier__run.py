import argparse, importlib.util, json, platform, shutil, statistics, subprocess, time
from pathlib import Path
import prototype as q
import recover as r
p=q.p;HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('packet_fixture',q.ROOT/'research/exception-packet/run.py')
# Avoid importing its recover module under this study's name; fixture uses neither.
old=importlib.util.module_from_spec(s);s.loader.exec_module(old)

def save(path,x):Path(path).write_text(json.dumps(x,indent=2,ensure_ascii=False),encoding='utf-8')

def main(out,small):
    out=Path(out);out.mkdir(parents=True,exist_ok=False);snap=out/'sources';snap.mkdir();sources=[]
    for f in [*HERE.glob('*.py'),*HERE.glob('*.cjs'),HERE/'plan.md',q.ROOT/'research/exception-packet/prototype.py',q.ROOT/'research/exception-packet/run.py',q.ROOT/'research/stack-cycle/transform.py',q.ROOT/'research/connectivity-elimination/prototype.py']:
        name=str(f.relative_to(q.ROOT)).replace('\\','__').replace('/','__');shutil.copyfile(f,snap/name);sources.append(dict(path=str(f.relative_to(q.ROOT)),sha256=p.digest(f),snapshot=name))
    save(out/'sources.json',sources)
    save(out/'environment.json',dict(python=platform.python_version(),platform=platform.platform(),node=json.loads(subprocess.check_output(['node','-e',"console.log(JSON.stringify({versions:process.versions,cpu:require('os').cpus()[0].model,logicalCPUs:require('os').cpus().length}))"],text=True)),wabt=p.w.tool('wat2wasm',['--version']),binaryen=p.w.tool('wasm-opt',['--version'])))
    allowed=r.profiles();save(out/'profiles.json',allowed);rows=[];attacks=[];transforms=[]
    for kernel in (('blend',) if small else ('blend','chain','rolling')):
        for k in ((4,) if small else (8,32)):
            name=f'{kernel}{k}';src=out/(name+'-source.wasm');p.compile(old.fixture(kernel,k),src)
            n,_,root=p.read(src);scalar,_=p.wat(n,'"run"',root,'plain')
            for mode in ('scalar','atomic','serial'):
                raw=out/f'{name}-{mode}-raw.wasm'
                if mode=='scalar':p.compile(scalar,raw)
                else:transforms.append(dict(kernel=kernel,k=k,**q.transform(src,raw,20261019,mode=='atomic')))
                for opt in ('raw','O3'):
                    f=raw if opt=='raw' else out/f'{name}-{mode}-O3.wasm'
                    if opt=='O3':q.optimize(raw,f)
                    row=dict(kernel=kernel,k=k,mode=mode,opt=opt,file=f.name,source=src.name,sha256=p.digest(f),bytes=f.stat().st_size)
                    if mode!='scalar':
                        dest=out/f'{f.stem}-recovered.wasm';attack=r.recover(f,dest,allowed)
                        attack['graph_equal']=old.canonical(p.read(dest)[2])==old.canonical(root)
                        samples=[]
                        for rep in range(10):
                            p.POOL.clear();t=time.perf_counter();r.decode(f.read_bytes(),allowed);ms=(time.perf_counter()-t)*1000
                            if rep:samples.append(ms)
                        attack.update(file=f.name,samples_ms=samples,median_ms=statistics.median(samples));attacks.append(attack)
                        row.update(recovered=dest.name,recovered_sha256=p.digest(dest))
                    rows.append(row)
            save(out/'manifest.json',rows);save(out/'attacks.json',attacks);save(out/'transforms.json',transforms);print(name,flush=True)
    subprocess.run(['node',str(HERE/'check.cjs'),str(out)],check=True,timeout=180)
    save(out/'summary.json',dict(status='complete',targets=len(rows),recovered=len(attacks),graph_equal=sum(x['graph_equal'] for x in attacks)))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('output');a.add_argument('--small',action='store_true');v=a.parse_args();main(v.output,v.small)
