"""Sink-free bulk-effect predication gate. Not a novelty/security claim."""
import argparse
import copy
import importlib.util
import json
from pathlib import Path
import time

spec=importlib.util.spec_from_file_location('extent_common',Path(__file__).resolve().parents[1]/'connectivity-elimination/prototype.py')
w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
PURE={'i32.add','i32.sub','i32.mul','i32.and','i32.or','i32.xor','i32.shl','i32.shr_u','i32.shr_s',
      'i32.rotl','i32.rotr','i32.eq','i32.ne','i32.lt_u','i32.le_u','i32.gt_u','i32.ge_u','i32.lt_s','i32.le_s','i32.gt_s','i32.ge_s'}
DECL={'type','param','result','local'}
WIDTH={'i32.store8':1,'i32.store16':2,'i32.store':4}
def c(n):return ['i32.const',str(n)]
def c64(n):return ['i64.const',str(n)]
def g(n):return ['local.get',str(n)]
def op(name,*xs):return [name,*xs]
def choose(a,b,p):return op('select',a,b,p)
def boolean(x):return op('i32.ne',x,c(0))
def conj(a,b):return b if a==c(1) else op('i32.and',a,b)
def nodes(x):
    if isinstance(x,list):
        yield x
        for y in x:yield from nodes(y)

def compile_wat(text,path):
    path=Path(path)
    if path.exists() or path.with_suffix('.wat').exists():raise FileExistsError(path)
    path.parent.mkdir(parents=True,exist_ok=True);path.with_suffix('.wat').write_text(text,encoding='utf-8')
    w.tool('wat2wasm',[path.with_suffix('.wat'),'-o',path]);w.tool('wasm-validate',[path])

def read(path):
    w.tool('wasm-validate',[path]);m=w.parse(w.tool('wasm2wat',[path,'--fold-exprs','--no-debug-names']))
    if any(x[0] not in {'type','memory','export','func'} for x in m[1:]):raise ValueError('Module sections unsupported')
    fs=[x for x in m[1:] if x[0]=='func'];ms=[x for x in m[1:] if x[0]=='memory'];es=[x for x in m[1:] if x[0]=='export']
    if len(fs)!=1 or len(ms)!=1 or len(ms[0])!=3 or not (0<=int(ms[0][1])<=int(ms[0][2])<=2):raise ValueError('One nonshared memory32, maximum <=2 pages required')
    if sorted(es)!=sorted([['export','"run"',['func','0']],['export','"memory"',['memory','0']]]):raise ValueError('run and memory exports required')
    f=fs[0];ps=[t for d in f[1:] if isinstance(d,list) and d[0]=='param' for t in d[1:]]
    if not 1<=len(ps)<=16 or any(t!='i32' for t in ps):raise ValueError('i32 parameters required')
    if [x for x in f[1:] if isinstance(x,list) and x[0]=='result']!=[['result','i32']]:raise ValueError('i32 result required')
    return m,f,len(ps)

def pure(x,params):
    if x[0]=='local.get' and len(x)==2 and 0<=int(x[1])<params:return
    if x[0]=='i32.const' and len(x)==2:int(x[1]);return
    arity=2 if x[0] in PURE else (1 if x[0] in {'i32.eqz','i32.clz','i32.ctz','i32.popcnt'} else (3 if x[0]=='select' else -1))
    if len(x)!=arity+1 or arity<0:raise ValueError('Not a supported total i32 expression: '+w.emit(x))
    for y in x[1:]:pure(y,params)

