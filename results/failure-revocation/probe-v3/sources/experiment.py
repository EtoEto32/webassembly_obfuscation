"""Generate controlled binaries, transform them, replay on two actual engines."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / '.tools/import-alias-quotient-python'))
import wasmtime as w
WAT = ROOT / '.tools/wabt-1.0.42/bin/wat2wasm.exe'
VALIDATE = ROOT / '.tools/wabt-1.0.42/bin/wasm-validate.exe'
REWRITE = ROOT / '.tools/failure-revocation-target/release/failure-revocation.exe'

def run(args):
    p = subprocess.run([str(x) for x in args], capture_output=True, text=True, encoding='utf8', timeout=60)
    return dict(args=[str(x) for x in args], code=p.returncode, stdout=p.stdout, stderr=p.stderr)

def source(route, outcome):
    elem = '(elem declare func $f $factory)'
    prep = ''
    if route == 'active': elem = '(elem (i32.const 0) func $f $factory)'
    elif route == 'set': prep = 'i32.const 0 ref.func $f table.set 0'
    elif route == 'passive':
        elem = '(elem $p func $f $factory)'
        prep = 'i32.const 0 i32.const 0 i32.const 2 table.init $p'
    elif route == 'host': prep = 'ref.func $f call $keep'
    elif route == 'global': prep = 'ref.func $f global.set $out'
    elif route == 'factory': prep = 'i32.const 1 ref.func $factory table.set 0'
    else: raise ValueError(route)
    failure = {'ok':'', 'trap':'unreachable', 'host-error':'call $fail'}[outcome]
    return f'''(module
      (type $ft (func (param i32) (result i32)))
      (import "env" "table" (table 8 funcref))
      (import "env" "memory" (memory 1))
      (import "env" "bias" (global $bias i32))
      (import "env" "out" (global $out (mut funcref)))
      (import "env" "keep" (func $keep (param funcref)))
      (import "env" "capture" (func $capture))
      (import "env" "fail" (func $fail))
      (global $private (mut i32) (i32.const 17))
      (func $helper (param i32) (result i32) local.get 0 i32.const 3 i32.mul)
      (func $f (export "f") (type $ft)
        i32.const 0 i32.const 0 i32.load i32.const 1 i32.add i32.store
        global.get $private i32.const 1 i32.add global.set $private
        local.get 0 call $helper global.get $bias i32.add global.get $private i32.add)
      (func $factory (export "factory") (result funcref) ref.func $f)
      {elem}
      (func $start {prep} call $capture {failure}) (start $start))'''

CONSUMER = '''(module (type $f (func (param i32) (result i32)))
 (import "env" "table" (table 1 funcref))
 (func (export "call") (param i32) (result i32) local.get 0 i32.const 0 call_indirect (type $f)))'''

def python_replay(spec):
    config = w.Config(); config.wasm_tail_call = True
    engine = w.Engine(config); rows = []
    consumer = w.Module.from_file(engine, spec['consumer'])
    for item in spec['cases']:
        for mode in ('original', 'rollback', 'entry', 'refs'):
            store = w.Store(engine)
            table = w.Table(store, w.TableType(w.ValType.funcref(), w.Limits(8, None)), None)
            memory = w.Memory(store, w.MemoryType(w.Limits(1, None)))
            bias = w.Global(store, w.GlobalType(w.ValType.i32(), False), 9)
            out = w.Global(store, w.GlobalType(w.ValType.funcref(), True), None)
            gate = w.Global(store, w.GlobalType(w.ValType.i32(), True), 1)
            held = []; during = []
            def keep(f):
                # The Python binding exposes a ctypes view into callback args.
                # Retain a copy of the funcref value before the callback returns.
                held.append(w.Func._from_raw(type(f._func).from_buffer_copy(f._func)))
            def capture():
                route = item['route']
                if route in ('active', 'set', 'passive'): held.append(table.get(store, 0))
                elif route == 'global': held.append(out.value(store))
                elif route == 'factory': held.append(table.get(store, 1)(store))
                assert len(held) == 1
                during.append(held[0](store, 5))
            def fail(): raise RuntimeError('controlled host failure')
            imports = [table, memory, bias, out,
                w.Func(store, w.FuncType([w.ValType.funcref()], []), keep),
                w.Func(store, w.FuncType([], []), capture), w.Func(store, w.FuncType([], []), fail)]
            if mode in ('entry', 'refs'): imports.append(gate)
            module = w.Module.from_file(engine, item['binaries']['original' if mode == 'rollback' else mode])
            error = None; instance = None
            try: instance = w.Instance(store, module, imports)
            except w.Trap as ex: error = 'trap'
            except RuntimeError as ex:
                if str(ex) != 'controlled host failure': raise
                error = 'host-error'
            if error:
                gate.set_value(store, 0)
                if mode == 'rollback':
                    for i in range(table.size(store)): table.set(store, i, None)
                    out.set_value(store, None)
            before = int.from_bytes(memory.read(store, 0, 4), 'little')
            # A separately instantiated module retains the reference, not the
            # original imported table slot. It exercises a Wasm-to-Wasm edge.
            saved = w.Table(store, w.TableType(w.ValType.funcref(), w.Limits(1, None)), held[0])
            consumer_i = w.Instance(store, consumer, [saved])
            attempts = []
            for route_name, f in [('host', held[0]), ('wasm', consumer_i.exports(store)['call'])]:
                for x in (-2147483648, -1, 0, 1, 2147483647):
                    try: value = f(store, x); result = dict(type='return', value=value)
                    except w.Trap: result = dict(type='trap')
                    attempts.append(dict(via=route_name, x=x, result=result))
            after = int.from_bytes(memory.read(store, 0, 4), 'little')
            rows.append(dict(name=item['name'], mode=mode, error=error, during=during,
                before=before, after=after, attempts=attempts))
    return dict(engine='Wasmtime Python 50.0.1', rows=rows)

def check(rows):
    by = {(r['name'],r['mode']):r for r in rows}
    for r in rows:
        failed = not r['name'].endswith(':ok')
        assert r['error'] == (r['name'].split(':')[1] if failed else None), r
        assert r['during'] == [42] and r['before'] == 1, r
        blocked = failed and r['mode'] in ('entry','refs')
        assert r['after'] == (1 if blocked else 11), r
        assert all(a['result']['type'] == ('trap' if blocked else 'return') for a in r['attempts']), r
        if not blocked:
            assert r['attempts'] == by[(r['name'],'original')]['attempts'], r
    return dict(instantiations=len(rows), postCalls=sum(len(r['attempts']) for r in rows),
        blockedCalls=sum(a['result']['type']=='trap' for r in rows for a in r['attempts']))

def main(out):
    out.mkdir(parents=True, exist_ok=False); cases=[]; commands=[]
    (out/'consumer.wat').write_text(CONSUMER)
    c=run([WAT,out/'consumer.wat','-o',out/'consumer.wasm']);commands.append(c);assert c['code']==0,c
    for route in ('active','set','passive','host','global','factory'):
        for outcome in ('ok','trap','host-error'):
            name=route+':'+outcome
            stem=route+'-'+outcome
            (out/(stem+'.wat')).write_text(source(route,outcome))
            original=out/(stem+'.wasm')
            c=run([WAT,out/(stem+'.wat'),'-o',original]);commands.append(c);assert c['code']==0,c
            binaries=dict(original=str(original.resolve())); transforms={}
            for mode in ('entry','refs'):
                target=out/(stem+'-'+mode+'.wasm')
                c=run([REWRITE,mode,original,target]);commands.append(c);assert c['code']==0,c
                transforms[mode]=json.loads(c['stdout']); binaries[mode]=str(target.resolve())
                c=run([VALIDATE,target]);commands.append(c);assert c['code']==0,c
            cases.append(dict(name=name,route=route,outcome=outcome,binaries=binaries,transforms=transforms))
    spec=dict(cases=cases,consumer=str((out/'consumer.wasm').resolve()))
    (out/'replay.json').write_text(json.dumps(spec,indent=2))
    c=run(['node',HERE/'replay.mjs',out/'replay.json']);commands.append(c);assert c['code']==0,c
    node=json.loads(c['stdout']);(out/'node.json').write_text(json.dumps(node,indent=2))
    py=python_replay(spec);(out/'wasmtime.json').write_text(json.dumps(py,indent=2))
    # name uses ':' so keep expected outcome parsing explicit in check.
    summary=dict(node=check(node['rows']),wasmtime=check(py['rows']),os=platform.platform(),python=sys.version)
    assert [{k:v for k,v in r.items() if k!='identity'} for r in node['rows']] == py['rows']
    summary['crossEngineExactRows']=True
    (out/'commands.json').write_text(json.dumps(commands,indent=2))
    sources=out/'sources';sources.mkdir()
    for p in (HERE/'experiment.py',HERE/'replay.mjs',HERE/'rewriter/src/main.rs',HERE/'rewriter/Cargo.toml',HERE/'rewriter/Cargo.lock',HERE/'plan.md'):
        shutil.copyfile(p,sources/p.name)
    hashes={str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file()}
    (out/'hashes.json').write_text(json.dumps(hashes,indent=2))
    (out/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('out',type=Path);main(ap.parse_args().out)
