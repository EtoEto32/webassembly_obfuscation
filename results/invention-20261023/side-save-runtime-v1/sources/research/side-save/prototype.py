"""Shared linear save synthesis with nested current-memory side information."""
import argparse
import importlib.util
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
def module(name, path):
    s=importlib.util.spec_from_file_location(name,path);r=importlib.util.module_from_spec(s);s.loader.exec_module(r);return r
base=module('side_save_base',ROOT/'research/prefix-repair/prototype.py')
q,m=base.q,base.m


def decoder(rows):
    """Return a solver tracking combinations of arbitrary original rows."""
    piv={}
    for i,row in enumerate(rows):
        mask=1<<i
        while row:
            k=row.bit_length()-1
            if k not in piv:piv[k]=(row,mask);break
            row^=piv[k][0];mask^=piv[k][1]
    def solve(row):
        mask=0
        while row:
            k=row.bit_length()-1
            if k not in piv:return None
            row^=piv[k][0];mask^=piv[k][1]
        return mask
    return solve


def saves(ps,ds):
    # Stronger (earlier) receivers have every later side-information row.
    for a,b in zip(ps,ps[1:]):
        solve=decoder(a)
        if any(solve(row) is None for row in b):raise ValueError('side information is not nested')
    v=[]
    for p,d in reversed(list(zip(ps,ds))):
        for row in d:
            if decoder(p+v)(row) is None:v.append(row)
    return v


def plan(n,ops,b):
    old=base.plan(n,ops,b);ps=[m.ident(n)]
    for op in ops:ps.append(m.product(m.matrix(n,op),ps[-1]))
    v=saves(ps,old['delta']);repairs=[]
    for prefix,delta in zip(ps,old['delta']):
        solve=decoder(prefix+v);coeff=[solve(row) for row in delta]
        if any(x is None for x in coeff):raise AssertionError('missing repair')
        if m.product(coeff,prefix+v)!=delta:raise AssertionError('invalid certificate')
        temp=base.basis(coeff);write=base.coordinates(coeff,temp)
        repairs.append(dict(coeff=coeff,temp=temp,write=write))
    return dict(**old,side_v=v,side_repairs=repairs,side_prefix=ps,entry_saved_bytes=len(v),
                temporary_values=max(len(x['temp']) for x in repairs))


def wat(data,ops,b,mode='side'):
    if mode in ('plain','basis'):return base.wat(data,ops,b,mode)
    if mode not in ('side','bad'):raise ValueError('mode')
    n=len(data);info=plan(n,ops,b);v=info['side_v'];r=len(v)
    def fix(j):
        repair=info['side_repairs'][j]
        reader=lambda i:base.load(i) if i<n else base.get(1+i-n)
        reads=[f'(local.set {r+1+i} {base.linear(row,reader)})' for i,row in enumerate(repair['temp'])]
        stores=[f'(i32.store8 {base.c(i)} (i32.xor {base.load(i)} {base.linear(row,lambda k:base.get(r+1+k))}))'
                for i,row in enumerate(repair['write']) if row]
        return ' '.join(reads+stores)
    parts=[base.snapshot(v)]
    for j,op in enumerate(ops):
        if mode=='side' and j:parts.append(f'(if (i32.eq (local.get 0) {base.c(j)}) (then {fix(j)}))')
        parts.append(base.rawcopy(op,j))
    parts.append(fix(len(ops)))
    locals_=r+info['temporary_values'];decl='(local '+' '.join(['i32']*locals_)+')' if locals_ else ''
    run='(func (export "run") (param i32) '+decl+' '+' '.join(parts)+')'
    digest=['(local.set 0 '+base.c(2166136261)+')']
    for row in info['inverse']:digest.append(f'(local.set 0 (i32.mul (i32.xor (local.get 0) {base.linear(row,base.load)}) {base.c(16777619)}))')
    observe='(func (export "digest") (result i32) (local i32) '+' '.join(digest)+' (local.get 0))'
    return '(module (memory 1 1) '+run+observe+' (data (i32.const 0) "'+base.blob(m.apply(b,data))+'"))'


def transform(src,dst,mode='side',seed=211070):
    start=time.perf_counter();data,ops=base.parse(src);b=base.encoding(len(data),seed);info=plan(len(data),ops,b)
    q.compile(wat(data,ops,b,mode),dst)
    return dict(n=len(data),ops=ops,mode=mode,seed=seed,**info,transform_ms=(time.perf_counter()-start)*1000)


def recovery():
    old=sys.modules.get('prototype')
    try:
        sys.modules['prototype']=base
        return module('side_save_attacker',ROOT/'research/prefix-repair/recover.py')
    finally:
        if old is None:del sys.modules['prototype']
        else:sys.modules['prototype']=old


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('source');a.add_argument('output');a.add_argument('--mode',choices=['side','basis'],default='side');a.add_argument('--seed',type=int,default=211070);x=a.parse_args()
    q.save(x.output+'.json',transform(x.source,x.output,x.mode,x.seed))
