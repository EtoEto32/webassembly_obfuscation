"""Known-family recovery from Wasm alone. No circuit/source/seed metadata input."""
import copy,itertools,json,statistics,sys,time
from pathlib import Path
from isolate import q
MASK=0xffffffff
class Unsupported(ValueError):pass
def demand(ok,msg):
    if not ok:raise Unsupported(msg)
def args(e):return [x for x in e[1:] if isinstance(x,list)]
def offset(e):return next((int(x[7:],0) for x in e[1:] if isinstance(x,str) and x.startswith('offset=')),0)
def integer(e):
    demand(e[0]=='i32.const','constant required');return int(e[1],0)&MASK
def normalize(d):return {k:v&MASK for k,v in d.items() if v&MASK}
def add(a,b,sign=1):
    d=dict(a)
    for k,v in b.items():d[k]=d.get(k,0)+sign*v
    return normalize(d)
def mul(a,b):
    d={}
    for x,v in a.items():
        for y,w in b.items():k=tuple(sorted(x+y));d[k]=d.get(k,0)+v*w
    return normalize(d)
def polynomial(e):
    op=e[0]
    if op=='c':return {():e[1]} if e[1] else {}
    if op in ('bit','load'):return {(e,):1}
    if op in ('add','sub'):return add(polynomial(e[1]),polynomial(e[2]),1 if op=='add' else -1)
    if op=='mul':return mul(polynomial(e[1]),polynomial(e[2]))
    if op=='shl' and e[2][0]=='c':return mul(polynomial(e[1]),{():1<<(e[2][1]&31)})
    raise Unsupported('nonpolynomial gate '+str(e)[:100])
def support(p):return sorted({a for k in p for a in k})
def evaluate(p,values):
    result=0
    for term,c in p.items():
        for a in term:c*=values[a]
        result+=c
    return result&MASK
def valuation(x):return 32 if not x else (x&-x).bit_length()-1

