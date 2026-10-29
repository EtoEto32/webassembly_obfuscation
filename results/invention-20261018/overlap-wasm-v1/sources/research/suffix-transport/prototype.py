"""Restricted Wasm DFA scanner -> suffix-vector transport, and dual recovery.

Classical reversal and linear representations are explicitly not claimed new.
The transformer checks an exact source template. Recovery targets the generated
scanner family, including its Binaryen O2/O3 forms, not arbitrary Wasm programs.
"""
import argparse
from collections import deque
from dataclasses import dataclass
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import tempfile
import time

spec = importlib.util.spec_from_file_location('common', Path(__file__).resolve().parents[1]/'connectivity-elimination/prototype.py')
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)
N = 16
C = 1 << N  # constant term in affine GF(2) expressions


def popcount(x):
    return bin(x).count('1')


def xor_all(xs):
    y = 0
    for x in xs:
        y ^= x
    return y


def compose(a, b):
    return [xor_all(b[j] for j in range(N) if row >> j & 1) for row in a]


def apply(a, x):
    return sum((popcount(row & x) & 1) << i for i, row in enumerate(a))


def inverse(a):
    rows = [r | (1 << (N+i)) for i, r in enumerate(a)]
    for j in range(N):
        p = next((i for i in range(j, N) if rows[i] >> j & 1), None)
        if p is None:
            raise ValueError('Singular basis')
        rows[j], rows[p] = rows[p], rows[j]
        for i in range(N):
            if i != j and rows[i] >> j & 1:
                rows[i] ^= rows[j]
    return [r >> N for r in rows]


def basis(seed):
    rng = random.Random(seed)
    rows = [1 << i for i in range(N)]
    for _ in range(96):
        i, j = rng.sample(range(N), 2)
        rows[i] ^= rows[j]
    assert compose(rows, inverse(rows)) == [1 << i for i in range(N)]
    return rows


def vconst(values):
    return '(v128.const i8x16 ' + ' '.join(map(str, values)) + ')'


def maskconst(bits):
    return vconst([255 if bits >> i & 1 else 0 for i in range(N)])


def signed64(x):
    return x-(1 << 64) if x >> 63 else x


def plain(delta, final):
    assert len(delta) == 2 and all(len(t) == N for t in delta)
    packed = [signed64(sum(q << (4*i) for i, q in enumerate(t))) for t in delta]
    return f'''(module
 (memory (export "memory") 1 1)
 (func (export "run") (param i32 i32) (result i32) (local i32 i32 i32)
  (block (loop
   (br_if 1 (i32.ge_u (local.get 2) (local.get 1)))
   (local.set 4 (i32.and (i32.load8_u (i32.add (local.get 0) (local.get 2))) (i32.const 1)))
   (local.set 3 (i32.and (i32.wrap_i64 (i64.shr_u
    (select (i64.const {packed[1]}) (i64.const {packed[0]}) (local.get 4))
    (i64.extend_i32_u (i32.shl (local.get 3) (i32.const 2))))) (i32.const 15)))
   (local.set 2 (i32.add (local.get 2) (i32.const 1))) (br 0)))
  (i32.and (i32.shr_u (i32.const {final}) (local.get 3)) (i32.const 1))))'''


def balanced_xor(terms):
    if not terms:
        return maskconst(0)
    if len(terms) == 1:
        return terms[0]
    m = len(terms)//2
    return f'(v128.xor {balanced_xor(terms[:m])} {balanced_xor(terms[m:])})'


