"""Binary-only parametric summary, modulo ad-bc=1. No call-stack unfolding."""
import argparse,json,time
from pathlib import Path
import prototype as p
M=p.MASK
class Algebra:
    def __init__(self):self.atoms=[];self.ids={};self.terms_peak=0;self.products=0
    def const(self,v):return {():v&M} if v&M else {}
    def atom(self,v):
        if v not in self.ids:self.ids[v]=len(self.atoms);self.atoms.append(v)
        return {(self.ids[v],):1}
    def var(self,n):return self.atom(('var',n))
    def frozen(self,x):return tuple(sorted(x.items()))
    def plus(self,x,y,scale=1):
        z=dict(x)
        for mon,v in y.items():
            c=(z.get(mon,0)+v*scale)&M
            if c:z[mon]=c
            else:z.pop(mon,None)
        self.terms_peak=max(self.terms_peak,len(z));return z
    def mul(self,x,y):
        z={};self.products+=1
        a=self.ids.get(('var','a'));d=self.ids.get(('var','d'));b=self.ids.get(('var','b'));c=self.ids.get(('var','c'))
        def insert(mon,v):
            # ad -> 1+bc. The leading coefficient is 1 even over Z/(2^32).
            if a is not None and a in mon and d in mon:
                rest=list(mon);rest.remove(a);rest.remove(d)
                insert(tuple(rest),v);insert(tuple(sorted(rest+[b,c])),v)
            else:
                new=(z.get(mon,0)+v)&M
                if new:z[mon]=new
                else:z.pop(mon,None)
        for mx,cx in x.items():
            for my,cy in y.items():insert(tuple(sorted(mx+my)),cx*cy)
        self.terms_peak=max(self.terms_peak,len(z))
        if len(z)>100000:raise p.Unsupported('polynomial budget')
        return z
    def operation(self,op,x,y=None):
        if op=='add':return self.plus(x,y)
        if op=='sub':return self.plus(x,y,-1)
        if op=='mul':return self.mul(x,y)
        if op=='shl' and (not y or set(y)=={()}):return self.mul(x,self.const(1<<((y.get((),0))&31)))
        if op in ('xor','or','and'):
            if x==y:return {} if op=='xor' else x
            if not x:return {} if op=='and' else y
            if not y:return {} if op=='and' else x
            if op=='and' and y==self.const(M):return x
            if op=='and' and x==self.const(M):return y
        if op in ('rotl','shl','shr_u') and not x:return {}
        if op=='rotl' and y==self.const(0):return x
        args=[self.frozen(x)] if y is None else [self.frozen(x),self.frozen(y)]
        if op in ('xor','or','and'):args.sort()
        return self.atom(('op',op,*args))
    def mat(self,mat,x,y):return self.plus(self.mul(mat[0],x),self.mul(mat[1],y)),self.plus(self.mul(mat[2],x),self.mul(mat[3],y))
    def inv(self,mat,x,y):return self.plus(self.mul(mat[3],x),self.mul(mat[1],y),-1),self.plus(self.mul(mat[0],y),self.mul(mat[2],x),-1)
    def determinant(self,mat):return self.plus(self.mul(mat[0],mat[3]),self.mul(mat[1],mat[2]),-1)
    def reachable(self,x):
        seen=set()
        def visit(poly):
            for mon,_ in poly:
                for i in mon:
                    if i in seen:continue
                    seen.add(i);a=self.atoms[i]
                    if a[0]=='op':
                        for arg in a[2:]:visit(arg)
                    elif a[0]=='call':
                        for arg in a[2:]:visit(arg)
        visit(self.frozen(x));return seen
    def emit(self,x):
        def atom(i):
            a=self.atoms[i]
            if a[0]=='var':
                if a[1] not in ('n','x','y'):raise p.Unsupported('frame dependence remains')
                return p.g(a[1])
            if a[0]=='op':return '(i32.'+a[1]+' '+' '.join(self.emit(dict(t)) for t in a[2:])+')'
            if a[0]=='call':return p.unpack(p.g('q'))[a[1]]
            raise p.Unsupported('unknown atom')
        terms=[]
        for mon,v in sorted(x.items()):
            if not mon:terms.append(p.c(v));continue
            expr=atom(mon[0])
            for i in mon[1:]:expr=p.mul(expr,atom(i))
            if v!=1:expr=p.mul(p.c(v),expr)
            terms.append(expr)
        if not terms:return p.c(0)
        out=terms[0]
        for t in terms[1:]:out=p.add(out,t)
        return out

