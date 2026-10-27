"""Small encoded-table experiment. Known encodings; no novelty/security claim."""
import argparse, hashlib, importlib.util, json, random, subprocess, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('swizzle_common', ROOT/'research/connectivity-elimination/prototype.py')
w=importlib.util.module_from_spec(s);s.loader.exec_module(w)
BIN=ROOT/'.tools/binaryen-version_133/bin'
MASK=[15]*16
class Unsupported(ValueError):pass
def save(f,x):Path(f).write_text(json.dumps(x,indent=2,ensure_ascii=False),encoding='utf-8')
def digest(f):return hashlib.sha256(Path(f).read_bytes()).hexdigest()
def tool(name,args):
    r=subprocess.run([str(BIN/(name+'.exe')),*map(str,args)],capture_output=True,text=True,timeout=60)
    if r.returncode:raise RuntimeError(r.stderr)
    return r.stdout
def compile(text,dst):
    dst=Path(dst)
    if dst.exists() or dst.with_suffix('.wat').exists():raise FileExistsError(dst)
    dst.parent.mkdir(parents=True,exist_ok=True);dst.with_suffix('.wat').write_text(text,encoding='utf-8')
    w.tool('wat2wasm',[dst.with_suffix('.wat'),'-o',dst]);w.tool('wasm-validate',[dst])
def read(f):
    w.tool('wasm-validate',[f]);return w.parse(w.tool('wasm2wat',[f,'--fold-exprs','--no-debug-names']))
def walk(e):
    if isinstance(e,list):
        yield e
        for x in e[1:]:yield from walk(x)
def vc(xs):return ['v128.const','i8x16',*map(str,xs)]
def vconst(e):
    if not isinstance(e,list) or e[:1]!=['v128.const']:raise Unsupported('not a vector constant')
    size={'i8x16':1,'i16x8':2,'i32x4':4,'i64x2':8}.get(e[1])
    if size is None:raise Unsupported('integer vector constant required')
    out=[]
    for x in e[2:]:out.extend((int(x,0)&((1<<(8*size))-1)).to_bytes(size,'little'))
    if len(out)!=16:raise Unsupported('vector width')
    return out
def inv(a):
    if sorted(a)!=list(range(16)):raise Unsupported('not a permutation')
    return [a.index(x) for x in range(16)]
def swiz(a,x):return ['i8x16.swizzle',vc(a),x]
def masked(e):return ['v128.and',e,vc(MASK)]
def op_eval(op,a,b):return {'add':lambda:(a+b)&15,'sub':lambda:(a-b)&15,'xor':lambda:a^b}[op]()
def operation(op,a,b):return masked([{'add':'i8x16.add','sub':'i8x16.sub','xor':'v128.xor'}[op],a,b])
def source_text(tree):
    def emit(t):
        if isinstance(t,int):return ['i32x4.splat',['local.get',str(t)]]
        return operation(t[0],emit(t[1]),emit(t[2]))
    return w.emit(['module',['func',['export','"run"'],['param','i32','i32','i32'],['result','i32'],['i32x4.extract_lane','0',emit(tree)]]])
def parse_source(m):
    if any(x[0] not in ('type','func','export') for x in m[1:]):raise Unsupported('pure module required')
    fs=[x for x in m[1:] if x[0]=='func'];es=[x for x in m[1:] if x[0]=='export']
    if len(fs)!=1 or es!=[['export','"run"',['func','0']]]:raise Unsupported('one exported function required')
    f=fs[0]
    if [x for x in f[1:] if isinstance(x,list) and x[0]=='param']!=[['param','i32','i32','i32']]:raise Unsupported('three i32 inputs required')
    if [x for x in f[1:] if isinstance(x,list) and x[0]=='result']!=[['result','i32']]:raise Unsupported('i32 result required')
    body=[x for x in f[1:] if not isinstance(x,list) or x[0] not in ('type','param','result')]
    if len(body)!=1 or body[0][:2]!=['i32x4.extract_lane','0']:raise Unsupported('extract lane source profile')
    def leaf(e):
        if e[:1]==['i32x4.splat'] and e[1][:1]==['local.get'] and len(e)==2 and len(e[1])==2:
            n=int(e[1][1])
            if 0<=n<3:return n
        if len(e)!=3 or e[0]!='v128.and':raise Unsupported('nibble mask required')
        a,b=e[1:]
        if a[0]=='v128.const':a,b=b,a
        if vconst(b)!=MASK or len(a)!=3 or a[0] not in ('i8x16.add','i8x16.sub','v128.xor'):raise Unsupported('source operation')
        return ({'i8x16.add':'add','i8x16.sub':'sub','v128.xor':'xor'}[a[0]],leaf(a[1]),leaf(a[2]))
    tree=leaf(body[0][2])
    if isinstance(tree,int):raise Unsupported('at least one operation required')
    return tree
