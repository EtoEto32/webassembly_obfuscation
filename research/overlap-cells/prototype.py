"""Overlap-consistent pair encodings; experimental, not cryptographic protection."""
import argparse,importlib.util,itertools,json,random,re,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sp=importlib.util.spec_from_file_location('overlap_common',ROOT/'research/isotope-swizzle/prototype.py');q=importlib.util.module_from_spec(sp);sp.loader.exec_module(q)
w=q.w;MASK=(1<<64)-1
class Unsupported(ValueError):pass
def c(n,t='i32'):return [t+'.const',str(n&((1<<int(t[1:]))-1))]
def g(n):return ['local.get',str(n)]
def init(i):return ['i32.and',['i32.wrap_i64',['i64.shr_u',g(0),c(2*i,'i64')]],c(3)]
def pack(xs):
    e=c(0,'i64')
    for i,x in enumerate(xs):e=['i64.or',e,['i64.shl',['i64.extend_i32_u',x],c(2*i,'i64')]]
    return e
def module(n,body,data=None,extra=0):
    m=['module']
    if data is not None:m += [['memory','1','1'],['data',c(0),'"'+''.join('\\%02x'%b for b in data)+'"']]
    return [*m,['func',['export','"run"'],['param','i64'],['result','i64'],['local',*(['i32']*(n+extra))],*body]]
def evaluate(e,env):
    if e[0]=='local.get':return env[int(e[1])]
    if e[0]=='i32.const':return int(e[1],0)&0xffffffff
    a,b=[evaluate(x,env) for x in e[1:]];k=b&31
    return {'i32.add':lambda:a+b,'i32.sub':lambda:a-b,'i32.mul':lambda:a*b,'i32.xor':lambda:a^b,'i32.and':lambda:a&b,'i32.or':lambda:a|b,'i32.shl':lambda:a<<k,'i32.shr_u':lambda:(a&0xffffffff)>>k}[e[0]]()&0xffffffff
def source(src):
    m=q.read(src)
    if any(x[0] not in ('type','func','export') for x in m[1:]):raise Unsupported('pure source module')
    fs=[x for x in m[1:] if x[0]=='func'];ex=[x for x in m[1:] if x[0]=='export']
    if len(fs)!=1 or ex!=[['export','"run"',['func','0']]]:raise Unsupported('one run')
    f=fs[0];typ=lambda t:[v for e in f[1:] if e[0]==t for v in e[1:]];n=len(typ('local'))
    if typ('param')!=['i64'] or typ('result')!=['i64'] or typ('local')!=['i32']*n or not 4<=n<=32:raise Unsupported('4..32 i32 cell locals, i64 ABI')
    body=[e for e in f[1:] if e[0] not in ('type','param','result','local')]
    if body[:n]!=[['local.set',str(i+1),init(i)] for i in range(n)] or body[-1]!=pack([g(i+1) for i in range(n)]):raise Unsupported('canonical packed-cell entry/exit')
    steps=[]
    for e in body[n:-1]:
        if e[0]!='local.set' or len(e)!=3:raise Unsupported('cell assignment')
        i=int(e[1])-1;l=(i-1)%n;r=(i+1)%n
        if not 0<=i<n:raise Unsupported('cell index')
        allowed={l+1,i+1,r+1}
        def valid(t):
            if t[0]=='local.get':return int(t[1]) in allowed
            if t[0]=='i32.const':return True
            return t[0] in ('i32.add','i32.sub','i32.mul','i32.and','i32.xor','i32.or','i32.shl','i32.shr_u') and len(t)==3 and all(valid(z) for z in t[1:])
        if not valid(e[2]):raise Unsupported('rule expression')
        table=[evaluate(e[2],{l+1:a,i+1:b,r+1:d}) for a,b,d in itertools.product(range(4),repeat=3)]
        if max(table)>3:raise Unsupported('rule range')
        if any(sorted(table[16*a+4*b+d] for b in range(4))!=list(range(4)) for a,d in itertools.product(range(4),repeat=2)):raise Unsupported('center update must be bijective')
        steps.append(dict(cell=i,table=table))
    if not 1<=len(steps)<=128:raise Unsupported('1..128 updates')
    return n,steps,m