def protected(delta, final, mode, seed=0):
    identity = [1 << i for i in range(N)]
    l = basis(seed) if mode == 'mixed' else identity
    li = inverse(l)
    matrices = [compose(compose(l, [1 << q for q in t]), li) for t in delta]
    init, out = apply(l, final), li[0]
    if mode == 'suffix':
        idx = f'(select (result v128) {vconst(delta[1])} {vconst(delta[0])} (local.get 3))'
        step = f'(i8x16.swizzle (local.get 4) {idx})'
    elif mode == 'mixed':
        terms = []
        for i in range(N):
            columns = [sum(((row >> i) & 1) << j for j, row in enumerate(mat)) for mat in matrices]
            if columns == [0, 0]:
                continue
            choose = f'(select (result v128) {maskconst(columns[1])} {maskconst(columns[0])} (local.get 3))'
            terms.append(f'(v128.and (i8x16.swizzle (local.get 4) {vconst([i]*N)}) {choose})')
        step = balanced_xor(terms)
    else:
        raise ValueError(mode)
    wat = f'''(module
 (memory (export "memory") 1 1)
 (func (export "run") (param i32 i32) (result i32) (local i32 i32 v128)
  (local.set 2 (local.get 1))
  (local.set 4 {maskconst(init)})
  (block (loop
   (br_if 1 (i32.eqz (local.get 2)))
   (local.set 2 (i32.sub (local.get 2) (i32.const 1)))
   (local.set 3 (i32.and (i32.load8_u (i32.add (local.get 0) (local.get 2))) (i32.const 1)))
   (local.set 4 {step}) (br 0)))
  (i32.and (i32.popcnt (i8x16.bitmask (v128.and (local.get 4) {maskconst(out)}))) (i32.const 1))))'''
    return wat, dict(basis=l, inverse_basis=li, matrices=matrices, initial=init, output=out)


def compile_wat(text, dst):
    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        raise FileExistsError(dst)
    src = dst.with_suffix('.wat')
    if src.exists():
        raise FileExistsError(src)
    src.write_text(text, encoding='utf-8')
    w.tool('wat2wasm', [src, '-o', dst])
    w.tool('wasm-validate', [dst])


def read(path):
    started = time.perf_counter()
    w.tool('wasm-validate', [path])
    mod = w.parse(w.tool('wasm2wat', [path, '--fold-exprs', '--no-debug-names']))
    if any(x[0] not in ('type', 'memory', 'func', 'export') for x in mod[1:]):
        raise ValueError('Unsupported module fields')
    fs = [x for x in mod[1:] if x[0] == 'func']
    mem = [x for x in mod[1:] if x[0] == 'memory']
    ex = [x for x in mod[1:] if x[0] == 'export']
    if len(fs) != 1 or mem != [['memory', '1', '1']]:
        raise ValueError('One pure scanner and one fixed memory required')
    if sorted(ex) != sorted([['export', '"memory"', ['memory', '0']], ['export', '"run"', ['func', '0']]]):
        raise ValueError('Exact public scanner API required')
    f = fs[0]
    decl = [x for x in f[1:] if isinstance(x, list) and x[0] in ('type', 'param', 'result', 'local')]
    params = [a for x in decl if x[0] == 'param' for a in x[1:]]
    if params != ['i32', 'i32'] or [x for x in decl if x[0] == 'result'] != [['result', 'i32']]:
        raise ValueError('Scanner signature')
    types = params + [a for x in decl if x[0] == 'local' for a in x[1:]]
    body = [x for x in f[1:] if isinstance(x, list) and x[0] not in ('type', 'param', 'result', 'local')]
    return dict(module=mod, types=types, body=body, parse_validate_ms=(time.perf_counter()-started)*1000)


@dataclass(frozen=True)
class Bits:
    data: tuple


@dataclass(frozen=True)
class Pop:
    data: tuple


def bits_int(x, size):
    return Bits(tuple(C if x >> i & 1 else 0 for i in range(size)))


def concrete(b):
    if isinstance(b, int):
        return b
    if any(x not in (0, C) for x in b.data):
        raise ValueError('Symbolic condition/index: unsupported')
    return sum((x == C) << i for i, x in enumerate(b.data))