def analyze(module):
    demand(all(x[0] in ('type','func','memory','global','export') for x in module[1:]),'closed module fields')
    demand([x for x in module[1:] if x[0]=='global']==[['global',['mut','i32'],['i32.const','0']]],'one initialized counter global')
    fs=[x for x in module[1:] if x[0]=='func'];demand(len(fs)==1,'isolated single helper required');f=fs[0]
    demand([x for x in f[1:] if isinstance(x,list) and x[0]=='param']==[['param','i32','i32','i32']],'three i32 parameters')
    body=[x for x in f[1:] if isinstance(x,list) and x[0] not in ('type','param','result','local')]
    demand(len(body)==6 and body[4][0]=='loop','one initialized loop and packing expression')
    counter=['global.set','0',['i32.add',['global.get','0'],['i32.const','1']]]
    demand(body[0]==counter,'counter effect')
    initial={int(x[1]):integer(x[2]) for x in body[1:3] if x[0]=='local.set'}
    demand(len(initial)==2 and body[3][0]=='memory.fill','buffer initialization')
    loop=body[4];stores=[]
    for e in loop[1:]:
        if e[0]!='i32.store':break
        stores.append(e)
    demand(len(stores)>0 and len(stores)%2==0,'two store stages')
    n=len(stores)//2;first,updates=stores[:n],stores[n:]
    addr=lambda e:args(e)[0]
    fbase=integer(addr(first[0]))+offset(first[0])
    for i,e in enumerate(first):demand(integer(addr(e))+offset(e)==fbase+4*i,'contiguous F stage')
    ulocal=int(addr(updates[0])[1]);demand(addr(updates[0])[0]=='local.get' and ulocal in initial,'next buffer')
    vlocal=next(k for k in initial if k!=ulocal);vbase,ubase=initial[vlocal],initial[ulocal]
    for i,e in enumerate(updates):demand(addr(e)==['local.get',str(ulocal)] and offset(e)==4*i,'contiguous next stage')
    fill=args(body[3]);filladdr=initial.get(int(fill[0][1])) if fill[0][0]=='local.get' else integer(fill[0])
    demand(filladdr==vbase and integer(fill[1])==255 and integer(fill[2])==4*n,'initial buffer fill')
    ranges=sorted((b,b+4*n) for b in (vbase,fbase,ubase));demand(all(ranges[i][1]<=ranges[i+1][0] for i in range(2)),'disjoint buffers')
    mem=next(x for x in module[1:] if x[0]=='memory');demand(len(mem)==3 and mem[1]==mem[2] and ranges[-1][1]<=int(mem[1])*65536,'fixed valid memory')
    env={i:('param',i) for i in range(3)};env[vlocal]=('ptr','v');env[ulocal]=('ptr','u')
    def expression(e):
        op=e[0]
        if op=='i32.const':return ('c',integer(e))
        if op=='local.get':
            k=int(e[1]);demand(k in env,'uninitialized expression local');return env[k]
        if op=='local.tee':
            value=expression(e[2]);env[int(e[1])]=value;return value
        if op=='i32.load':
            a=expression(args(e)[0]);off=offset(e)
            if a==('ptr','v'):region='v';index=off//4;demand(off%4==0,'unaligned coordinate')
            elif a[0]=='c':region='f';index=(a[1]+off-fbase)//4;demand((a[1]+off-fbase)%4==0,'unaligned F coordinate')
            else:raise Unsupported('unknown load base')
            demand(0<=index<n,'coordinate bounds');return ('load',region,index)
        demand(op in ('i32.add','i32.sub','i32.mul','i32.and','i32.or','i32.xor','i32.shl','i32.shr_u'),'scalar operation '+op)
        a,b=(expression(x) for x in args(e));short=op[4:]
        if short=='shr_u' and a[0]=='param' and b[0]=='c' and b[1]&31==31:return ('bit',a[1],31)
        if short=='and':
            if a==('c',1):a,b=b,a
            if b==('c',1):
                if a[0]=='bit':return a
                if a[0]=='param':return ('bit',a[1],0)
                if a[0]=='shr_u' and a[1][0]=='param' and a[2][0]=='c':return ('bit',a[1][1],a[2][1]&31)
        return (short,a,b)
    gates=[];depths=[]
    for i,e in enumerate(first):
        p=polynomial(expression(args(e)[1]));atoms=support(p);demand(len(atoms)<=2,'Boolean gate arity')
        deps=[]
        for atom in atoms:
            if atom[0]=='load':demand(atom[1]=='v' and atom[2]<i,'source order');deps.append(atom[2])
            else:demand(atom[0]=='bit' and 0<=atom[1]<3 and 0<=atom[2]<32,'external Boolean input')
        table=[evaluate(p,dict(zip(atoms,bits))) for bits in itertools.product((0,1),repeat=len(atoms))]
        demand(all(x in (0,1) for x in table),'nonboolean root operation')
        gates.append(dict(atoms=atoms,table=table,deps=deps));depths.append(1+max([depths[j] for j in deps] or [0]))
    matrices=[]
    for i,e in enumerate(updates):
        poly=polynomial(expression(args(e)[1]));demand(() not in poly and all(len(k)==1 and k[0][0]=='load' for k in poly),'nonlinear residual update')
        cv={k[0][2]:c for k,c in poly.items() if k[0][1]=='v'};cf={k[0][2]:c for k,c in poly.items() if k[0][1]=='f'}
        for j in set(cv)|set(cf)|{i}:
            demand((cv.get(j,0)+cf.get(j,0))&MASK==int(i==j),'not a root-preserving residual')
            demand((cf.get(j,0)&1)==(1 if i==j else 0) if j>=i else True,'mixer order condition')
        matrices.append((cv,cf))
    # Validate actual pointer swap and count, including WABT's partly unfolded O3 stack.
    tail=loop[1+2*n:];tenv={vlocal:('v',),ulocal:('u',)};stack=[];branch=None
    def texpr(e):
        op=e[0]
        if op=='i32.const':return ('c',integer(e))
        if op=='local.get':return tenv.get(int(e[1]),('counter',int(e[1])))
        if op=='local.tee':v=texpr(e[2]);tenv[int(e[1])]=v;return v
        demand(op in ('i32.add','i32.lt_u'),'loop tail operation');return (op,*[texpr(x) for x in args(e)])
    for e in tail:
        if e[0]=='local.set':tenv[int(e[1])]=texpr(e[2]) if len(e)>2 else stack.pop()
        elif e[0]=='local.get':stack.append(texpr(e))
        elif e[0]=='br_if':demand(e[1]=='0' and branch is None,'loop branch');branch=texpr(e[2])
        else:raise Unsupported('loop tail '+e[0])
    demand(not stack and tenv[vlocal]==('u',) and tenv[ulocal]==('v',),'pointer swap')
    demand(branch and branch[0]=='i32.lt_u' and branch[1][0]=='i32.add' and branch[1][1][0]=='counter' and branch[1][2]==('c',1) and branch[2][0]=='c','counted loop')
    count_local=branch[1][1][1]
    written={int(x[1]) for e in stores for x in q.walk(e) if x[0] in ('local.set','local.tee')}
    demand(count_local>=3 and count_local not in initial and count_local not in written,'zero-initialized independent loop counter')
    demand(tenv.get(count_local)==branch[1],'counter persists across iterations')
    steps=branch[2][1];demand(steps>0,'iteration count')
    packed=expression(body[-1]);outputs={}
    def packing(e):
        if e[0]=='add':packing(e[1]);packing(e[2]);return
        if e==('c',0):return
        shift=0
        if e[0]=='shl':demand(e[2][0]=='c','output shift');shift=e[2][1]&31;e=e[1]
        demand(e[0]=='load' and e[1]=='v' and shift not in outputs,'disjoint bit packing');outputs[shift]=e[2]
    packing(packed);demand(sorted(outputs)==list(range(32)),'32 output bits')
    # Conservative precision propagation of the extracted residual coefficients.
    inf=10**6;precision=[0]*n;history=[]
    for t in range(1,32*n+1):
        fprecision=[min([precision[j] for j in g['deps']] or [inf]) for g in gates]
        precision=[min([precision[j]+valuation(c) for j,c in cv.items()]+[fprecision[j]+valuation(c) for j,c in cf.items()] or [inf]) for cv,cf in matrices]
        history.append(min(precision))
        if min(precision)>=32:break
    else:raise Unsupported('no finite precision certificate')
    bound=t;demand(steps>=bound+1,'insufficient bound to preserve every scratch buffer')
    return dict(gates=gates,outputs=outputs,n=n,depth=max(depths),steps=steps,bound=bound,state_bound=bound+1,buffers=[vbase,fbase,ubase],memory_pages=int(mem[1]),precision_min=history)

