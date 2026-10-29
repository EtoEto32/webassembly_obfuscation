import hashlib
import json
from pathlib import Path
import random
import shutil
import statistics
import subprocess
import sys
import prototype as p

WRAPPER='''(module (import "target" "step" (func $step (param i32) (result i32)))
(func (export "bench") (param $n i32) (param $x i32) (result i32) (local $c i32)
 (loop $loop
  (local.set $x (i32.add (i32.mul (local.get $x) (i32.const 1664525)) (i32.const 1013904223)))
  (local.set $c (i32.xor (i32.shl (local.get $c) (i32.const 1)) (call $step (local.get $x))))
  (local.set $n (i32.sub (local.get $n) (i32.const 1))) (br_if $loop (local.get $n)))
 (local.get $c)))'''


def main(src,out):
    src,out=map(Path,(src,out));out.mkdir(parents=True,exist_ok=False)
    pins=json.loads((src/'pins.json').read_text())
    for name,h in pins.items():assert hashlib.sha256((src/name).read_bytes()).hexdigest()==h
    manifest=json.loads((src/'manifest.json').read_text());targets=[]
    for name in manifest['models']:
        for mode in ('plain','basis','quotient','perturb','recovered'):
            dest=out/(name+'-'+mode+'.wasm')
            original=src/(name+('-perturb-O3-recovered.wasm' if mode=='recovered' else '-'+mode+'-O3.wasm'))
            if mode=='recovered':p.w.tool('wasm-opt',[original,'-O3','-o',dest])
            else:shutil.copyfile(original,dest)
            p.w.tool('wasm-validate',[dest]);m=p.w.parse(p.w.tool('wasm2wat',[dest,'--fold-exprs']))
            targets.append({'name':name,'mode':mode,'stage':'O3','file':dest.name,'bytes':dest.stat().st_size,
                            'i32_globals':sum(x[0]=='global' for x in m[1:]),'linear_memory_bytes':0})
    (out/'manifest.json').write_text(json.dumps({'models':manifest['models'],'targets':targets},indent=2),encoding='utf8')
    result=subprocess.run(['node',str(p.HERE/'check.cjs'),str(out)],capture_output=True,text=True,timeout=120,check=True)
    (out/'checks.json').write_text(result.stdout,encoding='utf8')
    wrapper=out/'wrapper.wasm';p.save(WRAPPER,wrapper)
    schedule=[(t,i) for t in targets for i in range(3)];random.Random(20261022).shuffle(schedule);rows=[]
    for t,i in schedule:
        result=subprocess.run(['node','--no-liftoff','--no-wasm-lazy-compilation',str(p.HERE/'bench.cjs'),str(out/t['file']),str(wrapper)],capture_output=True,text=True,timeout=60,check=True)
        data=json.loads(result.stdout);filename=t['file']+f'.rep{i}.json';(out/filename).write_text(json.dumps(data,indent=2),encoding='utf8')
        rows.append({'name':t['name'],'mode':t['mode'],'rep':i,'file':filename,'median_ns':statistics.median(b['ns_per_step'] for b in data['batches'])})
    summary=[]
    for t in targets:
        medians=[r['median_ns'] for r in rows if r['name']==t['name'] and r['mode']==t['mode']]
        summary.append({**t,'median_ns':statistics.median(medians),'process_medians':medians})
    (out/'summary.json').write_text(json.dumps({'source_pins_verified':len(pins),'rows':rows,'summary':summary},indent=2),encoding='utf8')
    for file in ('performance.py','bench.cjs','check.cjs','prototype.py'):
        shutil.copyfile(p.HERE/file,out/('source-'+file))
    pins={x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in out.iterdir() if x.is_file()}
    (out/'pins.json').write_text(json.dumps(pins,indent=2),encoding='utf8')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main(*sys.argv[1:])