def table_expr(t,a,b):
    e=swiz(t[0],a)
    for i in range(1,16):e=['v128.bitselect',swiz(t[i],a),e,['i8x16.eq',b,vc([i]*16)]]
    return e
def transform(src,dst,mode='table',seed=7):
    t0=time.perf_counter();tree=parse_source(read(src));t1=time.perf_counter();r=random.Random(seed);cache={};sets=[];perms={}
    def build(t):
        if t in cache:return cache[t]
        p=list(range(16));r.shuffle(p)
        if isinstance(t,int):e=swiz(p,masked(['i32x4.splat',['local.get',str(t)]]))
        else:
            i,j=build(t[1]),build(t[2]);a=['local.get',str(i)];b=['local.get',str(j)];pa,pb=inv(perms[i]),inv(perms[j])
            if mode=='decode':e=swiz(p,operation(t[0],swiz(pa,a),swiz(pb,b)))
            elif mode=='table':e=table_expr([[p[op_eval(t[0],pa[x],pb[y])] for x in range(16)] for y in range(16)],a,b)
            else:raise Unsupported('mode')
        i=3+len(sets);cache[t]=i;perms[i]=p;sets.append(['local.set',str(i),e]);return i
    if mode=='plain':m=source_text(tree)
    else:
        i=build(tree);m=w.emit(['module',['func',['export','"run"'],['param','i32','i32','i32'],['result','i32'],['local',*(['v128']*len(sets))],*sets,['i32x4.extract_lane','0',swiz(inv(perms[i]),['local.get',str(i)])]]])
    t2=time.perf_counter();compile(m,dst);t3=time.perf_counter()
    return dict(mode=mode,seed=seed,read_ms=(t1-t0)*1000,build_ms=(t2-t1)*1000,compile_validate_ms=(t3-t2)*1000,transform_ms=(t3-t0)*1000)

def normalize(t):
    """t[row=b][col=a]. No generation seed, original operation, or encodings."""
    if len(t)!=16 or any(len(row)!=16 or sorted(row)!=list(range(16)) for row in t):raise Unsupported('not Latin rows')
    if any(sorted(t[b][a] for b in range(16))!=list(range(16)) for a in range(16)):raise Unsupported('not Latin columns')
    c=t[0];r=[t[b][0] for b in range(16)];ci,ri=inv(c),inv(r);e=t[0][0]
    # Output-label loop: x*y = T(C^-1(x), R^-1(y)).
    g=[[t[ri[y]][ci[x]] for y in range(16)] for x in range(16)]
    if any(g[e][x]!=x or g[x][e]!=x for x in range(16)):raise AssertionError('identity')
    checks=0
    for x in range(16):
        for y in range(16):
            for z in range(16):
                checks+=1
                if g[g[x][y]][z]!=g[x][g[y][z]]:raise Unsupported('nonassociative principal loop')
    if any(g[x][y]!=g[y][x] for x in range(16) for y in range(16)):raise Unsupported('noncommutative group')
    coord=None;op=None
    for gen in range(16):
        seq=[];x=e
        for k in range(16):seq.append(x);x=g[x][gen]
        if len(set(seq))==16 and x==e:coord=inv(seq);op='add';break
    if coord is None and all(g[x][x]==e for x in range(16)):
        d={e:0};bit=1
        while len(d)<16:
            gen=next(x for x in range(16) if x not in d)
            for x,v in list(d.items()):d[g[x][gen]]=v|bit
            bit<<=1
        coord=[d[x] for x in range(16)];op='xor'
    if coord is None:raise Unsupported('group outside C16/C2^4 profile')
    pa=[coord[c[x]] for x in range(16)];pb=[coord[r[y]] for y in range(16)];out=inv(coord)
    if any(out[op_eval(op,pa[x],pb[y])]!=t[y][x] for x in range(16) for y in range(16)):raise AssertionError('recovery witness failed')
    return dict(op=op,left=pa,right=pb,output=out,associativity_checks=checks,verification_pairs=256)
def extract(e):
    """Recognize full 16-row mux. Conservative syntactic profile, raw/O3 checked."""
    rows={};a=None;b=None;cur=e
    while isinstance(cur,list) and cur[:1]==['v128.bitselect'] and len(cur)==4:
        row,prev,cond=cur[1:]
        if row[:1]!=['i8x16.swizzle'] or len(row)!=3 or cond[:1]!=['i8x16.eq'] or len(cond)!=3:raise Unsupported('not table mux')
        y,k=cond[1:]
        if y[0]=='v128.const':y,k=k,y
        ix=vconst(k)
        if len(set(ix))!=1 or not 1<=ix[0]<16 or ix[0] in rows:raise Unsupported('row selector')
        if a is None:a,b=row[2],y
        if a!=row[2] or b!=y:raise Unsupported('inconsistent operands')
        rows[ix[0]]=vconst(row[1]);cur=prev
    if len(rows)!=15 or cur[:1]!=['i8x16.swizzle'] or cur[2]!=a:raise Unsupported('not complete table')
    rows[0]=vconst(cur[1]);return [rows[i] for i in range(16)],a,b
