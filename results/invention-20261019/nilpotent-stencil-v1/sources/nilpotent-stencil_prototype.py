"""Four counterfactual evaluations over Z/(2^32); pure polynomial profile."""
import argparse
import importlib.util
import json
from pathlib import Path
import time

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('lane_common', HERE.parent / 'lane-demand/prototype.py')
common = importlib.util.module_from_spec(spec); spec.loader.exec_module(common)
w = common.w
MASK = 0xffffffff
OPS = {'i32.add', 'i32.sub', 'i32.mul'}
const, get, vec, emit = common.const, common.get, common.vec, common.emit
compile_wat, read, expanded = common.compile_wat, common.read, common.expanded


def scalar_dag(expr):
    memo = {}; body = []
    def lower(e):
        if e[0] in ('local.get', 'i32.const'): return e
        key = id(e)
        if key in memo: return memo[key]
        value = [e[0], *[lower(x) if isinstance(x, list) else x for x in e[1:]]]
        idx = len(body) + 2; body.append(['local.set', str(idx), value]); memo[key] = get(idx)
        return memo[key]
    result = lower(expr)
    return '(module (func (export "run") (param i32 i32) (result i32) ' + '(local i32)'*len(body) + ''.join(emit(e) for e in body) + emit(result) + '))'


def lifted(expr, mode='dynamic', shift=8, weights=(4,-6,4,-1)):
    if mode not in ('diagonal', 'constant', 'dynamic'): raise ValueError(mode)
    memo = {}; body = []; locals_ = []
    def bind(typ, value):
        idx = len(locals_)+2; locals_.append(typ); body.append(['local.set',str(idx),value]); return get(idx)
    inputs = []
    for i in range(2):
        base = ['i32x4.splat', get(i)]
        if mode == 'diagonal': v = base
        else:
            d = const((1 if i == 0 else 3) << shift) if mode == 'constant' else ['i32.shl',['i32.sub',const(0),['i32.shr_u',get(i),const(10)]],const(shift)]
            v = ['i32x4.add',base,['i32x4.mul',['i32x4.splat',d],vec([1,2,3,4])]]
        inputs.append(bind('v128', v))
    def lower(e):
        key = id(e)
        if key in memo: return memo[key]
        op = e[0]
        if op == 'local.get': value = inputs[int(e[1])]
        elif op == 'i32.const': value = ['i32x4.splat', e]
        elif op in OPS: value = ['i32x4.'+op.split('.')[1],lower(e[1]),lower(e[2])]
        else: raise ValueError('Non-polynomial source operation: '+op)
        result = value if op == 'local.get' else bind('v128',value)
        memo[key] = result; return result
    v = lower(expr)
    if mode == 'diagonal': result = ['i32x4.extract_lane','0',v]
    else:
        terms = [['i32.mul',const(coef),['i32x4.extract_lane',str(i),v]] for i,coef in enumerate(weights)]
        result = terms[0]
        for term in terms[1:]: result = ['i32.add',result,term]
    code = '(module (func (export "run") (param i32 i32) (result i32) ' + ''.join('(local '+t+')' for t in locals_) + ''.join(emit(e) for e in body) + emit(result) + '))'
    return code, dict(expression_nodes=len(memo),mode=mode,shift=shift)


def transform(src, dst, mode='dynamic'):
    start=time.perf_counter(); expr=expanded(src); code,stats=lifted(expr,mode); compile_wat(code,dst)
    return dict(stats,transform_ms=(time.perf_counter()-start)*1000)


if __name__ == '__main__':
    ap=argparse.ArgumentParser();ap.add_argument('source');ap.add_argument('output');ap.add_argument('--mode',choices=['diagonal','constant','dynamic'],default='dynamic');a=ap.parse_args()
    print(json.dumps(transform(a.source,a.output,a.mode)))
