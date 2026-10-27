# -*- coding: utf-8 -*-
"""Family-aware recovery. Receives only the distributed Wasm, never source/seed."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import time
import prototype as p

# Reuse the previously audited binary data reader and basic ROBDD manager.
saved=sys.modules.get('prototype')
sys.modules['prototype']=p.w
spec=importlib.util.spec_from_file_location('span_bdd',p.HERE.parent/'connectivity-elimination/recover.py')
shared=importlib.util.module_from_spec(spec);spec.loader.exec_module(shared)
if saved is None:del sys.modules['prototype']
else:sys.modules['prototype']=saved


class BDD(shared.BDD):
    def __init__(self,limit=300000,seconds=60):
        super().__init__(limit);self.deadline=time.perf_counter()+seconds
    def mk(self,*args):
        if len(self.nodes)%1024==0 and time.perf_counter()>self.deadline:
            raise TimeoutError('Symbolic recovery time budget')
        return super().mk(*args)


def read(binary):
    t=time.perf_counter();binary=Path(binary)
    p.w.tool('wasm-validate',[binary])
    record=p.decode(shared.initial_memory(binary.read_bytes()))
    with tempfile.TemporaryDirectory(prefix='span-guard-') as folder:
        raw=Path(folder)/'raw.wasm';opt=Path(folder)/'opt.wasm'
        p.save(p.render(record),raw)
        if binary.read_bytes()!=raw.read_bytes():
            p.optimize(raw,opt)
            if binary.read_bytes()!=opt.read_bytes():
                raise ValueError('Not the exact raw/O3 evaluator family')
    return record,(time.perf_counter()-t)*1000


def coefficient_reduce(record):
    """Constant row operations in the vector space of coefficient arrays.

    This is a sound preprocessing, not polynomial division over Boolean rings.
    A pivot key is (column, monomial); the output has identical pointwise span.
    """
    basis={}
    for pairs in record['rows']:
        row=set()
        for mono,bits in pairs:
            for j in range(record['d']):
                if bits>>j&1:row.add((j,mono))
        while row:
            pivot=min(row)
            if pivot not in basis:
                basis[pivot]=row;break
            row ^= basis[pivot]
    # Back reduction to make equivalent constant mixes canonical.
    keys=sorted(basis,reverse=True)
    for k in keys:
        for j in basis:
            if j<k and k in basis[j]:basis[j] ^= basis[k]
    out=[]
    for k in sorted(basis):
        r={}
        for j,mono in basis[k]:r[mono]=r.get(mono,0)^(1<<j)
        out.append(sorted(r.items()))
    return {**record,'rows':out,'m':len(out)}


def symbolic(record,bdd):
    n,m,d=record['n'],record['m'],record['d']
    variables=[bdd.mk(i,0,1) for i in range(n)]
    cache={0:1}
    def monomial(mono):
        if mono not in cache:
            bit=mono & -mono
            cache[mono]=bdd.binary('and',monomial(mono^bit),variables[bit.bit_length()-1])
        return cache[mono]
    def vector(pairs):
        out=[0]*d
        for mono,bits in pairs:
            term=monomial(mono)
            for j in range(d):
                if bits>>j&1:out[j]=bdd.binary('xor',out[j],term)
        return out
    bas=[[0]*d for _ in range(d)]
    for pairs in record['rows']:
        v=vector(pairs)
        for j in range(d):
            a=v[j]
            if not a:continue
            new=bdd.binary('and',a,bdd.binary('xor',bas[j][j],1))
            for k in range(j,d):
                bas[j][k]=bdd.binary('xor',bas[j][k],bdd.binary('and',v[k],new))
                v[k]=bdd.binary('xor',v[k],bdd.binary('and',bas[j][k],a))
    v=vector(record['target'])
    for j in range(d):
        a=v[j]
        if not a:continue
        for k in range(j,d):v[k]=bdd.binary('xor',v[k],bdd.binary('and',bas[j][k],a))
    residual=0
    for a in v:residual=bdd.binary('or',residual,a)
    return bdd.binary('xor',residual,1)


def source_root(tree,bdd):
    if tree[0]=='var':return bdd.mk(tree[1],0,1)
    if tree[0]=='const':return int(bool(tree[1]))
    return bdd.binary(tree[0],source_root(tree[1],bdd),source_root(tree[2],bdd))


def reachable(bdd,root):
    found=set()
    def go(k):
        if k<2 or k in found:return
        found.add(k);_,lo,hi=bdd.nodes[k];go(lo);go(hi)
    go(root)
    return sorted(found)


def render_bdd(n,bdd,root):
    nodes=reachable(bdd,root);index={node:n+i for i,node in enumerate(nodes)}
    def ref(node):return f'(local.get {index[node]})' if node>=2 else f'(i32.const {-node})'
    lines=[]
    for node in nodes:
        var,lo,hi=bdd.nodes[node]
        # Shannon expansion for all 32 lanes; i32.select would be UNSOUND.
        lines.append(f'(local.set {index[node]} (i32.or (i32.and (local.get {var}) {ref(hi)}) '
                     f'(i32.and (i32.xor (local.get {var}) (i32.const -1)) {ref(lo)})))')
    locals_='(local '+ ' '.join(['i32']*len(nodes))+')' if nodes else ''
    return '(module (func (export "run") (param '+ ' '.join(['i32']*n)+') (result i32) '+locals_+'\n'+'\n'.join(lines)+'\n'+ref(root)+'))'


def recover(src,dest,method='direct',limit=300000,seconds=60):
    start=time.perf_counter();rec,reader_ms=read(src)
    bdd=BDD(limit,seconds)
    begin=time.perf_counter();pre_ms=0
    if method=='coefficient':
        rec=coefficient_reduce(rec);pre_ms=(time.perf_counter()-begin)*1000
    elif method!='direct':raise ValueError('Unknown attack method')
    try:
        root=symbolic(rec,bdd)
    except (OverflowError,TimeoutError) as e:
        return {'status':'node_budget' if isinstance(e,OverflowError) else 'timeout',
                'message':str(e),'reader_ms':reader_ms,'core_ms':(time.perf_counter()-begin)*1000,
                'bdd_nodes':len(bdd.nodes),'cache_entries':len(bdd.cache),'limit':limit}
    core=(time.perf_counter()-begin)*1000
    p.save(render_bdd(rec['n'],bdd,root),dest)
    return {'status':'recovered','reader_ms':reader_ms,'preprocess_ms':pre_ms,
            'core_ms':core,'total_ms':(time.perf_counter()-start)*1000,
            'bdd_nodes':len(bdd.nodes),'output_nodes':len(reachable(bdd,root)),
            'bdd_digest':bdd.digest(root),'limit':limit}


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('input');a.add_argument('output')
    a.add_argument('--method',choices=['direct','coefficient'],default='coefficient')
    a.add_argument('--limit',type=int,default=300000);a.add_argument('--seconds',type=float,default=60)
    q=a.parse_args();print(json.dumps(recover(q.input,q.output,q.method,q.limit,q.seconds)))