def boolean(op, a, b):
    if isinstance(a, int) and isinstance(b, int):
        return {'and': lambda: a & b, 'or': lambda: a | b, 'xor': lambda: a ^ b}[op]()
    size = len(a.data) if isinstance(a, Bits) else len(b.data)
    a = a if isinstance(a, Bits) else bits_int(a, size)
    b = b if isinstance(b, Bits) else bits_int(b, size)
    ans = []
    for x, y in zip(a.data, b.data):
        if op == 'xor':
            ans.append(x ^ y)
        elif op == 'and':
            if x == 0 or y == 0:
                ans.append(0)
            elif x == C:
                ans.append(y)
            elif y == C or x == y:
                ans.append(x)
            else:
                raise ValueError('Nonlinear symbolic AND')
        elif op == 'or':
            if x == C or y == C:
                ans.append(C)
            elif x == 0:
                ans.append(y)
            elif y == 0 or x == y:
                ans.append(x)
            else:
                raise ValueError('Nonlinear symbolic OR')
    return Bits(tuple(ans))


class Branch(Exception):
    def __init__(self, depth):
        self.depth = depth


class Return(Exception):
    def __init__(self, value):
        self.value = value


def carrier(program):
    initialized = [int(x[1]) for x in program['body'] if x[0] == 'local.set'
                   and program['types'][int(x[1])] == 'v128' and x[2][0] == 'v128.const']
    if len(initialized) != 1:
        raise ValueError('One explicitly initialized vector carrier required')
    return initialized[0]


