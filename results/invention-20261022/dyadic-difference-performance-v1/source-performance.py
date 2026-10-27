import argparse,json,random,shutil,statistics,subprocess
from pathlib import Path
import prototype as p


def run(main,out):
    main,out=Path(main).resolve(),Path(out).resolve()
    pins=json.loads((main/'pins.json').read_text(encoding='utf-8'))
    for name,digest in pins.items():assert p.q.digest(main/name)==digest,name
    out.mkdir(parents=True,exist_ok=False);manifest=json.loads((main/'manifest.json').read_text(encoding='utf-8'))
    wrapper=out/'wrapper.wasm'
    p.q.compile('''(module (import "target" "run" (func (param i32) (result i32)))
      (func (export "bench") (param i32 i32) (result i32) (local i32)
        (block (loop (br_if 1 (i32.eqz (local.get 0)))
          (local.set 1 (i32.add (i32.mul (local.get 1) (i32.const 1664525)) (i32.const 1013904223)))
          (local.set 2 (i32.xor (i32.shl (local.get 2) (i32.const 1)) (call 0 (local.get 1))))
          (local.set 0 (i32.sub (local.get 0) (i32.const 1))) (br 0))) (local.get 2)))''',wrapper)
    tasks=[(t,k) for t in manifest['targets'] if t['opt']=='O3' and (t['mode'] in ('plain','naive','delta') or (t['mode']=='recovered' and t['origin']=='delta')) for k in range(3)]
    random.Random(221016).shuffle(tasks);rows=[]
    for i,(t,repeat) in enumerate(tasks):
        run=subprocess.run(['node','--no-liftoff','--no-wasm-lazy-compilation',str(Path(__file__).with_name('bench.cjs')),str(main/t['file']),str(wrapper)],capture_output=True,text=True,timeout=60)
        (out/f'{i:02}.stderr.txt').write_text(run.stderr,encoding='utf-8')
        if run.returncode:raise RuntimeError(run.stderr)
        row=json.loads(run.stdout);row.update(file=t['file'],name=t['name'],mode=t['mode'],repeat=repeat,bytes=t['bytes']);p.q.save(out/f'{i:02}.json',row);rows.append(row)
    summary=[]
    for name in manifest['fixtures']:
        d={'name':name}
        for mode in ('plain','naive','delta','recovered'):
            rs=[r for r in rows if r['name']==name and r['mode']==mode];ms=[statistics.median(b['ns_per_word'] for b in r['batches']) for r in rs]
            d[mode]=dict(median_ns=statistics.median(ms),process_medians_ns=ms,bytes=rs[0]['bytes'],batch_range_ns=[min(b['ns_per_word'] for r in rs for b in r['batches']),max(b['ns_per_word'] for r in rs for b in r['batches'])])
        d['delta_over_plain']=d['delta']['median_ns']/d['plain']['median_ns'];d['delta_over_naive']=d['delta']['median_ns']/d['naive']['median_ns'];summary.append(d)
    result=dict(verified_pins=len(pins),processes=len(rows),batches=sum(len(r['batches']) for r in rows),short_batches=sum(b['ns']<10e6 for r in rows for b in r['batches']),rows=rows,summary=summary,limitations='LCG, checksum and imported calls included. Fixed random stream; no affinity or frequency control. RSS is whole Node; 3 synthetic polynomial cases.')
    p.q.save(out/'runtime.json',result)
    for f in [Path(__file__),Path(__file__).with_name('bench.cjs')]:shutil.copy2(f,out/('source-'+f.name))
    p.q.save(out/'pins.json',{str(f.relative_to(out)):p.q.digest(f) for f in out.rglob('*') if f.is_file()})
    print(json.dumps({k:v for k,v in result.items() if k!='rows'}))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('main');ap.add_argument('output');a=ap.parse_args();run(a.main,a.output)
