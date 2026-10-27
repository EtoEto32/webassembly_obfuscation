import json,subprocess,sys,time
from pathlib import Path
import prototype as p
q=p.q;m=p.m
src,out=map(Path,sys.argv[1:]);out.mkdir(parents=True,exist_ok=False);records=[];clones=[]
rows=json.loads((src/'manifest.json').read_text());q.save(out/'fixtures.json',json.loads((src/'fixtures.json').read_text()))
for row in rows:
    if row['mode']!='native':continue
    start=time.perf_counter();target=src/row['file'];module=q.read(target);ops=p.copy_ops(module)
    obs=out/(target.stem+'-attack-observed.wasm');p.probe(target,obs)
    result=json.loads(subprocess.check_output(['node',str(Path(__file__).with_name('query.cjs')),str(obs)],text=True,timeout=60))
    b=result['matrix'];inv=m.inverse(b)
    if inv is None or not result['zeroOutsideWindow']:raise ValueError('unsupported learned model')
    for op in ops:
        c=m.matrix(len(b),op)
        if m.product(b,c)!=m.product(c,b):raise ValueError('does not commute with copied operations')
    dst=out/(target.stem+'-recovered.wasm');q.compile(p.wat(bytes(result['plain']),ops),dst)
    observed=out/(dst.stem+'-observed.wasm');p.probe(dst,observed)
    records.append(dict(file=target.name,source_sha256=q.digest(target),recovered_file=dst.name,recovered_sha256=q.digest(dst),copies=ops,total_elapsed_ms=1000*(time.perf_counter()-start),**result))
    clones.append(dict(kernel=row['kernel'],mode='recovered',opt=row['opt'],n=row['n'],file=dst.name,observed=observed.name,matrix=m.ident(row['n']),inverse=m.ident(row['n']),bytes=dst.stat().st_size,sha256=q.digest(dst)))
q.save(out/'recovery.json',records);q.save(out/'manifest.json',clones)
subprocess.run(['node',str(Path(__file__).with_name('check.cjs')),str(out)],check=True,timeout=120)
print(json.dumps(dict(recovered=len(records),learning_calls=sum(r['learningCalls'] for r in records),holdout_calls=sum(r['holdoutCalls'] for r in records))))
