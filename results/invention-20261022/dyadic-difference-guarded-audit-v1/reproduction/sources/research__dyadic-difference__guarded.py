import argparse,json,shutil,subprocess
from pathlib import Path
import prototype as p
import recover as static
import public_recover as public
from run import FIXTURES


def run(out):
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False);targets=[];reports=[];rejections=[]
    for name,a in FIXTURES.items():
        src=out/(name+'.source.wasm');p.q.compile(p.source(a),src)
        for mode in ('plain','delta','guarded'):
            raw=out/f'{name}.{mode}.raw.wasm'
            if mode=='plain':p.q.compile(p.source(a),raw);info={}
            else:info=p.transform(src,raw,mode)
            opt=out/f'{name}.{mode}.O3.wasm';p.q.tool('wasm-opt',[raw,'-O3','-o',opt]);p.q.w.tool('wasm-validate',[opt])
            for kind,file in [('raw',raw),('O3',opt)]:
                targets.append(dict(name=name,mode=mode,opt=kind,file=file.name,bytes=file.stat().st_size,sha256=p.q.digest(file),info=info))
                dst=out/(file.stem+'.recovered.wasm');report=public.recover(file,dst)
                report.update(file=file.name,name=name,mode=mode,opt=kind)
                # Scoring is separate from recovery: prove the residual is the
                # zero function using the actual known polynomial degree bound.
                residual=p.add(report['coefficients'],a,-1);values=[p.evaluate(residual,x) for x in range(len(residual))]
                differences=[]
                while values:differences.append(values[0]);values=[(values[i+1]-values[i])&p.MASK for i in range(len(values)-1)]
                assert all(x==0 for x in differences)
                report['posthoc_source_certificate']=differences;reports.append(report)
                targets.append(dict(name=name,mode='recovered',origin=mode,opt=kind,file=dst.name,bytes=dst.stat().st_size,sha256=p.q.digest(dst),info={}))
                if mode=='guarded':
                    try:static.recover(file,out/(file.stem+'.must-not-exist.wasm'))
                    except ValueError as e:rejections.append(dict(file=file.name,error=str(e)))
                    else:raise AssertionError('unconditional helper recovery accepted guarded variant')
    p.q.save(out/'manifest.json',dict(fixtures=FIXTURES,targets=targets));p.q.save(out/'analysis.json',reports);p.q.save(out/'static-rejections.json',rejections)
    check=subprocess.run(['node',str(Path(__file__).with_name('check.cjs')),str(out)],capture_output=True,text=True,timeout=120)
    (out/'stderr.txt').write_text(check.stderr,encoding='utf-8');(out/'stdout.txt').write_text(check.stdout,encoding='utf-8')
    if check.returncode:raise RuntimeError(check.stderr)
    # Outside-promise negative: equal on queried inputs, different elsewhere.
    exceptional=0xdeadbeef;a=FIXTURES['cubic'];evil=out/'outside-promise.wasm'
    p.q.compile('(module (func (export "run") (param i32) (result i32) (i32.add '+p.horner(a)+' (i32.eq (local.get 0) '+p.c(exceptional)+'))))',evil)
    dst=out/'outside-promise.recovered.wasm';candidate=public.recover(evil,dst)
    js='const fs=require("fs");const es=process.argv.slice(1).map(f=>new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(f))).exports);const x=0xdeadbeef;console.log(JSON.stringify({x,source:es[0].run(x)>>>0,clone:es[1].run(x)>>>0}));'
    test=subprocess.run(['node','-e',js,str(evil),str(dst)],capture_output=True,text=True,check=True)
    counter=json.loads(test.stdout);assert counter['source']!=counter['clone'];p.q.save(out/'outside-promise.json',dict(recovery=candidate,counterexample=counter))
    srcdir=out/'sources';srcdir.mkdir()
    for f in [*Path(__file__).parent.glob('*.py'),*Path(__file__).parent.glob('*.cjs'),Path(__file__).parent/'plan.md',p.ROOT/'research/isotope-swizzle/prototype.py',p.ROOT/'research/connectivity-elimination/prototype.py']:
        shutil.copy2(f,srcdir/'__'.join(f.relative_to(p.ROOT).parts))
    p.q.save(out/'pins.json',{str(f.relative_to(out)):p.q.digest(f) for f in out.rglob('*') if f.is_file()})
    print(json.dumps(dict(targets=len(targets),recoveries=len(reports),queries=sum(r['query']['queries'] for r in reports),static_rejections=len(rejections),checks=check.stdout,outside_promise=counter)))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output');a=ap.parse_args();run(a.output)
