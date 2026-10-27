"""Binary-only decoder extraction and all failure-prefix linear verification."""
import argparse
import json
import time
from pathlib import Path
import prototype as p


def decoder(f):
    hashes=[]; env=[]
    for e in f[1:]:
        if e[0]=='param':raise ValueError('digest must have no inputs')
        if e[0]=='local':env.extend([(0,0,frozenset())]*len(e[1:]))
    def walk(e):
        op=e[0];args=[x for x in e[1:] if isinstance(x,list)]
        if op=='i32.const':return (0,int(e[1],0)&0xffffffff,frozenset())
        if op=='i32.load8_u':
            addr=walk(args[0]);offset=next((int(x[7:],0) for x in e[1:] if isinstance(x,str) and x.startswith('offset=')),0)
            if addr[0] or addr[2] or addr[1]+offset>=64:raise ValueError('digest address')
            return (1<<(addr[1]+offset),0,frozenset())
        if op=='local.get':return env[int(e[1])]
        if op in ('local.set','local.tee'):
            v=walk(e[2]);env[int(e[1])]=v;return v if op=='local.tee' else None
        if op=='i32.xor':
            a,b=map(walk,args);return (a[0]^b[0],a[1]^b[1],a[2]^b[2])
        if op=='i32.mul':
            a,b=map(walk,args)
            if a==(0,16777619,frozenset()):a,b=b,a
            if b!=(0,16777619,frozenset()):raise ValueError('non-FNV multiply')
            i=len(hashes);hashes.append(a);return (0,0,frozenset([i]))
        raise ValueError('digest instruction '+op)
    result=None
    for e in f[1:]:
        if e[0] not in ('type','param','result','local'):result=walk(e)
    rows=[]
    while True:
        if result[0] or result[1] or len(result[2])!=1:raise ValueError('digest result')
        value=hashes[next(iter(result[2]))];rows.append(value[0])
        if not value[2]:
            if value[1]!=2166136261:raise ValueError('digest initial constant')
            break
        if value[1]:raise ValueError('affine decoder not supported')
        result=(0,0,value[2])
    rows.reverse()
    if not 2<=len(rows)<=64 or any(row>>len(rows) for row in rows) or p.m.inverse(rows) is None:raise ValueError('decoder not square invertible')
    return rows


def scalar(e,fail):
    if e[0]=='i32.const':return int(e[1],0)&0xffffffff
    if e==['local.get','0']:return fail
    if e[0]=='i32.eq':return int(scalar(e[1],fail)==scalar(e[2],fail))
    if e[0]=='i32.eqz':return int(scalar(e[1],fail)==0)
    if e[0]=='select':return scalar(e[1],fail) if scalar(e[3],fail) else scalar(e[2],fail)
    raise ValueError('destination guard')


def copies(f):
    found=[];env=[('constant',0xffffffff)]
    for e in f[1:]:
        if e[0]=='local':env.extend([('constant',0)]*len(e[1:]))
    widths={'i32.store8':1,'i32.store16':2,'i32.store':4,'i64.store':8}
    def constant(v):
        if v[0]!='constant':raise ValueError('copy control is not constant on success path')
        return v[1]
    def walk(e):
        op=e[0]
        args=[x for x in e[1:] if isinstance(x,list)]
        if op in ('i32.const','i64.const'):return ('constant',int(e[1],0)&0xffffffff)
        if op=='local.get':return env[int(e[1])]
        if op in ('local.set','local.tee'):
            value=walk(e[2]);env[int(e[1])]=value;return value
        if op.startswith(('i32.load','i64.load')):
            offset=next((int(x[7:],0) for x in e[1:] if isinstance(x,str) and x.startswith('offset=')),0)
            return ('load',constant(walk(args[0]))+offset)
        if op=='i32.eq':return ('constant',int(constant(walk(args[0]))==constant(walk(args[1]))))
        if op=='i32.eqz':return ('constant',int(constant(walk(args[0]))==0))
        if op=='select':
            a,b,c=[walk(x) for x in args];return a if constant(c) else b
        if op=='if':
            branch='then' if constant(walk(args[0])) else 'else'
            for child in args[1:]:
                if child[0]==branch:
                    for item in child[1:]:walk(item)
            return ('opaque',)
        if op=='block':
            for child in args:
                if child[0] not in ('type','result'):walk(child)
            return ('opaque',)
        values=[walk(x) for x in args]
        if op not in ('memory.copy',*widths) or not args or args[0][0]!='select':return ('opaque',)
        d=scalar(args[0],0xffffffff)
        failures=[j for j in range(16) if scalar(args[0],j)==65536]
        if len(failures)!=1 or failures[0]!=len(found):raise ValueError('nonconsecutive failure guard')
        if e[0]=='memory.copy':
            if args[1][0]!='i32.const' or args[2][0]!='i32.const':raise ValueError('copy operands')
            s,l=int(args[1][1],0),int(args[2][1],0)
        else:
            if values[1][0]!='load':raise ValueError('lowered copy without load provenance')
            s=values[1][1]
            l=widths[e[0]]
        found.append((d,s,l))
        return ('opaque',)
    for e in f[1:]:
        if e[0] not in ('type','param','result','local'):walk(e)
    if not found:raise ValueError('no guarded copies')
    return found