class Machine:
    def __init__(self, program, letter=0, length=1, override=None):
        self.p = program
        self.env = [bits_int(0, 128) if t == 'v128' else 0 for t in program['types']]
        self.env[1] = length
        self.letter = letter
        self.override = override
        self.vindices = [i for i, t in enumerate(program['types']) if t == 'v128']
        self.carried = carrier(program) if override is not None else None
        if override is not None:
            for i in self.vindices:
                if i != self.carried:
                    self.env[i] = None  # reject an unmodeled second carried vector
        self.overridden = False
        self.steps = 0
        self.loads = 0

    def seq(self, xs):
        result = None
        for x in xs:
            if isinstance(x, list) and x[0] not in ('result', 'param'):
                result = self.ev(x)
        return result

    def ev(self, x):
        self.steps += 1
        if self.steps > 20000:
            raise ValueError('Interpreter step budget')
        op = x[0]
        if op in ('i32.const', 'i64.const'):
            return int(x[1], 0) & ((1 << (32 if op[1:3] == '32' else 64))-1)
        if op == 'v128.const':
            shape = x[1]
            size = int(shape[1:shape.index('x')])
            packed = b''.join((int(k, 0) & ((1 << size)-1)).to_bytes(size//8, 'little') for k in x[2:])
            if len(packed) != 16:
                raise ValueError('vector constant')
            return bits_int(int.from_bytes(packed, 'little'), 128)
        if op == 'local.get':
            val = self.env[int(x[1])]
            if val is None:
                raise ValueError('Temporary vector read before assignment')
            return val
        if op in ('local.set', 'local.tee'):
            i, val = int(x[1]), self.ev(x[2])
            if self.override is not None and i == self.carried and not self.overridden:
                # Generated scanner initializes its sole vector before the loop.
                concrete(val)
                val, self.overridden = self.override, True
            self.env[i] = val
            return val if op == 'local.tee' else None
        if op in ('block', 'loop'):
            while True:
                try:
                    return self.seq(x[1:])
                except Branch as br:
                    if br.depth:
                        br.depth -= 1
                        raise
                    if op == 'block':
                        return None
        if op == 'br':
            raise Branch(int(x[1]))
        if op == 'br_if':
            if concrete(self.ev(x[-1])):
                raise Branch(int(x[1]))
            return None
        if op == 'if':
            pieces = [v for v in x[1:] if isinstance(v, list) and v[0] != 'result']
            choose = concrete(self.ev(pieces[0])) != 0
            part = next((v for v in pieces[1:] if v[0] == ('then' if choose else 'else')), ['then'])
            try:
                return self.seq(part[1:])
            except Branch as br:
                if br.depth:
                    br.depth -= 1
                    raise
                return None
        if op == 'return':
            raise Return(self.ev(x[1]))
        if op == 'nop':
            return None
        if op == 'drop':
            self.ev(x[1])
            return None
        if op == 'select':
            args = [v for v in x[1:] if isinstance(v, list) and v[0] != 'result']
            # Evaluate both, as Wasm does. Conditions must be concrete here.
            a, b, cond = [self.ev(v) for v in args]
            return a if concrete(cond) else b
        args = [self.ev(v) for v in x[1:] if isinstance(v, list)]
        imm = [v for v in x[1:] if not isinstance(v, list)]
        if op == 'i32.load8_u':
            if concrete(args[0]) != 0 or any(v.startswith('offset=') and v != 'offset=0' for v in imm):
                raise ValueError('One-step scanner probe must load address zero')
            self.loads += 1
            return self.letter
        if op == 'i8x16.swizzle':
            src, idx = args
            index = concrete(idx).to_bytes(16, 'little')
            return Bits(tuple(t for i in index for t in (src.data[8*i:8*i+8] if i < 16 else (0,)*8)))
        if op == 'i8x16.shuffle':
            a = args[0].data + args[1].data
            return Bits(tuple(t for k in imm for t in a[8*int(k):8*int(k)+8]))
        if op in ('v128.and', 'v128.or', 'v128.xor'):
            return boolean(op[5:], *args)
        if op == 'v128.not':
            return Bits(tuple(t ^ C for t in args[0].data))
        if op == 'v128.bitselect':
            return boolean('xor', boolean('and', args[0], args[2]),
                           boolean('and', args[1], Bits(tuple(t ^ C for t in args[2].data))))
        if op == 'i8x16.bitmask':
            return Bits(tuple(args[0].data[8*i+7] for i in range(16))+(0,)*16)
        if op in ('i8x16.extract_lane_u', 'i8x16.extract_lane_s'):
            lane = args[0].data[8*int(imm[0]):8*int(imm[0])+8]
            return Bits(lane + (lane[-1] if op.endswith('_s') else 0,)*24)
        if op in ('i32.and', 'i32.or', 'i32.xor'):
            if op == 'i32.and' and any(isinstance(a, Pop) for a in args):
                pp = next(a for a in args if isinstance(a, Pop))
                cc = next(a for a in args if not isinstance(a, Pop))
                if concrete(cc) != 1:
                    raise ValueError('Only parity of symbolic popcnt supported')
                return Bits((xor_all(pp.data),)+(0,)*31)
            return boolean(op[4:], *args)
        if op == 'i32.popcnt':
            return Pop(args[0].data) if isinstance(args[0], Bits) else popcount(args[0])
        if op in ('i32.shl', 'i32.shr_u') and isinstance(args[0], Bits):
            count = concrete(args[1]) & 31
            data = args[0].data
            return Bits(((0,)*count+data)[:32] if op.endswith('shl') else (data[count:]+(0,)*count))
        if op in ('i32.wrap_i64', 'i64.extend_i32_u'):
            return concrete(args[0]) & 0xffffffff
        if op in ('i32.eqz', 'i64.eqz'):
            return int(concrete(args[0]) == 0)
        size = 64 if op.startswith('i64.') else 32
        mask = (1 << size)-1
        if op in ('i32.add', 'i32.sub', 'i32.shl', 'i32.shr_u', 'i64.shr_u',
                  'i32.ge_u', 'i32.lt_u', 'i32.le_u', 'i32.gt_u', 'i32.eq', 'i32.ne'):
            a, b = map(concrete, args)
            name = op.split('.')[1]
            return {'add': lambda: (a+b)&mask, 'sub': lambda: (a-b)&mask,
                    'shl': lambda: (a << (b & (size-1))) & mask,
                    'shr_u': lambda: a >> (b & (size-1)),
                    'ge_u': lambda: int(a >= b), 'lt_u': lambda: int(a < b),
                    'le_u': lambda: int(a <= b), 'gt_u': lambda: int(a > b),
                    'eq': lambda: int(a == b), 'ne': lambda: int(a != b)}[name]()
        raise ValueError('Unsupported opcode '+op)

    def run(self):
        try:
            out = self.seq(self.p['body'])
        except Return as r:
            out = r.value
        return out


def descendants(x):
    if isinstance(x, list):
        yield x
        for v in x[1:]:
            yield from descendants(v)


def source_model(p):
    # Exact input template: model extraction does not authorize arbitrary code.
    if p['types'] != ['i32']*5:
        raise ValueError('Source template local types')
    out = p['body'][-1]
    if out[0] != 'i32.and' or out[1][0] != 'i32.shr_u' or out[1][1][0] != 'i32.const':
        raise ValueError('Source final-state predicate')
    final = int(out[1][1][1])
    if not 0 <= final < 1 << N:
        raise ValueError('Final bitset')
    updates = [x for node in p['body'] for x in descendants(node) if x[0:2] == ['local.set', '3']]
    if len(updates) != 1:
        raise ValueError('Exactly one state update')
    delta = []
    for a in range(2):
        row = []
        for q in range(N):
            machine = Machine(p, a)
            machine.env[3], machine.env[4] = q, a
            row.append(concrete(machine.ev(updates[0][2])))
        delta.append(row)
    if any(q not in range(N) for row in delta for q in row):
        raise ValueError('State outside 0..15')
    return delta, final


def scanner_model(p):
    """Extract the finite transition table from the raw/optimized plain family."""
    out = p['body'][-1]
    shifts = [x for x in descendants(out) if x[0] == 'i32.shr_u'
              and len(x) == 3 and x[1][0] == 'i32.const' and x[2][0] == 'local.get']
    if len(shifts) != 1:
        raise ValueError('Plain scanner final observation not recognized')
    state = int(shifts[0][2][1])
    if state < 2 or p['types'][state] != 'i32':
        raise ValueError('Plain scanner state local')
    final = 0
    for q in range(N):
        machine = Machine(p, length=0)
        machine.env[state] = q
        accepted = concrete(machine.run())
        if accepted not in (0, 1) or machine.loads:
            raise ValueError('Plain scanner empty-word observation')
        final |= accepted << q
    delta = []
    for a in range(2):
        row = []
        for q in range(N):
            machine = Machine(p, letter=a, length=1)
            machine.env[state] = q
            machine.run()
            nxt = concrete(machine.env[state])
            if nxt not in range(N) or machine.loads != 1:
                raise ValueError('Plain scanner one-step shape')
            row.append(nxt)
        delta.append(row)
    return delta, final


def transform(src, dst, mode, seed):
    started = time.perf_counter()
    p = read(src)
    delta, final = source_model(p)
    parent = Path(dst).resolve().parent
    parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='source-template-', dir=parent) as td:
        expected = Path(td)/'expected.wasm'
        compile_wat(plain(delta, final), expected)
        if read(expected)['module'] != p['module']:
            raise ValueError('Source does not exactly match the verified scanner template')
    wat, meta = protected(delta, final, mode, seed)
    compile_wat(wat, dst)
    meta.update(mode=mode, seed=seed, transform_ms=(time.perf_counter()-started)*1000,
                source_sha256=hashlib.sha256(Path(src).read_bytes()).hexdigest())
    return meta


def canonical(delta, final, initial=0):
    # Reachability, stable partition refinement, and deterministic BFS numbering.
    reachable, todo = {initial}, deque([initial])
    while todo:
        q = todo.popleft()
        for a in range(2):
            t = delta[a][q]
            if t not in reachable:
                reachable.add(t)
                todo.append(t)
    order = sorted(reachable)
    groups = {q: (final >> q) & 1 for q in order}
    while True:
        mapping, updated = {}, {}
        for q in order:
            key = (groups[q], groups[delta[0][q]], groups[delta[1][q]])
            if key not in mapping:
                mapping[key] = len(mapping)
            updated[q] = mapping[key]
        if all((groups[a] == groups[b]) == (updated[a] == updated[b]) for a in order for b in order):
            groups = updated
            break
        groups = updated
    rep = {groups[q]: q for q in order}
    start = groups[initial]
    numbers, todo = {start: 0}, deque([start])
    rows, accepted = [[], []], 0
    while todo:
        g = todo.popleft()
        q, i = rep[g], numbers[g]
        accepted |= ((final >> q) & 1) << i
        for a in range(2):
            t = groups[delta[a][q]]
            if t not in numbers:
                numbers[t] = len(numbers)
                todo.append(t)
            rows[a].append(numbers[t])
    return rows, accepted


def protected_control(p):
    """Recognize the two concrete control skeletons emitted by the toolchain.

    This is intentionally restrictive. A successful one-step linear probe alone
    would not establish that every later iteration uses the same transition.
    """
    idx = carrier(p)
    loops = [x for node in p['body'] for x in descendants(node) if x[0] == 'loop']
    if len(loops) != 1:
        raise ValueError('Exactly one scanner loop required')
    loop = loops[0]
    body = [x for x in loop[1:] if isinstance(x, list)]
    if body and body[0][0] == 'br_if':
        guard = body[0]
        if guard[1] != '1' or guard[2][0] != 'i32.eqz' or guard[2][1][0] != 'local.get' or body[-1] != ['br', '0']:
            raise ValueError('Reverse-loop guard/backedge')
        counter = int(guard[2][1][1])
        work = body[1:-1]
        enclosing = [x for x in p['body'] if x[0] == 'block' and x[1:] == [loop]]
        if len(enclosing) != 1:
            raise ValueError('Reverse-loop enclosing block')
    elif len(body) == 1 and body[0][0] == 'if':
        branch = body[0]
        if len(branch) != 3 or branch[1][0] != 'local.get' or branch[2][0] != 'then' or branch[2][-1] != ['br', '1']:
            raise ValueError('Optimized reverse-loop guard/backedge')
        counter = int(branch[1][1])
        work = branch[2][1:-1]
    else:
        raise ValueError('Unsupported loop control skeleton')
    before, found = [], False
    for x in p['body'][:-1]:
        if any(t is loop for t in descendants(x)):
            found = True
        else:
            if found:
                raise ValueError('Unexpected statement after loop')
            before.append(x)
    allowed_pre = [['local.set', str(idx), next(x[2] for x in before if x[:2] == ['local.set', str(idx)])]]
    if counter != 1:
        allowed_pre.append(['local.set', str(counter), ['local.get', '1']])
    if sorted(map(w.emit, before)) != sorted(map(w.emit, allowed_pre)):
        raise ValueError('Scanner initialization shape')
    dec = ['i32.sub', ['local.get', str(counter)], ['i32.const', '1']]
    byte_vars, loads, decrements = set(), [], 0
    for node in work:
        for x in descendants(node):
            if x[0] in ('block', 'loop', 'if', 'br', 'br_if', 'return'):
                raise ValueError('Conditional or early step exit')
            if x[0] == 'i32.load8_u':
                loads.append(x)
            if x[0] in ('local.set', 'local.tee') and p['types'][int(x[1])] == 'i32':
                if int(x[1]) == counter and x[2] == dec:
                    decrements += 1
                elif x[2][0] == 'i32.and' and ['i32.const', '1'] in x[2][1:] and any(t[0] == 'i32.load8_u' for t in descendants(x[2])):
                    if int(x[1]) in (0, counter):
                        raise ValueError('Byte variable aliases pointer/counter')
                    byte_vars.add(int(x[1]))
                else:
                    raise ValueError('Unrecognized scalar write in step')
    if decrements != 1 or len(loads) != 1:
        raise ValueError('One decrement and one load required')
    load = loads[0]
    if len(load) != 2 or load[1][0] != 'i32.add':
        raise ValueError('Input address has offset or different arithmetic')
    addr = load[1][1:]
    if ['local.get', '0'] not in addr:
        raise ValueError('Input base pointer')
    other = next(x for x in addr if x != ['local.get', '0'])
    if other not in (['local.get', str(counter)], ['local.tee', str(counter), dec]):
        raise ValueError('Input index is not the reverse counter')
    def check_reads(x, in_load=False):
        if not isinstance(x, list):
            return
        if x[0] == 'local.get' and p['types'][int(x[1])] == 'i32':
            if int(x[1]) not in (set((0, counter)) if in_load else byte_vars):
                raise ValueError('Transition depends on position/length, not just its letter')
        if x[0] in ('local.set', 'local.tee') and int(x[1]) == counter:
            return
        for y in x[1:]:
            check_reads(y, in_load or x[0] == 'i32.load8_u')
    for node in work:
        check_reads(node)
    # All data reads must be reduced to the binary alphabet before use.
    parents = [x for node in work for x in descendants(node) if any(y is load for y in x[1:])]
    if len(parents) != 1 or parents[0][0] != 'i32.and' or ['i32.const', '1'] not in parents[0][1:]:
        raise ValueError('Input alphabet projection')
    for x in descendants(p['body'][-1]):
        if x[0] == 'local.get' and int(x[1]) != idx:
            raise ValueError('Final observation depends on another local')
        if x[0] in ('local.set', 'local.tee', 'if', 'loop', 'block', 'i32.load8_u'):
            raise ValueError('Final observation has effects/control')
    return idx


def recover(p):
    started = time.perf_counter()
    if 'v128' not in p['types']:
        delta, final = scanner_model(p)
        reduced, f = canonical(delta, final)
        return dict(delta=reduced, final=f, orbit_states=len(reduced[0]),
                    analysis_ms=(time.perf_counter()-started)*1000, mode='source')
    idx = protected_control(p)
    variable = Bits(tuple(1 << i for i in range(N) for _ in range(8)))
    init_machine = Machine(p, length=0)
    init_machine.run()
    initbytes = concrete(init_machine.env[idx]).to_bytes(16, 'little')
    if any(x not in (0, 255) for x in initbytes):
        raise ValueError('Initial lanes are not Boolean masks')
    init = sum((x == 255) << i for i, x in enumerate(initbytes))
    out_machine = Machine(p, length=0, override=variable)
    out = out_machine.run()
    if not isinstance(out, Bits) or any(out.data[1:]) or out.data[0] & C:
        raise ValueError('Output is not a homogeneous linear Boolean observation')
    output = out.data[0]
    matrices = []
    for a in range(2):
        machine = Machine(p, letter=a, length=1, override=variable)
        machine.run()
        if machine.loads != 1:
            raise ValueError('Expected one input-byte read per step')
        state = machine.env[idx].data
        rows = []
        for i in range(N):
            lane = state[8*i:8*i+8]
            if len(set(lane)) != 1 or lane[0] & C:
                raise ValueError('Update not homogeneous linear canonical masks')
            rows.append(lane[0])
        matrices.append(rows)
    numbers, todo = {output: 0}, deque([output])
    delta, final = [[], []], 0
    while todo:
        row = todo.popleft()
        i = numbers[row]
        final |= (popcount(row & init) & 1) << i
        for a in range(2):
            nxt = xor_all(matrices[a][j] for j in range(N) if row >> j & 1)
            if nxt not in numbers:
                if len(numbers) >= 4096:
                    raise ValueError('Dual orbit state budget exceeded')
                numbers[nxt] = len(numbers)
                todo.append(nxt)
            delta[a].append(numbers[nxt])
    reduced, f = canonical(delta, final)
    return dict(delta=reduced, final=f, orbit_states=len(numbers), matrices=matrices,
                initial=init, output=output, analysis_ms=(time.perf_counter()-started)*1000,
                mode='dual')


def emit_recovered(report, dst):
    if len(report['delta'][0]) > N:
        raise ValueError('Recovered DFA too large for output template')
    rows = [t+[0]*(N-len(t)) for t in report['delta']]
    compile_wat(plain(rows, report['final']), dst)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('mode', choices=['suffix', 'mixed', 'recover'])
    ap.add_argument('input', type=Path)
    ap.add_argument('output', type=Path)
    ap.add_argument('--seed', type=int, default=20261018)
    args = ap.parse_args()
    if args.mode == 'recover':
        result = recover(read(args.input))
        emit_recovered(result, args.output)
    else:
        result = transform(args.input, args.output, args.mode, args.seed)
    print(json.dumps(result))


if __name__ == '__main__':
    main()
