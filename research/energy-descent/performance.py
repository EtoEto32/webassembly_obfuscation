import hashlib
import json
from pathlib import Path
import platform
import random
import shutil
import statistics
import subprocess
import sys
import prototype as p

def main(src,dst):
    src=Path(src);root=Path(dst);root.mkdir(parents=True,exist_ok=False)
    for f,h in json.loads((src/'pins.json').read_text()).items():assert hashlib.sha256((src/f).read_bytes()).hexdigest()==h
    targets=[]
    for name in ('chain','diamond','fanout'):
        for mode in ('plain','dag','dag-gauge','lex-gauge','dag-gauge-recovered'):
            file=src/(name+'-'+(mode.replace('-recovered','')+'-O3-recovered' if mode.endswith('-recovered') else mode+'-O3')+'.wasm')
            optimized=root/(name+'-'+mode+'-optimized.wasm');p.w.tool('wasm-opt',[file,'-O3','-o',optimized])
            m=p.w.parse(p.w.tool('wasm2wat',[optimized,'--fold-exprs']))
            idx=int(next(x[2][1] for x in m[1:] if x[:2]==['export','"run"']))
            body=f'''(func (export "bench") (param $n i32) (param $x i32) (result i32) (local $a i32)
              (loop $l (local.set $x (i32.add (i32.mul (local.get $x) (i32.const 1664525)) (i32.const 1013904223)))
              (local.set $a (i32.add (local.get $a) (call {idx} (local.get $x))))
              (local.set $n (i32.sub (local.get $n) (i32.const 1))) (br_if $l (local.get $n))) (local.get $a))'''
            out=root/(name+'-'+mode+'-bench.wasm');p.save(p.w.emit(m)[:-1]+body+')',out)
            targets.append({'name':name,'mode':mode,'file':out.name,'source':str(file),'source_bytes':file.stat().st_size,'optimized_bytes':optimized.stat().st_size,'linear_memory_bytes':65536 if not mode in ('plain','dag-gauge-recovered') else 0})
    schedule=[(i,j) for i in range(len(targets)) for j in range(3)];random.Random(20261022).shuffle(schedule);rows=[]
    for i,j in schedule:
        r=subprocess.run(['node','--no-liftoff','--no-wasm-lazy-compilation',str(p.HERE/'bench.cjs'),str(root/targets[i]['file'])],capture_output=True,text=True,timeout=60)
        if r.returncode:raise RuntimeError(r.stderr)
        rows.append({**targets[i],'process':j,**json.loads(r.stdout)})
    summary=[]
    for t in targets:
        selected=[x for x in rows if x['name']==t['name'] and x['mode']==t['mode']]
        med=[statistics.median(v['ns'] for v in x['samples']) for x in selected]
        # All variants see the same benchmark seeds/count may differ. Checksum
        # varies with calibrated count; correctness is in the separate corpus.
        summary.append({**t,'ns':statistics.median(med),'process_medians_ns':med,'range_ns':[min(med),max(med)]})
    result={'warmup_calls':16384,'calibration_target_ms':20,'batches':7,'processes':3,'rows':rows,'summary':summary,'platform':platform.platform(),'machine':platform.machine(),'cpu_affinity_fixed':False,'frequency_fixed':False}
    (root/'performance.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    shutil.copyfile(p.HERE/'performance.py',root/'source-performance.py');shutil.copyfile(p.HERE/'bench.cjs',root/'source-bench.cjs')
    (root/'pins.json').write_text(json.dumps({x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in root.iterdir() if x.is_file()},indent=2),encoding='utf8')
    print(json.dumps({'processes':len(rows),'short_batches':sum(s['milliseconds']<10 for x in rows for s in x['samples']),'summary':summary},indent=2))

if __name__=='__main__':main(*sys.argv[1:])
