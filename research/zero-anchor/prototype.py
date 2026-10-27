"""Restricted .wasm transformer: code assignment for zero-on-overflow lookup.

Not a general Wasm pass or a claim of patentability/security.
"""
import argparse, importlib.util, json, random, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sp = importlib.util.spec_from_file_location('za_common', ROOT/'research/isotope-swizzle/prototype.py')
q = importlib.util.module_from_spec(sp); sp.loader.exec_module(q)
MODES = ('plain', 'random-masked', 'anchor-masked', 'anchor-free', 'random-table', 'anchor-table')
OPS = {'add': 'i8x16.add', 'sub': 'i8x16.sub', 'xor': 'v128.xor'}

def get(i): return ['local.get', str(i)]
def splat(i): return ['i32x4.splat', get(i)]
def bit(param, shift):
    return ['v128.and', ['i8x16.shr_u', splat(param), ['i32.const', str(shift)]], q.vc([1]*16)]
def sw(table, index): return ['i8x16.relaxed_swizzle', q.vc(table), index]
def module(body, sets=()):
    f = ['func', ['export', '"run"'], ['param', 'i32', 'i32', 'i32'], ['result', 'i32']]
    if sets: f += [['local', *(['v128']*len(sets))], *sets]
    f += [['i32x4.extract_lane', '0', body]]
    return q.w.emit(['module', f])
def source(steps):
    e = q.masked(splat(0))
    for op, param, shift in steps: e = q.masked([OPS[op], e, bit(param, shift)])
    return module(e)

def parse(src):
    m = q.read(src)
    if any(e[0] not in ('type', 'func', 'export') for e in m[1:]): raise q.Unsupported('pure module required')
    fs = [e for e in m[1:] if e[0] == 'func']
    if len(fs) != 1 or [e for e in m[1:] if e[0] == 'export'] != [['export', '"run"', ['func', '0']]]: raise q.Unsupported('one run function required')
    f = fs[0]
    if [e for e in f[1:] if isinstance(e,list) and e[0]=='param'] != [['param','i32','i32','i32']]: raise q.Unsupported('three i32 parameters')
    if [e for e in f[1:] if isinstance(e,list) and e[0]=='result'] != [['result','i32']]: raise q.Unsupported('one i32 result')
    body = [e for e in f[1:] if not isinstance(e,list) or e[0] not in ('type','param','result')]
    if len(body)!=1 or body[0][:2]!=['i32x4.extract_lane','0']: raise q.Unsupported('one extract expression')
    def mask(e, value):
        if not isinstance(e,list) or len(e)!=3 or e[0]!='v128.and': raise q.Unsupported('explicit mask required')
        a,b=e[1:]
        if a[0]=='v128.const': a,b=b,a
        if q.vconst(b)!=[value]*16: raise q.Unsupported('wrong mask')
        return a
    steps=[]; e=body[0][2]
    while True:
        u=mask(e,15)
        if u==splat(0): break
        if len(u)!=3 or u[0] not in OPS.values(): raise q.Unsupported('unit-bit arithmetic chain required')
        b=mask(u[2],1)
        if b[:1]!=['i8x16.shr_u'] or len(b)!=3 or b[2][:1]!=['i32.const']: raise q.Unsupported('bit extraction')
        shift=int(b[2][1],0)
        if b[1] not in (splat(1),splat(2)) or not 0<=shift<8: raise q.Unsupported('input bit profile')
        steps.append((next(k for k,v in OPS.items() if v==u[0]), int(b[1][1][1]), shift)); e=u[1]
    if not steps: raise q.Unsupported('empty chain')
    return list(reversed(steps))

def permutation(rng, anchor=None):
    p=list(range(16)); rng.shuffle(p)
    if anchor is not None:
        z=p.index(0); p[z],p[anchor]=p[anchor],p[z]
    return p

def required_zeros(op, left=range(16), right=range(2)):
    """Residues that a zero-producing out-of-range access must represent.

    A bijection exists iff at most one distinct residue is required. This is
    only a finite byte arithmetic planner, not arbitrary-program analysis.
    """
    index=lambda x,y: (x+y)&255 if op=='add' else (x-y)&255 if op=='sub' else x^y
    reachable={index(x,y) for x in left for y in right}
    required=sorted({i&15 for i in reachable if i>=16})
    return dict(indices=sorted(reachable),required=required,feasible=len(required)<=1)

def transform(src, dst, mode, seed=7):
    start=time.perf_counter(); steps=parse(src); read_ms=(time.perf_counter()-start)*1000
    if mode not in MODES: raise ValueError(mode)
    if mode=='plain':
        q.compile(source(steps),dst)
        return dict(mode=mode,seed=seed,steps=len(steps),read_ms=read_ms,ms=(time.perf_counter()-start)*1000,removed_masks=0)
    rng=random.Random(seed); p=permutation(rng); sets=[['local.set','3',sw(p,q.masked(splat(0)))]]; removed=0; proof=[]
    for op,param,shift in steps:
        constraint=required_zeros(op)
        if not constraint['feasible']:raise q.Unsupported('incompatible zero assignments')
        anchor=constraint['required'][0] if mode.startswith('anchor') and constraint['required'] else None
        out=permutation(rng,anchor); x=get(2+len(sets)); b=bit(param,shift); dec=q.inv(p)
        if mode.endswith('table'):
            rows=[[out[q.op_eval(op,dec[i],j)] for i in range(16)] for j in range(2)]
            e=['v128.bitselect',sw(rows[1],x),sw(rows[0],x),['i8x16.eq',b,q.vc([1]*16)]]
        else:
            e=[OPS[op],sw(dec,x),b]
            # xor is already in range in every method, so a redundant mask is
            # not counted as a benefit of the anchor allocation.
            omit=op=='xor' or mode=='anchor-free'
            if not omit: e=q.masked(e)
            if omit and op!='xor': removed+=1
            e=sw(out,e)
        proof.append(dict(op=op,anchor=anchor,output_zero_input=out.index(0),constraint=constraint))
        sets.append(['local.set',str(3+len(sets)),e]); p=out
    text=module(sw(q.inv(p),get(2+len(sets))),sets)
    built=time.perf_counter(); q.compile(text,dst)
    return dict(mode=mode,seed=seed,steps=len(steps),read_ms=read_ms,build_ms=(built-start)*1000-read_ms,ms=(time.perf_counter()-start)*1000,removed_masks=removed,proof=proof)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source');p.add_argument('output');p.add_argument('--mode',choices=MODES,default='anchor-free');p.add_argument('--seed',type=int,default=7)
    a=p.parse_args(); print(json.dumps(transform(a.source,a.output,a.mode,a.seed)))
