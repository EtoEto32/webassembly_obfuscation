"""Boolean Wasm -> probabilistic bisimulation graph; exact recovery included."""
import argparse,functools,importlib.util,json,math,random,struct,tempfile,time
from fractions import Fraction as F
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
spec=importlib.util.spec_from_file_location('square_common',HERE.parent/'isotope-swizzle/prototype.py')
q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)

def expr(t):
    if t[0]=='bit':
        e=f'(i32.and (i32.shr_u (local.get 0) (i32.const {t[1]})) (i32.const 1))'
        return f'(i32.xor {e} (i32.const 1))' if t[2] else e
    return f'(i32.{t[0]} {expr(t[1])} {expr(t[2])})'
def plain(t):return '(module (func (export "run") (param i32) (result i32) '+expr(t)+'))'
def source(src):
    m=q.read(src)
    if any(e[0] not in ('type','func','export') for e in m[1:]):raise ValueError('pure source only')
    fs=[e for e in m[1:] if e[0]=='func'];es=[e for e in m[1:] if e[0]=='export']
    if len(fs)!=1 or es!=[['export','"run"',['func','0']]]:raise ValueError('single run')
    f=fs[0]
    if [e for e in f[1:] if e[0]=='param']!=[['param','i32']] or [e for e in f[1:] if e[0]=='result']!=[['result','i32']]:raise ValueError('signature')
    body=[e for e in f[1:] if e[0] not in ('type','param','result')]
    if len(body)!=1:raise ValueError('expression required')
    def parse(e):
        neg=0
        if e[0]=='i32.xor' and e[2]==['i32.const','1']:neg=1;e=e[1]
        if e[0]=='i32.and' and e[2]==['i32.const','1']:
            x=e[1]
            if x[0]=='i32.shr_u' and x[1]==['local.get','0'] and x[2][0]=='i32.const' and 0<=int(x[2][1])<32:
                return ('bit',int(x[2][1]),neg)
        if not neg and e[0] in ('i32.and','i32.or'):return (e[0][4:],parse(e[1]),parse(e[2]))
        raise ValueError('unsupported Boolean source')
    return parse(body[0])

def graph(t,seed):
    labels=[];edges=[];cache={};group=0
    def color():
        nonlocal group
        group+=2;return group
    def node(label,children=None):
        i=len(labels);labels.append(label);edges.append(children if children is not None else [i,i]);return i
    def build(t):
        if t in cache:return cache[t]
        g=color()
        if t[0]=='bit':pair=(node((g,32,0)),node((g,t[1],1-t[2])))
        else:
            a,b=build(t[1]),build(t[2]);label=(g,32,0)
            if t[0]=='and':pair=(node(label,[a[0],b[0]]),node(label,[a[1],b[1]]))
            else:
                h=(color(),32,0)
                w=node(h,[a[0],b[0]]);x=node(h,[a[1],b[1]])
                y=node(h,[a[1],b[0]]);z=node(h,[a[0],b[1]])
                pair=(node(label,[w,x]),node(label,[y,z]))
        cache[t]=pair;return pair
    roots=build(t);n=len(labels)
    if n>192:raise ValueError('graph exceeds prototype bound')
    order=list(range(n));random.Random(seed).shuffle(order);idx={old:new for new,old in enumerate(order)}
    a=[[0]*n for _ in range(n)]
    for i,old in enumerate(order):
        for j in edges[old]:a[i][idx[j]]+=1
    return [labels[i] for i in order],a,tuple(idx[i] for i in roots)

def square(a):
    n=len(a);s=[[v+2*(i==j) for j,v in enumerate(row)] for i,row in enumerate(a)]
    return [[sum(s[i][k]*s[k][j] for k in range(n)) for j in range(n)] for i in range(n)]
def pack(labels,a,roots):
    n=len(labels)
    return struct.pack('<3I',n,*roots)+b''.join(struct.pack('<3I',*x) for x in labels)+bytes(v for row in a for v in row)
