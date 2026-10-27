# -*- coding: utf-8 -*-
import hashlib
import json
from pathlib import Path
import platform
import random
import shutil
import statistics
import subprocess
import sys
import relaxed as r


def main(src,dst):
    src=Path(src);root=Path(dst);root.mkdir(parents=True,exist_ok=False)
    for f,h in json.loads((src/'pins.json').read_text()).items():assert hashlib.sha256((src/f).read_bytes()).hexdigest()==h
    m=json.loads((src/'manifest.json').read_text());targets=[]
    for t in m['targets']:
        if t['stage']!='O3':continue
        file=src/t['file'];name=t['name'];mode=t['mode'];optimized=root/(name+'-'+mode+'-optimized.wasm')
        r.p.w.tool('wasm-opt',[file,'-O3','-o',optimized]);mod=r.p.w.parse(r.p.w.tool('wasm2wat',[optimized,'--fold-exprs']))
        idx=int(next(x[2][1] for x in mod[1:] if x[:2]==['export','"run"']))
        body=f'''(func (export "bench") (param $n i32) (param $x i32) (result i32) (local $a i32)
          (loop $l (local.set $x (i32.add (i32.mul (local.get $x) (i32.const 1664525)) (i32.const 1013904223)))
          (local.set $a (i32.add (local.get $a) (call {idx} (local.get $x))))
          (local.set $n (i32.sub (local.get $n) (i32.const 1))) (br_if $l (local.get $n))) (local.get $a))'''
        out=root/(name+'-'+mode+'-bench.wasm');r.p.save(r.p.w.emit(mod)[:-1]+body+')',out)
        memory=next((x for x in mod[1:] if x[0]=='memory'),None)
        targets.append({'name':name,'mode':mode,'file':out.name,'source':str(file),'optimized_file':optimized.name,'source_bytes':file.stat().st_size,'optimized_bytes':optimized.stat().st_size,'linear_memory_bytes':65536 if memory else 0})
    schedule=[(i,j) for i in range(len(targets)) for j in range(3)];random.Random(20261022).shuffle(schedule);rows=[]
    for i,j in schedule:
        proc=subprocess.run(['node','--no-liftoff','--no-wasm-lazy-compilation',str(r.p.HERE/'bench.cjs'),str(root/targets[i]['file'])],capture_output=True,text=True,timeout=60)
        if proc.returncode:raise RuntimeError(proc.stderr)
        rows.append({**targets[i],'process':j,**json.loads(proc.stdout)})
    summary=[]
    for t in targets:
        vals=[statistics.median(s['ns'] for s in x['samples']) for x in rows if (x['name'],x['mode'])==(t['name'],t['mode'])]
        summary.append({**t,'ns':statistics.median(vals),'process_medians_ns':vals,'range_ns':[min(vals),max(vals)]})
    data={'models':m['models'],'targets':targets,'warmup_calls':16384,'calibration_target_ms':20,'batches':7,'processes_per_target':3,'rows':rows,'summary':summary,'platform':platform.platform(),'cpu_affinity_fixed':False,'frequency_fixed':False}
    (root/'performance.json').write_text(json.dumps(data,indent=2),encoding='utf8')
    # Independent JS oracle verifies the exact optimized artifacts and wrappers.
    check=subprocess.run(['node',str(r.p.HERE/'relaxed-performance-check.cjs'),str(root)],capture_output=True,text=True,timeout=60)
    (root/'checks.json').write_text(check.stdout,encoding='utf8');(root/'check-stderr.txt').write_text(check.stderr,encoding='utf8')
    if check.returncode:raise RuntimeError(check.stderr)
    for f in ('relaxed-performance.py','relaxed-performance-check.cjs','bench.cjs'):shutil.copyfile(r.p.HERE/f,root/('source-'+f))
    (root/'pins.json').write_text(json.dumps({x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in root.iterdir() if x.is_file()},indent=2),encoding='utf8')
    print(json.dumps({'processes':len(rows),'short_batches':sum(s['milliseconds']<10 for x in rows for s in x['samples']),'summary':summary},indent=2))

if __name__=='__main__':main(*sys.argv[1:])
