import json
from pathlib import Path
import subprocess
import sys
import time
import recover as r


def main(source,dest):
    source=Path(source).resolve();out=Path(dest).resolve();out.mkdir(parents=True,exist_ok=False)
    manifest=json.loads((source/'manifest.json').read_text(encoding='utf-8'));cases=json.loads((source/'cases.json').read_text(encoding='utf-8'))
    expected={c['name']:c for c in cases};attacks=[];outputs=[];rejects=[]
    for row in manifest:
        if row['variant']=='recovered':continue
        dst=out/(Path(row['file']).stem+'-recovered.wasm');start=time.perf_counter()
        try:stats=r.recover(source/row['file'],dst)
        except ValueError as e:
            if not row.get('negative'):raise
            rejects.append(dict(file=row['file'],status='rejected',message=str(e)));continue
        if row.get('negative'):raise AssertionError('negative accepted')
        c=expected[row['name']];reference=out/(row['name']+'-plain.wasm')
        if not reference.exists():r.p.q.compile(r.p.render(c['edges'],c['payload']),reference)
        same=dst.read_bytes()==reference.read_bytes()
        if not same:raise AssertionError('wrong recovered binary')
        attacks.append(dict(file=row['file'],status='success',byte_identical=same,**stats))
        outputs.append(dict(name=row['name'],file=dst.name,variant='recovered',opt=row['opt']))
        print(json.dumps(dict(file=row['file'],status='success')),flush=True)
    # A range-correct but effectful expression, a missing guard, and an exported memory
    # must not be admitted by the limited proof rule.
    base=r.p.q.read(source/'n4-v0-original-raw.wasm');c=expected['n4-v0']
    for label in ('effectful-partner','missing-guard','exported-memory'):
        import copy
        m=copy.deepcopy(base);f=[x for x in m[1:] if x[0]=='func'][1]
        if label=='effectful-partner':
            t=next(x for x in r.b.walk(f) if x[:2]==['local.set','5']);t[2]=['local.tee','4',t[2]]
        elif label=='missing-guard':
            f.remove(next(x for x in f if isinstance(x,list) and x[0]=='if'))
        else:m.append(['export','"memory"',['memory','0']])
        src=out/(label+'.wasm');r.p.q.compile(r.p.q.w.emit(m),src)
        try:r.recover(src,out/(label+'-recovered.wasm'))
        except ValueError as e:rejects.append(dict(file=src.name,status='rejected',message=str(e)))
        else:raise AssertionError('unsafe/unsupported module accepted')
    r.p.q.save(out/'cases.json',cases);r.p.q.save(out/'manifest.json',outputs)
    r.p.q.save(out/'attacks.json',attacks);r.p.q.save(out/'rejections.json',rejects)
    check=subprocess.run(['node',str(r.HERE/'check.cjs'),str(out)],capture_output=True,text=True,timeout=180)
    (out/'checks.stdout.txt').write_text(check.stdout,encoding='utf-8');(out/'checks.stderr.txt').write_text(check.stderr,encoding='utf-8')
    if check.returncode:raise RuntimeError(check.stderr)
    checks=json.loads(check.stdout);r.p.q.save(out/'checks.json',checks)
    sources=[r.HERE/f for f in ('run.py','recover.py','adapt.py','check.cjs','plan.md')]
    snapshot=out/'sources';snapshot.mkdir()
    for f in sources:(snapshot/f.name).write_bytes(f.read_bytes())
    r.p.q.save(out/'provenance.json',[dict(file=str(f.relative_to(out)),sha256=r.p.q.digest(f)) for f in sorted(out.rglob('*')) if f.is_file()])
    print(json.dumps(dict(recovered=len(attacks),rejected=len(rejects),calls=checks['calls'],traps=checks['traps'],mismatches=checks['mismatches'])))


if __name__=='__main__':main(*sys.argv[1:])