def fixture(n,rounds,family):
    body=[['local.set',str(i+1),init(i)] for i in range(n)];rng=random.Random(1900+family+n)
    for k in range(n*rounds):
        i=k%n;l=g((i-1)%n+1);mid=g(i+1);r=g((i+1)%n+1);key=c(rng.randrange(4));a=c(rng.choice([1,3]))
        if family==0:e=['i32.add',mid,['i32.add',['i32.mul',['i32.xor',l,r],a],key]]
        elif family==1:e=['i32.xor',mid,['i32.add',['i32.mul',['i32.add',l,r],a],key]]
        else:e=['i32.add',['i32.or',['i32.shl',['i32.and',mid,c(1)],c(1)],['i32.shr_u',mid,c(1)]],['i32.add',['i32.mul',l,r],key]]
        body.append(['local.set',str(i+1),['i32.and',e,c(3)]])
    return w.emit(module(n,body+[pack([g(i+1) for i in range(n)])]))
def transform(src,dst,mode='pair-recode',seed=37,broken=False):
    t=time.perf_counter();n,steps,m=source(src);tr=time.perf_counter();rng=random.Random(seed);data=bytearray();body=[]
    def perm(k):a=list(range(k));rng.shuffle(a);return a
    def lut(table,index):
        offset=len(data);data.extend(bytes(table));data.extend(b'\0'*(256-len(table)));return ['i32.load8_u','offset='+str(offset),index]
    if mode=='plain':q.compile(w.emit(m),dst);return dict(mode=mode,n=n,steps=len(steps),seed=seed,transform_ms=(time.perf_counter()-t)*1000)
    if mode not in ('single','pair-zero','pair-noise','pair-recode'):raise Unsupported('mode')
    enc=[perm(4 if mode=='single' else 16) for _ in range(n)]
    for i in range(n):
        index=init(i) if mode=='single' else ['i32.or',['i32.shl',init(i),c(2)],init((i+1)%n)]
        body.append(['local.set',str(i+1),lut(enc[i],index)])
    for stepno,s in enumerate(steps):
        i=s['cell'];l=(i-1)%n;r=(i+1)%n;f=s['table']
        if mode=='single':
            new=perm(4);table=[0]*64
            for a,b,d in itertools.product(range(4),repeat=3):table[(enc[l][a]<<4)|(enc[i][b]<<2)|enc[r][d]]=new[f[16*a+4*b+d]]
            index=['i32.or',['i32.shl',g(l+1),c(4)],['i32.or',['i32.shl',g(i+1),c(2)],g(r+1)]]
            body.append(['local.set',str(i+1),lut(table,index)]);enc[i]=new
        else:
            oldl,oldr=enc[l],enc[i];newl=perm(16) if mode=='pair-recode' else oldl;newr=perm(16) if mode=='pair-recode' else oldr
            table=[None]*256
            for a,b,d in itertools.product(range(4),repeat=3):
                v=f[16*a+4*b+d]
                if broken and stepno==0 and a==b==d==0:v=(v+1)&3
                table[(oldl[4*a+b]<<4)|oldr[4*b+d]]=(newl[4*a+v]<<4)|newr[4*v+d]
            free=[x for x in range(256) if x not in set(v for v in table if v is not None)];rng.shuffle(free)
            for j in range(256):
                if table[j] is None:table[j]=0 if mode=='pair-zero' else free.pop() if free else 0
            body += [['local.set',str(n+1),lut(table,['i32.or',['i32.shl',g(l+1),c(4)],g(i+1)])],['local.set',str(l+1),['i32.shr_u',g(n+1),c(4)]],['local.set',str(i+1),['i32.and',g(n+1),c(15)]]]
            enc[l],enc[i]=newl,newr
    outs=[]
    for i in range(n):
        inv=[0]*len(enc[i])
        for j,v in enumerate(enc[i]):inv[v]=j if mode=='single' else j//4
        outs.append(lut(inv,g(i+1)))
    body.append(pack(outs))
    if len(data)>65536:raise Unsupported('table memory capacity')
    tb=time.perf_counter();q.compile(w.emit(module(n,body,data,extra=1)),dst)
    return dict(mode=mode,n=n,steps=len(steps),seed=seed,table_bytes=len(data),read_ms=(tr-t)*1000,build_ms=(tb-tr)*1000,transform_ms=(time.perf_counter()-t)*1000)
