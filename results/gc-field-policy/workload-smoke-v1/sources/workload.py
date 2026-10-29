"""Controlled live-view workload. Not a third-party application benchmark."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import random
import shutil
import statistics
import subprocess
import sys
import time
from experiment import ROOT, HERE, CHECK, w

MODES = ('shared', 'accessor', 'project', 'split')
TYPES = '''(type $Full (struct (field i32) (field i32) (field i32)))
 (type $FullRows (array (mut (ref null $Full))))
 (type $Public (struct (field i32) (field i32)))
 (type $PublicRows (array (mut (ref null $Public))))
 (type $Private (array (mut i32)))'''


def loop(limit, body, var='$i'):
    return f'''i32.const 0 local.set {var}
      block loop local.get {var} {limit} i32.ge_u br_if 1
      {body} local.get {var} i32.const 1 i32.add local.set {var} br 0 end end'''


def producer(mode):
    split = mode == 'split'
    row, arr = ('$Public', '$PublicRows') if split else ('$Full', '$FullRows')
    private_init = 'global.get $private local.get $i local.get $i local.get $secret i32.xor array.set $Private' if split else ''
    init = f'''global.get $rows local.get $i
      local.get $i i32.const 17 i32.mul i32.const 1023 i32.and
      local.get $i i32.const 31 i32.mul i32.const 1023 i32.and
      {'' if split else 'local.get $i local.get $secret i32.xor'}
      struct.new {row} array.set {arr} {private_init}'''
    view = 'global.get $rows'
    if mode == 'project':
        copy = '''local.get $out local.get $i
          global.get $rows local.get $i array.get $FullRows local.tee $old struct.get $Full 0
          local.get $old struct.get $Full 1 struct.new $Public array.set $PublicRows'''
        view = f'''(local $i i32) (local $out (ref null $PublicRows)) (local $old (ref null $Full))
          global.get $n array.new_default $PublicRows local.set $out
          {loop('global.get $n', copy)} local.get $out'''
    view_func = '' if mode == 'accessor' else f'(func (export "view") (result anyref) {view})'
    accessor = '' if mode != 'accessor' else '''
      (func (export "x") (param i32) (result i32) global.get $rows local.get 0 array.get $FullRows struct.get $Full 0)
      (func (export "y") (param i32) (result i32) global.get $rows local.get 0 array.get $FullRows struct.get $Full 1)'''
    return f'''(module {TYPES}
      (global $rows (mut (ref null {arr})) (ref.null {arr}))
      (global $n (mut i32) (i32.const 0))
      {'(global $private (mut (ref null $Private)) (ref.null $Private))' if split else ''}
      (func (export "init") (param $n i32) (param $secret i32) (local $i i32)
        local.get $n global.set $n local.get $n array.new_default {arr} global.set $rows
        {'local.get $n array.new_default $Private global.set $private' if split else ''}
        {loop('local.get $n', init)})
      (func (export "refresh") (param $seed i32) (local $i i32)
        local.get $seed global.get $n i32.const 1 i32.sub i32.and local.set $i
        global.get $rows local.get $i
        local.get $i i32.const 17 i32.mul local.get $seed i32.add i32.const 1023 i32.and
        local.get $i i32.const 31 i32.mul local.get $seed i32.const 3 i32.mul i32.add i32.const 1023 i32.and
        {'' if split else 'global.get $rows local.get $i array.get $FullRows struct.get $Full 2'}
        struct.new {row} array.set {arr})
      {view_func} {accessor}
      (func (export "private-at") (param i32) (result i32)
        {'global.get $private local.get 0 array.get $Private' if split else 'global.get $rows local.get 0 array.get $FullRows struct.get $Full 2'}))'''


def consumer(mode, forbidden=False):
    row, arr = ('$Full', '$FullRows') if mode == 'shared' else ('$Public', '$PublicRows')
    imports = '(import "lib" "refresh" (func $refresh (param i32)))'
    view = ''
    if mode == 'accessor':
        imports += '(import "lib" "x" (func $x (param i32) (result i32))) (import "lib" "y" (func $y (param i32) (result i32)))'
        read = 'local.get $j call $x local.set $x local.get $j call $y local.set $y'
    else:
        imports += '(import "lib" "view" (func $view (result anyref)))'
        view = f'call $view ref.cast (ref {arr}) local.set $rows'
        read = f'''local.get $rows local.get $j array.get {arr} local.tee $row
            struct.get {row} {2 if forbidden else 0} local.set $x
            local.get $row struct.get {row} 1 local.set $y'''
    body = f'''local.get $i local.get $stride i32.mul local.get $n i32.const 1 i32.sub i32.and local.set $j
      {read} local.get $x i32.const 31 i32.and i32.const 17 i32.lt_u if
      local.get $sum local.get $x i32.const 3 i32.mul local.get $y i32.add i32.add local.set $sum end'''
    return f'''(module {TYPES} {imports}
      (func (export "run") (param $n i32) (param $passes i32) (param $stride i32) (param $seed i32) (result i32)
        (local $i i32) (local $j i32) (local $pass i32) (local $x i32) (local $y i32) (local $sum i32)
        (local $rows (ref null {arr})) (local $row (ref null {row}))
        local.get $seed call $refresh {view}
        {loop('local.get $passes', loop('local.get $n', body), '$pass')} local.get $sum))'''


def policy(mode):
    # The embedding enforces an import allowlist separately from GC policy.
    # private-at/init remain available only to the trusted test observer.
    if mode == 'shared':
        return [dict(type=0, deny='read', field=2), dict(type=0, deny='create'),
                dict(type=1, deny='write', field=0), dict(type=1, deny='create')]
    if mode in ('project', 'split'):
        return [dict(type=3, deny='write', field=0), dict(type=3, deny='create')]
    return []


def expected(n, passes):
    rows = [((i * 17) & 1023, (i * 31) & 1023) for i in range(n)]
    def value(pair):
        x, y = pair
        return 3*x+y if (x & 31) < 17 else 0
    total = sum(map(value, rows)); checks = []
    for k in list(range(12)) + list(range(11)):
        seed = 123456 + k; i = seed & (n-1)
        total -= value(rows[i]); rows[i] = ((i*17+seed)&1023, (i*31+seed*3)&1023); total += value(rows[i])
        x = (total * passes) & 0xffffffff
        checks.append(x if x < 0x80000000 else x - 0x100000000)
    return checks[12:]


def command(args):
    t = time.perf_counter()
    p = subprocess.run([str(x) for x in args], capture_output=True, text=True, encoding='utf8', timeout=60)
    return dict(args=list(map(str,args)),code=p.returncode,stdout=p.stdout,stderr=p.stderr,wallMs=(time.perf_counter()-t)*1000)


def main(out, smoke):
    out.mkdir(parents=True,exist_ok=False); commands=[]; pairs=[]
    for mode in MODES:
        lib=out/f'{mode}-lib.wasm'; client=out/f'{mode}-client.wasm'; p=out/f'{mode}-policy.json'
        for path,source in ((lib,producer(mode)),(client,consumer(mode))):
            path.with_suffix('.wat').write_text(source);path.write_bytes(w.wat2wasm(source))
        p.write_text(json.dumps(policy(mode),indent=2))
        c=command([CHECK,lib,p,client]);commands.append(c);assert c['code']==0,c
        parsed=json.loads(c['stdout']);assert next(r['accepted'] for r in parsed['results'] if r['mode']=='closure')
        pairs.append(dict(mode=mode,library=str(lib.resolve()),consumer=str(client.resolve()),policy=str(p.resolve()),
                          allowedImports=['refresh']+(['x','y'] if mode=='accessor' else ['view']),
                          libraryBytes=lib.stat().st_size,consumerBytes=client.stat().st_size,checker=parsed,checkerWallMs=c['wallMs']))
    bad=out/'forbidden-read.wasm';bad.write_bytes(w.wat2wasm(consumer('shared',True)))
    c=command([CHECK,pairs[0]['library'],pairs[0]['policy'],bad]);commands.append(c)
    assert c['code']==0 and not next(r['accepted'] for r in json.loads(c['stdout'])['results'] if r['mode']=='closure'),c
    jobs=[dict(pair=pair,n=n,passes=passes,stride=stride,engine=engine,repeat=repeat) for pair in pairs
          for n in ((128,) if smoke else (128,4096,65536)) for passes in (1,8) for stride in (1,257)
          for engine in ('Node','Wasmtime') for repeat in range(1 if smoke else 3)]
    random.Random(261026).shuffle(jobs); measurements=[]
    for index,job in enumerate(jobs):
        pair=job['pair'];spec={**pair,**{k:v for k,v in job.items() if k!='pair'},'checkerPath':str(CHECK.resolve())}
        specfile=out/'job.json';specfile.write_text(json.dumps(spec))
        args=['node',HERE/'workload-bench.mjs'] if job['engine']=='Node' else [sys.executable,HERE/'workload-bench.py']
        c=command(args+[specfile]);commands.append(c)
        (out/'commands.json').write_text(json.dumps(commands,indent=2))
        assert c['code']==0,c
        r=json.loads(c['stdout']);assert r['checks']==expected(job['n'],job['passes']),(job,r)
        assert r['privateAfter']==(0 ^ 77123),(job,r)
        measurements.append({**{k:v for k,v in spec.items() if k not in ('checker','checkerPath')},**r})
        (out/'measurements.json').write_text(json.dumps(measurements,indent=2))
        if index%24==0:print(f'{index+1}/{len(jobs)} checked',flush=True)
    summary=[]
    for pair in pairs:
        for n in sorted({j['n'] for j in jobs}):
            for passes in (1,8):
                for stride in (1,257):
                    for engine in ('Node','Wasmtime'):
                        rows=[r for r in measurements if (r['mode'],r['n'],r['passes'],r['stride'],r['engine'])==(pair['mode'],n,passes,stride,engine)]
                        medians=[statistics.median(r['samples']) for r in rows]
                        pooled=[v for r in rows for v in r['samples']];q=statistics.quantiles(pooled,n=4,method='inclusive')
                        summary.append(dict(mode=pair['mode'],n=n,passes=passes,stride=stride,engine=engine,medianMs=statistics.median(medians),
                            processMedians=medians,pooledIqrMs=q[2]-q[0],medianSetupMs=statistics.median(r['setupMs'] for r in rows),
                            medianInitMs=statistics.median(r['initMs'] for r in rows),peakBytes=max(r['peakBytes'] for r in rows)))
    (out/'summary.json').write_text(json.dumps(dict(processes=len(jobs),warmups=12,samples=11,seed=261026,
        platform=platform.platform(),python=sys.version,smoke=smoke,pairs=pairs,rows=summary),indent=2))
    sources=out/'sources';sources.mkdir()
    for path in (HERE/'workload.py',HERE/'workload-bench.py',HERE/'workload-bench.mjs',HERE/'workload-plan.md',HERE/'checker/src/main.rs',HERE/'checker/Cargo.lock',HERE/'loader.mjs'):
        shutil.copyfile(path,sources/path.name)
    (out/'hashes.json').write_text(json.dumps({str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file()},indent=2))
    print(json.dumps(dict(processes=len(jobs),status='all checks agree')))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('out',type=Path);ap.add_argument('--smoke',action='store_true');a=ap.parse_args();main(a.out,a.smoke)
