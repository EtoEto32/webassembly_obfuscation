"""Recover a forward DFA by composing observable predicates, without decoding E."""
import argparse
import functools
import tempfile
import time
from pathlib import Path
import prototype as p

MASK = 0xffffffff


def expression(f):
    if [v for e in f[1:] if e[0] == 'param' for v in e[1:]] != ['i32']:
        raise ValueError('one i32 helper argument')
    if [v for e in f[1:] if e[0] == 'result' for v in e[1:]] != ['i32']:
        raise ValueError('one i32 helper result')
    env = [('x',)]
    for e in f[1:]:
        if e[0] == 'local':
            if any(t != 'i32' for t in e[1:]): raise ValueError('i32 locals only')
            env += [('c', 0)] * len(e[1:])
    allowed = {'i32.and', 'i32.or', 'i32.xor', 'i32.add', 'i32.sub', 'i32.mul',
               'i32.shl', 'i32.shr_u', 'i32.shr_s', 'i32.eq', 'i32.ne'}
    def walk(e):
        op = e[0]
        if op == 'local.get': return env[int(e[1])]
        if op == 'i32.const': return ('c', int(e[1], 0) & MASK)
        if op in ('local.set', 'local.tee'):
            value = walk(e[2]); env[int(e[1])] = value
            return value if op == 'local.tee' else None
        if op in allowed: return (op, walk(e[1]), walk(e[2]))
        if op == 'i32.eqz': return (op, walk(e[1]))
        raise ValueError('helper instruction ' + op)
    result = None
    for e in f[1:]:
        if e[0] not in ('type', 'param', 'result', 'local'): result = walk(e)
    if result is None: raise ValueError('no result')
    return result


@functools.lru_cache(None)
def dependencies(e, demand=MASK):
    op = e[0]
    if not demand or op == 'c': return 0
    if op == 'x': return demand
    if op == 'i32.and':
        if e[1][0] == 'c': return dependencies(e[2], demand & e[1][1])
        if e[2][0] == 'c': return dependencies(e[1], demand & e[2][1])
    if op in ('i32.shl', 'i32.shr_u', 'i32.shr_s'):
        if e[2][0] != 'c': raise ValueError('variable helper shift')
        shift = e[2][1] & 31
        mask = demand >> shift if op == 'i32.shl' else (demand << shift) & MASK
        if op == 'i32.shr_s' and demand >> (32-shift if shift else 32): mask |= 1 << 31
        return dependencies(e[1], mask)
    if op in ('i32.add', 'i32.sub', 'i32.mul'): demand = (1 << demand.bit_length()) - 1
    if op in ('i32.eq', 'i32.ne', 'i32.eqz'): demand = MASK if demand & 1 else 0
    result = 0
    for child in e[1:]: result |= dependencies(child, demand)
    return result


def table(expr, size):
    @functools.lru_cache(None)
    def walk(e):
        op = e[0]
        if op == 'c': return (e[1],) * size
        if op == 'x': return tuple(range(size))
        a = walk(e[1])
        if op == 'i32.eqz': return tuple(int(x == 0) for x in a)
        b = walk(e[2])
        functions = {'i32.and': lambda x, y: x & y, 'i32.or': lambda x, y: x | y,
                     'i32.xor': lambda x, y: x ^ y, 'i32.add': lambda x, y: (x+y) & MASK,
                     'i32.sub': lambda x, y: (x-y) & MASK, 'i32.mul': lambda x, y: (x*y) & MASK,
                     'i32.shl': lambda x, y: (x << (y & 31)) & MASK,
                     'i32.shr_u': lambda x, y: x >> (y & 31),
                     'i32.shr_s': lambda x, y: ((x if x < 2**31 else x-2**32) >> (y & 31)) & MASK,
                     'i32.eq': lambda x, y: int(x == y), 'i32.ne': lambda x, y: int(x != y)}
        return tuple(functions[op](x, y) for x, y in zip(a, b))
    result = walk(expr); walk.cache_clear(); return result


