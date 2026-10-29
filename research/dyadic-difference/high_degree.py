import argparse,json,re,shutil,subprocess
from pathlib import Path
import prototype as p
import public_recover as public


def run(out):
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False);targets=[];analyses=[];wabt=[]
    xs=[0,1,2,7,0x7fffffff,0x80000000,0xffffffff,0xaaaaaaaa]
    for depth in (5,12,20):
        body='(local.set 1 (local.get 0)) '+('(local.set 1 (i32.add (i32.add (i32.mul (local.get 1) (local.get 1)) (i32.mul (local.get 1) (i32.const 3))) (i32.const 5))) '*depth)+'(local.get 1)'
        raw=out/f'depth{depth}.raw.wasm';p.q.compile('(module (func (export "run") (param i32) (result i32) (local i32) '+body+'))',raw)
        opt=out/f'depth{depth}.O3.wasm';p.q.tool('wasm-opt',[raw,'-O3','-o',opt]);p.q.w.tool('wasm-validate',[opt])
        for source in (raw,opt):
            dst=out/(source.stem+'.recovered.wasm');a=public.recover(source,dst);a.update(file=source.name,depth=depth,formal_source_degree=2**depth);analyses.append(a)
            for file in (source,dst):
                targets.append(dict(file=file.name,depth=depth,bytes=file.stat().st_size,sha256=p.q.digest(file)))
                mod=p.q.read(file)
                for i,x in enumerate(xs):mod.append(['func',['export','"case'+str(i)+'"'],['result','i32'],['call','0',['i32.const',str(x)]]])
                wrapper=out/'wabt'/file.name;p.q.compile(p.q.w.emit(mod),wrapper)
                stdout=p.q.w.tool('wasm-interp',[wrapper,'--run-all-exports']);wrapper.with_suffix('.log').write_text(stdout,encoding='utf-8')
                for i,x in enumerate(xs):
                    value=x
                    for _ in range(depth):value=(value*value+3*value+5)&p.MASK
                    rows=[line for line in stdout.splitlines() if line.startswith('case'+str(i)+'()')]
                    assert len(rows)==1 and re.search(r'=> i32:'+str(value)+r'\s*$',rows[0]),stdout
                wabt.append(dict(file=file.name,calls=len(xs),mismatches=0))
    p.q.save(out/'manifest.json',targets);p.q.save(out/'analysis.json',analyses);p.q.save(out/'wabt.json',wabt)
    check=subprocess.run(['node',str(Path(__file__).with_suffix('.cjs')),str(out)],capture_output=True,text=True,timeout=60)
    (out/'stderr.txt').write_text(check.stderr,encoding='utf-8')
    if check.returncode:raise RuntimeError(check.stderr)
    checks=json.loads(check.stdout);p.q.save(out/'checks.json',checks)
    srcdir=out/'sources';srcdir.mkdir()
    for f in [Path(__file__),Path(__file__).with_suffix('.cjs'),Path(__file__).with_name('prototype.py'),Path(__file__).with_name('recover.py'),Path(__file__).with_name('public_recover.py'),Path(__file__).with_name('query.cjs'),p.ROOT/'research/isotope-swizzle/prototype.py',p.ROOT/'research/connectivity-elimination/prototype.py']:
        shutil.copy2(f,srcdir/'__'.join(f.relative_to(p.ROOT).parts))
    p.q.save(out/'pins.json',{str(f.relative_to(out)):p.q.digest(f) for f in out.rglob('*') if f.is_file()})
    print(json.dumps(dict(targets=len(targets),calls=checks['calls'],wabt_calls=sum(r['calls'] for r in wabt),queries=sum(a['query']['queries'] for a in analyses),recovered_degrees=[a['degree'] for a in analyses])))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output');a=ap.parse_args();run(a.output)
