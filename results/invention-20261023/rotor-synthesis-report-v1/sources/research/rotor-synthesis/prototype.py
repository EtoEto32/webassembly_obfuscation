"""Bounded whole-function synthesis into stateful switching graphs.

Experimental generator, not a claim that rotor-routing or SMT synthesis is new.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import struct
import sys
import tempfile
import time

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
w=load('rotor_wasm',HERE.parent/'connectivity-elimination/prototype.py')
old=sys.modules.get('prototype');sys.modules['prototype']=w
reader=load('rotor_reader',HERE.parent/'connectivity-elimination/recover.py')
if old is None:del sys.modules['prototype']
else:sys.modules['prototype']=old
MAGIC=0x31525452
MASK=0xffffffff

def evaluate(t,x):
    if t[0]=='var':return x>>t[1]&1
    if t[0]=='const':return bool(t[1])
    a,b=evaluate(t[1],x),evaluate(t[2],x)
    return {'and':lambda:a&b,'or':lambda:a|b,'xor':lambda:a^b}[t[0]]()

def simulate(r,x):
    d=r['d'];state=x;pc=0;trace=[]
    for step in range(r['bound']):
        if pc>=d:return pc-d,trace
        trace.append(pc);bit=state>>pc&1;state^=1<<pc;pc=r['edges'][pc][bit]
    return (pc-d if pc>=d else None),trace

def synthesize(n,truth,d,bound,timeout=20000,cyclic=False):
    if not (1<=n<=d<=16 and 1<=bound<=128):raise ValueError('Unsupported synthesis dimensions')
    sys.path.insert(0,str(ROOT/'.tools/encoding-synthesis-python'));import z3 as z
    started=time.perf_counter();s=z.Solver();s.set(timeout=timeout,random_seed=23)
    width=(d+1).bit_length()
    edges=[[z.BitVec('e%d_%d'%(v,b),width) for b in (0,1)] for v in range(d)]
    for pair in edges:
        for e in pair:s.add(z.ULE(e,d+1))
    visits=[[] for _ in range(d)]
    if cyclic:
        # Known SCC enlargement is not itself a security argument.
        for v in range(d):s.add(z.Or(edges[v][0]==(v+1)%d,edges[v][1]==(v+1)%d))
    for x,target in enumerate(truth):
        pcs=[z.BitVec('p%d_%d'%(x,k),width) for k in range(bound+1)]
        states=[z.BitVec('s%d_%d'%(x,k),d) for k in range(bound+1)]
        s.add(pcs[0]==0,states[0]==x)
        for k in range(bound):
            pc=pcs[k];bits=states[k];nxt=z.BitVecVal(d+1,width);flip=z.BitVecVal(0,d)
            for v in reversed(range(d)):
                nxt=z.If(pc==v,z.If(z.Extract(v,v,bits)==0,edges[v][0],edges[v][1]),nxt)
                flip=z.If(pc==v,z.BitVecVal(1<<v,d),flip);visits[v].append(pc==v)
            s.add(pcs[k+1]==z.If(z.UGE(pc,d),pc,nxt),states[k+1]==(bits^flip))
        s.add(pcs[-1]==d+int(target))
    # Every node must participate in at least one concrete input trace.
    for vs in visits:s.add(z.Or(*vs))
    status=s.check();elapsed=1000*(time.perf_counter()-started)
    report={'status':str(status),'synthesis_ms':elapsed,'n':n,'d':d,'bound':bound,'cyclic_constraint':cyclic,'timeout_ms':timeout}
    if status==z.sat:
        m=s.model();r={'n':n,'d':d,'bound':bound,'edges':[[m.eval(e).as_long() for e in pair] for pair in edges]}
        assert all(simulate(r,x)[0]==int(y) for x,y in enumerate(truth))
        report['graph']=r
    elif status==z.unknown:report['reason']=s.reason_unknown()
    return report

def save(wat,dest):
    dest=Path(dest);dest.parent.mkdir(parents=True,exist_ok=True)
    if dest.exists() or dest.with_suffix('.wat').exists():raise ValueError('Output already exists')
    dest.with_suffix('.wat').write_text(wat,encoding='utf8');w.tool('wat2wasm',[dest.with_suffix('.wat'),'-o',dest]);w.tool('wasm-validate',[dest])

def pack(r):return struct.pack('<'+'I'*(4+2*r['d']),MAGIC,r['n'],r['d'],r['bound'],*[e for p in r['edges'] for e in p])

def decode(data):
    magic,n,d,bound=struct.unpack_from('<IIII',data)
    if magic!=MAGIC or not(1<=n<=d<=16 and 1<=bound<=128):raise ValueError('Unsupported graph header')
    a=struct.unpack_from('<'+'I'*(2*d),data,16)
    if max(a)>d+1:raise ValueError('Invalid successor')
    return {'n':n,'d':d,'bound':bound,'edges':[list(a[2*i:2*i+2]) for i in range(d)]}

def render(r):
    n,d,bound=r['n'],r['d'],r['bound'];data=''.join('\\%02x'%b for b in pack(r));init=[]
    for v in range(d):init.append(f'(i32.store (i32.const {256+4*v}) '+(f'(local.get {v})' if v<n else '(i32.const 0)')+')')
    for v in range(d+2):init.append(f'(i32.store (i32.const {512+4*v}) (i32.const {-1 if v==0 else 0}))')
    clear=''.join(f'(i32.store (i32.const {768+4*v}) (i32.const 0))' for v in range(d))
    clear+=''.join(f'(i32.store (i32.const {768+4*v}) (i32.load (i32.const {512+4*v})))' for v in (d,d+1))
    return f'''(module (memory 1 1) (data (i32.const 0) "{data}")
      (func (export "run") (param {' '.join(['i32']*n)}) (result i32)
       (local $round i32) (local $v i32) (local $active i32) (local $rotor i32)
       (local $m0 i32) (local $m1 i32) (local $dst i32)
       {''.join(init)}
       (loop $roundloop
        {clear} (local.set $v (i32.const 0))
        (loop $vertices
         (local.set $active (i32.load offset=512 (i32.shl (local.get $v) (i32.const 2))))
         (local.set $rotor (i32.load offset=256 (i32.shl (local.get $v) (i32.const 2))))
         (local.set $m0 (i32.and (local.get $active) (i32.xor (local.get $rotor) (i32.const -1))))
         (local.set $m1 (i32.and (local.get $active) (local.get $rotor)))
         (i32.store offset=256 (i32.shl (local.get $v) (i32.const 2)) (i32.xor (local.get $active) (local.get $rotor)))
         (local.set $dst (i32.add (i32.const 768) (i32.shl (i32.load offset=16 (i32.shl (local.get $v) (i32.const 3))) (i32.const 2))))
         (i32.store (local.get $dst) (i32.or (i32.load (local.get $dst)) (local.get $m0)))
         (local.set $dst (i32.add (i32.const 768) (i32.shl (i32.load offset=20 (i32.shl (local.get $v) (i32.const 3))) (i32.const 2))))
         (i32.store (local.get $dst) (i32.or (i32.load (local.get $dst)) (local.get $m1)))
         (br_if $vertices (i32.lt_u (local.tee $v (i32.add (local.get $v) (i32.const 1))) (i32.const {d}))))
        (memory.copy (i32.const 512) (i32.const 768) (i32.const {4*(d+2)}))
        (br_if $roundloop (i32.lt_u (local.tee $round (i32.add (local.get $round) (i32.const 1))) (i32.const {bound}))))
       (i32.load (i32.const {512+4*(d+1)}))))'''

def read(binary):
    binary=Path(binary);w.tool('wasm-validate',[binary]);r=decode(reader.initial_memory(binary.read_bytes()))
    with tempfile.TemporaryDirectory(prefix='rotor-bind-') as folder:
        raw=Path(folder)/'raw.wasm';opt=Path(folder)/'opt.wasm';save(render(r),raw)
        if binary.read_bytes()!=raw.read_bytes():
            w.tool('wasm-opt',[raw,'-O3','--enable-bulk-memory','-o',opt])
            if binary.read_bytes()!=opt.read_bytes():raise ValueError('Not exact raw/O3 evaluator')
    return r

def recover(r):
    start=time.perf_counter();truth=[];steps=0
    for x in range(1<<r['n']):
        answer,trace=simulate(r,x);steps+=len(trace)
        if answer is None:raise ValueError('Graph not total within bound')
        truth.append(answer)
    coeff=list(truth)
    for i in range(r['n']):
        for x in range(1<<r['n']):
            if x>>i&1:coeff[x]^=coeff[x^(1<<i)]
    formula=('const',0)
    for mask,c in enumerate(coeff):
        if not c:continue
        term=('const',0xffffffff)
        for i in range(r['n']):
            if mask>>i&1:term=('and',term,('var',i))
        formula=('xor',formula,term)
    return formula,{'status':'recovered','analysis_ms':1000*(time.perf_counter()-start),'input_assignments':len(truth),'simulation_steps':steps,'anf_terms':sum(coeff)}

def symbolic_recover(r):
    """Exact Boolean symbolic simulation, without enumerating input assignments."""
    start=time.perf_counter();d,n=r['d'],r['n'];b=reader.BDD();rot=[b.mk(i,0,1) if i<n else 0 for i in range(d)];act=[1]+[0]*(d+1)
    for _ in range(r['bound']):
        new=[0]*d+act[d:]
        for v,(left,right) in enumerate(r['edges']):
            zero=b.binary('and',act[v],b.binary('xor',rot[v],1));one=b.binary('and',act[v],rot[v])
            rot[v]=b.binary('xor',rot[v],act[v]);new[left]=b.binary('or',new[left],zero);new[right]=b.binary('or',new[right],one)
        act=new
    if any(act[:d]) or b.binary('or',*act[d:])!=1 or b.binary('and',*act[d:])!=0:raise ValueError('Graph not total within bound')
    memo={0:('const',0),1:('const',0xffffffff)}
    def expr(i):
        if i not in memo:
            var,lo,hi=b.nodes[i];a,c=expr(lo),expr(hi);memo[i]=('xor',a,('and',('var',var),('xor',a,c)))
        return memo[i]
    t=expr(act[d+1]);return t,{'status':'recovered','analysis_ms':1000*(time.perf_counter()-start),'bdd_nodes':len(b.nodes),'input_assignments':0,'vertex_updates':d*r['bound']}

def transform(src,dest,d=6,bound=12,cyclic=False):
    start=time.perf_counter();n,name,t=w.source(src)
    if name!='"run"' or n>3 or n>d:raise ValueError('Early synthesis profile: run and at most 3 inputs')
    truth=[int(evaluate(t,x)) for x in range(1<<n)];result=synthesize(n,truth,d,bound,cyclic=cyclic)
    if result['status']=='sat':save(render(result['graph']),dest)
    result['elapsed_ms']=1000*(time.perf_counter()-start);return result

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['transform','recover']);ap.add_argument('input');ap.add_argument('output');ap.add_argument('--nodes',type=int,default=6);ap.add_argument('--bound',type=int,default=12);ap.add_argument('--cyclic',action='store_true');a=ap.parse_args()
    if a.mode=='transform':r=transform(a.input,a.output,a.nodes,a.bound,a.cyclic)
    else:
        g=read(a.input);t,r=recover(g);save(w.plain_wat(g['n'],'"run"',t),a.output)
    print(json.dumps(r,indent=2))
