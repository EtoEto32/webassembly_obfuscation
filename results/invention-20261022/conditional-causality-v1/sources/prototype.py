# -*- coding: utf-8 -*-
"""Conditional schedules -> shared cyclic evaluator. A falsification prototype.

The schedule principle is prior art; this module claims no independent novelty.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import struct
import time

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('causal_wat', HERE.parent/'connectivity-elimination/prototype.py')
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)
MAGIC = 0x31434357
STATE = 32768
OPS = {'add', 'sub', 'mul', 'and', 'or', 'xor', 'shl', 'shr_s', 'shr_u', 'rotl', 'rotr'}


def save(text, out):
    out = Path(out)
    if out.exists() or out.with_suffix('.wat').exists():
        raise FileExistsError(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.with_suffix('.wat').write_text(text, encoding='utf8')
    w.tool('wat2wasm', [out.with_suffix('.wat'), '-o', out])
    w.tool('wasm-validate', [out])


def optimize(src, out):
    if Path(out).exists():
        raise FileExistsError(out)
    w.tool('wasm-opt', [src, '-O3', '-o', out])
    w.tool('wasm-validate', [out])


def function_parts(f):
    declarations = {'type', 'param', 'result', 'local'}
    return [x for x in f[1:] if x[0] in declarations], [x for x in f[1:] if x[0] not in declarations]


def helper(f):
    head, body = function_parts(f)
    params = [v for x in head if x[0] == 'param' for v in x[1:]]
    locals_ = [v for x in head if x[0] == 'local' for v in x[1:]]
    if params != ['i32'] or [x for x in head if x[0] == 'result'] != [['result', 'i32']] or any(v != 'i32' for v in locals_) or len(locals_) > 64:
        raise ValueError('Unary i32 helper profile')
    nodes = [0]
    def visit(t):
        nodes[0] += 1
        if not isinstance(t, list) or not t:
            raise ValueError('Folded pure helper required')
        if t[0] == 'i32.const' and len(t) == 2:
            int(t[1]); return
        if t[0] == 'local.get' and len(t) == 2 and 0 <= int(t[1]) <= len(locals_):
            return
        if t[0] in ('local.set', 'local.tee') and len(t) == 3 and 1 <= int(t[1]) <= len(locals_):
            visit(t[2]); return
        if t[0].startswith('i32.') and t[0][4:] in OPS and len(t) == 3:
            visit(t[1]); visit(t[2]); return
        raise ValueError('Non-total helper instruction: '+w.emit(t))
    for t in body:
        visit(t)
    if nodes[0] > 512:
        raise ValueError('Helper size cap')
    return [x for x in head if x[0] != 'type'] + body


def source(src):
    w.tool('wasm-validate', [src])
    m = w.parse(w.tool('wasm2wat', [src, '--fold-exprs']))
    if any(t[0] not in ('type', 'func', 'export') for t in m[1:]):
        raise ValueError('Only pure source module supported')
    fs = [t for t in m[1:] if t[0] == 'func']
    n = len(fs)-1
    if not 2 <= n <= 16 or [t for t in m[1:] if t[0] == 'export'] != [['export', '"run"', ['func', str(n)]]]:
        raise ValueError('Source functions/exports')
    helpers = [helper(f) for f in fs[:-1]]
    head, body = function_parts(fs[-1])
    if [v for t in head if t[0] == 'param' for v in t[1:]] != ['i32', 'i32'] or [t for t in head if t[0] == 'result'] != [['result', 'i32']] or any(t[0] == 'local' for t in head):
        raise ValueError('run signature')
    if len(body) != 1 or len(body[0]) != 5:
        raise ValueError('One if expression required')
    b = body[0]
    if b[:3] != ['if', ['result', 'i32'], ['i32.and', ['local.get', '1'], ['i32.const', '1']]] or b[3][0] != 'then' or b[4][0] != 'else' or len(b[3]) != 2 or len(b[4]) != 2:
        raise ValueError('Selector profile')
    def chain(t):
        if t == ['local.get', '0']:
            return []
        if t[0] != 'call' or len(t) != 3 or not 0 <= int(t[1]) < n:
            raise ValueError('Composition profile')
        return chain(t[2]) + [int(t[1])]
    orders = [chain(b[4][1]), chain(b[3][1])]
    if any(sorted(o) != list(range(n)) for o in orders):
        raise ValueError('Each branch must use every helper exactly once')
    return helpers, orders


def direct(helpers, orders):
    def chain(o):
        x = '(local.get 0)'
        for j in o:
            x = f'(call {j} {x})'
        return x
    functions = '\n'.join(w.emit(['func']+f) for f in helpers)
    return f'''(module {functions}
    (func (export "run") (param i32 i32) (result i32)
      (if (result i32) (i32.and (local.get 1) (i32.const 1))
        (then {chain(orders[1])}) (else {chain(orders[0])}))))'''


def scs(a, b):
    dp = [[[] for _ in range(len(b)+1)] for _ in range(len(a)+1)]
    for i in range(len(a), -1, -1):
        for j in range(len(b), -1, -1):
            if i == len(a): dp[i][j] = b[j:]
            elif j == len(b): dp[i][j] = a[i:]
            elif a[i] == b[j]: dp[i][j] = [a[i]] + dp[i+1][j+1]
            else:
                aa, bb = [a[i]]+dp[i+1][j], [b[j]]+dp[i][j+1]
                dp[i][j] = min((aa, bb), key=lambda x: (len(x), x))
    return dp[0][0]


def is_subsequence(order, schedule):
    i = 0
    for j in schedule:
        if i < len(order) and order[i] == j: i += 1
    return i == len(order)


def make_record(helpers, orders, mode):
    n = len(helpers)
    preds = []
    for o in orders:
        p = [0]*n
        for k, j in enumerate(o): p[j] = o[k-1] if k else n
        preds.append(p)
    schedule = scs(*orders) if mode == 'cyclic' else orders[0]+orders[1]
    return {'n': n, 'mode': mode, 'preds': preds, 'roots': [o[-1] for o in orders], 'schedule': schedule}


def recover_orders(r, check_schedule=True):
    n = r['n']; orders = []
    for p, root in zip(r['preds'], r['roots']):
        rev = []; j = root
        while j != n:
            if not 0 <= j < n or j in rev: raise ValueError('Predecessor graph is not a finite chain')
            rev.append(j); j = p[j]
        if sorted(rev) != list(range(n)): raise ValueError('Uncovered helper')
        orders.append(rev[::-1])
    if check_schedule:
        if r['mode'] == 'cyclic':
            if any(not is_subsequence(o, r['schedule']) for o in orders):
                raise ValueError('Schedule does not cover both causal orders')
        elif r['schedule'] != orders[0]+orders[1]:
            raise ValueError('Ordered schedule mismatch')
    return orders


def render(helpers, r, probe=False):
    n = r['n']; mode = int(r['mode'] == 'cyclic'); sched = r['schedule']
    words = [MAGIC, n, mode, len(sched), *r['roots'], *r['preds'][0], *r['preds'][1], *sched]
    blob = struct.pack('<'+'I'*len(words), *words)
    literal = '"'+''.join('\\%02x'%b for b in blob)+'"'
    functions = '\n'.join(w.emit(['func']+f) for f in helpers)
    table = ' '.join(str(j) for j in range(n))
    count = len(sched) if mode else n
    begin = '(i32.const 0)' if mode else f'(i32.mul (local.get $s) (i32.const {n}))'
    export = '(export "memory" (memory 0))' if probe else ''
    return f'''(module
      (type $op (func (param i32) (result i32)))
      {functions}
      (table {n} {n} funcref) (elem (i32.const 0) {table})
      (memory 1 1) {export} (data (i32.const 0) {literal})
      (func (export "run") (param $x i32) (param $s i32) (result i32)
        (local $k i32) (local $end i32) (local $j i32) (local $p i32) (local $arg i32)
        (local.set $s (i32.and (local.get $s) (i32.const 1)))
        (local.set $k {begin})
        (local.set $end (i32.add (local.get $k) (i32.const {count})))
        (loop $L
          (local.set $j (i32.load offset={24+8*n} (i32.shl (local.get $k) (i32.const 2))))
          (local.set $p (i32.load offset=24 (i32.shl (i32.add (local.get $j) (i32.mul (local.get $s) (i32.const {n}))) (i32.const 2))))
          (local.set $arg (if (result i32) (i32.eq (local.get $p) (i32.const {n}))
             (then (local.get $x))
             (else (i32.load offset={STATE} (i32.shl (local.get $p) (i32.const 2))))))
          (i32.store offset={STATE} (i32.shl (local.get $j) (i32.const 2))
            (call_indirect (type $op) (local.get $arg) (local.get $j)))
          (local.set $k (i32.add (local.get $k) (i32.const 1)))
          (br_if $L (i32.lt_u (local.get $k) (local.get $end))))
        (i32.load offset={STATE} (i32.shl
          (i32.load offset=16 (i32.shl (local.get $s) (i32.const 2))) (i32.const 2)))))'''


def memory_bytes(m):
    mem = bytearray(65536)
    for d in (x for x in m[1:] if x[0] == 'data'):
        if d[1][0] != 'i32.const': raise ValueError('Active constant segment')
        at = int(d[1][1]); raw = bytearray()
        for s in d[2:]:
            s = s[1:-1]; i = 0
            while i < len(s):
                if s[i] != '\\': raw.append(ord(s[i])); i += 1
                elif len(s[i+1:i+3]) == 2 and all(c in '0123456789abcdefABCDEF' for c in s[i+1:i+3]):
                    raw.append(int(s[i+1:i+3], 16)); i += 3
                else:
                    raw.append({'t':9, 'n':10, 'r':13, '"':34, "'":39, '\\':92}[s[i+1]]); i += 2
        if at < 0 or at+len(raw) > 65536: raise ValueError('Data bounds')
        mem[at:at+len(raw)] = raw
    return mem


def read_family(src, directory):
    w.tool('wasm-validate', [src])
    m = w.parse(w.tool('wasm2wat', [src, '--fold-exprs']))
    mem = memory_bytes(m)
    magic, n, mode, count, root0, root1 = struct.unpack_from('<6I', mem)
    if magic != MAGIC or not 2 <= n <= 16 or mode not in (0,1) or not 1 <= count <= 32:
        raise ValueError('Public family header')
    preds = [list(struct.unpack_from('<'+'I'*n, mem, 24+4*n*b)) for b in (0,1)]
    sched = list(struct.unpack_from('<'+'I'*count, mem, 24+8*n))
    if any(j >= n for j in sched): raise ValueError('Schedule index')
    r = {'n':n, 'mode':'cyclic' if mode else 'ordered', 'preds':preds, 'roots':[root0,root1], 'schedule':sched}
    fs = [x for x in m[1:] if x[0] == 'func']
    els = [x for x in m[1:] if x[0] == 'elem']
    if len(els) != 1 or els[0][1] != ['i32.const','0'] or els[0][2] != 'func': raise ValueError('Table initialization')
    idx = list(map(int, els[0][3:]))
    if len(idx) != n or len(set(idx)) != n: raise ValueError('Table functions')
    helpers = [helper(fs[j]) for j in idx]
    directory = Path(directory); directory.mkdir(parents=True, exist_ok=False)
    rebuilt = directory/'family.wasm'; save(render(helpers,r), rebuilt)
    match = rebuilt.read_bytes() == Path(src).read_bytes()
    if not match:
        opt = directory/'family-O3.wasm'; optimize(rebuilt, opt)
        match = opt.read_bytes() == Path(src).read_bytes()
    if not match: raise ValueError('Actual binary differs from public evaluator template/raw-O3')
    return helpers, r


def transform(src, out, mode='cyclic'):
    t = time.perf_counter(); helpers, orders = source(src)
    r = make_record(helpers, orders, mode)
    recover_orders(r)
    save(render(helpers, r), out)
    return {'milliseconds':(time.perf_counter()-t)*1000, 'record':r}


def recover(src, out):
    t = time.perf_counter()
    helpers, r = read_family(src, Path(out).with_suffix('.family'))
    read_ms = (time.perf_counter()-t)*1000
    u = time.perf_counter(); orders = recover_orders(r); core_ms = (time.perf_counter()-u)*1000
    save(direct(helpers, orders), out)
    return {'milliseconds':(time.perf_counter()-t)*1000, 'read_guard_ms':read_ms, 'core_ms':core_ms, 'orders':orders, 'family_checked':True}


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('action', choices=['transform','recover'])
    ap.add_argument('source'); ap.add_argument('output'); ap.add_argument('--mode', choices=['cyclic','ordered'], default='cyclic')
    a = ap.parse_args()
    print(json.dumps(transform(a.source,a.output,a.mode) if a.action == 'transform' else recover(a.source,a.output), indent=2))