def ssa(m):
    """Hoist pure local assignments in Wasm evaluation order; preserve versions."""
    fs=[x for x in m[1:] if x[0]=='func'];es=[x for x in m[1:] if x[0]=='export']
    if len(fs)!=1 or es!=[['export','"run"',['func','0']]]:raise Unsupported('one run function')
    f=fs[0];decl=[x for x in f[1:] if isinstance(x,list) and x[0] in ('type','param','result')]
    if [x for x in decl if x[0]=='param']!=[['param','i32','i32','i32']]:raise Unsupported('lowering inputs')
    if [x for x in decl if x[0]=='result']!=[['result','i32']]:raise Unsupported('lowering result')
    locals_=[t for e in f[1:] if isinstance(e,list) and e[0]=='local' for t in e[1:]]
    if any(t!='v128' for t in locals_):raise Unsupported('only vector locals')
    env={i:vc([0]*16) for i in range(3,3+len(locals_))};sets=[]
    def expr(e):
        if not isinstance(e,list):return e
        if e[0]=='local.get':
            i=int(e[1]);return e if i<3 else env[i]
        if e[0] in ('local.set','local.tee'):
            v=expr(e[2]);i=3+len(sets);sets.append(['local.set',str(i),v]);env[int(e[1])]=['local.get',str(i)]
            return env[int(e[1])] if e[0]=='local.tee' else None
        return [expr(x) for x in e]
    results=[]
    for e in f[1:]:
        if isinstance(e,list) and e[0] in ('type','param','result','local'):continue
        v=expr(e)
        if v is not None:results.append(v)
    if len(results)!=1 or results[0][:2]!=['i32x4.extract_lane','0']:raise Unsupported('one final extract')
    nf=['func',*decl]
    if sets:nf.append(['local',*(['v128']*len(sets))])
    nf.extend(sets+results)
    return [m[0],*[nf if x is f else x for x in m[1:]]],{int(e[1]):e[2] for e in sets}
def lower(src,dst=None):
    t0=time.perf_counter();m=read(src);t1=time.perf_counter();stats=[]
    # Only pure numeric modules; reject effects, calls, and traps outside this profile.
    allowed=set('module type func export param result local local.get local.set local.tee i32x4.splat i32x4.extract_lane v128.const v128.and v128.or v128.xor v128.not v128.bitselect i8x16.swizzle i8x16.eq i8x16.add i8x16.sub'.split())
    if any(e[0] not in allowed for e in walk(m)):raise Unsupported('lowering module profile')
    m,defs=ssa(m);ranges={}
    def nibble(e):
        if e[0]=='local.get':
            i=int(e[1])
            if i<3:return False
            if i not in ranges:ranges[i]=nibble(defs[i])
            return ranges[i]
        if e[0]=='v128.const':return max(vconst(e))<16
        if e[0]=='i8x16.swizzle' and e[1][0]=='v128.const':return max(vconst(e[1]))<16
        if e[0]=='v128.and':return any(nibble(x) for x in e[1:])
        if e[0] in ('v128.or','v128.xor'):return all(nibble(x) for x in e[1:])
        if e[0]=='v128.bitselect':return all(nibble(x) for x in e[1:3])
        return False
    def rec(e):
        if not isinstance(e,list):return e
        if e[:1]==['v128.bitselect']:
            try:t,a,b=extract(e)
            except Unsupported:pass
            else:
                if not nibble(a) or not nibble(b):raise Unsupported('table inputs not proven nibble range')
                s=normalize(t);stats.append(s);return swiz(s['output'],operation(s['op'],swiz(s['left'],rec(a)),swiz(s['right'],rec(b))))
        return [rec(x) for x in e]
    m=rec(m);t2=time.perf_counter()
    if dst is not None:compile(w.emit(m),dst)
    return dict(read_ms=(t1-t0)*1000,normalize_rewrite_ms=(t2-t1)*1000,tables=len(stats),groups=[s['op'] for s in stats],associativity_checks=sum(s['associativity_checks'] for s in stats),verification_pairs=sum(s['verification_pairs'] for s in stats))
def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='cmd',required=True)
    a=sub.add_parser('transform');a.add_argument('source');a.add_argument('output');a.add_argument('--mode',choices=['plain','decode','table'],default='table');a.add_argument('--seed',type=int,default=7)
    a=sub.add_parser('lower');a.add_argument('source');a.add_argument('output')
    v=p.parse_args();print(json.dumps(transform(v.source,v.output,v.mode,v.seed) if v.cmd=='transform' else lower(v.source,v.output)))
if __name__=='__main__':main()