def inspect(src):
    mod = p.q.read(src)
    if any(e[0] not in ('type', 'func', 'table', 'export', 'elem') for e in mod[1:]):
        raise ValueError('closed pure module required')
    if [e for e in mod[1:] if e[0] == 'table'] != [['table', '3', '3', 'funcref']]:
        raise ValueError('three fixed table entries')
    if [e for e in mod[1:] if e[0] == 'elem'] != [['elem', ['i32.const', '0'], 'func', '0', '1', '2']]:
        raise ValueError('canonical table')
    if [e for e in mod[1:] if e[0] == 'export'] != [['export', '"run"', ['func', '3']]]:
        raise ValueError('single run export')
    fs = [e for e in mod[1:] if e[0] == 'func']
    if len(fs) != 4: raise ValueError('four functions')
    initial = {int(e[2][1], 0) & MASK for e in p.q.walk(fs[3]) if e[0] in ('local.set', 'local.tee')
               and len(e) == 3 and e[2][0] == 'i32.const' and int(e[2][1], 0) != 0}
    if len(initial) != 1: raise ValueError('unique nonzero initial state')
    return mod, fs, next(iter(initial))


def verify_driver(fs, initial):
    hs = [p.q.w.emit(['func', *[e for e in f[1:] if e[0] != 'type']]) for f in fs[:3]]
    with tempfile.TemporaryDirectory(dir=p.ROOT / 'tmp', prefix='observer-driver-') as td:
        raw, opt = Path(td)/'raw.wasm', Path(td)/'opt.wasm'
        p.q.compile(p.assemble(hs, initial, True), raw)
        expected = [e for e in p.q.read(raw)[1:] if e[0] == 'func'][-1]
        if expected == fs[3]: return 'raw-canonical'
        p.q.tool('wasm-opt', [raw, '-O3', '-o', opt])
        expected = [e for e in p.q.read(opt)[1:] if e[0] == 'func'][-1]
        if expected == fs[3]: return 'O3-canonical'
        raise ValueError('consumer differs from reverse-input driver')


def recover(src, dst):
    start = time.perf_counter(); mod, fs, initial = inspect(src); read_end = time.perf_counter()
    expressions = [expression(f) for f in fs[:3]]
    deps = 0
    for expr in expressions: deps |= dependencies(expr)
    width = deps.bit_length()
    if not 3 <= width <= 10 or initial >= 1 << width: raise ValueError('state width outside bounded analysis')
    driver = verify_driver(fs, initial); verified = time.perf_counter()
    zero, one, output = [table(expr, 1 << width) for expr in expressions]
    if max(zero+one) >= 1 << width or any(x not in (0, 1) for x in output):
        raise ValueError('transition range or output')
    table_end = time.perf_counter()
    observers = [output]; ids = {output: 0}; delta = []
    index = 0
    while index < len(observers):
        row = []
        for step in (zero, one):
            nxt = tuple(observers[index][step[z]] for z in range(1 << width))
            if nxt not in ids:
                if len(observers) >= 1024: raise ValueError('observer limit exceeded')
                ids[nxt] = len(observers); observers.append(nxt)
            row.append(ids[nxt])
        delta.append(row); index += 1
    accept = sum(observer[initial] << i for i, observer in enumerate(observers))
    orbit_end = time.perf_counter()
    if len(delta) > 32: raise ValueError('recovered acceptance mask width')
    p.q.compile(p.source(delta, accept), dst)
    end = time.perf_counter(); dependencies.cache_clear()
    return dict(width=width, full_state_domain=1 << width, observer_states=len(observers),
                delta=delta, accept=accept, driver=driver, original_api_queries=0,
                read_ms=(read_end-start)*1000, verify_driver_ms=(verified-read_end)*1000,
                table_ms=(table_end-verified)*1000, orbit_ms=(orbit_end-table_end)*1000,
                emit_ms=(end-orbit_end)*1000, total_ms=(end-start)*1000,
                original_code_or_encoding_used=False)


if __name__ == '__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('source'); ap.add_argument('output'); a=ap.parse_args()
    p.q.save(str(a.output)+'.json', recover(a.source, a.output))
