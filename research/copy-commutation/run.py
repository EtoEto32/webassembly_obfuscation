import argparse,hashlib,json,platform,random,shutil,subprocess
from pathlib import Path
import prototype as q
p=q.p;HERE=Path(__file__).resolve().parent
def save(path,x):Path(path).write_text(json.dumps(x,indent=2,ensure_ascii=False),encoding='utf-8')
def main(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=False);snap=out/'sources';snap.mkdir();snapshot=[]
    for f in [*HERE.glob('*.py'),*HERE.glob('*.cjs'),HERE/'plan.md',q.ROOT/'research/exception-packet/prototype.py',q.ROOT/'research/difference-boundary/prototype.py',q.ROOT/'research/zero-extent/prototype.py',q.ROOT/'research/connectivity-elimination/prototype.py',q.ROOT/'research/stack-cycle/transform.py']:
        name=str(f.relative_to(q.ROOT)).replace('\\','__').replace('/','__');shutil.copyfile(f,snap/name);snapshot.append(dict(path=str(f.relative_to(q.ROOT)),sha256=p.digest(f),snapshot=name))
    save(out/'sources.json',snapshot);rows=[];refusals=[]
    save(out/'environment.json',dict(python=platform.python_version(),platform=platform.platform(),node=subprocess.check_output(['node','--version'],text=True).strip(),wabt=p.w.tool('wat2wasm',['--version']).strip(),binaryen=p.w.tool('wasm-opt',['--version']).strip()))
    for seed in (7,19):
        rng=random.Random(seed);data=bytearray(rng.randrange(256) for _ in range(65536));data[:8]=bytes(range(8))
        (out/f'initial-{seed}.bin').write_bytes(data)
        for alignment in (1,2):
            label=f'seed{seed}-align{alignment}';src=out/(label+'-source.wasm');p.compile(q.wat(data,'plain',alignment),src)
            for mode in q.MODES:
                raw=out/f'{label}-{mode}-raw.wasm'
                legal=mode in ('plain','uniform') or mode=='coupled' and alignment==2
                if not legal:
                    try:q.transform(src,raw,mode);raise AssertionError('illegal transform accepted')
                    except ValueError as e:refusals.append(dict(seed=seed,alignment=alignment,mode=mode,error=str(e)))
                info=q.transform(src,raw,mode,not legal)
                for opt in ('raw','O3'):
                    f=raw if opt=='raw' else out/f'{label}-{mode}-O3.wasm'
                    if opt=='O3':p.w.tool('wasm-opt',[raw,'--enable-bulk-memory','--enable-bulk-memory-opt','-O3','-o',f]);p.w.tool('wasm-validate',[f])
                    m=p.w.parse(p.w.tool('wasm2wat',[f,'--fold-exprs','--no-debug-names']));m.append(['export','"memory"',['memory','0']])
                    probe=out/(f.stem+'-probe.wasm');p.compile(p.w.emit(m),probe)
                    rows.append(dict(info,seed=seed,opt=opt,source=src.name,file=f.name,probe=probe.name,sha256=p.digest(f),probe_sha256=p.digest(probe),bytes=f.stat().st_size))
    save(out/'manifest.json',rows);save(out/'refusals.json',refusals)
    subprocess.run(['node',str(HERE/'check.cjs'),str(out)],check=True,timeout=120)
    c=json.loads((out/'native.json').read_text());save(out/'summary.json',dict(targets=len(rows),positive_targets=sum(x['legal'] for x in rows),negative_targets=sum(not x['legal'] for x in rows),native_calls=c['total_calls'],positive_mismatches=c['positive_mismatches'],negative_with_counterexample=c['negative_with_counterexample'],unmodified_copy_counts=c['unmodified_copy_counts']))
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('output');v=a.parse_args();main(v.output)
