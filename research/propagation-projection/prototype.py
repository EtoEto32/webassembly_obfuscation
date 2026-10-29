"""Experimental bit-sliced unit-propagation compiler. Established CNF/VE rules."""
import argparse, importlib.util, json, random, subprocess, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('pp_common',ROOT/'research/isotope-swizzle/prototype.py');q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
ZERO='(v128.const i32x4 0 0 0 0)';ONES='(v128.const i32x4 -1 -1 -1 -1)'
class Unsupported(ValueError):pass
def demand(ok,msg):
    if not ok:raise Unsupported(msg)
def header(n):return f'(module (memory (export "memory") 1 1) (global (export "arity") i32 (i32.const {n})) '
def source(n,ops):
    body=[f'(local.set {i} (v128.load (i32.const {16*i})))' for i in range(n)]
    for j,(op,a,b) in enumerate(ops):
        e=f'(v128.{op} (local.get {a})'+(')' if op=='not' else f' (local.get {b}))')
        body.append(f'(local.set {n+j} {e})')
    body.append(f'(v128.store (i32.const {16*n}) (local.get {n+len(ops)-1}))')
    return header(n)+f'(func (export "run") (local {" ".join(["v128"]*(n+len(ops)))}) '+ ' '.join(body)+'))'
def parse(src):
    m=q.read(src);gs=[x for x in m[1:] if x[0]=='global']
    demand(len(gs)==1 and gs[0][1]=='i32' and gs[0][2][0]=='i32.const','arity constant')
    n=int(gs[0][2][1]);demand(2<=n<=20,'2..20 inputs')
    fs=[x for x in m[1:] if x[0]=='func'];demand(len(fs)==1,'one function')
    body=[x for x in fs[0][1:] if isinstance(x,list) and x[0] not in ('type','local')]
    ops=[]
    demand(len(body)>n+1,'nonempty DAG')
    for j,e in enumerate(body[n:-1]):
        demand(e[:2]==['local.set',str(n+j)],'ordered local DAG')
        v=e[2];demand(v[0] in ('v128.and','v128.or','v128.xor','v128.not'),'bitwise only')
        op=v[0].split('.')[1];demand(len(v)==(2 if op=='not' else 3),'gate arity')
        demand(all(a[0]=='local.get' and 0<=int(a[1])<n+j for a in v[1:]),'earlier operands')
        ops.append((op,int(v[1][1]),int(v[2][1]) if op!='not' else 0))
    demand(len(ops)<=64,'64 gates maximum')
    # Exact normalized module comparison rejects side effects, imports, extra exports and altered loads.
    import tempfile
    # Compare text after removing only the explicit normalized type-use, which q.read inserts.
    expected=q.w.parse(source(n,ops))
    # Generate the canonical normalized module through the same WABT frontend in memory-backed temp files.
    with tempfile.TemporaryDirectory(dir=ROOT/'tmp',prefix='pp-profile-') as td:
        f=Path(td)/'profile.wasm';q.compile(q.w.emit(expected),f);canonical=q.read(f)
    demand(m==canonical,'exact closed vector profile');return n,ops
def cnf(n,ops):
    clauses=[]
    for j,(op,a,b) in enumerate(ops):
        a+=1;b+=1;z=n+j+1
        if op=='and':cs=[[-a,-b,z],[a,-z],[b,-z]]
        elif op=='or':cs=[[a,b,-z],[-a,z],[-b,z]]
        elif op=='xor':cs=[[-a,-b,-z],[a,b,-z],[a,-b,z],[-a,b,z]]
        else:cs=[[a,z],[-a,-z]]
        clauses.extend(cs)
    return normalize(clauses)
def normalize(cs):
    out=set()
    for c in cs:
        c=frozenset(c)
        if any(-x in c for x in c):continue
        demand(c,'empty clause')
        out.add(tuple(sorted(c)))
    return sorted(out)
def eliminate(cs,n,output):
    budget=(3*len(cs))//2;log=[]
    while True:
        choices=[]
        for x in sorted({abs(l) for c in cs for l in c} - set(range(1,n+1)) - {output}):
            pos=[c for c in cs if x in c];neg=[c for c in cs if -x in c]
            if len(pos)*len(neg)>budget*8:continue
            rs=normalize([(set(a)-{x}) | (set(b)-{-x}) for a in pos for b in neg])
            new=normalize([c for c in cs if x not in c and -x not in c]+rs)
            if len(new)>budget or max(map(len,new),default=0)>8:continue
            choices.append((sum(map(len,new)),len(new),x,new,len(rs)))
        if not choices:break
        _,_,x,new,nr=min(choices,key=lambda v:v[:3]);log.append(dict(variable=x,before=len(cs),after=len(new),resolvents=nr));cs=new
    return cs,log
