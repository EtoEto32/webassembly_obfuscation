import argparse
import json
from pathlib import Path
import random
import statistics
import subprocess
import time
import prototype as p


def pack(offset):
    z=p.node('i32x4.splat',p.node('local.get',str(offset)))
    for i in range(1,4):z=p.node('i32x4.replace_lane',str(i),z,p.node('local.get',str(offset+i)))
    return z


def kernels():
    x,y=pack(0),pack(4);N=p.node;V=p.vec
    gt=lambda a,b:N('i8x16.gt_u',a,b);lt=lambda a,b:N('i8x16.lt_u',a,b);eq=lambda a,b:N('i8x16.eq',a,b)
    AND=lambda a,b:N('v128.and',a,b);OR=lambda a,b:N('v128.or',a,b);NOT=lambda a:N('v128.not',a)
    return {
      'range':OR(AND(AND(gt(x,V(23)),lt(x,V(201))),NOT(lt(y,V(7)))),eq(x,y)),
      'pair':N('v128.xor',gt(x,y),AND(N('i8x16.ge_u',x,V(71)),N('i8x16.le_u',y,V(99)))),
      'filter':OR(AND(lt(x,V(64)),gt(y,V(200))),AND(NOT(eq(x,V(17))),OR(gt(y,x),eq(y,V(127)))))
    }


def run(out):
    if out.exists():raise ValueError('Refuse overwrite output folder')
    out.mkdir(parents=True);rows=[];transforms=[];attacks=[]
    for name,e in kernels().items():
        src=out/(name+'-plain.wasm');p.emit(src,p.module(8,'"run"',p.node('i8x16.bitmask',e)))
        for mode in ('plain','normalized','fused'):
            raw=src if mode=='plain' else out/(name+'-'+mode+'.wasm')
            if mode!='plain':transforms.append({'kernel':name,**p.transform(src,raw,mode)})
            for opt in ('raw','O2','O3'):
                path=raw if opt=='raw' else out/(raw.stem+'-'+opt+'.wasm')
                if opt!='raw':p.w.tool('wasm-opt',[raw,'--enable-simd','-'+opt,'-o',path])
                row={'kernel':name,'mode':mode,'opt':opt,'path':str(path.resolve()),'bytes':path.stat().st_size};rows.append(row)
                try:
                    target=out/(path.stem+'-recovered.wasm');a=p.recover(path,target);a['recovered']=str(target.resolve())
                    _,_,expr=p.program(path);times=[]
                    for repeat in range(10):
                        start=time.perf_counter();q=p.quotient(expr);dt=time.perf_counter()-start
                        if repeat:times.append(dt)
                    a.update({'samples_seconds':times,'median_ms':statistics.median(times)*1000})
                except ValueError as e:a={'status':'unsupported','error':str(e)}
                except Exception as e:a={'status':'crash','error':repr(e)}
                attacks.append({**row,**a});print(json.dumps({'case':path.name,'attack':a['status']}),flush=True)
    for a in attacks:
        base=next(b for b in attacks if b['kernel']==a['kernel'] and b['mode']=='plain' and b['opt']==a['opt'])
        a['same_formula']=a.get('formula')==base.get('formula') if a['status']=='ok' else None
    (out/'manifest.json').write_text(json.dumps({'records':rows,'transforms':transforms,'attacks':attacks},indent=2),encoding='utf-8')
    cp=subprocess.run(['node',str(Path(__file__).with_name('check.cjs')),str(out)],capture_output=True,text=True,timeout=120)
    (out/'check.log').write_text(cp.stdout+cp.stderr)
    if cp.returncode:raise RuntimeError(cp.stdout+cp.stderr)
    print(cp.stdout)
    work=[(row,rep) for row in rows for rep in range(3)];random.Random(20261018).shuffle(work);measure=[]
    for row,rep in work:
        cp=subprocess.run(['node',str(Path(__file__).with_name('bench.cjs')),row['path']],capture_output=True,text=True,timeout=30)
        if cp.returncode:raise RuntimeError(cp.stderr)
        measure.append({**row,'trial':rep,**json.loads(cp.stdout)})
    (out/'runtime.json').write_text(json.dumps(measure,indent=2));print(json.dumps({'runtime_processes':len(measure)}))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);a=ap.parse_args();run(a.output)
