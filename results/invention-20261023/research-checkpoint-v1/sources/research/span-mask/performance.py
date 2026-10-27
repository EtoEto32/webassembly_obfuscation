# -*- coding: utf-8 -*-
import hashlib
import json
from pathlib import Path
import random
import shutil
import statistics
import subprocess
import sys
import prototype as p


def wrapper(src,n,dest):
    mod=p.w.parse(p.w.tool('wasm2wat',[src,'--fold-exprs']))
    args=[]
    for j in range(n):
        args.append(['i32.xor',['i32.rotl',['local.get','1'],['i32.const',str(j)]],['i32.const',str((0x9e3779b9*(j+1))&p.MASK)]])
    body=f'''(module (func (export "bench") (param i32 i32) (result i32) (local i32 i32)
      (block $done (loop $next
        (br_if $done (i32.ge_u (local.get 2) (local.get 0)))
        (local.set 1 (i32.add (i32.mul (local.get 1) (i32.const 1664525)) (i32.const 1013904223)))
        (local.set 3 (i32.xor (local.get 3) {p.w.emit(['call','0']+args)}))
        (local.set 2 (i32.add (local.get 2) (i32.const 1))) (br $next)))
      (local.get 3)))'''
    # Append the SAME wrapper after the core's sole O3 pass; no second whole-module optimization.
    mod.append(p.w.parse(body)[1]);p.save(p.w.emit(mod),dest)


def main(mainpath,iopath,out):
    mainpath=Path(mainpath);iopath=Path(iopath);out=Path(out);out.mkdir(parents=True,exist_ok=False);(out/'sources').mkdir()
    for name in ('prototype.py','performance.py','bench.cjs'):shutil.copyfile(p.HERE/name,out/'sources'/name)
    manifest=json.loads((mainpath/'manifest.json').read_text(encoding='utf8'))
    targets=[]
    for name,f in manifest['fixtures'].items():
        for mode in ('plain','span','constant','dependent','recovered'):
            src=mainpath/name/(mode+'-O3.wasm')
            if mode=='recovered':
                src=out/(name+'-recovered-core.wasm')
                p.optimize(iopath/(name+'-dependent-recovered.wasm'),src)
            dest=out/(name+'-'+mode+'-bench.wasm');wrapper(src,f['n'],dest)
            targets.append({'fixture':name,'mode':mode,'file':dest.name,'core_bytes':src.stat().st_size,
                            'linear_memory_bytes':0 if mode in ('plain','recovered') else 65536*p.layout(p.decode(__import__('attack').shared.initial_memory(src.read_bytes())))[-1]})
    schedule=[(j,r) for j in range(len(targets)) for r in range(3)];random.Random(20261023).shuffle(schedule)
    results=[]
    for j,repetition in schedule:
        target=targets[j];r=subprocess.run(['node','--no-liftoff','--no-wasm-lazy-compilation',str(p.HERE/'bench.cjs'),str(out/target['file'])],capture_output=True,text=True,timeout=120)
        label=target['fixture']+'-'+target['mode']+'-'+str(repetition)
        (out/(label+'.stdout.txt')).write_text(r.stdout,encoding='utf8');(out/(label+'.stderr.txt')).write_text(r.stderr,encoding='utf8')
        if r.returncode:raise RuntimeError(r.stderr)
        value=json.loads(r.stdout);result={**target,'repetition':repetition,**value};results.append(result)
        (out/'raw.json').write_text(json.dumps(results,indent=2),encoding='utf8')
        print(json.dumps({'done':len(results),'fixture':target['fixture'],'mode':target['mode'],'median_ns':statistics.median(value['ns_per_call'])}),flush=True)
    summary=[]
    for t in targets:
        rs=[r for r in results if r['file']==t['file']]
        medians=[statistics.median(r['ns_per_call']) for r in rs]
        summary.append({**t,'median_ns':statistics.median(medians),'process_medians_ns':medians,
                        'all_batch_min_ns':min(x for r in rs for x in r['ns_per_call']),
                        'all_batch_max_ns':max(x for r in rs for x in r['ns_per_call']),
                        'rss_kib':[r['max_rss_kib'] for r in rs]})
    (out/'summary.json').write_text(json.dumps({'targets':summary,'processes':len(results),'batches':7*len(results),'batches_under_10ms':sum(b['ms']<10 for r in results for b in r['batches'])},indent=2),encoding='utf8')
    (out/'sha256.json').write_text(json.dumps({str(f.relative_to(out)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(out.rglob('*')) if f.is_file()},indent=2),encoding='utf8')


if __name__=='__main__':main(*sys.argv[1:])
