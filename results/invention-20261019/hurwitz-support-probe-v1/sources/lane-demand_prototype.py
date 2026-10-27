"""Pure i32 expression lifting into input-dependent SIMD lane coordinates."""
import argparse
import importlib.util
import json
from pathlib import Path
import random
import time

spec = importlib.util.spec_from_file_location('common', Path(__file__).resolve().parents[1] / 'output-recurrence/prototype.py')
c = importlib.util.module_from_spec(spec); spec.loader.exec_module(c)
w = c.w
MASK = 0xffffffff
BINARY = {'i32.add', 'i32.sub', 'i32.mul', 'i32.and', 'i32.or', 'i32.xor'}
SHIFT = {'i32.shl', 'i32.shr_u', 'i32.rotl', 'i32.rotr'}

def const(n): return ['i32.const', str(n & MASK)]
def get(n): return ['local.get', str(n)]
def vec(values): return ['v128.const', 'i32x4', *map(lambda x: str(x & MASK), values)]
def bytesvec(values): return ['v128.const', 'i8x16', *map(str, values)]
def emit(x): return w.emit(x)
def compile_wat(code, path): c.compile_wat(code, path)
def read(path): return c.read(path)

def expanded(path, allow_vector=False):
    w.tool('wasm-validate',[path])
    mod = read(path)
    if any(x[0] not in ('type', 'func', 'export') for x in mod[1:]): raise ValueError('Module effects or unsupported sections')
    funcs = [x for x in mod[1:] if x[0] == 'func']
    exports = [x for x in mod[1:] if x[0] == 'export']
    if len(funcs) != 1 or exports != [['export', '"run"', ['func', '0']]]: raise ValueError('Expected only run')
    f = funcs[0]; params = []; results = []; locals_ = []
    for e in f[1:]:
        if e[0] == 'param': params += e[1:]
        if e[0] == 'result': results += e[1:]
        if e[0] == 'local': locals_ += e[1:]
    if params != ['i32','i32'] or results != ['i32']: raise ValueError('Expected i32,i32 -> i32')
    if any(t not in (('i32','v128') if allow_vector else ('i32',)) for t in locals_): raise ValueError('Unsupported locals')
    env = {0:get(0), 1:get(1)}
    for i,t in enumerate(locals_, 2): env[i] = const(0) if t=='i32' else vec([0]*4)
    allowed = BINARY | SHIFT | {'i32.eqz', 'i32.eq','i32.ne','select'}
    if allow_vector:
        allowed |= {'i32x4.extract_lane','i32x4.splat','i8x16.splat','i8x16.add','i8x16.swizzle','i8x16.shuffle','v128.const','v128.and','v128.or','v128.xor','v128.not','i32x4.add','i32x4.sub','i32x4.mul','i32x4.shl','i32x4.shr_u'}
    def walk(e):
        op=e[0]
        if op=='local.get': return env[int(e[1])]
        if op in ('local.set','local.tee'):
            value=walk(e[2]); env[int(e[1])]=value
            return value if op=='local.tee' else None
        if op=='block':
            value=None
            for child in e[1:]:
                if child[0] in ('result','type'): continue
                value=walk(child)
            return value
        if op=='i32.const': return const(int(e[1],0))
        if op not in allowed: raise ValueError('Unsupported instruction '+op)
        return [op, *[walk(x) if isinstance(x,list) else x for x in e[1:]]]
    value=None
    for e in f[1:]:
        if e[0] in ('type','param','result','local'): continue
        value=walk(e)
    if value is None: raise ValueError('No returned expression')
    return value

def scalar_module(expr): return '(module (func (export "run") (param i32 i32) (result i32) '+emit(expr)+'))'

def rotate(v, delta):
    indices=['v128.and', ['i8x16.add',bytesvec(range(16)), ['i8x16.splat',['i32.shl',delta,const(2)]]], bytesvec([15]*16)]
    return ['i8x16.swizzle',v,indices]

def lifted(expr, mode, seed=20261019):
    rng=random.Random(seed); locals_=[]; body=[]; cache={}; frame_count=0
    def bind(typ,value):
        idx=len(locals_)+2;locals_.append(typ);body.append(['local.set',str(idx),value]);return get(idx)
    def frame():
        nonlocal frame_count
        frame_count+=1
        if mode=='vector': return const(0)
        if mode=='static': return const(rng.randrange(4))
        if mode!='dynamic': raise ValueError(mode)
        key=const(rng.getrandbits(32)); shift=const(rng.randrange(1,32))
        return bind('i32',['i32.and',['i32.xor',['i32.rotl',['i32.add',get(0),key],shift],['i32.mul',get(1),const(rng.randrange(1,256)|1)]],const(3)])
    def lower(e):
        key=emit(e)
        if key in cache: return cache[key]
        op=e[0];r=frame()
        if op=='i32.const': value=['i32x4.splat',e]
        elif op=='local.get':
            scale=1 if e[1]=='0' else 3
            value=rotate(['i32x4.add',['i32x4.splat',e],vec([scale*i for i in range(4)])],['i32.sub',const(0),r])
        elif op in BINARY:
            left,lr=lower(e[1]);right,rr=lower(e[2])
            a=rotate(left,['i32.sub',lr,r]);b=rotate(right,['i32.sub',rr,r])
            vop='v128.'+op.split('.')[1] if op in ('i32.and','i32.or','i32.xor') else 'i32x4.'+op.split('.')[1]
            value=[vop,a,b]
        elif op in SHIFT and e[2][0]=='i32.const':
            child,cr=lower(e[1]);v=rotate(child,['i32.sub',cr,r]);s=int(e[2][1])&31
            if op in ('i32.rotl','i32.rotr'):
                if op=='i32.rotr': s=(-s)&31
                value=v if not s else ['v128.or',['i32x4.shl',v,const(s)],['i32x4.shr_u',v,const(32-s)]]
            else:value=['i32x4.'+op.split('.')[1],v,const(s)]
        else: raise ValueError('Outside pure expression transform: '+op)
        result=(bind('v128',value),r);cache[key]=result;return result
    v,r=lower(expr);answer=['i32x4.extract_lane','0',rotate(v,r)]
    head='(module (func (export "run") (param i32 i32) (result i32) '+''.join('(local '+t+')' for t in locals_)
    return head+''.join(emit(x) for x in body)+emit(answer)+'))',dict(expression_nodes=len(cache),frames=frame_count)

def transform(src,dst,mode):
    start=time.perf_counter();expr=expanded(src);code,stats=lifted(expr,mode);compile_wat(code,dst)
    return dict(stats,transform_ms=(time.perf_counter()-start)*1000)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('source');ap.add_argument('output');ap.add_argument('--mode',choices=['vector','static','dynamic'],default='dynamic');a=ap.parse_args();print(json.dumps(transform(a.source,a.output,a.mode)))
if __name__=='__main__':main()
