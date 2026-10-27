"""Post-implementation checks of extra expressions and the remaining boundary."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import recover as r


def main(source,dest):
    source=Path(source).resolve();out=Path(dest).resolve();out.mkdir(parents=True,exist_ok=False)
    cases=json.loads((source/'cases.json').read_text(encoding='utf-8'));manifest=[];outcomes=[]
    for c in cases:
        n=len(c['edges']);base=r.p.q.read(source/(c['name']+'-original-raw.wasm'))
        g=lambda i:['local.get',str(i)];k=lambda i:['i32.const',str(i)]
        expressions={
            'shift-sub':['i32.and',['i32.sub',['i32.xor',['i32.shl',g(0),g(3)],g(1)],g(3)],k(n-1)],
            'unsigned-shift-or':['i32.and',['i32.or',['i32.shr_u',g(3),g(0)],g(1)],k(n-1)],
            'self-partner':g(0),
            'wide-mask':['i32.and',['i32.add',['i32.add',g(0),g(1)],g(3)],k(2*n-1)]}
        for label,expr in expressions.items():
            m=copy.deepcopy(base);t=next(x for x in r.b.walk(m) if x[:2]==['local.set','5']);t[2]=expr
            raw=out/(c['name']+'-'+label+'-raw.wasm');r.p.q.compile(r.p.q.w.emit(m),raw)
            for opt in ('raw','O3'):
                f=out/(c['name']+'-'+label+'-'+opt+'.wasm')
                if opt=='O3':r.p.q.w.tool('wasm-opt',[raw,'--enable-bulk-memory','-O3','-o',f])
                manifest.append(dict(name=c['name'],file=f.name,variant=label,opt=opt,negative=label=='wide-mask'))
                dst=out/(f.stem+'-recovered.wasm')
                try:
                    stats=r.recover(f,dst)
                    if label=='wide-mask':raise AssertionError('invalid range accepted')
                    reference=out/(c['name']+'-plain.wasm')
                    if not reference.exists():r.p.q.compile(r.p.render(c['edges'],c['payload']),reference)
                    if dst.read_bytes()!=reference.read_bytes():raise AssertionError('wrong recovered module')
                    outcomes.append(dict(file=f.name,status='success',**stats))
                    manifest.append(dict(name=c['name'],file=dst.name,variant='recovered',opt=opt))
                except ValueError as e:
                    if label not in ('self-partner','wide-mask'):raise
                    outcomes.append(dict(file=f.name,status='rejected',reason=str(e)))
    r.p.q.save(out/'cases.json',cases);r.p.q.save(out/'manifest.json',manifest);r.p.q.save(out/'outcomes.json',outcomes)
    result=subprocess.run(['node',str(r.HERE/'check.cjs'),str(out)],capture_output=True,text=True,timeout=180)
    (out/'checks.stdout.txt').write_text(result.stdout,encoding='utf-8');(out/'checks.stderr.txt').write_text(result.stderr,encoding='utf-8')
    if result.returncode:raise RuntimeError(result.stderr)
    checks=json.loads(result.stdout);r.p.q.save(out/'checks.json',checks)
    snapshot=out/'sources';snapshot.mkdir()
    for name in ('run.py','recover.py','holdout.py','check.cjs'):(snapshot/name).write_bytes((r.HERE/name).read_bytes())
    r.p.q.save(out/'provenance.json',[dict(file=str(f.relative_to(out)),sha256=r.p.q.digest(f)) for f in sorted(out.rglob('*')) if f.is_file()])
    print(json.dumps(dict(success=sum(x['status']=='success' for x in outcomes),rejected=sum(x['status']=='rejected' for x in outcomes),calls=checks['calls'],traps=checks['traps'],mismatches=checks['mismatches'])))


if __name__=='__main__':main(*sys.argv[1:])