class Trap(Exception):pass


def check_parameter_uses(f):
    """Original fail value may only feed the already-checked branch conditions.

    Checking guards alone is insufficient: an untested equality can also be
    stored into memory. Permit reuse of local 0 only after it is overwritten.
    The boolean denotes whether local 0 may still contain the original input.
    """
    def walk(e,live,condition=False):
        op=e[0];args=[x for x in e[1:] if isinstance(x,list)]
        if condition and live:
            # recover() has checked this exact condition's syntax/partition.
            return live
        if op=='local.get' and e[1]=='0' and live:
            raise ValueError('failure parameter used outside verified guards')
        if op in ('local.set','local.tee'):
            live=walk(e[2],live)
            return False if e[1]=='0' else live
        if op=='if':
            live=walk(args[0],live,True);states=[]
            for arm in args[1:]:
                state=live
                for child in arm[1:]:state=walk(child,state)
                states.append(state)
            if not any(arm[0]=='else' for arm in args[1:]):states.append(live)
            return any(states)
        if op=='select':
            live=walk(args[0],live);live=walk(args[1],live)
            return walk(args[2],live,True)
        for child in args:live=walk(child,live)
        return live
    live=True
    for e in f[1:]:
        if e[0] not in ('type','param','result','local'):live=walk(e,live)


def execute(f,n,fail):
    one=1<<(8*n)
    def const(v,width=32):return tuple(one if (v>>i)&1 else 0 for i in range(width))
    def integer(v):
        if any(bit not in (0,one) for bit in v):raise ValueError('symbolic control/address')
        return sum((bit==one)<<i for i,bit in enumerate(v))
    env=[const(fail)];memory={i:tuple(1<<(8*i+j) for j in range(8)) for i in range(n)};trace=[]
    for e in f[1:]:
        if e[0]=='local':env.extend([const(0,64 if t=='i64' else 32) for t in e[1:]])
    def bounds(addr,width):
        if addr+width>65536:raise Trap()
    def walk(e):
        op=e[0];args=[x for x in e[1:] if isinstance(x,list)]
        if op in ('i32.const','i64.const'):return const(int(e[1],0),64 if op[1]=='6' else 32)
        if op=='local.get':return env[int(e[1])]
        if op in ('local.set','local.tee'):
            v=walk(e[2]);env[int(e[1])]=v;return v if op=='local.tee' else None
        if op=='i32.xor':return tuple(a^b for a,b in zip(walk(args[0]),walk(args[1])))
        if op=='i32.eq':return const(int(integer(walk(args[0]))==integer(walk(args[1]))))
        if op=='i32.eqz':return const(int(integer(walk(args[0]))==0))
        if op=='select':
            a,b,c=[walk(x) for x in args];return a if integer(c) else b
        if op=='if':
            condition=integer(walk(args[0]));branch='then' if condition else 'else'
            for child in args[1:]:
                if child[0]==branch:
                    for item in child[1:]:walk(item)
            return None
        if op=='block':
            value=None
            for item in args:
                if item[0] not in ('type','result'):value=walk(item)
            return value
        offset=next((int(x[7:],0) for x in e[1:] if isinstance(x,str) and x.startswith('offset=')),0)
        loads={'i32.load8_u':(1,32),'i32.load16_u':(2,32),'i32.load':(4,32),'i64.load':(8,64)}
        stores={'i32.store8':1,'i32.store16':2,'i32.store':4,'i64.store':8}
        if op in loads:
            width,total=loads[op];addr=integer(walk(args[0]))+offset;bounds(addr,width)
            bits=tuple(bit for i in range(addr,addr+width) for bit in memory.get(i,(0,)*8))
            return bits+(0,)*(total-8*width)
        if op in stores:
            width=stores[op];addr=integer(walk(args[0]))+offset;value=walk(args[1]);bounds(addr,width)
            if addr+width>n:raise ValueError('successful store outside encoded window')
            for i in range(width):memory[addr+i]=value[8*i:8*i+8]
            return None
        if op=='memory.copy':
            d,s,l=[integer(walk(x)) for x in args];bounds(d,l);bounds(s,l)
            if max(d+l,s+l)>n:raise ValueError('successful copy outside window')
            values=[memory.get(i,(0,)*8) for i in range(s,s+l)]
            for i,v in enumerate(values):memory[d+i]=v
            return None
        if op=='nop':return None
        if op=='drop':walk(args[0]);return None
        raise ValueError('run instruction '+op)
    trapped=False
    try:
        for e in f[1:]:
            if e[0] not in ('type','param','result','local'):walk(e)
    except Trap:trapped=True
    return memory,trapped