def unpack(data):
    n,u,v=struct.unpack_from('<3I',data)
    if not 2<=n<=192 or max(u,v)>=n:raise ValueError('header')
    labels=[struct.unpack_from('<3I',data,12+12*i) for i in range(n)]
    if any(bit>32 or flip>1 for base,bit,flip in labels):raise ValueError('label descriptor')
    off=12+12*n;a=[list(data[off+n*i:off+n*(i+1)]) for i in range(n)]
    if any(len(row)!=n for row in a):raise ValueError('short data')
    d=sum(a[0])
    if d not in (2,16) or any(sum(row)!=d for row in a):raise ValueError('constant stochastic denominator')
    return labels,a,(u,v)

def render(labels,a,roots):
    n=len(labels);data=pack(labels,a,roots);weights=12+12*n
    old=(len(data)+3)&~3;new=old+4*n;mass=new+4*n;pages=math.ceil((mass+4*n*n)/65536)
    g=lambda s:f'(local.get ${s})';c=lambda x:f'(i32.const {x})'
    add=lambda x,y:f'(i32.add {x} {y})';mul=lambda x,y:f'(i32.mul {x} {y})'
    index=lambda base,i:add(c(base),mul(i,c(4)))
    ld=lambda base,i:f'(i32.load {index(base,i)})'
    st=lambda base,i,v:f'(i32.store {index(base,i)} {v})'
    serial=iter(range(100))
    def loop(var,limit,body):
        k=next(serial)
        return f'(local.set ${var} {c(0)}) (block $end{k} (loop $loop{k} (br_if $end{k} (i32.ge_u {g(var)} {limit})) {body} (local.set ${var} {add(g(var),c(1))}) (br $loop{k})))'
    label_addr=add(c(12),mul(g('i'),c(12)))
    init=loop('i',g('n'),f'''(local.set $base (i32.load {label_addr}))
      (local.set $bit (i32.load offset=4 {label_addr}))
      (local.set $flip (i32.load offset=8 {label_addr}))
      (if (i32.lt_u {g('bit')} {c(32)}) (then (local.set $base {add(g('base'),f'(i32.xor (i32.and (i32.shr_u {g("x")} {g("bit")}) {c(1)}) {g("flip")})')})))
      {st(new,g('i'),g('base'))} (local.set $a {g('i')})
      (block $foundlabel {loop('j',g('i'),f'(if (i32.eq {ld(new,g("j"))} {g("base")}) (then (local.set $a {ld(old,g("j"))}) (br $foundlabel)))')})
      {st(old,g('i'),g('a'))}''')
    massindex=add(mul(g('i'),g('n')),g('g'))
    fill=loop('i',g('n'),loop('k',g('n'),f'''(local.set $v (i32.load8_u {add(c(weights),add(mul(g('i'),g('n')),g('k')))}))
      (local.set $g {ld(old,g('k'))}) {st(mass,massindex,add(ld(mass,massindex),g('v')))}'''))
    compare=loop('g',g('n'),f'''(if (i32.ne {ld(mass,add(mul(g('i'),g('n')),g('g')))} {ld(mass,add(mul(g('j'),g('n')),g('g')))}) (then (br $nextcandidate)))''')
    candidate=loop('j',g('i'),f'''(block $nextcandidate
      (br_if $nextcandidate (i32.ne {ld(old,g('i'))} {ld(old,g('j'))})) {compare}
      (local.set $a {ld(new,g('j'))}) (br $foundclass))''')
    classify=loop('i',g('n'),f'''(local.set $a {g('i')}) (block $foundclass {candidate})
      {st(new,g('i'),g('a'))}
      (local.set $changed (i32.or {g('changed')} (i32.ne {g('a')} {ld(old,g('i'))})))''')
    token='"'+''.join('\\%02x'%b for b in data)+'"'
    return f'''(module (memory {pages} {pages}) (data (i32.const 0) {token})
      (func (export "run") (param $x i32) (result i32)
        (local $n i32) (local $i i32) (local $j i32) (local $k i32) (local $g i32)
        (local $v i32) (local $a i32) (local $base i32) (local $bit i32) (local $flip i32)
        (local $changed i32) (local $iter i32)
        (local.set $n (i32.load (i32.const 0))) {init}
        (block $stable (loop $refine
          (memory.fill {c(mass)} {c(0)} {c(4*n*n)}) {fill}
          (local.set $changed {c(0)}) {classify}
          (memory.copy {c(old)} {c(new)} {c(4*n)})
          (br_if $stable (i32.eqz {g('changed')}))
          (local.set $iter {add(g('iter'),c(1))})
          (br_if $refine (i32.lt_u {g('iter')} {g('n')}))))
        (i32.eq {ld(old,'(i32.load (i32.const 4))')} {ld(old,'(i32.load (i32.const 8))')})))'''