def source(path):
    m,f,params=read(path)
    if any(x[0]=='local' for x in f[1:] if isinstance(x,list)):raise ValueError('Source local updates unsupported')
    body=[x for x in f[1:] if isinstance(x,list) and x[0] not in DECL]
    if not body:raise ValueError('No function body')
    pure(body[-1],params);effects=[]
    def walk(seq,pred):
        for x in seq:
            if x[0]=='if':
                if len(x) not in (3,4) or x[2][0]!='then' or (len(x)==4 and x[3][0]!='else'):raise ValueError('Only void if supported')
                pure(x[1],params);p=boolean(x[1]);walk(x[2][1:],conj(pred,p))
                if len(x)==4:walk(x[3][1:],conj(pred,op('i32.eqz',p)))
            elif x[0] in WIDTH:
                xs=[y for y in x[1:] if isinstance(y,list)];imms=[y for y in x[1:] if isinstance(y,str)]
                if len(xs)!=2 or any(not y.startswith(('offset=','align=')) for y in imms):raise ValueError('Store memarg unsupported')
                off=next((int(y[7:]) for y in imms if y.startswith('offset=')),0)
                if not 0<=off<=256:raise ValueError('Offset limited to 256')
                for y in xs:pure(y,params)
                effects.append(dict(pred=pred,kind='store',width=WIDTH[x[0]],offset=off,args=xs,original=x))
            elif x[0] in ('memory.fill','memory.copy'):
                if len(x)!=4 or not all(isinstance(y,list) for y in x[1:]):raise ValueError('Only memory 0 bulk operations')
                for y in x[1:]:pure(y,params)
                effects.append(dict(pred=pred,kind=x[0],args=x[1:],original=x))
            else:raise ValueError('Effect unsupported: '+w.emit(x))
    walk(body[:-1],c(1))
    if not effects:raise ValueError('No effects')
    return m,f,params,effects,body[-1]

def boundary(address,length):
    end=op('i64.add',op('i64.extend_i32_u',address),op('i64.extend_i32_u',length))
    size=op('i64.shl',op('i64.extend_i32_u',['memory.size']),c64(16))
    return op('if',op('i64.gt_u',end,size),['then',['unreachable']])

def transform(src,dst,mode='extent'):
    start=time.perf_counter();m,f,n,es,result=source(src)
    if mode not in ('flat','extent','explicit'):raise ValueError(mode)
    body=[];decl=[x for x in f[1:] if isinstance(x,list) and x[0] in DECL]
    if mode=='flat':body=[op('if',e['pred'],['then',e['original']]) for e in es]
    else:
        # Reused scratch locals are unobservable and do not allocate linear memory.
        pred,addr,val,length,wide=n,n+1,n+2,n+3,n+4
        decl += [['local','i32','i32','i32','i32','i64']]
        for e in es:
            body.append(op('local.set',str(pred),e['pred']))
            if e['kind']=='store':
                a,v=e['args'];off=e['offset'];width=e['width']
                if off:
                    body.append(op('local.set',str(wide),op('i64.add',op('i64.extend_i32_u',a),c64(off))))
                    # Overflow cannot be a valid address with max <=2 pages.
                    a=choose(c(-1),op('i32.wrap_i64',g(wide)),op('i64.gt_u',g(wide),c64(0xffffffff)))
                body += [op('local.set',str(addr),choose(a,c(0),g(pred))),op('local.set',str(val),v)]
                if width>1:
                    extent=op('i32.mul',g(pred),c(width))
                    body.append(op('memory.copy',g(addr),g(addr),extent) if mode=='extent' else boundary(g(addr),extent))
                for i in range(width):
                    a=g(addr) if i==0 else op('i32.add',g(addr),op('i32.mul',g(pred),c(i)))
                    v=g(val) if i==0 else op('i32.shr_u',g(val),c(i*8))
                    body.append(op('memory.fill',a,v,g(pred)))
            else:
                a,b,l=e['args'];a=choose(a,c(0),g(pred))
                if e['kind']=='memory.copy':b=choose(b,c(0),g(pred))
                body.append(op(e['kind'],a,b,choose(l,c(0),g(pred))))
    f[:]=['func',*decl,*body,result];compile_wat(w.emit(m),dst)
    return dict(mode=mode,effects=len(es),transform_ms=(time.perf_counter()-start)*1000)

def upper(x,env):
    if any(y[0]=='local.tee' for y in nodes(x)):return 0xffffffff
    k=x[0]
    if k=='i32.const':return int(x[1])&0xffffffff
    if k=='local.get':return env.get(int(x[1]),0xffffffff)
    if k=='local.tee':return upper(x[2],env)
    if k=='i32.eqz' or k in {f'i32.{r}' for r in ('eq','ne','lt_u','le_u','gt_u','ge_u','lt_s','le_s','gt_s','ge_s')}:return 1
    if k=='i32.and':return min(upper(x[1],env),upper(x[2],env))
    if k=='select':return max(upper(x[1],env),upper(x[2],env))
    if k in ('i32.add','i32.mul'):
        a,b=upper(x[1],env),upper(x[2],env);v=a+b if k=='i32.add' else a*b
        return v if v<=0xffffffff else 0xffffffff
    return 0xffffffff

