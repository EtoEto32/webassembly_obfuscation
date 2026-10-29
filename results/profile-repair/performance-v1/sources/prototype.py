"""Restricted, profile-aware partial determinization of actual Wasm binaries.

CEGIS and cost minimization are established methods, not claimed inventions.
"""
import argparse
import copy
import importlib.util
import json
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT/'.tools/encoding-synthesis-python'))
import z3 as z
spec = importlib.util.spec_from_file_location('wat_reader', ROOT/'research/connectivity-elimination/prototype.py')
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)
U32 = 0xffffffff
RELAXED = 'i8x16.relaxed_swizzle'
STRICT = 'i8x16.swizzle'
X, Y = z.BitVecs('input_x input_y', 32)


def c(n): return ['i32.const', str(n & U32)]
def g(n): return ['local.get', str(n)]
def op(name, *children): return [name, *children]


def walk(node):
    if isinstance(node, list):
        yield node
        for child in node[1:]:
            yield from walk(child)


def read(path):
    w.tool('wasm-validate', [path])
    mod = w.parse(w.tool('wasm2wat', [path, '--fold-exprs']))
    return Program(mod)


class Program:
    def __init__(self, mod):
        self.mod = mod
        if any(x[0] not in ('type', 'func', 'export') for x in mod[1:]):
            raise ValueError('only types/function/export allowed')
        funcs = [x for x in mod[1:] if x[0] == 'func']
        exports = [x for x in mod[1:] if x[0] == 'export']
        if len(funcs) != 1 or exports != [['export', '"run"', ['func', '0']]]:
            raise ValueError('single exported run required')
        self.func = funcs[0]
        params = [p for x in self.func[1:] if isinstance(x, list) and x[0] == 'param' for p in x[1:]]
        self.locals = [p for x in self.func[1:] if isinstance(x, list) and x[0] == 'local' for p in x[1:]]
        if params != ['i32', 'i32'] or any(t != 'i32' for t in self.locals):
            raise ValueError('two i32 parameters and i32 locals required')
        if [x for x in self.func[1:] if isinstance(x, list) and x[0] == 'result'] != [['result', 'i32']]:
            raise ValueError('one i32 result required')
        self.body = [x for x in self.func[1:] if isinstance(x, list) and x[0] not in ('type', 'param', 'result', 'local')]
        if not self.body: raise ValueError('empty body')
        self.sites = [x for x in walk(self.func) if x[0] == RELAXED]
        self.ids = {id(node): i for i, node in enumerate(self.sites)}
        if len(self.sites) > 16: raise ValueError('site limit')
        self.model([False]*len(self.sites), [z.BoolVal(False)]*len(self.sites))

    def model(self, repair, choices):
        local = [X, Y] + [z.BitVecVal(0, 32)]*len(self.locals)
        deps = [set() for _ in local]

        def value(e):
            name = e[0]
            if name == 'local.get' and len(e) == 2:
                i = int(e[1]); return local[i], deps[i].copy()
            if name == 'i32.const' and len(e) == 2:
                return z.BitVecVal(int(e[1], 0) & U32, 32), set()
            if name == 'i8x16.extract_lane_u' and len(e) == 3 and e[1] == '0':
                sw = e[2]
                if sw[0] not in (RELAXED, STRICT) or len(sw) != 3 or any(v[0] != 'i8x16.splat' or len(v) != 2 for v in sw[1:]):
                    raise ValueError('only splat/swizzle/extract lane 0 supported')
                a, da = value(sw[1][1]); index, di = value(sw[2][1]); a = a & 255; index = index & 255
                if sw[0] == RELAXED:
                    sid = self.ids[id(sw)]
                    choice = z.And(z.Not(repair[sid]), choices[sid])
                    dep = da | di | {sid}
                else:
                    choice = z.BoolVal(False); dep = da | di
                return z.If(z.Or(z.ULT(index, 16), z.And(z.ULT(index, 128), choice)), a, z.BitVecVal(0, 32)), dep
            if name == 'i32.eqz' and len(e) == 2:
                a, da = value(e[1]); return z.If(a == 0, z.BitVecVal(1, 32), z.BitVecVal(0, 32)), da
            if name == 'select' and len(e) == 4:
                a, da = value(e[1]); b, db = value(e[2]); cond, dc = value(e[3])
                return z.If(cond != 0, a, b), da | db | dc
            if name in ('i32.and','i32.or','i32.xor','i32.add','i32.sub','i32.mul','i32.shl','i32.shr_u','i32.eq','i32.ne','i32.lt_u') and len(e) == 3:
                a, da = value(e[1]); b, db = value(e[2])
                operations = {'i32.and':lambda:a&b,'i32.or':lambda:a|b,'i32.xor':lambda:a^b,
                    'i32.add':lambda:a+b,'i32.sub':lambda:a-b,'i32.mul':lambda:a*b,
                    'i32.shl':lambda:a<<(b&31),'i32.shr_u':lambda:z.LShR(a,b&31),
                    'i32.eq':lambda:z.If(a==b,z.BitVecVal(1,32),z.BitVecVal(0,32)),
                    'i32.ne':lambda:z.If(a!=b,z.BitVecVal(1,32),z.BitVecVal(0,32)),
                    'i32.lt_u':lambda:z.If(z.ULT(a,b),z.BitVecVal(1,32),z.BitVecVal(0,32))}
                return operations[name](), da | db
            raise ValueError('unsupported expression '+w.emit(e))

        for statement in self.body[:-1]:
            if statement[0] != 'local.set' or len(statement) != 3: raise ValueError('sequential local.set required')
            i = int(statement[1]); v, d = value(statement[2]); local[i] = v; deps[i] = d
        return value(self.body[-1])