def transform(src,dst,mode,seed):
    start=time.perf_counter();t=source(src);labels,a,roots=graph(t,seed)
    if mode=='square':a=square(a)
    elif mode=='bad-square':a=[[sum(a[i][k]*a[k][j] for k in range(len(a))) for j in range(len(a))] for i in range(len(a))]
    elif mode!='base':raise ValueError('mode')
    q.compile(render(labels,a,roots),dst)
    return {'milliseconds':(time.perf_counter()-start)*1000,'nodes':len(a),'nonzero_edges':sum(v!=0 for row in a for v in row),'bytes':Path(dst).stat().st_size}

def string_bytes(token):
    s=token[1:-1];out=bytearray();i=0
    while i<len(s):
        if s[i]=='\\':
            if i+2<len(s) and all(c in '0123456789abcdefABCDEF' for c in s[i+1:i+3]):out.append(int(s[i+1:i+3],16));i+=3
            else:out.append({'t':9,'n':10,'r':13,'"':34,"'":39,'\\':92}[s[i+1]]);i+=2
        else:out.extend(s[i].encode('utf-8'));i+=1
    return out
def extracted(src):
    m=q.read(src)
    if any(e[0] not in ('type','func','export','memory','data') for e in m[1:]):raise ValueError('unsupported module')
    data=bytearray(65536*4)
    for e in m[1:]:
        if e[0]!='data':continue
        if not isinstance(e[1],list) or e[1][0]!='i32.const':raise ValueError('active constant data only')
        offset=int(e[1][1]);chunk=b''.join(string_bytes(s) for s in e[2:])
        if offset<0 or offset+len(chunk)>len(data):raise ValueError('data range')
        data[offset:offset+len(chunk)]=chunk
    labels,a,roots=unpack(data)
    # Exact optimized-profile check: a valid-looking table alone is insufficient.
    (ROOT/'tmp').mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=ROOT/'tmp') as folder:
        d=Path(folder);expected=d/'expected.wasm';q.compile(render(labels,a,roots),expected)
        for p,name in ((expected,'expected-opt'),(src,'actual-opt')):q.w.tool('wasm-opt',[p,'--enable-bulk-memory','-O3','--strip-debug','-o',d/(name+'.wasm')])
        if (d/'expected-opt.wasm').read_bytes()!=(d/'actual-opt.wasm').read_bytes():raise ValueError('unsupported evaluator profile')
    return labels,a,roots

