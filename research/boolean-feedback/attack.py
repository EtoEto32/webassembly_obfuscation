"""SCC fixed-point elimination from public H only, including convergence check."""
import argparse
import json
from pathlib import Path
import time
from shared import h,a


def components(maps,n):
    deps=[{v//32-n for m in poly for v in m if v//32>=n} for poly in maps]
    order=[];indices={};low={};stack=[];active=set()
    def visit(i):
        indices[i]=low[i]=len(indices);stack.append(i);active.add(i)
        for j in sorted(deps[i]):
            if j not in indices:visit(j);low[i]=min(low[i],low[j])
            elif j in active:low[i]=min(low[i],indices[j])
        if low[i]==indices[i]:
            group=[]
            while True:
                j=stack.pop();active.remove(j);group.append(j)
                if j==i:break
            order.append(sorted(group))
    for i in range(len(maps)):
        if i not in indices:visit(i)
    return order,deps


def solve(r):
    start=time.perf_counter();n,d=r['n'],r['d'];maps=[{tuple(m) for m in poly} for poly in r['maps']];groups,deps=components(maps,n)
    expr=a.Expr(n);values=list(expr.params)+[None]*d;bounds={};details=[]
    def compile_poly(poly):
        z=expr.zero
        for mono in sorted(poly):
            v=expr.one
            for atom in mono:
                ev=values[atom//32]
                if ev is None:raise ValueError('Uneliminated dependency')
                v=expr.and_(v,expr.rot(ev,atom%32))
            z=expr.xor(z,v)
        return z
    for group in groups:
        k=len(group);internal=set(group)
        if k==1 and group[0] not in deps[group[0]]:
            fixed=[maps[group[0]]];local_bound=1
        else:
            if k>3:raise ValueError('SCC larger than three coordinates')
            if any(v%32 for i in group for mono in maps[i] for v in mono if v//32-n in internal):raise ValueError('Internal bit rotation')
            fixed=[set() for _ in group];cover=set();conditions=[];local_bound=0
            for assignment in range(1<<k):
                env=[h.var(i) for i in range(n+d)]
                for j,i in enumerate(group):env[n+i]=h.const(h.MASK if assignment>>j&1 else 0)
                nexts=[h.sub(maps[i],env) for i in group];cond={()}
                for j,poly in enumerate(nexts):cond=h.mul(cond,poly if assignment>>j&1 else h.add({()},poly))
                for prev in conditions:
                    if h.mul(prev,cond):raise ValueError('Fixed point not unique')
                conditions.append(cond);cover^=cond
                for j in range(k):
                    if assignment>>j&1:fixed[j]^=cond
            if cover!={()}:raise ValueError('Some external input lacks a fixed point')
            # Independent of producer N/F: symbolically iterate from every
            # Boolean state, with external words treated as arbitrary constants.
            for assignment in range(1<<k):
                state=[h.const(h.MASK if assignment>>j&1 else 0) for j in range(k)]
                for t in range(8):
                    if state==fixed:local_bound=max(local_bound,t);break
                    env=[h.var(i) for i in range(n+d)]
                    for j,i in enumerate(group):env[n+i]=state[j]
                    state=[h.sub(maps[i],env) for i in group]
                else:raise ValueError('No verified seven-round stabilization')
        outside=set().union(*(deps[i] for i in group))-internal
        depth=local_bound+max([bounds[j] for j in outside]+[0])
        for j,i in enumerate(group):
            values[n+i]=compile_poly(fixed[j]);bounds[i]=depth
        details.append({'group':group,'local_bound':local_bound,'global_bound':depth,'fixed_terms':[len(poly) for poly in fixed]})
    if max(bounds.values())>r['depth']:raise ValueError('Emitted iteration count below verified bound')
    wat,nodes=expr.wat(values[-1],n)
    return {'status':'recovered','components':details,'verified_bound':max(bounds.values()),'expression_nodes':nodes,'elapsed_ms':1000*(time.perf_counter()-start)},wat


def run(binary,output):
    r,ms=a.read(binary);res,wat=solve(r);res['read_ms']=ms;h.save(wat,output);opt=Path(output).with_name(Path(output).stem+'-O3.wasm');h.w.tool('wasm-opt',[output,'-O3','-o',opt]);h.w.tool('wasm-validate',[opt]);return {**res,'output':str(Path(output).resolve()),'optimized':str(opt.resolve())}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('input');ap.add_argument('output');q=ap.parse_args();print(json.dumps(run(q.input,q.output),indent=2))