def generate(n,cs,output):
    variables=sorted(set(range(1,n+1))|{abs(l) for c in cs for l in c}|{output});ids={v:i for i,v in enumerate(variables)}
    def loc(l,true=True):return 2*ids[abs(l)] + (0 if (l>0)==true else 1)
    sets=[]
    for i in range(n):
        sets += [f'(local.set {loc(i+1)} (v128.load (i32.const {16*i})))',f'(local.set {loc(-(i+1))} (v128.not (local.get {loc(i+1)})))']
    rng=random.Random(211029);order=list(cs);rng.shuffle(order);updates=[]
    for c in order:
        for l in c:
            terms=[f'(local.get {loc(x,False)})' for x in c if x!=l]
            value=terms[0] if terms else ONES
            for t in terms[1:]:value=f'(v128.and {value} {t})'
            target=loc(l);updates.append(f'(local.set {target} (v128.or (local.get {target}) {value}))')
    outt,outf=loc(output),loc(-output);counter=2*len(variables)
    finish=f'(i32.eqz (v128.any_true (v128.not (v128.or (local.get {outt}) (local.get {outf})))))'
    body=' '.join(sets)+f''' (loop
      {' '.join(updates)}
      (if {finish} (then
        (if (v128.any_true (v128.and (local.get {outt}) (local.get {outf}))) (then (unreachable)))
        (v128.store (i32.const {16*n}) (local.get {outt})) (return)))
      (local.set {counter} (i32.add (local.get {counter}) (i32.const 1)))
      (if (i32.ge_u (local.get {counter}) (i32.const {len(variables)+1})) (then (unreachable))) (br 0))'''
    return header(n)+f'(func (export "run") (local {" ".join(["v128"]*(2*len(variables)))}) (local i32) {body}))',dict(variables=len(variables),clauses=len(cs),literal_occurrences=sum(map(len,cs)),maximum_width=max(map(len,cs)),pass_limit=len(variables)+1)
def transform(src,dst,mode):
    t=time.perf_counter();n,ops=parse(src);cs=cnf(n,ops);before=len(cs);log=[]
    demand(mode in ('cnf','project'),'mode')
    if mode=='project':cs,log=eliminate(cs,n,n+len(ops))
    wat,info=generate(n,cs,n+len(ops));q.compile(wat,dst)
    return dict(mode=mode,inputs=n,gates=len(ops),initial_clauses=before,eliminations=log,elapsed_ms=1000*(time.perf_counter()-t),**info)
def bdd_wat(n,truth):
    demand(len(truth)==1<<n and set(truth)<={0,1},'truth table')
    ids={};nodes=[];level=list(truth)
    for var in range(n):
        new=[]
        for low,high in zip(level[::2],level[1::2]):
            if low==high:new.append(low);continue
            key=(var,low,high)
            if key not in ids:ids[key]=len(nodes)+2;nodes.append(key)
            new.append(ids[key])
        level=new
    def value(i):return ZERO if i==0 else ONES if i==1 else f'(local.get {i-2})'
    lines=[f'(local.set {i} (v128.bitselect {value(hi)} {value(lo)} (v128.load (i32.const {16*var}))))' for i,(var,lo,hi) in enumerate(nodes)]
    lines.append(f'(v128.store (i32.const {16*n}) {value(level[0])})')
    return header(n)+f'(func (export "run") '+(f'(local {" ".join(["v128"]*len(nodes))})' if nodes else '')+' '.join(lines)+'))',len(nodes)
def recover(src,dst):
    t=time.perf_counter();r=json.loads(subprocess.check_output(['node',str(Path(__file__).with_name('query.cjs')),str(src)],text=True,timeout=60))
    wat,nodes=bdd_wat(r['arity'],r.pop('truth'));q.compile(wat,dst)
    return dict(**r,bdd_nodes=nodes,elapsed_ms=1000*(time.perf_counter()-t),scope='known bitwise-independent ABI; full Boolean truth table, not arbitrary Wasm equivalence')
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('command',choices=['transform','recover']);ap.add_argument('source',type=Path);ap.add_argument('output',type=Path);ap.add_argument('--mode',choices=['cnf','project'],default='project');a=ap.parse_args()
    print(json.dumps(transform(a.source,a.output,a.mode) if a.command=='transform' else recover(a.source,a.output)))