def normalize(m):
    """Binary-only semantic lifting; retains zero-length traps, never guesses guards."""
    m=copy.deepcopy(m);f=next(x for x in m[1:] if x[0]=='func')
    decl=[x for x in f[1:] if isinstance(x,list) and x[0] in DECL]
    count=sum(len(x)-1 for x in decl if x[0] in ('param','local'))
    a,b,n=count,count+1,count+2;decl += [['local','i32','i32','i32']]
    stats=dict(bulk=0,byte_fills=0,identity_copies=0,guarded_bulk=0)
    env={}
    def visit(x):
        if not isinstance(x,list):return x
        k=x[0]
        if k in ('local.set','local.tee'):
            x=copy.deepcopy(x);x[2]=visit(x[2]);env[int(x[1])]=upper(x[2],env);return x
        if k in ('loop','br','br_if','br_table','return','call','call_indirect'):
            raise ValueError('Normalizer does not support nonlocal control transfers')
        if k=='if':
            prefix=[];j=1
            while j<len(x) and isinstance(x[j],list) and x[j][0] in ('type','result','param'):
                prefix.append(x[j]);j+=1
            condition=visit(x[j]);base=dict(env);arms=[];states=[]
            for arm in x[j+1:]:
                env.clear();env.update(base);arms.append(visit(arm));states.append(dict(env))
            if len(arms)==1:states.append(base)
            env.clear()
            for key in set().union(*(set(s) for s in states)):env[key]=max(s.get(key,0xffffffff) for s in states)
            return ['if',*prefix,condition,*arms]
        if k not in ('memory.fill','memory.copy'):return [visit(y) for y in x]
        if len(x)!=4 or not all(isinstance(t,list) for t in x[1:]):raise ValueError('Bulk indices unsupported')
        stats['bulk']+=1
        # Wasm evaluates operands left-to-right; address/value local.tee can
        # change the bound of the later length operand.
        args=[visit(x[1]),visit(x[2])];bound=upper(x[3],env);args.append(visit(x[3]))
        save=[op('local.set',str(i),y) for i,y in zip((a,b,n),args)]
        if k=='memory.copy' and args[0]==args[1] and all(y[0] not in {'local.set','local.tee','call'} for arg in args for y in nodes(arg)):
            stats['identity_copies']+=1;return ['block',*save,boundary(g(a),g(n))]
        if k=='memory.fill' and bound<=1:
            stats['byte_fills']+=1
            return ['block',*save,op('if',g(n),['then',op('i32.store8',g(a),g(b))],['else',boundary(g(a),c(0))])]
        stats['guarded_bulk']+=1
        zero=[boundary(g(a),c(0))]
        if k=='memory.copy':zero.append(boundary(g(b),c(0)))
        return ['block',*save,op('if',g(n),['then',op(k,g(a),g(b),g(n))],['else',*zero])]
    body=[visit(x) for x in f[1:] if isinstance(x,list) and x[0] not in DECL]
    f[:]=['func',*decl,*body];return m,stats

def recover(src,dst):
    t=time.perf_counter();m,_,_=read(src);parse=(time.perf_counter()-t)*1000
    t=time.perf_counter();m,stats=normalize(m);analysis=(time.perf_counter()-t)*1000
    compile_wat(w.emit(m),dst);return dict(stats,parse_ms=parse,analysis_ms=analysis)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['transform','recover']);ap.add_argument('source',type=Path);ap.add_argument('destination',type=Path);ap.add_argument('--mode',default='extent',choices=['flat','extent','explicit']);a=ap.parse_args()
    print(json.dumps(transform(a.source,a.destination,a.mode) if a.action=='transform' else recover(a.source,a.destination)))
if __name__=='__main__':main()
