"""Build the preregistered narrow corpus and attempt family-aware recovery."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import statistics
import time
import traceback
import prototype as p
import recover as r


def kernels():
    v=lambda i:('v',i)
    c=lambda x:('c',x)
    add=lambda a,b:('add',a,b)
    mul=lambda a,b:('mul',a,b)
    def summation(items):
        if len(items)==1:return items[0]
        middle=len(items)//2
        return add(summation(items[:middle]),summation(items[middle:]))
    chain=v(0)
    for i in range(6): chain=add(mul(chain,add(v(1+i%3),c(2*i+1))),c(0x9e3779b1-i*0x12345))
    return {'mul2':(2,mul(v(0),v(1))),
            'dot8':(16,summation([mul(v(2*i),v(2*i+1)) for i in range(8)])),
            'affine4':(4,add(mul(add(mul(v(0),c(4294967291)),c(17)),add(mul(v(1),c(65537)),c(3))),mul(v(2),v(3)))),
            'chain6':(4,chain),
            'quadratic12':(12,summation([mul(add(v(i),v((i+1)%12)),add(v(i),v((i+5)%12))) for i in range(12)]))}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path)
    a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    report={'status':'building','python':platform.python_version(),'wabt':p.w.tool('wat2wasm',['--version']).strip(),
            'binaryen':p.w.tool('wasm-opt',['--version']).strip(),'conditions':[],'transforms':[],'recovery':[]}
    fixtures={}
    try:
        for name,(n,t) in kernels().items():
            fixtures[name]={'n':n,'tree':t,'role':'synthetic_arithmetic; not an IP benchmark'}
            wp=a.output/f'{name}-plain-raw.wat';wp.write_text(p.plain(n,'"run"',t),encoding='utf-8')
            original=wp.with_suffix('.wasm');p.w.tool('wat2wasm',[wp,'-o',original])
            for mode in ('per_op','fused'):
                data=p.transform(original,a.output/f'{name}-{mode}-raw.wasm',mode)
                report['transforms'].append({'kernel':name,**data})
            for mode in ('plain','per_op','fused'):
                for opt in ('raw','O2','O3'):
                    path=a.output/f'{name}-{mode}-{opt}.wasm'
                    if opt!='raw': p.w.tool('wasm-opt',[a.output/f'{name}-{mode}-raw.wasm','-'+opt,'-o',path])
                    p.w.tool('wasm-validate',[path])
                    dis=p.w.tool('wasm2wat',[path,'--fold-exprs']);path.with_suffix('.dis.wat').write_text(dis,encoding='utf-8')
                    row={'kernel':name,'mode':mode,'opt':opt,'file':path.name,'n':n,'bytes':path.stat().st_size,
                         'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'f64_mul_count':dis.count('(f64.mul'), 'linear_memory_bytes':0}
                    report['conditions'].append(row)
                    try:
                        result=r.recover(path,a.output/'recovered'/path.name)
                        mod=p.w.parse(dis);samples=[]
                        for _ in range(5):
                            start=time.perf_counter();r.recover_model(mod);samples.append(time.perf_counter()-start)
                        result.update(samples_seconds=samples,median_seconds=statistics.median(samples))
                    except ValueError as exc: result={'status':'unsupported_or_rejected','error':str(exc)}
                    report['recovery'].append({'file':path.name,**result})
        p.transform(a.output/'dot8-plain-raw.wasm',a.output/'bad-width.wasm','fused',True)
        try:
            r.recover(a.output/'bad-width.wasm',a.output/'bad-recovered.wasm')
        except ValueError as exc: report['bad_width_analysis']={'status':'rejected','error':str(exc)}
        else: report['bad_width_analysis']={'status':'incorrectly_accepted'}
        report['status']='built'
    except Exception:
        report['status']='failed';report['error']=traceback.format_exc();raise
    finally:
        (a.output/'build.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        (a.output/'fixtures.json').write_text(json.dumps(fixtures,indent=2),encoding='utf-8')
        for name in ('plan.md','prototype.py','recover.py','experiment.py','check.cjs'):
            (a.output/('source-'+name)).write_bytes(Path(__file__).with_name(name).read_bytes())
        print(json.dumps({'status':report['status'],'binaries':len(report['conditions']),
                          'recovery':{s:sum(x['status']==s for x in report['recovery']) for s in set(x['status'] for x in report['recovery'])}}))


if __name__=='__main__': main()
