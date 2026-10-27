"""Build matched inputs, specialize, and save status without concealing errors."""
import argparse
from collections import Counter
import hashlib
import itertools
import json
from pathlib import Path
import platform
import random
import shutil
import statistics
import subprocess
import time
import traceback
import transform as t
import specialize as s


def save(path,value):path.write_text(json.dumps(value,indent=2,ensure_ascii=False),encoding='utf-8')


def shifts(rounds,local):
    return '\n'.join(f'local.tee {local} local.get {local} i32.const {k} i32.{op} i32.xor'
                     for _ in range(rounds) for k,op in [(13,'shl'),(17,'shr_u'),(5,'shl')])


def kernels():
    # Small unrolled computations, not representative application benchmarks.
    result={
      'xorshift16':'(module (func (export "run") (param i32) (result i32) (local i32) local.get 0 '+shifts(16,1)+'))',
      'mixed4':'(module (func (export "run") (param i32 i64 f64 i32) (result i32) (local i32) '+
        'local.get 0 local.get 1 local.get 2 local.get 3 '+shifts(8,4)+
        ' local.set 4 i64.reinterpret_f64 i64.xor i32.wrap_i64 i32.xor local.get 4 i32.xor))',
      'crc32word':'(module (func (export "run") (param i32 i32) (result i32) (local i32) '+
        'local.get 0 local.get 1 i32.xor '+
        ' '.join('local.tee 2 i32.const 1 i32.shr_u i32.const 0 local.get 2 i32.const 1 i32.and i32.sub i32.const -306674912 i32.and i32.xor' for _ in range(32))+'))'
    }
    body=['local.get 1']
    for i in range(16):
        body.append(f'local.get 0 i32.load offset={4*i} i32.add i32.const {2*i+3} i32.mul local.tee 3 local.get 0 local.get 3 i32.store offset={4*i}')
        if i in (0,7):body.append('local.get 2 i32.div_s')
    result['memory16']='(module (memory (export "memory") 1 1) (data (i32.const 128) "stack-cycle") (func (export "run") (param i32 i32 i32) (result i32) (local i32) '+' '.join(body)+'))'
    return result


def planner_check():
    rng=random.Random(20261018);checks=0
    for _ in range(200):
        shapes=[()]+[rng.choice([(),('i32',),('i64','i32'),('f64',)]) for _ in range(rng.randrange(8,16))]+[()]
        count=rng.randrange(1,4)
        # Exhaustive enumeration of every valid cut tuple, independent of DP.
        allcuts=[]
        for shape in set(shapes)-{()}:
            positions=[i for i,x in enumerate(shapes) if x==shape]
            if len(positions)<count+1:continue
            for inner in itertools.combinations(positions[1:-1],count-1):
                cuts=(positions[0],*inner,positions[-1])
                allcuts.append((cuts[-1]-cuts[0],len(shape),shape,-max(b-a for a,b in zip(cuts,cuts[1:])),cuts))
        if not allcuts:
            try:t.cuts_for(shapes,count)
            except ValueError:checks+=1;continue
            raise AssertionError('Planner accepted impossible input')
        expected=max(allcuts);shape,cuts,cost=t.cuts_for(shapes,count)
        assert (cuts[-1]-cuts[0],len(shape),shape,-cost)==expected[:4]
        checks+=1
    return {'exhaustive_small_cases':checks,'mismatches':0}


def main(out):
    out.mkdir(parents=True,exist_ok=False)
    for file in Path(__file__).parent.glob('*'):
        if file.is_file() and file.suffix in ('.py','.cjs','.ps1','.md'):shutil.copy2(file,out/('source-'+file.name))
    save(out/'planner-check.json',planner_check())
    env={'python':platform.python_version(),'platform':platform.platform(),
         'node':subprocess.check_output(['node','--version'],text=True).strip(),
         'wabt':t.w.tool('wat2wasm',['--version']).strip(),'binaryen':t.w.tool('wasm-opt',['--version']).strip(),
         'seed':20261018,'fragments':[4,8,16], 'profile':'straight-line scalar, one defined function'}
    save(out/'environment.json',env)
    rows=[];transforms=[]
    for kernel,wat in kernels().items():
        p=out/kernel;p.mkdir();source=p/'plain-raw.wasm';source.with_suffix('.wat').write_text(wat,encoding='utf-8')
        t.w.tool('wat2wasm',[source.with_suffix('.wat'),'-o',source])
        modes=['plain']
        for count in (4,8,16):
            for mode in ('locals','payload'):
                label=f'{mode}{count}';modes.append(label)
                report=t.transform(source,p/(label+'-raw.wasm'),mode,count)
                transforms.append({'kernel':kernel,'variant':label,**report})
        for variant in modes:
            for opt in ('raw','O2','O3'):
                f=p/f'{variant}-{opt}.wasm'
                if opt!='raw':t.w.tool('wasm-opt',[p/f'{variant}-raw.wasm','--enable-multivalue','-'+opt,'-o',f])
                t.w.tool('wasm-validate',[f])
                mod=t.w.parse(t.w.tool('wasm2wat',[f,'--fold-exprs','--no-debug-names']))
                counts=Counter(op for op,args,sig in s.program(mod)[1])
                row={'kernel':kernel,'variant':variant,'opt':opt,'path':str(f.relative_to(out)).replace('\\','/'),
                     'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'instructions':dict(counts)}
                try:
                    rec=f.with_name(f.stem+'-recovered.wasm');row['recovery']=s.recover(f,rec)
                    row['recovered_path']=str(rec.relative_to(out)).replace('\\','/')
                    row['recovered_sha256']=hashlib.sha256(rec.read_bytes()).hexdigest()
                    s.model(mod) # Warmup, then measure analysis only, excluding WABT and parse.
                    samples=[]
                    for _ in range(9):
                        a=time.perf_counter_ns();s.model(mod);samples.append((time.perf_counter_ns()-a)/1e6)
                    row['analysis_ms']={'samples':samples,'median':statistics.median(samples),'min':min(samples),'max':max(samples)}
                except Exception as exc:
                    row['recovery']={'status':'implementation_error','error':repr(exc),'traceback':traceback.format_exc()}
                rows.append(row)
                save(out/'manifest.json',rows);save(out/'transforms.json',transforms)
        print(kernel,'built',flush=True)
    # One semantically wrong but type-correct control chain: skip logical fragment 1.
    original=out/'xorshift16/payload8-raw.wat'
    bad=original.read_text(encoding='utf-8').replace('i32.const 1\nbr $dispatch','i32.const 2\nbr $dispatch',1)
    assert bad!=original.read_text(encoding='utf-8')
    (out/'wrong-next.wat').write_text(bad,encoding='utf-8')
    t.w.tool('wat2wasm',[out/'wrong-next.wat','-o',out/'wrong-next.wasm']);t.w.tool('wasm-validate',[out/'wrong-next.wasm'])
    print(json.dumps({'conditions':len(rows),'recovery':dict(Counter(x['recovery']['status'] for x in rows))}),flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);a=ap.parse_args();main(a.output)
