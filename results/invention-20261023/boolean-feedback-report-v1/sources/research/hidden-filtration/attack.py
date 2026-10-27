"""Binary-only bounded observable lifting; no coordinate keys or source input."""
import argparse
import importlib.util
import itertools
import json
from pathlib import Path
import sys
import tempfile
import time
import prototype as p

saved=sys.modules.get('prototype');sys.modules['prototype']=p.w
sp=importlib.util.spec_from_file_location('hfl_reader',p.HERE.parent/'connectivity-elimination/recover.py')
shared=importlib.util.module_from_spec(sp);sp.loader.exec_module(shared)
if saved is None:del sys.modules['prototype']
else:sys.modules['prototype']=saved


def read(binary):
    start=time.perf_counter();binary=Path(binary);p.w.tool('wasm-validate',[binary])
    r=p.decode(shared.initial_memory(binary.read_bytes()))
    with tempfile.TemporaryDirectory(prefix='hfl-guard-') as folder:
        raw=Path(folder)/'raw.wasm';opt=Path(folder)/'opt.wasm';p.save(p.render(r),raw)
        if binary.read_bytes()!=raw.read_bytes():
            p.w.tool('wasm-opt',[raw,'-O3','--enable-bulk-memory','-o',opt])
            if binary.read_bytes()!=opt.read_bytes():raise ValueError('Not the exact raw/O3 evaluator family')
    return r,(time.perf_counter()-start)*1000


class Expr:
    def __init__(self,n):
        self.nodes=[];self.ids={};self.zero=self.make('c',0);self.one=self.make('c',-1)
        self.params=[self.make('p',i) for i in range(n)]
    def make(self,*key):
        if key not in self.ids:self.ids[key]=len(self.nodes);self.nodes.append(key)
        return self.ids[key]
    def xor(self,a,b):
        if a==b:return self.zero
        if a==self.zero:return b
        if b==self.zero:return a
        return self.make('xor',*sorted((a,b)))
    def and_(self,a,b):
        if self.zero in (a,b):return self.zero
        if a==self.one or a==b:return b
        if b==self.one:return a
        return self.make('and',*sorted((a,b)))
    def rot(self,a,r):return self.make('rot',a,r) if r else a
    def total(self,mask,items):
        z=self.zero
        while mask:
            b=mask&-mask;mask^=b;z=self.xor(z,items[b.bit_length()-1])
        return z
    def wat(self,out,n):
        used=set()
        def visit(i):
            if i in used:return
            used.add(i);op,*a=self.nodes[i]
            if op=='rot':visit(a[0])
            elif op in ('xor','and'):
                for v in a:visit(v)
        visit(out);ordered=sorted(used);loc={i:n+j for j,i in enumerate(ordered)};body=[]
        for i in ordered:
            op,*a=self.nodes[i]
            if op=='p':v=f'(local.get {a[0]})'
            elif op=='c':v=f'(i32.const {a[0]})'
            elif op=='rot':v=f'(i32.rotl (local.get {loc[a[0]]}) (i32.const {a[1]}))'
            else:v=f'(i32.{op} (local.get {loc[a[0]]}) (local.get {loc[a[1]]}))'
            body.append(f'(local.set {loc[i]} {v})')
        return f'(module (func (export "run") (param {" ".join(["i32"]*n)}) (result i32) (local {" ".join(["i32"]*len(ordered))}) {"".join(body)} (local.get {loc[out]})))',len(used)


def eliminate(v,basis,mask=0):
    # A quotient representative must remove ALL pivot coordinates. Stopping
    # at the first free coordinate leaves lower known-algebra terms behind.
    remainder=0
    while v:
        k=v.bit_length()-1
        if k in basis:
            row,rep=basis[k];v^=row;mask^=rep
        else:
            bit=1<<k;remainder^=bit;v^=bit
    return remainder,mask


def eliminate_dense(v,basis,mask=0):
    """Historical main-v1 reduction, retained for reproducing its time caps."""
    for k in sorted(basis,reverse=True):
        if v>>k&1:
            row,rep=basis[k];v^=row;mask^=rep
    return v,mask