def data_string(t):
    s=t[1:-1];out=bytearray();i=0;esc={'n':10,'r':13,'t':9,'"':34,"'":39,'\\':92}
    while i<len(s):
        if s[i]!='\\':out.append(ord(s[i]));i+=1
        elif i+2<len(s) and all(c in '0123456789abcdefABCDEF' for c in s[i+1:i+3]):out.append(int(s[i+1:i+3],16));i+=3
        else:out.append(esc[s[i+1]]);i+=2
    return bytes(out)
def lift(src):
    m=q.read(src);mem=bytearray(65536)
    if any(e[0] not in ('type','func','export','memory','data') for e in m[1:]):raise Unsupported('target module section')
    fs=[e for e in m[1:] if e[0]=='func'];ex=[e for e in m[1:] if e[0]=='export'];ms=[e for e in m[1:] if e[0]=='memory']
    if len(fs)!=1 or ex!=[['export','"run"',['func','0']]] or ms!=[['memory','1','1']]:raise Unsupported('target module ABI/memory')
    for e in m[1:]:
        if e[0]=='data':
            if e[1][0]!='i32.const':raise Unsupported('active data')
            off=int(e[1][1],0);blob=b''.join(data_string(t) for t in e[2:]);mem[off:off+len(blob)]=blob
    f=fs[0];ty=lambda t:[v for e in f[1:] if e[0]==t for v in e[1:]]
    if ty('param')!=['i64'] or ty('result')!=['i64'] or any(t not in ('i32','i64') for t in ty('local')):raise Unsupported('target function types')
    env=[[('arg',i) for i in range(64)]]+[[0]*int(t[1:]) for t in ty('local')];stack=[];loads=[]
    def operands(es,n):
        vals=[walk(e) for e in es];k=n-len(vals)
        if k<0 or k>len(stack):raise Unsupported('stack arity')
        if k:vals=stack[-k:]+vals;del stack[-k:]
        return vals
    def integer(bits):
        if any(b not in (0,1) for b in bits):raise Unsupported('constant required')
        return sum(b<<i for i,b in enumerate(bits))
    def walk(e):
        op=e[0]
        if op=='local.get':return env[int(e[1])]
        if op in ('local.set','local.tee'):
            v=operands(e[2:],1)[0];env[int(e[1])]=v;return v if op=='local.tee' else None
        if op in ('i32.const','i64.const'):
            v=int(e[1],0);return [(v>>i)&1 for i in range(int(op[1:3]))]
        if op in ('i32.load8_u','i64.load8_u'):
            a=operands([x for x in e[1:] if isinstance(x,list)],1)[0];off=0
            for x in e[1:]:
                if isinstance(x,str) and x.startswith('offset='):off=int(x[7:])
                elif isinstance(x,str) and not x.startswith('align='):raise Unsupported('memory immediate')
            base=integer(a[8:])<<8;off+=base
            if off%256 or not 0<=off<=65280:raise Unsupported('aligned table address')
            idx=a[:8];table=list(mem[off:off+256]);rid=len(loads);loads.append(dict(id=rid,base=off,index=idx,table=table))
            return [('load',rid,i) if any(v&(1<<i) for v in table) else 0 for i in range(8)]+[0]*(int(op[1:3])-8)
        if op=='i32.wrap_i64':return operands(e[1:],1)[0][:32]
        if op=='i64.extend_i32_u':return operands(e[1:],1)[0]+[0]*32
        if op in ('i32.shl','i32.shr_u','i64.shl','i64.shr_u'):
            a,b=operands(e[1:],2);k=integer(b)&(len(a)-1)
            return ([0]*k+a)[:len(a)] if op.endswith('.shl') else a[k:]+[0]*k
        if op in ('i32.or','i64.or','i32.and','i64.and','i32.add','i64.add'):
            a,b=operands(e[1:],2);out=[]
            for x,y in zip(a,b):
                if op.endswith('.and'):
                    if x==0 or y==0:out.append(0)
                    elif x==1:out.append(y)
                    elif y==1 or x==y:out.append(x)
                    else:raise Unsupported('nonwiring and')
                else:
                    if x==0:out.append(y)
                    elif y==0:out.append(x)
                    elif op.endswith('.or') and (x==y or x==1 or y==1):out.append(1 if x==1 or y==1 else x)
                    else:raise Unsupported('nonwiring or/add')
            return out
        raise Unsupported('target op '+op)
    for e in f[1:]:
        if e[0] not in ('type','param','result','local'):
            v=walk(e)
            if v is not None:stack.append(v)
    if len(stack)!=1 or len(stack[0])!=64:raise Unsupported('one i64 result')
    return loads,stack[0]
