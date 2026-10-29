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

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('conditional_perf',HERE/'prototype.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)


def write(path,value):Path(path).write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf8')


def wrapper(core):
    m=p.w.parse(p.w.tool('wasm2wat',[core,'--fold-exprs']))
    export=next(x for x in m[1:] if x[:2]==['export','"run"'])
    index=export[2][1]
    extra=f'''(func (export "bench") (param $n i32) (param $x i32) (param $s i32) (result i32)
      (local $sum i32) (local $i i32)
      (if (i32.eqz (local.get $n)) (then (return (i32.const 0))))
      (loop $L
        (local.set $x (i32.add (i32.mul (local.get $x) (i32.const 1664525)) (i32.const 1013904223)))
        (local.set $s (i32.add (i32.mul (local.get $s) (i32.const 1664525)) (i32.const 1013904223)))
        (local.set $sum (i32.xor (local.get $sum) (call {index} (local.get $x) (local.get $s))))
        (local.set $i (i32.add (local.get $i) (i32.const 1)))
        (br_if $L (i32.lt_u (local.get $i) (local.get $n))))
      (local.get $sum))'''
    return p.w.emit(m)[:-1]+extra+')'


def main(main_dir,out):
    main_dir=Path(main_dir);out=Path(out);out.mkdir(parents=True,exist_ok=False)
    (out/'sources').mkdir()
    for name in ('prototype.py','performance.py','bench.cjs','check.cjs'):
        shutil.copyfile(HERE/name,out/'sources'/name)
    m=json.loads((main_dir/'manifest.json').read_text(encoding='utf8'))
    pm={'fixtures':m['fixtures'],'targets':[],'probes':[],'negative':[]}
    for t in m['targets']:
        if t['form']!='raw':continue
        stem=t['fixture']+'-'+t['mode']
        core=out/(stem+'-core.wasm');p.optimize(main_dir/t['file'],core)
        binary=out/(stem+'-bench.wasm');p.save(wrapper(core),binary)
        pm['targets'].append({**t,'file':binary.name,'core':core.name,'core_bytes':core.stat().st_size})
    write(out/'manifest.json',pm)
    chk=subprocess.run(['node',str(HERE/'check.cjs'),str(out)],text=True,capture_output=True,timeout=120)
    (out/'check.stdout.txt').write_text(chk.stdout,encoding='utf8');(out/'check.stderr.txt').write_text(chk.stderr,encoding='utf8')
    if chk.returncode:raise RuntimeError(chk.stderr)
    schedule=[(j,r) for j in range(len(pm['targets'])) for r in range(3)]
    random.Random(20261022).shuffle(schedule);write(out/'schedule.json',schedule)
    runs=[]
    for k,(j,r) in enumerate(schedule):
        t=pm['targets'][j]
        proc=subprocess.run(['node','--no-liftoff','--no-wasm-lazy-compilation',str(HERE/'bench.cjs'),str(out/t['file'])],text=True,capture_output=True,timeout=60)
        (out/f'process-{k:02d}.stderr.txt').write_text(proc.stderr,encoding='utf8')
        if proc.returncode:raise RuntimeError(proc.stderr)
        v=json.loads(proc.stdout);row={'target':j,'repeat':r,**v};runs.append(row);write(out/f'process-{k:02d}.json',row)
        print(f'{k+1}/{len(schedule)} {t["fixture"]} {t["mode"]}',flush=True)
    facts=[]
    for j,t in enumerate(pm['targets']):
        rr=[r for r in runs if r['target']==j];med=[statistics.median(r['ns_per_call']) for r in rr]
        facts.append({**t,'median_ns':statistics.median(med),'process_median_range_ns':[min(med),max(med)],'process_medians_ns':med,'rss_range_kib':[min(r['max_rss_kib'] for r in rr),max(r['max_rss_kib'] for r in rr)]})
    short=[{'target':r['target'],'ms':b['ms']} for r in runs for b in r['batches'] if b['ms']<10]
    write(out/'facts.json',{'processes':len(runs),'batches':sum(len(r['batches']) for r in runs),'short_batches':short,'targets':facts,'cpu_affinity_fixed':False,'frequency_fixed':False,'selector_distribution':'LCG low bit alternates; both orders equally used'})
    write(out/'sha256.json',{str(f.relative_to(out)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(out.rglob('*')) if f.is_file()})
    print(json.dumps({'processes':len(runs),'short_batches':len(short)}))


if __name__=='__main__':main(*sys.argv[1:])