def root_matrix(qmatrix):
    n=len(qmatrix);order=[];seen=set();active=set()
    def visit(i):
        if i in active:raise ValueError('off-diagonal cycle')
        if i in seen:return
        active.add(i)
        for j,w in enumerate(qmatrix[i]):
            if w and j!=i:visit(j)
        active.remove(i);seen.add(i);order.append(i)
    for i in range(n):visit(i)
    order.reverse();qtri=[[F(qmatrix[i][j],16) for j in order] for i in order]
    l=[[F(0) for _ in range(n)] for _ in range(n)]
    for i in range(n):
        if qtri[i][i] not in (F(1,4),F(1)):raise ValueError('diagonal outside profile')
        l[i][i]=F(1,2) if qtri[i][i]==F(1,4) else F(1)
    for width in range(1,n):
        for i in range(n-width):
            j=i+width;l[i][j]=(qtri[i][j]-sum(l[i][k]*l[k][j] for k in range(i+1,j)))/(l[i][i]+l[j][j])
    a=[[0]*n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            value=4*l[i][j]-2*(i==j)
            if value.denominator!=1 or not 0<=value<=2:raise ValueError('not a binary-branch source')
            a[order[i]][order[j]]=int(value)
    if any(sum(row)!=2 for row in a) or square(a)!=qmatrix:raise ValueError('root certificate failed')
    return a

class BDD:
    def __init__(self):self.nodes=[None,None];self.unique={};self.memo={}
    def mk(self,v,lo,hi):
        if lo==hi:return lo
        key=(v,lo,hi)
        if key not in self.unique:self.unique[key]=len(self.nodes);self.nodes.append(key)
        return self.unique[key]
    def op(self,op,a,b):
        key=(op,min(a,b),max(a,b))
        if key in self.memo:return self.memo[key]
        if a<2 and b<2:return (a&b) if op=='and' else (a|b)
        v=min(self.nodes[x][0] for x in (a,b) if x>=2)
        def child(x,h):return self.nodes[x][1+h] if x>=2 and self.nodes[x][0]==v else x
        r=self.mk(v,self.op(op,child(a,0),child(b,0)),self.op(op,child(a,1),child(b,1)))
        self.memo[key]=r;return r
    def wasm(self,root):
        used=[];seen=set()
        def walk(i):
            if i<2 or i in seen:return
            seen.add(i);v,lo,hi=self.nodes[i];walk(lo);walk(hi);used.append(i)
        walk(root);idx={v:i+1 for i,v in enumerate(used)}
        get=lambda x:f'(i32.const {x})' if x<2 else f'(local.get {idx[x]})'
        sets=[]
        for i in used:
            v,lo,hi=self.nodes[i];sets.append(f'(local.set {idx[i]} (select {get(hi)} {get(lo)} (i32.and (i32.shr_u (local.get 0) (i32.const {v})) (i32.const 1))))')
        return '(module (func (export "run") (param i32) (result i32) '+('(local '+' '.join(['i32']*len(used))+') ' if used else '')+' '.join(sets)+' '+get(root)+'))',len(used)

def decode(labels,a,roots):
    n=len(a);bdd=BDD();edges=[[j for j,w in enumerate(row) for _ in range(w)] for row in a]
    active=set()
    def label_bit(label,x):
        base,bit,flip=label;return base if bit==32 else base+(((x>>bit)&1)^flip)
    def label_eq(la,lb):
        variables=sorted({label[1] for label in (la,lb) if label[1]<32})
        def build(k,x):
            if k==len(variables):return int(label_bit(la,x)==label_bit(lb,x))
            v=variables[k];return bdd.mk(v,build(k+1,x),build(k+1,x|(1<<v)))
        return build(0,0)
    @functools.lru_cache(None)
    def eq(i,j):
        if i==j:return 1
        if (i,j) in active:raise ValueError('non-leaf recursive pair')
        lab=label_eq(labels[i],labels[j])
        if lab==0:return 0
        if edges[i]==[i,i] and edges[j]==[j,j]:return lab
        active.add((i,j));x,y=edges[i];u,v=edges[j]
        r=bdd.op('and',lab,bdd.op('or',bdd.op('and',eq(x,u),eq(y,v)),bdd.op('and',eq(x,v),eq(y,u))))
        active.remove((i,j));return r
    root=eq(*roots);return bdd,root,eq.cache_info().currsize

def recover(src,dst):
    start=time.perf_counter();labels,a,roots=extracted(src);read_ms=(time.perf_counter()-start)*1000
    t=time.perf_counter();den=sum(a[0]);base=root_matrix(a) if den==16 else a;root_ms=(time.perf_counter()-t)*1000
    t=time.perf_counter();bdd,r,pairs=decode(labels,base,roots);wat,count=bdd.wasm(r);decode_ms=(time.perf_counter()-t)*1000
    q.compile(wat,dst)
    return {'milliseconds':(time.perf_counter()-start)*1000,'profile_ms':read_ms,'root_ms':root_ms,'decode_ms':decode_ms,'pairs':pairs,'bdd_nodes':count,'denominator':den,'nodes':len(a)}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('command',choices=['transform','recover']);ap.add_argument('source');ap.add_argument('output');ap.add_argument('--mode',choices=['base','square','bad-square'],default='square');ap.add_argument('--seed',type=int,default=213071);a=ap.parse_args()
    print(json.dumps(transform(a.source,a.output,a.mode,a.seed) if a.command=='transform' else recover(a.source,a.output)))
