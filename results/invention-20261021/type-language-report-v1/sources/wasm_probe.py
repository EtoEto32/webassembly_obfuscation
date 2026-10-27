"""Loop-peeling control and small memory-load constraint frontend, no novel obfuscator."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('type_gate_common', ROOT/'research/isotope-swizzle/prototype.py')
q = importlib.util.module_from_spec(spec)
spec.loader.exec_module(q)
PY = ROOT/'.tools/retypd-python/Scripts/python.exe'
HERE = Path(__file__).resolve().parent


def step(src):
    return f'''(if (result i32)
      (i32.and (i32.shr_u (local.get 1) (local.get 4)) (i32.const 1))
      (then (i32.load offset=4 (local.get {src})))
      (else (i32.load (local.get {src}))))'''


def module(n, peeled, forced=False):
    # All integer parameter words supported. Bit shift counts use Wasm's mod-32 rule.
    total = '(i32.and (local.get 2) (i32.const 31))'
    if not peeled:
        total = f'(i32.add {total} (i32.const {n}))'
    suffix, pointer = [], 3
    if peeled:
        for j in range(n):
            dest = 6+j
            move=f'(i32.load offset=4 (local.get {pointer}))' if forced and j==0 else step(pointer)
            suffix += [f'(local.set {dest} {move})',
                       '(local.set 4 (i32.add (local.get 4) (i32.const 1)))']
            pointer = dest
    move=step(3)
    if forced and not peeled:
        move=f'''(if (result i32) (i32.eq (local.get 4) (i32.and (local.get 2) (i32.const 31)))
          (then (i32.load offset=4 (local.get 3))) (else {move}))'''
    return f'''(module (memory (export "memory") 1)
      (func (export "run") (param i32 i32 i32) (result i32)
        (local {' '.join(['i32']*(3+(n if peeled else 0)))})
        (local.set 3 (local.get 0)) (local.set 5 {total})
        (block (loop
          (br_if 1 (i32.ge_u (local.get 4) (local.get 5)))
          (local.set 3 {move})
          (local.set 4 (i32.add (local.get 4) (i32.const 1)))
          (br 0)))
        {' '.join(suffix)}
        (i32.load offset=8 (local.get {pointer}))))'''


def extract(binary):
    m = q.read(binary)
    fs = [e for e in m[1:] if e[0]=='func']
    if len(fs)!=1:
        raise q.Unsupported('one-function diagnostic profile')
    f = fs[0]
    # Limited structured SSA-style frontend for this probe, NOT NotDec's LLVM
    # frontend. Version locals so O3 local reuse does not falsely unify suffixes.
    cs, serial = set(['int \u2291 F.out']), [0]
    def fresh():
        serial[0] += 1
        return f'v{serial[0]}'
    def sub(a,b):
        if a is not None and b is not None and a!=b:
            cs.add(f'{a} \u2291 {b}')
    env = {0:'F.in_0',1:None,2:None}
    def sequence(es, env):
        value = None
        for e in es:
            if isinstance(e,list):
                value = visit(e,env)
        return value
    def join(a,b):
        if a==b:
            return a
        v=fresh()
        sub(a,v);sub(b,v)
        return v
    def visit(e,env):
        op=e[0]
        if op in ('type','param','result','local'):
            return None
        if op=='local.get':
            return env.get(int(e[1]))
        if op in ('local.set','local.tee'):
            v=visit(e[2],env);env[int(e[1])]=v
            return v if op=='local.tee' else None
        if op=='i32.load':
            base=visit(e[-1],env)
            if base is None:
                raise q.Unsupported('unmodeled load address')
            off=next((int(x[7:]) for x in e[1:-1] if isinstance(x,str) and x.startswith('offset=')),0)
            v=fresh();sub(f'{base}.load.\u03c34@{off}',v)
            return v
        if op=='if':
            branches={x[0]:x[1:] for x in e[1:] if isinstance(x,list) and x[0] in ('then','else')}
            left,right=dict(env),dict(env)
            a=sequence(branches.get('then',[]),left)
            b=sequence(branches.get('else',[]),right)
            for key in set(left)|set(right):
                env[key]=join(left.get(key),right.get(key))
            return join(a,b) if any(x[:1]==['result'] for x in e[1:] if isinstance(x,list)) else None
        if op=='block':
            return sequence(e[1:],env)
        if op=='loop':
            writes={int(x[1]) for x in q.walk(e) if x[0] in ('local.set','local.tee')}
            phis={k:fresh() if env.get(k) is not None else None for k in writes}
            for k,v in phis.items():
                sub(env.get(k),v);env[k]=v
            sequence(e[1:],env)
            for k,v in phis.items():
                sub(env.get(k),v);env[k]=v
            return None
        if op in ('br','br_if','i32.const','i32.add','i32.and','i32.shr_u','i32.eq','i32.eqz','i32.ge_u','i32.le_u'):
            # These are only integer loop controls in this input family.
            if any(x[0]=='i32.load' for x in q.walk(e)):
                raise q.Unsupported('load in integer-control expression')
            return None
        raise q.Unsupported('opcode outside diagnostic profile: '+op)
    v=sequence(f[1:],env)
    if v is None:
        raise q.Unsupported('return value missing')
    sub(v,'int')
    return sorted(cs)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('out', type=Path)
    p.add_argument('--forced',action='store_true',help='one compulsory right edge at suffix entry')
    a = p.parse_args()
    a.out.mkdir(parents=True, exist_ok=False)
    rows = []
    # Only bounded synthetic examples; stop a solver family after its first timeout.
    timedout = set()
    for n in (1,2,4,6,8):
        for peeled in (False, True):
            mode = 'peeled' if peeled else 'loop'
            start = time.perf_counter()
            raw = a.out/f'{mode}-{n}-raw.wasm'
            q.compile(module(n,peeled,a.forced), raw)
            opt = a.out/f'{mode}-{n}-O3.wasm'
            q.tool('wasm-opt', [raw,'-O3','--enable-bulk-memory','-o',opt])
            q.w.tool('wasm-validate',[opt])
            build_ms = (time.perf_counter()-start)*1000
            for binary in (raw,opt):
                row = {'n':n,'mode':mode,'forced':a.forced,'file':binary.name,'sha256':q.digest(binary),
                       'bytes':binary.stat().st_size,'build_pair_ms':build_ms,
                       'linear_memory_bytes':65536}
                try:
                    txt = q.w.tool('wasm-decompile',[binary])
                    (a.out/(binary.stem+'.dcmp')).write_text(txt,encoding='utf-8')
                    row['wabt_decompile'] = {'status':'ok','chars':len(txt)}
                except Exception as e:
                    row['wabt_decompile'] = {'status':'error','detail':str(e)}
                try:
                    cs = extract(binary)
                    cf = a.out/(binary.stem+'.constraints.json')
                    q.save(cf,cs)
                    row['frontend'] = 'ok'
                    row['constraints'] = len(cs)
                    row['retypd'] = []
                    for solver in ('dfa','pathexpr'):
                        if (solver,mode) in timedout:
                            row['retypd'].append({'mode':solver,'status':'not_run_after_timeout'})
                            continue
                        cmd = [str(PY),str(HERE/'pilot.py'),'--worker',str(n),'--mode',solver,'--constraints',str(cf)]
                        dest = a.out/(binary.stem+'.'+solver)
                        try:
                            run = subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',timeout=15,
                                                 env=dict(os.environ,PYTHONHASHSEED='0',PYTHONIOENCODING='utf-8'))
                            dest.with_suffix(dest.suffix+'.stdout.txt').write_text(run.stdout,encoding='utf-8')
                            dest.with_suffix(dest.suffix+'.stderr.txt').write_text(run.stderr,encoding='utf-8')
                            result = json.loads(run.stdout) if run.returncode==0 else {'mode':solver,'status':'error','exit_code':run.returncode}
                        except subprocess.TimeoutExpired:
                            result={'mode':solver,'status':'timeout','seconds':15}
                            timedout.add((solver,mode))
                        row['retypd'].append(result)
                except q.Unsupported as e:
                    row['frontend'] = 'unsupported'
                    row['frontend_reason'] = str(e)
                rows.append(row)
                print(json.dumps({'file':binary.name,'frontend':row['frontend'],
                                  'solvers':[(r['mode'],r['status']) for r in row.get('retypd',[])]}),flush=True)
                q.save(a.out/'manifest.json',{'scope':'known loop-peeling control, not a novel obfuscator','rows':rows})
    q.save(a.out/'environment.json',{'python':sys_version(),'wabt':q.w.tool('wat2wasm',['--version']).strip(),
                                      'binaryen':q.tool('wasm-opt',['--version']).strip()})


def sys_version():
    import sys
    return sys.version


if __name__=='__main__':
    main()