def wire(bits,width):
    if len(bits)!=width or any(not isinstance(b,tuple) or b[0]!='load' for b in bits):raise Unsupported('wire bits')
    first=bits[0]
    if bits!=[('load',first[1],first[2]+i) for i in range(width)]:raise Unsupported('contiguous wire')
    return (first[1],first[2])
def components(edges):
    adj={}
    for a,b in edges:adj.setdefault(('l',a),set()).add(('r',b));adj.setdefault(('r',b),set()).add(('l',a))
    groups={};count=0
    for v in sorted(adj):
        if v in groups:continue
        todo=[v];groups[v]=count
        while todo:
            for u in adj[todo.pop()]:
                if u not in groups:groups[u]=count;todo.append(u)
        count+=1
    return groups,count
def canonical(n,steps,decoders):
    data=bytearray();body=[['local.set',str(i+1),init(i)] for i in range(n)]
    def lut(t,idx):off=len(data);data.extend(t);return ['i32.load8_u','offset='+str(off),idx]
    for s in steps:
        l,i,r=s['cells'];idx=['i32.or',['i32.shl',g(l+1),c(4)],['i32.or',['i32.shl',g(i+1),c(2)],g(r+1)]];body.append(['local.set',str(i+1),lut(s['table'],idx)])
    outs=[lut(decoders[i],g(i+1)) for i in range(n)];body.append(pack(outs));return w.emit(module(n,body,data))
