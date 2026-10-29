"""Candidate B follow-up: true reentry, transitive effects, sparse read sets.

Untrusted Wasm summaries are derived from the exact optimized binary. This
restricted analyzer rejects shared memory and falls back on unknown effects.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import time

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('probe', HERE / 'probe.py')
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


def summary(mod, export='"callback"'):
    flat = p.w.emit(mod)
    if ' shared' in flat:
        return {'kind': 'reject', 'reason': 'shared memory'}
    memory = [x for x in mod[1:] if x[0] == 'memory']
    if len(memory) != 1:
        return {'kind': 'reject', 'reason': 'one defined nonshared memory required'}
    imports = [x for x in mod[1:] if x[0] == 'import' and x[3][0] == 'func']
    funcs = [x for x in mod[1:] if x[0] == 'func']
    exports = {x[1]:x[2] for x in mod[1:] if x[0] == 'export'}
    if exports.get(export, [''])[0] != 'func':
        return {'kind': 'reject', 'reason': 'entry missing'}
    if exports.get('"memory"') != ['memory', '0']:
        return {'kind': 'reject', 'reason': 'wrong exported memory'}
    effects, visited = [], set()
    fuel = [10000]

    def val(x, env):
        if x[0] == 'i32.const' and len(x) == 2:
            return ['const', int(x[1]) & 0xffffffff]
        if x[0] == 'local.get' and len(x) == 2 and 0 <= int(x[1]) < len(env):
            return env[int(x[1])]
        if x[0] in ('i32.add', 'i32.sub', 'i32.and') and len(x) == 3:
            return [x[0][4:], val(x[1], env), val(x[2], env)]
        raise ValueError('value/address outside restricted language')

    def function(index, env, stack):
        if index < len(imports):
            raise ValueError('reachable host import')
        if index in stack:
            raise ValueError('recursive call summary unavailable')
        f = funcs[index-len(imports)]
        params = [a for x in f[1:] if isinstance(x,list) and x[0]=='param' for a in x[1:]]
        if params != ['i32']*len(env):
            raise ValueError('signature unsupported')
        visited.add(index)
        for x in f[1:]:
            if isinstance(x,str):
                raise ValueError('unexpected function atom')
            if x[0] in ('type','param'):
                continue
            walk(x, env, stack+(index,))

    def walk(x, env, stack):
        fuel[0] -= 1
        if fuel[0] < 0:
            raise ValueError('analysis expansion budget exceeded')
        if not isinstance(x,list):
            raise ValueError('unexpected statement atom')
        op = x[0]
        sizes = {'i32.store8':1,'i32.store16':2,'i32.store':4}
        if op in sizes:
            args=[a for a in x[1:] if isinstance(a,list)]
            attrs=[a for a in x[1:] if isinstance(a,str)]
            if len(args)!=2 or any(not a.startswith(('offset=','align=')) for a in attrs):
                raise ValueError('store form unsupported')
            val(args[1],env)
            effects.append({'addr':val(args[0],env), 'offset':next((int(a.split('=')[1]) for a in attrs if a.startswith('offset=')),0),'length':['const',sizes[op]]})
        elif op in ('memory.fill','memory.copy'):
            if len(x)!=4 or not all(isinstance(a,list) for a in x[1:]):
                raise ValueError('bulk form unsupported')
            val(x[2],env)
            effects.append({'addr':val(x[1],env),'offset':0,'length':val(x[3],env)})
        elif op=='call':
            function(int(x[1]),[val(a,env) for a in x[2:]],stack)
        elif op=='if':
            val(x[1],env)
            for a in x[2:]: walk(a,env,stack)
        elif op in ('then','else','block'):
            for a in x[1:]: walk(a,env,stack)
        elif op in ('nop','unreachable') and len(x)==1:
            pass  # Effects before unreachable remain part of the upper bound.
        else:
            raise ValueError('unsupported instruction: '+op)
    try:
        function(int(exports[export][1]),[['arg',i] for i in range(3)],())
        return {'kind':'ranges','writes':effects,'visitedFunctions':sorted(visited),'ignoredFunctionImports':len(imports)}
    except (ValueError,IndexError,KeyError) as e:
        return {'kind':'full','reason':str(e)}


def main(out):
    out.mkdir(parents=True,exist_ok=False)
    (out/'sources').mkdir()
    for name in ('boundary.py','boundary.cjs','probe.py'):
        shutil.copy2(HERE/name,out/'sources'/name)
    cases = {
        'transitive':('(i32.store8 (local.get 0) (local.get 1))','(call $helper (i32.add (local.get 0) (i32.const 4)) (local.get 1) (local.get 2))'),
        'descriptor-change':('(i32.store (i32.const 4) (i32.const 9000)) (i32.store8 (local.get 0) (local.get 1))','(call $helper (local.get 0) (local.get 1) (local.get 2))'),
        'bulk-overlap':('(memory.copy (local.get 0) (i32.const 520) (local.get 2))','(call $helper (local.get 0) (local.get 1) (local.get 2))'),
        'prefix-trap':('(i32.store8 (i32.const 512) (local.get 1)) unreachable','(call $helper (local.get 0) (local.get 1) (local.get 2))'),
        'alias-branches':('(if (local.get 2) (then (i32.store16 (local.get 0) (local.get 1))) (else (i32.store (i32.const 516) (local.get 1))))','(call $helper (local.get 0) (local.get 1) (local.get 2)) (i32.store8 (local.get 0) (local.get 1))'),
        'reachable-import':('(call $mutate)','(call $helper (local.get 0) (local.get 1) (local.get 2))'),
        'memory-grow':('(drop (memory.grow (i32.const 1))) (i32.store8 (i32.const 512) (local.get 1))','(call $helper (local.get 0) (local.get 1) (local.get 2))'),
    }
    manifest=[]
    for name,(helper,callback) in cases.items():
        wat=f'''(module
          (import "host" "before" (func $before))
          (import "host" "mutate" (func $mutate))
          (memory (export "memory") 2 4)
          (func $helper (param i32 i32 i32) {helper})
          (func (export "callback") (param i32 i32 i32) {callback})
          (func (export "drive") (call $before)))'''
        source=out/(name+'.wat');source.write_text(wat,encoding='utf8')
        raw=out/(name+'-raw.wasm');p.w.tool('wat2wasm',[source,'-o',raw])
        opt=out/(name+'-O3.wasm');p.w.tool('wasm-opt',[raw,'-O3','--enable-bulk-memory','-o',opt])
        for binary in (raw,opt):
            p.w.tool('wasm-validate',[binary])
            folded=p.w.tool('wasm2wat',[binary,'--fold-exprs'])
            binary.with_suffix('.wat').write_text(folded,encoding='utf8')
            start=time.perf_counter();certificate=summary(p.w.parse(folded));elapsed=time.perf_counter()-start
            manifest.append({'name':name,'file':binary.name,'sha256':p.digest(binary),'bytes':binary.stat().st_size,'summary':certificate,'analysis_ms':elapsed*1000})
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
    r=subprocess.run(['node',str(HERE/'boundary.cjs'),str(out)],capture_output=True,text=True,timeout=120)
    (out/'stdout.txt').write_text(r.stdout,encoding='utf8');(out/'stderr.txt').write_text(r.stderr,encoding='utf8')
    (out/'sha256.json').write_text(json.dumps({str(q.relative_to(out)):p.digest(q) for q in out.rglob('*') if q.is_file()},indent=2),encoding='utf8')
    if r.returncode: raise RuntimeError(r.stderr)
    print(r.stdout)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path)
    main(ap.parse_args().output.resolve())
