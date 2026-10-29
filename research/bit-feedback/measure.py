import argparse
import collections
import hashlib
import json
from pathlib import Path
import random
import re
import statistics
import subprocess
import time
import recover
import transform as t


def run(out):
    manifest = json.loads((out/'manifest.json').read_text()); rows = manifest['records']; rng = random.Random(20261018)
    samples = []; tasks = [(r, trial) for r in rows for trial in range(3)]; rng.shuffle(tasks)
    for n, (r, trial) in enumerate(tasks):
        cp = subprocess.run(['node', str(Path(__file__).with_name('bench.cjs')), r['path']], capture_output=True, text=True, timeout=30)
        if cp.returncode: raise RuntimeError(cp.stderr)
        samples.append({**r, 'trial':trial, **json.loads(cp.stdout)})
        if n % 36 == 0: print(json.dumps({'runtime_processes':n+1}), flush=True)
    (out/'runtime.json').write_text(json.dumps(samples, indent=2))
    analysis = []
    for r in rows:
        np, expr, equations, rounds = recover.expressions(Path(r['path'])); times=[]
        for rep in range(10):
            start = time.perf_counter(); engine = recover.Bits(equations); roots = [engine.bit(expr,b) for b in range(32)]; digest, live = engine.digest(roots)
            if rounds is not None: assert max(engine.ranks[(expr,b)] for b in range(32)) <= rounds
            dt = time.perf_counter()-start
            if rep: times.append(dt)
        analysis.append({**r, 'samples_seconds':times, 'median_ms':statistics.median(times)*1000,
                         'min_ms':min(times)*1000, 'max_ms':max(times)*1000, 'live_gates':len(live), 'visited_bits':len(engine.memo)})
    (out/'analysis-timing.json').write_text(json.dumps(analysis, indent=2))
    cross = []; values = [(0,0),(1,0xffffffff),(0x80000000,255),(0xaaaaaaaa,0x55555555)]
    for r in rows:
        mod = t.w.parse(t.w.tool('wasm2wat',[r['path'],'--fold-exprs','--no-debug-names']))
        _, _, nodes, result = t.source(out/(r['kernel']+'-plain.wasm'))
        expected = []
        for a,b in values:
            state=[]
            for node in nodes: state.append(t.calc(node,state,[a,b]))
            expected.append(state[result[1]] if result[0]=='n' else [a,b][result[1]] if result[0]=='p' else result[1])
        for i,(a,b) in enumerate(values): mod.append(['func',['export','"check'+str(i)+'"'],['result','i32'],['call','0',['i32.const',str(a)],['i32.const',str(b)]]])
        wp = out/(Path(r['path']).stem+'-interp.wat'); bp=wp.with_suffix('.wasm'); wp.write_text(t.w.emit(mod))
        t.w.tool('wat2wasm',[wp,'-o',bp]); stdout=t.w.tool('wasm-interp',[bp,'--run-all-exports'])
        actual=[int(x) for x in re.findall(r'check\d+\(\) => i32:(\d+)',stdout)]
        cross.append({**r,'expected':expected,'actual':actual,'stdout':stdout,'mismatches':sum(a!=b for a,b in zip(actual,expected))+abs(len(actual)-len(expected))})
    (out/'wabt.json').write_text(json.dumps(cross,indent=2))
    table=[]
    for r in rows:
        rt=[x for x in samples if x['path']==r['path']]; medians=[statistics.median(x['samples_ns']) for x in rt]
        a=next(x for x in analysis if x['path']==r['path'])
        table.append({**r,'runtime_median_ns':statistics.median(medians),'process_medians_ns':medians,
                      'rss_min_kib':min(x['max_rss_kib'] for x in rt),'rss_max_kib':max(x['max_rss_kib'] for x in rt),
                      'analysis_median_ms':a['median_ms'],'analysis_range_ms':[a['min_ms'],a['max_ms']]})
    (out/'summary.json').write_text(json.dumps(table,indent=2))
    print(json.dumps({'runtime_processes':len(samples),'analysis_conditions':len(analysis),'wabt_calls':len(cross)*4,'wabt_mismatches':sum(x['mismatches'] for x in cross)}))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);a=ap.parse_args();run(a.output)