def emit(info,state=True):
    n=info['n'];code=[]
    def atom(a):
        return f'(local.get {3+a[2]})' if a[0]=='load' else f'(i32.and (i32.shr_u (local.get {a[1]}) (i32.const {a[2]})) (i32.const 1))'
    for i,g in enumerate(info['gates']):
        a=list(map(atom,g['atoms']));table=g['table']
        if len(a)==0:value=f'(i32.const {table[0]})'
        elif len(a)==1:value=a[0] if table==[0,1] else f'(i32.xor {a[0]} (i32.const 1))' if table==[1,0] else f'(i32.const {table[0]})'
        elif table in ([0,0,0,1],[0,1,1,0],[0,1,1,1]):value=f'(i32.{dict([((0,0,0,1),"and"),((0,1,1,0),"xor"),((0,1,1,1),"or")])[tuple(table)]} {a[0]} {a[1]})'
        else:
            terms=[]
            for bits,v in zip(itertools.product((0,1),repeat=2),table):
                if v:terms.append('(i32.and '+' '.join(x if bit else f'(i32.xor {x} (i32.const 1))' for x,bit in zip(a,bits))+')')
            value='(i32.const 0)'
            for x in terms:value=f'(i32.or {value} {x})'
        code.append(f'(local.set {3+i} {value})')
    if state:
        for base in info['buffers']:
            for i in range(n):code.append(f'(i32.store (i32.const {base+4*i}) (local.get {3+i}))')
    result='(i32.const 0)'
    for shift,index in sorted(info['outputs'].items()):result=f'(i32.or {result} (i32.shl (local.get {3+index}) (i32.const {shift})))'
    mem=f'(memory (export "memory") {info["memory_pages"]} {info["memory_pages"]})' if state else ''
    return f'''(module {mem} (global (export "evaluations") (mut i32) (i32.const 0))
      (func (export "run") (param i32 i32 i32) (result i32) (local {' '.join(['i32']*n)})
        (global.set 0 (i32.add (global.get 0) (i32.const 1))) {''.join(code)} {result}))'''

def recover(src,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=False);start=time.perf_counter();module=q.read(src);reader_ms=(time.perf_counter()-start)*1000
    times=[]
    for _ in range(11):
        t=time.perf_counter();info=analyze(module);times.append((time.perf_counter()-t)*1000)
    for mode,state in [('recovered-state',True),('recovered-io',False)]:q.compile(emit(info,state),out/(mode+'.wasm'))
    short=copy.deepcopy(module);loop=next(x for x in q.walk(short) if x[0]=='loop');branch=loop[-1];demand(branch[0]=='br_if','last branch');args(branch)[0][-1]=['i32.const',str(info['state_bound'])]
    q.compile(q.w.emit(short),out/'certified.wasm')
    q.save(out/'recovery.json',dict(source_sha256=q.digest(src),reader_ms=reader_ms,analysis_ms=times,analysis_ms_median=statistics.median(times),**info))
    return dict(gates=info['n'],depth=info['depth'],state_bound=info['state_bound'],reader_ms=reader_ms,analysis_ms_median=statistics.median(times))
if __name__=='__main__':print(json.dumps(recover(*sys.argv[1:])))