def recover(r,degree=2,seconds=60,monomial_cap=200000,column_cap=100000,prune=False):
    start=time.perf_counter();deadline=start+seconds;n,d=r['n'],r['d'];expr=Expr(n)
    h=[{tuple(m) for m in a} for a in r['maps']]
    features=[p.var(n+i) for i in range(d)]
    pulls=list(h)
    if degree==2:
        for i,j in itertools.combinations(range(d),2):
            features.append(p.mul(p.var(n+i),p.var(n+j)));pulls.append(p.mul(h[i],h[j]))
    rotations=sorted({0}|{v%32 for a in h for m in a for v in m})
    monos={}
    def check():
        if time.perf_counter()>deadline:raise TimeoutError('Observable lifting time budget')
    def vec(poly):
        v=0
        for m in sorted(poly):
            if m not in monos:
                if len(monos)>=monomial_cap:raise OverflowError('Monomial budget')
                monos[m]=len(monos)
            v^=1<<monos[m]
        return v
    hp=[vec(a) for a in pulls];known=[];generators=[];kb={};rounds=[];out=None
    status='stalled'
    try:
        for iteration in range(d+1):
            check();atoms=[];seen=set()
            candidates=[(p.var(i),expr.params[i]) for i in range(n)]+[(known[i][1],known[i][2]) for i in generators]
            for a,e in candidates:
                for rot in rotations:
                    poly=p.rotate(a,rot);key=frozenset(poly)
                    if key not in seen:seen.add(key);atoms.append((poly,expr.rot(e,rot)))
            ab={};aes=[]
            def column(poly,e):
                if len(aes)>=column_cap:raise OverflowError('Known-algebra column budget')
                if len(aes)%128==0:check()
                v,mask=eliminate(vec(poly),ab,1<<len(aes));aes.append(e)
                if v:ab[v.bit_length()-1]=(v,mask)
            column({()},expr.one)
            for a,e in atoms:column(a,e)
            for i,(a,e) in enumerate(atoms):
                for b,f in atoms[i+1:]:column(p.mul(a,b),expr.and_(e,f))
            relations={};new=[]
            for i,a in enumerate(hp):
                check();rem,am=eliminate(a,ab);fm=1<<i
                while rem:
                    k=rem.bit_length()-1
                    if k not in relations:relations[k]=(rem,fm,am);break
                    row,fpart,apart=relations[k];rem^=row;fm^=fpart;am^=apart
                if not rem:
                    reduced,km=eliminate(fm,kb)
                    if reduced:
                        obs=set()
                        for j,phi in enumerate(features):
                            if fm>>j&1:obs^=phi
                        e=expr.total(am,aes);idx=len(known);known.append((fm,obs,e))
                        kb[reduced.bit_length()-1]=(reduced,(1<<idx)^km);new.append(idx)
                        # Heuristic: exclude observations already in the algebra
                        # of previous generators. Exact identities, but degree-2
                        # future closure can be weaker; a stall is not a proof.
                        rem_obs,_=eliminate(vec(obs),ab) if prune else (1,0)
                        if rem_obs:generators.append(idx)
            rounds.append({'iteration':iteration,'known':len(known),'generators':len(generators),'new':len(new),'atoms':len(atoms),'algebra_columns':len(aes),'algebra_rank':len(ab),'monomials':len(monos),'elapsed_ms':(time.perf_counter()-start)*1000})
            rem,km=eliminate(1<<(d-1),kb)
            if not rem:out=expr.total(km,[a[2] for a in known]);status='recovered';break
            if not new:break
    except TimeoutError:status='timeout'
    except OverflowError as e:status='resource_budget';rounds.append({'reason':str(e)})
    result={'status':status,'degree':degree,'prune':prune,'rotations':rotations,'features':len(features),'known':len(known),'rounds':rounds,'monomials':len(monos),'elapsed_ms':(time.perf_counter()-start)*1000}
    text=None
    if out is not None:text,result['expression_nodes']=expr.wat(out,n)
    return result,text


def run(binary,output,degree=2,seconds=60,prune=False):
    r,ms=read(binary);result,text=recover(r,degree,seconds,prune=prune);result['read_ms']=ms
    if text:
        p.save(text,output);opt=Path(output).with_name(Path(output).stem+'-O3.wasm')
        p.w.tool('wasm-opt',[output,'-O3','-o',opt]);p.w.tool('wasm-validate',[opt])
        result.update(output=str(Path(output).resolve()),optimized=str(opt.resolve()))
    return result


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('input');a.add_argument('output');a.add_argument('--degree',type=int,choices=[1,2],default=2);a.add_argument('--seconds',type=float,default=60);a.add_argument('--prune',action='store_true')
    q=a.parse_args();log=Path(q.output).with_suffix('.json');log.parent.mkdir(parents=True,exist_ok=True)
    if log.exists():raise FileExistsError(log)
    res=run(q.input,q.output,q.degree,q.seconds,q.prune)
    log.write_text(json.dumps(res,indent=2),encoding='utf8');print(json.dumps(res,indent=2))
