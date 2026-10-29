"""Sequential fresh-process benchmark; fixed memory-copy scenarios, no concurrency."""
import argparse
import hashlib
import json
from pathlib import Path
import random
import shutil
import statistics
import prototype as p
from run import save,command,HERE
from verify import hash_bytes

def main():
    ap=argparse.ArgumentParser();ap.add_argument('input',type=Path);ap.add_argument('output',type=Path);o=ap.parse_args();out=o.output;out.mkdir(parents=True,exist_ok=False);(out/'sources').mkdir()
    for name in ['measure.py','batch.cjs']:shutil.copyfile(HERE/name,out/'sources'/name)
    manifest=json.loads((o.input/'manifest.json').read_text());files=[];checks=[]
    for q in manifest['files']:
        if q['opt']!='O3' or q['recovered']:continue
        text=p.w.tool('wasm2wat',[o.input/q['path']]);mod=p.w.parse(text);exports={x[1]:x[2][1] for x in mod[1:] if x[0]=='export'};cp=exports['"copy"'];dg=exports['"digest"'];N=len(manifest['datasets'][q['dataset']])
        scenarios=[(1,0,N//4),(N//2,0,8),(N-16,0,16)]
        near,far,tail=[f'(call {cp} (i32.const {d}) (i32.const {s}) (i32.const {n}))' for d,s,n in scenarios]
        observe=f'(local.set $sink (i32.add (i32.rotl (local.get $sink) (i32.const 1)) (call {dg})))'
        extra=f'''(func (export "bench") (param $kind i32) (param $count i32) (result i32) (local $sink i32)
        (block $done (loop $loop (br_if $done (i32.eqz (local.get $count)))
          (if (i32.eq (local.get $kind) (i32.const 0)) (then {near})
          (else (if (i32.eq (local.get $kind) (i32.const 1)) (then {far})
          (else (if (i32.eq (local.get $kind) (i32.const 2)) (then {tail})
          (else (if (i32.eq (local.get $kind) (i32.const 3)) (then {observe})
          (else {near} {observe}))))))))
          (local.set $count (i32.sub (local.get $count) (i32.const 1))) (br $loop))) (i32.xor (call {dg}) (local.get $sink)))'''
        target=out/q['path'];p.c.compile_wat(text.rstrip()[:-1]+extra+')',target)
        # Observe digest on every iteration as a checksum; a dropped pure call
        # could otherwise be eliminated by an optimizer/JIT.
        # This harness is assembled without another wasm-opt pass.
        files.append(dict(q,harness_sha256=hashlib.sha256(target.read_bytes()).hexdigest()))
        for kind in range(5):
            A=bytearray(manifest['datasets'][q['dataset']]);sink=0
            for _ in range(7):
                if kind!=3:
                    d,s,n=scenarios[kind if kind<3 else 0];A[d:d+n]=bytes(A[s:s+n])
                if kind>=3:sink=(((sink<<1)|(sink>>31))+hash_bytes(A))&0xffffffff
            actual=command(['node','-e','const fs=require("fs");const e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(process.argv[1]))).exports;console.log(JSON.stringify(e.bench(Number(process.argv[2]),7)>>>0));',target,kind]);assert actual==(hash_bytes(A)^sink)
            checks.append(dict(path=q['path'],kind=kind,steps=7,result=actual))
    save(out/'manifest.json',dict(files=files,input_directory=str(o.input)))
    save(out/'correctness.json',dict(harnesses=len(files),checks=checks,mismatches=0))
    tasks=[(q,r) for q in files for r in range(3)];random.Random(78617).shuffle(tasks);raw=[]
    for i,(q,r) in enumerate(tasks):
        raw.append(dict(q,repeat=r,**command(['node',HERE/'batch.cjs',out/q['path']])))
        if i%10==0:print('process '+str(i),flush=True)
    save(out/'benchmark.json',raw);summary=[]
    for q in files:
        for scenario in ('near','far','tail','digest','paired'):
            records=[b for b in raw if b['path']==q['path']];times=[next(x for x in b['rows'] if x['scenario']==scenario)['median_ns'] for b in records]
            summary.append(dict(q,scenario=scenario,median_ns=statistics.median(times),range_ns=[min(times),max(times)],median_RSS_KiB=statistics.median(b['maxRSS_KiB'] for b in records)))
    save(out/'summary.json',summary);print(json.dumps(dict(harnesses=len(files),fresh_processes=len(raw),conditions=len(summary))))

if __name__=='__main__':main()