def recover(src,dst=None,diagnostics=False):
    start=time.perf_counter();loads,result=lift(src);readend=time.perf_counter();wires={};steps=[];terminal={};visited=0;stats=[]
    for rec in loads:
        bits=rec['index'];tbl=rec['table'];rid=rec['id'];variable=[b for b in bits if b!=0]
        if variable and all(isinstance(b,tuple) and b[0]=='arg' for b in variable):
            width=len(variable)
            if width not in (2,4) or bits[width:]!=[0]*(8-width):raise Unsupported('input table')
            ids=[]
            for j in range(0,width,2):
                a=bits[j]
                if a[1]%2 or bits[j:j+2]!=[('arg',a[1]),('arg',a[1]+1)]:raise Unsupported('input cell bits')
                ids.append(a[1]//2)
            ids=tuple(reversed(ids));enc={((i,) if width==2 else (i//4,i%4)):tbl[i] for i in range(1<<width)}
            if len(set(enc.values()))!=1<<width:raise Unsupported('input encoding not bijective')
            wires[(rid,0)]=(ids,enc);continue
        if bits[4:]==[0]*4:
            width=2 if bits[2:]==[0]*6 else 4;key=wire(bits[:width],width)
            if key not in wires:raise Unsupported('terminal input missing')
            terminal[rid]=(key,tbl);continue
        if bits[6:]==[0]*2:
            left,mid,right=[wire(bits[j:j+2],2) for j in (4,2,0)];ls,es=wires[left];ms,em=wires[mid];rs,er=wires[right]
            if len(ls)!=1 or len(ms)!=1 or len(rs)!=1:raise Unsupported('single states')
            mapping={};rule=[]
            for a,b,d in itertools.product(range(4),repeat=3):
                v=tbl[(es[(a,)]<<4)|(em[(b,)]<<2)|er[(d,)]];mapping.setdefault(v,len(mapping));rule.append(mapping[v]);visited+=1
            if len(mapping)!=4:raise Unsupported('single range')
            wires[(rid,0)]=(ms,{(v,):k for k,v in mapping.items()});steps.append(dict(cells=[ls[0],ms[0],rs[0]],table=rule));continue
        left,right=wire(bits[4:],4),wire(bits[:4],4);ls,el=wires[left];rs,er=wires[right]
        if len(ls)!=2 or len(rs)!=2 or ls[1]!=rs[0] or len(set(ls+rs))!=3:raise Unsupported('overlap topology')
        triples=[];edges=[]
        for a,b,d in itertools.product(range(4),repeat=3):
            value=tbl[(el[(a,b)]<<4)|er[(b,d)]];aa,bb=value>>4,value&15;triples.append((a,b,d,aa,bb));edges.append((aa,bb));visited+=1
        groups,count=components(edges)
        if count!=4 or any(sum(k[0]=='l' and v==j for k,v in groups.items())!=4 or sum(k[0]=='r' and v==j for k,v in groups.items())!=4 for j in range(4)) or len(set(edges))!=64:raise Unsupported('not four K4,4 support components')
        labels={};newl={};newr={};rule=[]
        for a,b,d,aa,bb in triples:
            component=groups[('l',aa)];labels.setdefault(component,len(labels));v=labels[component];rule.append(v)
            for mapping,key,value in ((newl,(a,v),aa),(newr,(v,d),bb)):
                if key in mapping and mapping[key]!=value:raise Unsupported('boundary not preserved')
                mapping[key]=value
        if len(newl)!=16 or len(newr)!=16 or len(set(newl.values()))!=16 or len(set(newr.values()))!=16:raise Unsupported('pair encoding range')
        wires[(rid,4)]=(ls,newl);wires[(rid,0)]=(rs,newr);steps.append(dict(cells=[ls[0],ls[1],rs[1]],table=rule));stats.append(dict(valid_entries=64,support_components=count))
        if diagnostics:stats[-1]['all_table_components']=components([(v>>4,v&15) for v in tbl])[1]
    decoders=[]
    for i in range(32):
        b=result[2*i:2*i+2]
        if b==[0,0]:
            if any(x!=0 for x in result[2*i:]):raise Unsupported('noncontiguous output')
            break
        rid,off=wire(b,2)
        if off!=0 or rid not in terminal:raise Unsupported('final decoder')
        key,tbl=terminal[rid];ids,enc=wires[key]
        if ids[0]!=i:raise Unsupported('output cell ordering')
        decoder=[]
        for a in range(4):
            values={tbl[enc[(a,)]]} if len(ids)==1 else {tbl[enc[(a,b)]] for b in range(4)}
            if len(values)!=1 or max(values)>3:raise Unsupported('decoder depends on other cell')
            decoder.append(values.pop())
        decoders.append(decoder)
    n=len(decoders)
    if not 4<=n<=32 or not steps:raise Unsupported('cell program size')
    code=canonical(n,steps,decoders);end=time.perf_counter()
    if dst:q.compile(code,dst)
    return dict(n=n,steps=len(steps),loads=len(loads),visited_entries=visited,support=stats,read_ms=(readend-start)*1000,recovery_ms=(end-readend)*1000,code=code)
def plain_canonical(src,dst=None):
    n,ss,_=source(src);frames=[list(range(4)) for _ in range(n)];out=[]
    for s in ss:
        i=s['cell'];l=(i-1)%n;r=(i+1)%n;mapping={};rule=[]
        for a,b,d in itertools.product(range(4),repeat=3):
            raw=s['table'][16*frames[l][a]+4*frames[i][b]+frames[r][d]];mapping.setdefault(raw,len(mapping));rule.append(mapping[raw])
        frames[i]=list(mapping);out.append(dict(cells=[l,i,r],table=rule))
    code=canonical(n,out,frames)
    if dst:q.compile(code,dst)
    return code
def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest='cmd',required=True);a=sub.add_parser('transform');a.add_argument('source');a.add_argument('output');a.add_argument('--mode',default='pair-recode');a.add_argument('--seed',type=int,default=37);a=sub.add_parser('recover');a.add_argument('source');a.add_argument('output');v=ap.parse_args();result=transform(v.source,v.output,v.mode,v.seed) if v.cmd=='transform' else recover(v.source,v.output);result.pop('code',None);print(json.dumps(result))
if __name__=='__main__':main()
