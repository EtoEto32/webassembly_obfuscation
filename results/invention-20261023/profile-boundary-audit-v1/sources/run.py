"""Metamorphic scope audit, not a new obfuscator or a general deobfuscator."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
spec = importlib.util.spec_from_file_location('factor', HERE.parent/'mutable-factor/prototype.py')
p = importlib.util.module_from_spec(spec); spec.loader.exec_module(p)
VARIANTS = ('original', 'locals', 'add-zero', 'guards', 'xor-partner', 'affine-partner', 'select-partner')


def walk(x):
    if isinstance(x, list):
        yield x
        for y in x[1:]: yield from walk(y)


def expression(variant, n):
    a, b, s = (['local.get', str(i)] for i in (0, 1, 3))
    c = lambda v: ['i32.const', str(v)]
    if variant == 'xor-partner': t = ['i32.xor', ['i32.xor', a, b], s]
    elif variant == 'affine-partner': t = ['i32.add', ['i32.mul', a, c(1664525)], ['i32.mul', b, s]]
    elif variant == 'select-partner':
        # Both arms are in range by the guards, without an explicit final mask.
        return ['select', a, b, ['i32.and', s, c(1)]]
    elif variant == 'bad-range': return c(n)
    else: raise ValueError(variant)
    return ['i32.and', t, c(n-1)]


def mutate(module, variant, n):
    m = copy.deepcopy(module)
    fs = [x for x in m[1:] if x[0] == 'func']; run = fs[1]
    if variant == 'original': return m
    if variant == 'locals':
        renaming = {4:8, 5:7, 6:6, 7:5, 8:4}
        for node in walk(run):
            if node[0] in ('local.get', 'local.set', 'local.tee'):
                node[1] = str(renaming.get(int(node[1]), int(node[1])))
    elif variant == 'add-zero':
        target = next(x for x in walk(run) if x[:2] == ['local.set', '5'])
        target[2] = ['i32.add', target[2], ['i32.const', '0']]
    elif variant == 'guards':
        indices = [i for i,x in enumerate(run) if isinstance(x,list) and x[0]=='if']
        assert len(indices)==3
        old = [run[i] for i in indices]
        for i,v in zip(indices, reversed(old)): run[i]=v
    else:
        target = next(x for x in walk(run) if x[:2] == ['local.set', '5'])
        target[2] = expression(variant, n)
    return m


def range_proofs():
    sys.path.insert(0, str(ROOT/'.tools/encoding-synthesis-python'))
    import z3 as z
    u,v,s = z.BitVecs('u v steps',32)
    def evaluate(e):
        op=e[0]
        if op=='local.get': return {0:u,1:v,3:s}[int(e[1])]
        if op=='i32.const': return z.BitVecVal(int(e[1]),32)
        args=[evaluate(t) for t in e[1:]]
        if op=='i32.add': return args[0]+args[1]
        if op=='i32.mul': return args[0]*args[1]
        if op=='i32.and': return args[0]&args[1]
        if op=='i32.xor': return args[0]^args[1]
        if op=='select': return z.If(args[2]!=0,args[0],args[1])
        raise ValueError(op)
    rows=[]
    for n in (4,16,128):
        for variant in ('xor-partner','affine-partner','select-partner','bad-range'):
            solver=z.Solver();solver.set(timeout=10000)
            solver.add(z.ULT(u,n),z.ULT(v,n),z.UGE(evaluate(expression(variant,n)),n))
            t=time.perf_counter();status=str(solver.check())
            assert status==('sat' if variant=='bad-range' else 'unsat')
            rows.append(dict(n=n,variant=variant,status=status,ms=(time.perf_counter()-t)*1000))
    return dict(z3=z.get_version_string(),results=rows)


def main(source, dest):
    source=Path(source).resolve();out=Path(dest).resolve();out.mkdir(parents=True,exist_ok=False)
    cases=json.loads((source/'cases.json').read_text(encoding='utf-8'));manifest=[];attacks=[]
    p.q.save(out/'range-proofs.json',range_proofs())
    for c in cases:
        n=len(c['edges']);src=source/(c['name']+'-moving-raw.wasm');module=p.q.read(src)
        for variant in VARIANTS:
            raw=out/(c['name']+'-'+variant+'-raw.wasm')
            p.q.compile(p.q.w.emit(mutate(module,variant,n)),raw)
            for opt in ('raw','O3'):
                f=out/(c['name']+'-'+variant+'-'+opt+'.wasm')
                if opt=='O3': p.q.w.tool('wasm-opt',[raw,'--enable-bulk-memory','-O3','-o',f])
                p.q.w.tool('wasm-validate',[f])
                manifest.append(dict(name=c['name'],variant=variant,opt=opt,file=f.name,bytes=f.stat().st_size))
                t=time.perf_counter();record=dict(file=f.name,variant=variant,opt=opt)
                recovered=out/(f.stem+'-recovered.wasm')
                try:
                    stats=p.recover(f,recovered)
                    equal=recovered.read_bytes()==(source/(c['name']+'-plain-raw.wasm')).read_bytes()
                    record.update(status='success',recovered=recovered.name,byte_identical=equal,details=stats)
                    if not equal: raise AssertionError('unexpected output')
                    manifest.append(dict(name=c['name'],variant='recovered',opt=opt,file=recovered.name,bytes=recovered.stat().st_size))
                except ValueError as e: record.update(status='unsupported',message=str(e))
                except subprocess.TimeoutExpired as e: record.update(status='timeout',message=str(e))
                except Exception as e: record.update(status='crash',message=repr(e))
                record['wall_ms']=(time.perf_counter()-t)*1000;attacks.append(record)
        for variant in ('bad-range','bad-order'):
            f=out/(c['name']+'-'+variant+'.wasm')
            if variant=='bad-range': text=p.q.w.emit(mutate(module,variant,n))
            else:
                edges,payload,_,perm=p.recognize(src,['moving'])
                text=p.render(edges,payload,'bad-order',perm)
            p.q.compile(text,f)
            manifest.append(dict(name=c['name'],variant=variant,file=f.name,negative=True))
        print(json.dumps(dict(done=c['name'])),flush=True)
    p.q.save(out/'cases.json',cases);p.q.save(out/'manifest.json',manifest);p.q.save(out/'attacks.json',attacks)
    r=subprocess.run(['node',str(HERE/'check.cjs'),str(out)],capture_output=True,text=True,timeout=180)
    (out/'checks.stdout.txt').write_text(r.stdout,encoding='utf-8');(out/'checks.stderr.txt').write_text(r.stderr,encoding='utf-8')
    if r.returncode: raise RuntimeError(r.stderr)
    checks=json.loads(r.stdout);p.q.save(out/'checks.json',checks)
    sources=[HERE/'run.py',HERE/'check.cjs',HERE/'plan.md',p.HERE/'prototype.py',p.HERE/'model.py',p.HERE.parent/'mutation-quotient/prototype.py',p.HERE.parent/'isotope-swizzle/prototype.py',p.HERE.parent/'connectivity-elimination/prototype.py']
    snapshot=out/'sources';snapshot.mkdir()
    for f in sources:
        target=snapshot/f.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(f.read_bytes())
    p.q.save(out/'provenance.json',[dict(file=str(f.relative_to(out)),sha256=p.q.digest(f)) for f in sorted(out.rglob('*')) if f.is_file()])
    counts={s:sum(a['status']==s for a in attacks) for s in ('success','unsupported','timeout','crash')}
    print(json.dumps(dict(attacks=counts,calls=checks['calls'],traps=checks['traps'],mismatches=checks['mismatches'])))


if __name__=='__main__': main(*sys.argv[1:])