class Evaluator:
    def __init__(self,alg,encoded):self.a=alg;self.encoded=encoded;self.calls=[]
    def body(self,f):return [x for x in f[1:] if x[0] not in ('type','param','result','local')]
    def locals(self,f,values):
        ty=[t for e in f[1:] if e[0]=='local' for t in e[1:]]
        return list(values)+[({}, {}) if t=='i64' else {} for t in ty]
    def sequence(self,body,env):
        last=None
        for e in body:
            v=self.eval(e,env)
            if v is not None:last=v
        return last
    def eval(self,e,env):
        op=e[0];a=self.a
        if op=='local.get':return env[int(e[1])]
        if op in ('local.set','local.tee'):
            if len(e)!=3:raise p.Unsupported('flat local assignment')
            value=self.eval(e[2],env);env[int(e[1])]=value
            return value if op=='local.tee' else None
        if op=='i32.const':return a.const(int(e[1]))
        if op=='i64.const':
            v=int(e[1])&((1<<64)-1);return a.const(v&M),a.const(v>>32)
        if op=='call':
            if e[1]!='0':raise p.Unsupported('only self call allowed')
            args=[self.eval(t,env) for t in e[2:]]
            if len(args)!=(7 if self.encoded else 3):raise p.Unsupported('call arity')
            n,x,y=args[:3];mat=args[3:] if self.encoded else [a.const(v) for v in (1,0,0,1)]
            if a.determinant(mat)!=a.const(1):raise p.Unsupported('child determinant is not established as one')
            x,y=a.inv(mat,x,y);key=tuple(a.frozen(t) for t in (n,x,y));self.calls.append(key)
            lo=a.atom(('call',0,*key));hi=a.atom(('call',1,*key));return a.mat(mat,lo,hi)
        if op=='i64.extend_i32_u':return self.eval(e[1],env),{}
        if op=='i32.wrap_i64':return self.eval(e[1],env)[0]
        if op in ('i64.or','i64.and','i64.xor'):
            x=self.eval(e[1],env);y=self.eval(e[2],env)
            return tuple(a.operation(op[4:],u,v) for u,v in zip(x,y))
        if op in ('i64.shl','i64.shr_u'):
            x=self.eval(e[1],env);shift=self.eval(e[2],env)
            if shift!=(a.const(32),{}):raise p.Unsupported('only pair half shift')
            return ({},x[0]) if op=='i64.shl' else (x[1],{})
        if op.startswith('i32.') and op[4:] in ('add','sub','mul','xor','or','and','rotl','shl','shr_u','eqz'):
            vals=[self.eval(t,env) for t in e[1:]]
            return a.operation(op[4:],*vals)
        raise p.Unsupported('symbolic operation '+op)

def analyse(src):
    t0=time.perf_counter();mod=p.read(src);t1=time.perf_counter()
    if any(x[0] not in ('type','func','export') for x in mod[1:]):raise p.Unsupported('pure closed module')
    fs=[x for x in mod[1:] if x[0]=='func']
    if len(fs)!=2 or [x for x in mod[1:] if x[0]=='export']!=[['export','"run"',['func','1']]]:raise p.Unsupported('ABI')
    params=[t for x in fs[0][1:] if x[0]=='param' for t in x[1:]]
    if params not in (['i32']*3,['i32']*7):raise p.Unsupported('work parameters')
    for f in fs:
        if [x for x in f[1:] if x[0]=='result']!=[['result','i64']]:raise p.Unsupported('pair result required')
    if [t for x in fs[1][1:] if x[0]=='param' for t in x[1:]]!=['i32']*3:raise p.Unsupported('wrapper parameters')
    a=Algebra();n,x,y=[a.var(t) for t in ('n','x','y')];mat=[a.var(t) for t in ('a','b','c','d')]
    ev=Evaluator(a,len(params)==7);inp=[n,*a.mat(mat,x,y),*mat] if ev.encoded else [n,x,y]
    env=ev.locals(fs[0],inp);body=ev.body(fs[0])
    if len(body)!=1 or body[0][0]!='if':raise p.Unsupported('top-level recursive conditional')
    branch=body[0];parts=[v for v in branch[1:] if v[0]!='result']
    cond=ev.eval(parts[0],env)
    if cond==a.operation('eqz',n):basepart,recpart=parts[1][1:],parts[2][1:]
    elif cond==n:recpart,basepart=parts[1][1:],parts[2][1:]
    else:raise p.Unsupported('depth test')
    base=ev.sequence(basepart,list(env))
    if ev.calls:raise p.Unsupported('base case must not recurse')
    step=ev.sequence(recpart,list(env))
    if ev.encoded:base=a.inv(mat,*base);step=a.inv(mat,*step)
    if len(ev.calls)!=1 or dict(ev.calls[0][0])!=a.plus(n,a.const(1),-1):raise p.Unsupported('one strictly decreasing recursive call')
    key=ev.calls[0]
    outputs=[*base,*step,dict(key[1]),dict(key[2])]
    for value in outputs:
        if any(a.atoms[i][0]=='var' and a.atoms[i][1] in ('a','b','c','d') for i in a.reachable(value)):raise p.Unsupported('frame parameter did not cancel')
    before=len(ev.calls);wr=ev.sequence(ev.body(fs[1]),ev.locals(fs[1],[n,x,y]))
    expected=tuple(a.frozen(t) for t in (a.operation('and',n,a.const(31)),x,y))
    if len(ev.calls)!=before+1 or ev.calls[-1]!=expected:raise p.Unsupported('wrapper must call once at bounded depth and identity value')
    if wr!=tuple(a.atom(('call',i,*expected)) for i in (0,1)):raise p.Unsupported('wrapper does not decode the result')
    # The one recursive call is emitted once; its two projections share q.
    call='(call $work '+' '.join(a.emit(dict(v)) for v in key)+')'
    text=f'''(module (func $work (param $n i32) (param $x i32) (param $y i32) (result i64) (local $q i64)
    (if (result i64) (i32.eqz {p.g('n')}) (then {p.pack(*(a.emit(t) for t in base))})
    (else {p.setv('q',call)} {p.pack(*(a.emit(t) for t in step))})))
    (func (export "run") (param $n i32) (param $x i32) (param $y i32) (result i64)
      (call $work (i32.and {p.g('n')} {p.c(31)}) {p.g('x')} {p.g('y')})))'''
    t2=time.perf_counter()
    return text,dict(read_validate_ms=(t1-t0)*1000,summary_ms=(t2-t1)*1000,polynomial_products=a.products,peak_polynomial_terms=a.terms_peak,interned_atoms=len(a.atoms),function_summaries=1,stack_unfoldings=0)
def recover(src,dst):
    text,stats=analyse(src);t=time.perf_counter();p.compile(text,dst);stats['compile_validate_ms']=(time.perf_counter()-t)*1000;return stats
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('source');ap.add_argument('output');args=ap.parse_args();print(json.dumps(recover(args.source,args.output)))
