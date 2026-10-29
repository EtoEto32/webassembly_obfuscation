"""Find semantic blocks with a universal external-state transition certificate.

Input is the public binary only. Rotated unknown state bits are conservatively
independent adversarial inputs. Candidate groups need not be graph SCCs.
"""
import argparse
import functools
import itertools
import json
from pathlib import Path
import time
from shared import h,a


class BDD(a.shared.BDD):
    def __init__(self,seconds=60,limit=1000000):
        super().__init__(limit);self.deadline=time.perf_counter()+seconds
    def check(self):
        if time.perf_counter()>self.deadline:raise TimeoutError('Semantic-block analysis budget')
    def mk(self,*args):
        if len(self.nodes)%1024==0:self.check()
        return super().mk(*args)
    def select(self,cond,lo,hi):return self.binary('xor',lo,self.binary('and',cond,self.binary('xor',lo,hi)))
    def restrict(self,root,assignment):
        @functools.lru_cache(None)
        def go(v):
            if v<2:return v
            k,lo,hi=self.nodes[v]
            if k in assignment:return go(hi if assignment[k] else lo)
            return self.mk(k,go(lo),go(hi))
        return go(root)
    def quantify_state(self,root,first):
        @functools.lru_cache(None)
        def go(v):
            if v<2:return v
            k,lo,hi=self.nodes[v];lo,hi=go(lo),go(hi)
            return self.binary('or',lo,hi) if k>=first else self.mk(k,lo,hi)
        return go(root)
    def compose(self,root,replacements):
        @functools.lru_cache(None)
        def go(v):
            if v<2:return v
            k,lo,hi=self.nodes[v];cond=replacements.get(k)
            if cond is None:cond=self.mk(k,0,1)
            return self.select(cond,go(lo),go(hi))
        return go(root)
    @functools.lru_cache(None)
    def rotate(self,root,amount):
        if root<2:return root
        k,lo,hi=self.nodes[root];key=(k//32)*32+(k%32+amount)%32
        return self.select(self.mk(key,0,1),self.rotate(lo,amount),self.rotate(hi,amount))


def certificate(bdd,maps,group,n):
    k=len(group);width=1<<k;T=[]
    for state in range(width):
        assignments={32*(n+i):(state>>j)&1 for j,i in enumerate(group)}
        values=[bdd.restrict(maps[i],assignments) for i in group];row=[]
        for target in range(width):
            cond=1
            for j,v in enumerate(values):cond=bdd.binary('and',cond,v if target>>j&1 else bdd.binary('xor',1,v))
            row.append(bdd.quantify_state(cond,32*n))
        T.append(row)
    reachable=[1]*width
    for rounds in range(1,8):
        bdd.check();new=[]
        for target in range(width):
            value=0
            for state in range(width):value=bdd.binary('or',value,bdd.binary('and',reachable[state],T[state][target]))
            new.append(value)
        if new==reachable:return None  # Non-singleton closed set cannot shrink later.
        reachable=new
        if any(bdd.binary('and',reachable[i],reachable[j]) for i in range(width) for j in range(i)):continue
        cover=0
        for v in reachable:cover=bdd.binary('or',cover,v)
        if cover!=1:raise AssertionError('Total transition lost coverage')
        if any(bdd.binary('and',reachable[i],bdd.binary('xor',T[i][i],1)) for i in range(width)):continue
        fixed=[]
        for bit in range(k):
            value=0
            for state in range(width):
                if state>>bit&1:value=bdd.binary('or',value,reachable[state])
            fixed.append(value)
        return {'rounds':rounds,'values':fixed}
    return None


def solve(record,seconds=60):
    start=time.perf_counter();n,d=record['n'],record['d'];bdd=BDD(seconds);maps=[]
    for poly in record['maps']:
        result=0
        for mon in poly:
            term=1
            for atom in mon:term=bdd.binary('and',term,bdd.mk(atom,0,1))
            result=bdd.binary('xor',result,term)
        maps.append(result)
    todo=set(range(d));values={};details=[];attempts=0;bound=0
    while todo:
        found=None
        for size in range(1,min(3,len(todo))+1):
            for group in itertools.combinations(sorted(todo),size):
                bdd.check();attempts+=1;c=certificate(bdd,maps,group,n)
                if c is not None:found=(group,c);break
            if found:break
        if not found:return {'status':'stalled','remaining':sorted(todo),'groups':details,'attempts':attempts,'bdd_nodes':len(bdd.nodes),'analysis_ms':1000*(time.perf_counter()-start)},None
        group,c=found;bound+=c['rounds'];replacements={}
        for i,v in zip(group,c['values']):
            values[i]=v;todo.remove(i)
            for rotation in range(32):replacements[32*(n+i)+rotation]=bdd.rotate(v,rotation)
        maps=[bdd.compose(v,replacements) for v in maps]
        details.append({'group':group,'local_bound':c['rounds'],'cumulative_bound':bound})
    if bound>record['depth']:return {'status':'bound_not_certified','verified_bound':bound,'emitted_bound':record['depth'],'groups':details,'attempts':attempts},None
    expr=a.Expr(n);cache={0:expr.zero,1:expr.one}
    def emit(v):
        if v not in cache:
            key,lo,hi=bdd.nodes[v]
            if key//32>=n:raise AssertionError('Unresolved state in result')
            atom=expr.rot(expr.params[key//32],key%32);low,high=emit(lo),emit(hi)
            cache[v]=expr.xor(low,expr.and_(atom,expr.xor(low,high)))
        return cache[v]
    wat,nodes=expr.wat(emit(values[d-1]),n)
    return {'status':'recovered','groups':details,'verified_bound':bound,'attempts':attempts,'bdd_nodes':len(bdd.nodes),'expression_nodes':nodes,'analysis_ms':1000*(time.perf_counter()-start)},wat


def run(binary,output,seconds=60):
    record,ms=a.read(binary);start=time.perf_counter()
    try:result,wat=solve(record,seconds)
    except TimeoutError as e:return {'status':'timeout','reason':str(e),'read_ms':ms,'analysis_ms':1000*(time.perf_counter()-start)}
    except OverflowError as e:return {'status':'node_budget','reason':str(e),'read_ms':ms,'analysis_ms':1000*(time.perf_counter()-start)}
    result['read_ms']=ms
    if wat:
        h.save(wat,output);opt=Path(output).with_name(Path(output).stem+'-O3.wasm');h.w.tool('wasm-opt',[output,'-O3','-o',opt]);h.w.tool('wasm-validate',[opt]);result.update(output=str(Path(output).resolve()),optimized=str(opt.resolve()))
    return result

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('input');ap.add_argument('output');ap.add_argument('--seconds',type=float,default=60);q=ap.parse_args();result=run(q.input,q.output,q.seconds);Path(q.output).parent.mkdir(parents=True,exist_ok=True);Path(q.output).with_suffix('.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
