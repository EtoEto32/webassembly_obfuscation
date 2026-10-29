"""State-dependent residual coefficients, including non-congruent rotl."""
import argparse, importlib.util, json, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'research/bit-feedback'))
import transform as frontend
import recover as bitrecover
spec=importlib.util.spec_from_file_location('rd_common',ROOT/'research/unit-minor/prototype.py')
w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
MASK=w.MASK
save=w.save;digest=w.digest;tool=w.tool;compile_wat=w.compile_wat

def C(n):return ('c',n&MASK)
def V(i):return ('v',i)
def O(op,a,b):return (op,a,b)
def source(path):
    _,np,nodes,result=frontend.source(path)
    if np!=3 or not 1<=len(nodes)<=12:raise ValueError('three parameters, one to twelve nodes required')
    for op,a,b in nodes:
        if op in ('shr_u','shr_s','rotl','rotr') and a[0]=='n':raise ValueError('non-congruent source dependency')
    return nodes,result

def coeff(i,j,old,mode,width=32):
    if mode=='constant':return C(3) if i==j else C(0)
    c=((i+1)*0x9e3779b1+(j+1)*0x85ebca6b)&((1<<width)-1)
    r=O('xor',V(old+j),C(c))
    if mode in ('rotated','bad'):r=O('rotl',r,C((5*i+3*j+1)%(width-1)+1))
    if i==j:return O('or',r,C(1))
    if j>i:return O('shl',r,C(1))
    return r

def ast_wat(e,slots=None):
    if e[0]=='c':return '(i32.const '+str(e[1])+')'
    if e[0]=='p':return f'(local.get {e[1]})'
    if e[0]=='v':return f'(local.get {slots[e[1]] if slots else e[1]})'
    return f'(i32.{e[0]} {ast_wat(e[1],slots)} {ast_wat(e[2],slots)})'

def equation_nodes(nodes,old=3):
    def ref(x):return ('p',x[1]) if x[0]=='p' else C(x[1]) if x[0]=='c' else V(old+x[1])
    return [O(op,ref(a),ref(b)) for op,a,b in nodes]

def equations(nodes,mode,width=32):
    f=equation_nodes(nodes);n=len(f);h=[]
    for i in range(n):
        e=V(3+i)
        for j in range(n):
            m=coeff(i,j,3,mode,width)
            if mode=='bad' and i==0 and j==n-1:m=C(1)
            # Distribute before emitting. No residual or F temporary survives.
            e=O('add',e,O('sub',O('mul',m,f[j]),O('mul',m,V(3+j))))
        h.append(e)
    return h

def emit(nodes,result,mode,initial=0):
    n=len(nodes);counter=3+2*n;parts=['(module (func (export "run") (param i32 i32 i32) (result i32)', '(local '+' '.join(['i32']*(2*n+1))+')']
    for i in range(n):parts.append(f'(local.set {3+i} (i32.const {(initial+i*17)&MASK}))')
    parts.append(f'(local.set {counter} (i32.const {n*32}))');parts.append('(loop')
    for i,e in enumerate(equations(nodes,mode)):parts.append(f'(local.set {3+n+i} {ast_wat(e)})')
    for i in range(n):parts.append(f'(local.set {3+i} (local.get {3+n+i}))')
    parts.append(f'(br_if 0 (local.tee {counter} (i32.sub (local.get {counter}) (i32.const 1)))))')
    out=V(3+result[1]) if result[0]=='n' else result
    parts.extend([ast_wat(out),'))']);return '\n'.join(parts)

def transform(src,dst,mode='rotated',initial=0):
    start=time.perf_counter();nodes,result=source(src);compile_wat(emit(nodes,result,mode,initial),dst)
    return dict(mode=mode,nodes=len(nodes),rounds=len(nodes)*32,initial=initial,transform_ms=1000*(time.perf_counter()-start),sha256=digest(dst))

def evaluate(e,states,params,width=32):
    mask=(1<<width)-1;op=e[0]
    if op=='c':return e[1]&mask
    if op=='p':return params[e[1]]&mask
    if op=='v':return states[e[1]-3]&mask
    a,b=evaluate(e[1],states,params,width),evaluate(e[2],states,params,width)
    if op=='add':return (a+b)&mask
    if op=='sub':return (a-b)&mask
    if op=='mul':return a*b&mask
    if op=='xor':return a^b
    if op=='and':return a&b
    if op=='or':return a|b
    if op=='shl':return a<<(b%width)&mask
    if op=='rotl':b%=width;return ((a<<b)|(a>>(width-b)))&mask
    raise ValueError(op)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('source');ap.add_argument('output');ap.add_argument('--mode',choices=['constant','congruent','rotated'],default='rotated');ap.add_argument('--initial',type=int,default=0);a=ap.parse_args()
    print(json.dumps(transform(a.source,a.output,a.mode,a.initial)))
