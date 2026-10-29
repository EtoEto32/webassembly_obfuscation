# -*- coding: utf-8 -*-
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import shutil
import statistics
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('conditional',HERE/'prototype.py')
p = importlib.util.module_from_spec(spec); spec.loader.exec_module(p)


def write(out, value):
    Path(out).write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf8')


def expr(op):
    x=['local.get','0']; c=lambda v:['i32.const',str(v)]
    rot=lambda t:['i32.rotl',t,c(op['k'])]
    if op['kind']==0: return ['i32.xor',rot(['i32.add',x,c(op['a'])]),c(op['b'])]
    if op['kind']==1: return ['i32.add',['i32.mul',['i32.xor',x,c(op['a'])],c(op['b'])],rot(x)]
    return ['i32.xor',['i32.xor',rot(['i32.xor',x,c(op['a'])]),['i32.shr_u',x,c(op['h'])]],c(op['b'])]


def main(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    (out/'sources').mkdir()
    for name in ('prototype.py','run.py','check.cjs','plan.md'):
        shutil.copyfile(HERE/name,out/'sources'/name)
    shutil.copyfile(HERE.parent/'connectivity-elimination/prototype.py',out/'sources'/'shared-wat.py')
    rng=random.Random(20261022)
    manifest={'fixtures':{},'targets':[],'probes':[],'negative':[],'transforms':[],'recoveries':[],'rejections':[]}
    for name,n in (('reverse4',4),('permuted8',8),('permuted12',12)):
        ops=[{'kind':i%3,'a':rng.getrandbits(32),'b':rng.getrandbits(32)|1,'k':rng.randrange(1,32),'h':rng.randrange(1,32)} for i in range(n)]
        helpers=[[['param','i32'],['result','i32'],expr(o)] for o in ops]
        order0=list(range(n));order1=order0[::-1]
        if n>4:rng.shuffle(order1)
        orders=[order0,order1]
        manifest['fixtures'][name]={'ops':ops,'orders':orders,'meaningful_input_bits':33}
        d=out/name;d.mkdir()
        src=d/'plain.wasm';p.save(p.direct(helpers,orders),src)
        files={'plain':src}
        for mode in ('ordered','cyclic'):
            dest=d/(mode+'.wasm');meta=p.transform(src,dest,mode);files[mode]=dest
            manifest['transforms'].append({'fixture':name,'mode':mode,**meta})
        for mode,base in list(files.items()):
            opt=base.with_stem(base.stem+'-O3');p.optimize(base,opt)
            for form,path in (('raw',base),('O3',opt)):
                manifest['targets'].append({'fixture':name,'mode':mode,'form':form,'file':str(path.relative_to(out)),'bytes':path.stat().st_size,'linear_memory_bytes':0 if mode=='plain' else 65536})
                if mode!='plain':
                    rec=d/(mode+'-'+form+'-recovered.wasm')
                    result=p.recover(path,rec)
                    manifest['recoveries'].append({'fixture':name,'mode':mode,'form':form,**result})
                    manifest['targets'].append({'fixture':name,'mode':mode+'-recovered','form':form,'file':str(rec.relative_to(out)),'bytes':rec.stat().st_size,'linear_memory_bytes':0})
            if mode!='plain':
                r=p.make_record(helpers,orders,mode);probe=d/(mode+'-probe.wasm');p.save(p.render(helpers,r,True),probe)
                probeopt=probe.with_stem(probe.stem+'-O3');p.optimize(probe,probeopt)
                manifest['probes'].extend({'fixture':name,'file':str(q.relative_to(out))} for q in (probe,probeopt))
        r=p.make_record(helpers,orders,'cyclic');r['schedule']=r['schedule'][:-1]
        bad=d/'bad-short-schedule.wasm';p.save(p.render(helpers,r),bad)
        manifest['negative'].append({'fixture':name,'file':str(bad.relative_to(out))})
        try:p.recover(bad,d/'bad-recovered.wasm')
        except ValueError as e:manifest['rejections'].append({'fixture':name,'case':'short-schedule','reason':str(e)})
        else:raise AssertionError('Unsound missing-schedule acceptance')
        model=p.make_record(helpers,orders,'cyclic');timing=[]
        for _ in range(101):
            t=time.perf_counter();p.recover_orders(model);timing.append((time.perf_counter()-t)*1000)
        manifest['fixtures'][name]['core_recovery_101_ms']=timing
        manifest['fixtures'][name]['core_recovery_median_ms']=statistics.median(timing)
    # A valid source containing a trapping helper must be rejected before mutation.
    f=next(iter(manifest['fixtures'].values()));hs=[[['param','i32'],['result','i32'],expr(o)] for o in f['ops']]
    hs[0][-1]=['i32.div_s',['local.get','0'],['i32.const','0']]
    invalid=out/'unsupported-div.wasm';p.save(p.direct(hs,f['orders']),invalid)
    try:p.transform(invalid,out/'must-not-exist.wasm')
    except ValueError as e:manifest['rejections'].append({'case':'trapping-helper','reason':str(e)})
    else:raise AssertionError('Accepted trap-capable helper')
    write(out/'manifest.json',manifest)
    r=subprocess.run(['node',str(HERE/'check.cjs'),str(out)],text=True,capture_output=True,timeout=120)
    (out/'check.stdout.txt').write_text(r.stdout,encoding='utf8');(out/'check.stderr.txt').write_text(r.stderr,encoding='utf8')
    if r.returncode:raise RuntimeError(r.stderr)
    # Byte replay is independent of the measured runner. Record all source assets.
    checks=json.loads((out/'checks.json').read_text(encoding='utf8'))
    write(out/'summary.json',{'targets':len(manifest['targets']),'recoveries':len(manifest['recoveries']),'rejections':manifest['rejections'],'checks':checks})
    write(out/'sha256.json',{str(f.relative_to(out)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(out.rglob('*')) if f.is_file()})
    print(r.stdout.strip())


if __name__=='__main__':main(sys.argv[1])