def query(program, selected, independent=False):
    n = len(program.sites)
    choices = [z.Bool('choice_'+str(i)) for i in range(n)] if independent else [z.Bool('profile')]*n
    value, _ = program.model([i in selected for i in range(n)], choices)
    reference, _ = program.model([True]*n, [z.BoolVal(False)]*n)
    solver = z.Solver(); solver.set(timeout=15000); solver.add(value != reference)
    status = solver.check()
    if status == z.unknown: raise RuntimeError('query unknown: '+solver.reason_unknown())
    if status == z.unsat: return None
    model = solver.model()
    return {'x':model.eval(X,model_completion=True).as_long(), 'y':model.eval(Y,model_completion=True).as_long(),
            'choices':[z.is_true(model.eval(v,model_completion=True)) for v in choices],
            'actual':model.eval(value,model_completion=True).as_long(), 'reference':model.eval(reference,model_completion=True).as_long()}


def synthesize(program, weights=None, independent=False):
    n = len(program.sites); weights = [1]*n if weights is None else weights
    if len(weights) != n or any(not isinstance(v,int) or isinstance(v,bool) or v<=0 for v in weights): raise ValueError('positive integer weights')
    h = [z.Bool('repair_'+str(i)) for i in range(n)]
    constraints = []; iterations = []; start = time.perf_counter()
    for _ in range(1024):
        optimizer = z.Optimize(); optimizer.set(timeout=15000); optimizer.add(*constraints)
        optimizer.minimize(z.Sum([z.If(h[i],weights[i],0) for i in range(n)]) if n else z.IntVal(0))
        optimizer.minimize(z.Sum([z.If(h[i],1<<i,0) for i in range(n)]) if n else z.IntVal(0))
        status = optimizer.check()
        if status != z.sat: raise RuntimeError('optimization '+str(status))
        m = optimizer.model(); selected = [i for i in range(n) if z.is_true(m.eval(h[i],model_completion=True))]
        witness = query(program, selected, independent)
        iterations.append({'selected':selected,'witness':witness})
        if witness is None:
            return {'selected':selected,'cost':sum(weights[i] for i in selected),'weights':weights,
                'independentSiteModel':independent,'iterations':iterations,'synthesisMs':(time.perf_counter()-start)*1000,
                'finalStatus':'unsat','z3':z.get_version_string()}
        choices = [z.BoolVal(v) for v in witness['choices']]
        symbolic, _ = program.model(h, choices)
        reference, _ = program.model([True]*n, choices)
        constraint = z.simplify(z.substitute(symbolic == reference,(X,z.BitVecVal(witness['x'],32)),(Y,z.BitVecVal(witness['y'],32))))
        constraints.append(constraint)
        iterations[-1]['repairConstraint'] = str(constraint)
    raise RuntimeError('CEGIS iteration limit')


def rewritten(program, selected, profile=None):
    mod = copy.deepcopy(program.mod)
    sites = [e for e in walk(mod) if e[0] == RELAXED]
    for sid, node in enumerate(sites):
        if sid in selected or profile == 0: node[0] = STRICT
        elif profile == 1:
            node[0] = STRICT
            node[2][1] = op('i32.and',node[2][1],c(143))
    return mod


def compile_mod(mod, dest):
    dest = Path(dest)
    if dest.exists() or dest.with_suffix('.wat').exists(): raise FileExistsError(dest)
    dest.with_suffix('.wat').write_text(w.emit(mod),encoding='utf8')
    w.tool('wat2wasm',[dest.with_suffix('.wat'),'-o',dest]); w.tool('wasm-validate',[dest])


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('input',type=Path); parser.add_argument('output',type=Path)
    parser.add_argument('--independent',action='store_true'); args = parser.parse_args()
    start=time.perf_counter(); program=read(args.input); result=synthesize(program,independent=args.independent)
    compile_mod(rewritten(program,result['selected']),args.output)
    result['transformMs']=(time.perf_counter()-start)*1000
    args.output.with_suffix('.json').write_text(json.dumps(result,indent=2),encoding='utf8'); print(json.dumps(result))


if __name__ == '__main__': main()
