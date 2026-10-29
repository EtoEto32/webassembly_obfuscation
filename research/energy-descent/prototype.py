"""Boolean DAG -> weighted violation energy -> Wasm; binary-only recovery gate.

Known penalty/energy principles. No novelty or protection guarantee is asserted.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import random
import struct
import time

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('energy_wat',HERE.parent/'connectivity-elimination/prototype.py')
w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
MAGIC=0x31474445

def save(text,out):
    out=Path(out)
    if out.exists() or out.with_suffix('.wat').exists():raise FileExistsError(out)
    out.parent.mkdir(parents=True,exist_ok=True);out.with_suffix('.wat').write_text(text,encoding='utf8')
    w.tool('wat2wasm',[out.with_suffix('.wat'),'-o',out]);w.tool('wasm-validate',[out])

def source(path):
    w.tool('wasm-validate',[path]);m=w.parse(w.tool('wasm2wat',[path,'--fold-exprs']))
    if any(x[0] not in ('type','func','export') for x in m[1:]):raise ValueError('Only pure source modules')
    fs=[x for x in m[1:] if x[0]=='func'];ex=[x for x in m[1:] if x[0]=='export']
    if len(fs)!=1 or ex!=[['export','"run"',['func','0']]]:raise ValueError('Source exports')
    f=fs[0];params=[x for x in f[1:] if x[0]=='param'];res=[x for x in f[1:] if x[0]=='result']
    ls=[a for x in f[1:] if x[0]=='local' for a in x[1:]]
    if params!=[['param','i32']] or res!=[['result','i32']] or not 1<=len(ls)<=20 or any(x!='i32' for x in ls):raise ValueError('Source types')
    body=[x for x in f[1:] if x[0] not in ('type','param','result','local')];gates=[];bits=set()
    def operand(x,i):
        if x[0]=='local.get' and 1<=int(x[1])<=i:return ['gate',int(x[1])-1]
        if len(x)==3 and x[0]=='i32.and' and x[2]==['i32.const','1']:
            t=x[1]
            if t==['local.get','0']:b=0
            elif t[0]=='i32.shr_u' and t[1]==['local.get','0'] and t[2][0]=='i32.const':b=int(t[2][1])
            else:raise ValueError('Source bit extraction')
            if not 0<=b<32:raise ValueError('Input bit')
            bits.add(b);return ['input',b]
        raise ValueError('Source operand '+w.emit(x))
    if len(body)!=len(ls)+1:raise ValueError('Source body')
    for i,s in enumerate(body[:-1]):
        if s[:2]!=['local.set',str(i+1)] or len(s)!=3:raise ValueError('Ordered SSA locals required')
        e=s[2]
        if len(e)!=3 or e[0] not in ('i32.and','i32.or','i32.xor'):raise ValueError('Boolean gate')
        gates.append([e[0][4:],operand(e[1],i),operand(e[2],i)])
    if not bits or body[-1]!=['local.get',str(len(ls))]:raise ValueError('Output must be last gate')
    inputs=max(bits)+1
    if inputs+len(gates)>32:raise ValueError('Packed state exceeds i32')
    return inputs,gates

def plain(inputs,gates):
    def operand(x):return f'(local.get {x[1]+1})' if x[0]=='gate' else f'(i32.and (i32.shr_u (local.get 0) (i32.const {x[1]})) (i32.const 1))'
    rows=[f'(local.set {i+1} (i32.{op} {operand(a)} {operand(b)}))' for i,(op,a,b) in enumerate(gates)]
    return '(module (func (export "run") (param i32) (result i32) (local '+ ' '.join(['i32']*len(gates))+') '+' '.join(rows)+f' (local.get {len(gates)})))'

def plus(*ps):
    r={}
    for p in ps:
        for m,c in p.items():r[m]=r.get(m,0)+c
    return {m:c for m,c in r.items() if c}
def scale(p,c):return {m:v*c for m,v in p.items() if v*c}
def product(a,b):
    r={}
    for m,c in a.items():
        for k,v in b.items():r[m|k]=r.get(m|k,0)+c*v
    return {m:c for m,c in r.items() if c}
def boolean(op,a,b):
    q=product(a,b)
    return q if op=='and' else plus(a,b,scale(q,-1 if op=='or' else -2))

def build(inputs,gates,mode='dag',gauge=False,seed=20261022):
    n=len(gates);rng=random.Random(seed);order=list(range(n));flips=[0]*n
    if gauge:rng.shuffle(order);flips=[rng.randrange(2) for _ in range(n)]
    weights=[1]*n
    for i in reversed(range(n)):
        children=[j for j,g in enumerate(gates) if ['gate',i] in g[1:]]
        if mode=='dag':weights[i]=1+sum(weights[j] for j in children)
        elif mode=='lex':weights[i]=1+sum(weights[i+1:])
        elif mode!='flat':raise ValueError(mode)
    def var(x):
        if x[0]=='input':return {1<<x[1]:1}
        i=x[1];p={1<<(inputs+order[i]):1}
        return plus({0:1},scale(p,-1)) if flips[i] else p
    energy={}
    for i,(op,a,b) in enumerate(gates):
        z=var(['gate',i]);f=boolean(op,var(a),var(b));error=plus(z,f,scale(product(z,f),-2))
        energy=plus(energy,scale(error,weights[i]))
    terms=sorted(energy.items())
    if sum(abs(c) for _,c in terms)>=1<<62:raise ValueError('No signed i64 range certificate')
    record={'inputs':inputs,'n':n,'output':order[-1],'flip':flips[-1],'terms':terms}
    return record,{'weights':weights,'permutation':order,'complements':flips,'coefficient_abs_sum':sum(abs(c) for _,c in terms)}

def render(r):
    I,n,o,f=r['inputs'],r['n'],r['output'],r['flip'];terms=r['terms']
    data=struct.pack('<6I',MAGIC,I,n,o,f,len(terms))+b''.join(struct.pack('<Iq',m,c) for m,c in terms)
    if len(data)>65536:raise ValueError('Data capacity')
    quoted='"'+''.join('\\%02x'%b for b in data)+'"'
    # The table contains only aggregate monomials. No gate order or weights.
    return f'''(module (memory 1 1) (data (i32.const 0) {quoted})
    (func $energy (param $s i32) (result i64) (local $p i32) (local $a i64)
      (local.set $p (i32.const 24))
      (loop $terms
        (local.set $a (i64.add (local.get $a)
          (i64.mul (i64.load offset=4 align=1 (local.get $p))
            (i64.extend_i32_u (i32.eq
              (i32.and (local.get $s) (i32.load (local.get $p))) (i32.load (local.get $p)))))))
        (local.set $p (i32.add (local.get $p) (i32.const 12)))
        (br_if $terms (i32.lt_u (local.get $p) (i32.const {len(data)}))))
      (local.get $a))
    (func (export "run") (param $x i32) (result i32)
      (local $s i32) (local $e i64) (local $q i64) (local $v i32) (local $i i32) (local $t i32)
      (local.set $s (i32.or (i32.and (local.get $x) (i32.const {(1<<I)-1}))
        (i32.and (i32.shl (local.get $x) (i32.const {I})) (i32.const {((1<<n)-1)<<I}))))
      (local.set $e (call $energy (local.get $s)))
      (loop $sweeps
        (local.set $i (i32.const {I}))
        (loop $coordinate
          (local.set $v (i32.xor (local.get $s) (i32.shl (i32.const 1) (local.get $i))))
          (local.set $q (call $energy (local.get $v)))
          (if (i64.lt_s (local.get $q) (local.get $e)) (then
            (local.set $s (local.get $v)) (local.set $e (local.get $q))))
          (local.set $i (i32.add (local.get $i) (i32.const 1)))
          (br_if $coordinate (i32.lt_u (local.get $i) (i32.const {I+n}))))
        (local.set $t (i32.add (local.get $t) (i32.const 1)))
        (br_if $sweeps (i32.lt_u (local.get $t) (i32.const {n}))))
      (i32.xor (i32.and (i32.shr_u (local.get $s) (i32.const {I+o})) (i32.const 1)) (i32.const {f}))))'''

def transform(src,out,mode,gauge=False):
    start=time.perf_counter();I,gates=source(src);r,cert=build(I,gates,mode,gauge);save(render(r),out)
    return {'milliseconds':(time.perf_counter()-start)*1000,'record':r,'certificate':cert}

def rawdata(mod):
    mem=bytearray(65536)
    for d in (x for x in mod[1:] if x[0]=='data'):
        if d[1][0]!='i32.const':raise ValueError('Active constant data expected')
        offset=int(d[1][1]);raw=bytearray()
        for s in d[2:]:
            s=s[1:-1];i=0
            while i<len(s):
                if s[i]=='\\':
                    if s[i+1:i+3] and all(x in '0123456789abcdefABCDEF' for x in s[i+1:i+3]) and len(s[i+1:i+3])==2:raw.append(int(s[i+1:i+3],16));i+=3
                    else:raw.append({'t':9,'n':10,'r':13,'"':34,"'":39,'\\':92}[s[i+1]]);i+=2
                else:raw.append(ord(s[i]));i+=1
        if offset<0 or offset+len(raw)>len(mem):raise ValueError('Data bounds')
        mem[offset:offset+len(raw)]=raw
    magic,I,n,o,f,t=struct.unpack_from('<6I',mem)
    if magic!=MAGIC or not 1<=I or not 1<=n<=20 or I+n>32 or o>=n or f>1 or not 1<=t<=4000 or 24+12*t>len(mem):raise ValueError('Energy profile')
    terms=[struct.unpack_from('<Iq',mem,24+12*i) for i in range(t)]
    if any(m>=1<<(I+n) or c==0 for m,c in terms) or len(set(m for m,c in terms))!=t or sum(abs(c) for m,c in terms)>=1<<62:raise ValueError('Energy coefficient bounds')
    return {'inputs':I,'n':n,'output':o,'flip':f,'terms':terms}

def recover_model(r):
    start=time.perf_counter();I,n=r['inputs'],r['n'];rules=[];rows=0;maximum=0
    for j in range(I,I+n):
        p={m^(1<<j):c for m,c in r['terms'] if m&(1<<j)}
        support=sorted({k for m in p for k in range(I+n) if m&(1<<k)})
        maximum=max(maximum,len(support))
        if len(support)>20:raise ValueError('Attack support exceeds explicit 20-bit enumeration cap')
        truth=[]
        for a in range(1<<len(support)):
            state=sum(1<<k for q,k in enumerate(support) if a>>q&1)
            d=sum(c for m,c in p.items() if state&m==m)
            if d==0:raise ValueError('Coordinate has a tie: no unique local rule')
            truth.append(int(d<0))
        rows+=len(truth)
        essential=[q for q in range(len(support)) if any(truth[a]!=truth[a^(1<<q)] for a in range(len(truth)) if not a>>q&1)]
        args=[support[q] for q in essential]
        if len(args)>5:raise ValueError('Recovered rule exceeds 5-input WAT lookup profile')
        table=0
        for a in range(1<<len(args)):
            k=sum(1<<q for t,q in enumerate(essential) if a>>t&1)
            table|=truth[k]<<a
        rules.append({'coordinate':j,'args':args,'truth':table,'before_support':len(support)})
    pending={x['coordinate']:x for x in rules};done=set(range(I));ordered=[]
    while pending:
        ready=sorted(j for j,v in pending.items() if set(v['args'])<=done)
        if not ready:raise ValueError('Recovered dependency graph is cyclic')
        for j in ready:ordered.append(pending.pop(j));done.add(j)
    return {'inputs':I,'n':n,'output':I+r['output'],'flip':r['flip'],'rules':ordered,'enumerated_rows':rows,'max_support':maximum,'milliseconds':(time.perf_counter()-start)*1000}

def recovered_wat(m):
    I=m['inputs'];local={x['coordinate']:i+1 for i,x in enumerate(m['rules'])}
    def value(k):return f'(local.get {local[k]})' if k>=I else f'(i32.and (i32.shr_u (local.get 0) (i32.const {k})) (i32.const 1))'
    rows=[]
    for r in m['rules']:
        index='(i32.const 0)'
        for q,k in enumerate(r['args']):index=f'(i32.or {index} (i32.shl {value(k)} (i32.const {q})))'
        rows.append(f'(local.set {local[r["coordinate"]]} (i32.and (i32.shr_u (i32.const {r["truth"]}) {index}) (i32.const 1)))')
    return '(module (func (export "run") (param i32) (result i32) (local '+' '.join(['i32']*m['n'])+') '+' '.join(rows)+f' (i32.xor {value(m["output"])} (i32.const {m["flip"]}))))'

def recover(src,out):
    start=time.perf_counter();w.tool('wasm-validate',[src]);mod=w.parse(w.tool('wasm2wat',[src,'--fold-exprs']));r=rawdata(mod)
    # Exact generated-family check. Do not trust a table hidden in arbitrary code.
    candidate=Path(out).with_stem(Path(out).stem+'-family-check');save(render(r),candidate)
    match=candidate.read_bytes()==Path(src).read_bytes()
    if not match:
        opt=candidate.with_stem(candidate.stem+'-O3');w.tool('wasm-opt',[candidate,'-O3','-o',opt]);match=opt.read_bytes()==Path(src).read_bytes()
    if not match:raise ValueError('Binary differs from supported evaluator and its O3 form')
    model=recover_model(r);save(recovered_wat(model),out)
    return {'milliseconds':(time.perf_counter()-start)*1000,'model':model,'family_checked':True}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['transform','recover']);ap.add_argument('source');ap.add_argument('output');ap.add_argument('--mode',choices=['dag','lex','flat'],default='dag');ap.add_argument('--gauge',action='store_true');a=ap.parse_args()
    print(json.dumps(transform(a.source,a.output,a.mode,a.gauge) if a.action=='transform' else recover(a.source,a.output),indent=2))