def recover(src,dst):
    start=time.perf_counter();mod=p.q.read(src);loaded=time.perf_counter()
    if any(e[0] not in ('type','func','memory','export','data') for e in mod[1:]):raise ValueError('module effects')
    if [e for e in mod[1:] if e[0]=='memory']!=[['memory','1','1']]:raise ValueError('memory profile')
    fs=[e for e in mod[1:] if e[0]=='func']
    if len(fs)!=2:raise ValueError('two functions required')
    for f,params,results in [(fs[0],['i32'],[]),(fs[1],[],['i32'])]:
        if [v for e in f[1:] if e[0]=='param' for v in e[1:]]!=params or [v for e in f[1:] if e[0]=='result' for v in e[1:]]!=results:raise ValueError('function signature')
    if [e for e in mod[1:] if e[0]=='export']!=[['export','"run"',['func','0']],['export','"digest"',['func','1']]]:raise ValueError('export profile')
    inverse=decoder(fs[1]);n=len(inverse);b=p.m.inverse(inverse);ops=copies(fs[0]);data=p.data_image(mod)
    if len(data)!=n:raise ValueError('data length')
    nodes=list(p.q.walk(fs[0]));guards=[]
    for i,e in enumerate(nodes):
        if e[0] not in ('if','select'):continue
        args=[v for v in e[1:] if isinstance(v,list)];cond=args[0] if e[0]=='if' else args[2]
        allowed=cond==['local.get','0'] or cond==['i32.eqz',['local.get','0']]
        if cond[0]=='i32.eq' and len(cond)==3:
            a,c=cond[1:]
            if a[0]=='i32.const':a,c=c,a
            allowed=a==['local.get','0'] and c[0]=='i32.const' and 0<=(int(c[1],0)&0xffffffff)<len(ops)
        if not allowed:raise ValueError('guard outside the verified failure partition')
        guards.append(i)
    last=max(guards,default=-1)
    if any(i<last and e[0] in ('local.set','local.tee') and e[1]=='0' for i,e in enumerate(nodes)):
        raise ValueError('failure parameter overwritten before final guard')
    check_parameter_uses(fs[0])
    prefix=p.m.ident(n);proof=[]
    for fail in range(len(ops)+1):
        expected=p.m.product(p.m.product(b,prefix),inverse)
        actual,trapped=execute(fs[0],n,fail)
        if trapped!=(fail<len(ops)):raise ValueError('trap path differs')
        for i,row in enumerate(expected):
            for bit in range(8):
                mask=0
                for k in p.m.bits(row):mask^=1<<(8*k+bit)
                if actual[i][bit]!=mask:raise ValueError('prefix state differs at '+str(fail))
        proof.append(dict(prefix=fail,trapped=trapped))
        if fail<len(ops):prefix=p.m.product(p.m.matrix(n,ops[fail]),prefix)
    analyzed=time.perf_counter();logical=p.m.apply(inverse,data);p.q.compile(p.wat(logical,ops),dst)
    return dict(n=n,ops=ops,proof=proof,read_ms=(loaded-start)*1000,analysis_ms=(analyzed-loaded)*1000,
                recovered_sha256=p.q.digest(dst),matrix_hex=[hex(x) for x in b])

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('source');ap.add_argument('output');a=ap.parse_args();p.q.save(str(a.output)+'.json',recover(a.source,a.output))
