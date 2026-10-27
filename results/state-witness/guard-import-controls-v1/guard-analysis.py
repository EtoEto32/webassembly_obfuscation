"""Equality-precondition fixed point for constant bulk-memory API programs.

This is an application of known predicate-transformer/equality-abstraction ideas.
The contract observes all memory after every API, including traps and re-entry.
"""
import argparse,collections,hashlib,json,time
from pathlib import Path
import prototype as k

class Unsupported(ValueError):pass
M=lambda i:('m',i)
C=lambda i:('c',i)

def canonical(atoms):
    if atoms is None:return None
    parent={}
    def root(x):
        parent.setdefault(x,x)
        if parent[x]!=x:parent[x]=root(parent[x])
        return parent[x]
    for x,y in atoms:
        a,b=root(x),root(y)
        if a!=b:parent[max(a,b)]=min(a,b)
    groups=collections.defaultdict(list)
    for x in parent:groups[root(x)].append(x)
    result=[]
    for group in groups.values():
        constants={x[1] for x in group if x[0]=='c'}
        if len(constants)>1:return None
        group.sort();result.extend((group[0],x) for x in group[1:])
    return frozenset(result)

def combine(*guards):
    if any(g is None for g in guards):return None
    return canonical([p for g in guards for p in g])

def pullback(guard,mapping):
    if guard is None:return None
    def subst(x):return mapping.get(x[1],x) if x[0]=='m' else x
    return canonical([(subst(x),subst(y)) for x,y in guard])

def literal(text):
    # WABT-emitted byte strings: ASCII text or two-hex-digit escapes.
    data=bytearray();i=1
    while i<len(text)-1:
        if text[i]=='\\':
            pair=text[i+1:i+3]
            if len(pair)==2 and all(c in '0123456789abcdefABCDEF' for c in pair):data.append(int(pair,16));i+=3;continue
            escapes={'n':10,'r':13,'t':9,'\\':92,'"':34,"'":39}
            if text[i+1] not in escapes:raise Unsupported('non-byte WAT escape')
            data.append(escapes[text[i+1]]);i+=2
        else:
            if ord(text[i])>127:raise Unsupported('non-ASCII WAT literal')
            data.append(ord(text[i]));i+=1
    return bytes(data)

def parse(module):
    _,meta=k.augment(module,True)
    if k.p.section(module,'global') or k.p.section(module,'table') or k.p.section(module,'elem'):
        raise Unsupported('memory-only model; globals/tables excluded')
    memories=k.p.section(module,'memory')
    if len(memories)!=1:raise Unsupported('exactly one memory required')
    size=int(memories[0][1])*65536
    segments=[]
    for s,desc in zip(k.p.section(module,'data'),meta['segments']):
        segments.append({'data':b''.join(literal(x) for x in s[1:] if isinstance(x,str) and x.startswith('"')),
                         'initialLive':desc['initialLive']})
    funcs=k.p.section(module,'func');types=k.p.section(module,'type');actions=[];cells=set()
    for e in k.p.section(module,'export'):
        if e[2][0]!='func':continue
        f=funcs[int(e[2][1])];typ=types[int(next(x[1] for x in f[1:] if x[0]=='type'))][1]
        body=[x for x in f[1:] if x[0] not in k.p.DECL];name=json.loads(e[1])
        if typ==['func',['param','i32'],['result','i32']] and body==[['i32.load8_u',['local.get','0']]]:
            actions.append({'name':name,'readonly':True,'ops':[]});continue
        if typ!=['func']:raise Unsupported('API signature/body outside profile')
        ops=[]
        for n in body:
            op=n[0]
            if op=='nop':continue
            if op=='data.drop':ops.append((op,int(n[1])));continue
            if op not in ('memory.init','memory.copy','memory.fill'):raise Unsupported('unsupported opcode '+op)
            args=[x for x in n[1:] if isinstance(x,list)]
            if len(args)!=3 or any(len(x)!=2 or x[0]!='i32.const' for x in args):raise Unsupported('nonconstant operands')
            dst,src,length=[int(x[1],0)&0xffffffff for x in args]
            if length>128:raise Unsupported('transfer length exceeds 128 bytes')
            # Only in-bounds addresses can become state variables. Full mathematical
            # bounds are checked before updates; unsigned addition never wraps.
            if dst+length<=size:cells.update(range(dst,dst+length))
            if op=='memory.copy' and src+length<=size:cells.update(range(src,src+length))
            immediates=[x for x in n[1:] if isinstance(x,str)]
            index=int(immediates[-1]) if op=='memory.init' else None
            ops.append((op,dst,src,length,index))
        actions.append({'name':name,'readonly':False,'ops':ops})
    if len(cells)>256:raise Unsupported('footprint exceeds 256 cells')
    return {'size':size,'segments':segments,'actions':actions,'cells':sorted(cells)}

def effect(model,alive,action):
    state=list(alive);mapping={};outcome='return'
    get=lambda x:mapping.get(x,M(x))
    for op in action['ops']:
        if op[0]=='data.drop':state[op[1]]=False;continue
        name,dst,src,n,index=op
        end=model['size']
        limit=(len(model['segments'][index]['data']) if state[index] else 0) if name=='memory.init' else end
        if dst+n>end or (name!='memory.fill' and src+n>limit):outcome='trap';break
        if name=='memory.init':values=[C(x) for x in model['segments'][index]['data'][src:src+n]]
        elif name=='memory.fill':values=[C(src&255)]*n
        else:values=[get(i) for i in range(src,src+n)]
        for i,value in enumerate(values):mapping[dst+i]=value
    return {'alive':tuple(state),'mapping':mapping,'outcome':outcome}

def solve(model,left,right):
    if len(left)!=len(model['segments']) or len(right)!=len(model['segments']):raise Unsupported('segment state length')
    for side in (left,right):
        if any(live and not s['initialLive'] for live,s in zip(side,model['segments'])):
            raise Unsupported('cannot revive active or empty data segments')
    initial=(tuple(left),tuple(right));states=[initial];index={initial:0};edges=[]
    for pair in states:
        if len(states)>1024:raise Unsupported('segment-state-pair bound')
        row=[]
        if pair[0]!=pair[1]:
            for action in model['actions']:
                if action['readonly']:continue
                a,b=effect(model,pair[0],action),effect(model,pair[1],action)
                target=(a['alive'],b['alive'])
                if target not in index:index[target]=len(states);states.append(target)
                cells=set(a['mapping'])|set(b['mapping'])
                local=canonical([(a['mapping'].get(i,M(i)),b['mapping'].get(i,M(i))) for i in cells])
                if a['outcome']!=b['outcome']:local=None
                row.append({'action':action['name'],'target':index[target],'local':local,'mapping':a['mapping'],
                            'outcomes':[a['outcome'],b['outcome']]})
        edges.append(row)
    guards=[frozenset() for _ in states]
    for iteration in range(1,1025):
        new=[combine(*[combine(e['local'],pullback(guards[e['target']],e['mapping'])) for e in row]) for row in edges]
        if new==guards:break
        guards=new
    else:raise Unsupported('fixed-point iteration bound')
    def serial(g):return None if g is None else [[list(x),list(y)] for x,y in sorted(g)]
    return {'status':'conditional' if guards[0] else ('impossible' if guards[0] is None else 'unconditional'),
      'guard':serial(guards[0]),'iterations':iteration,'states':[{'left':list(a),'right':list(b),'guard':serial(g)} for (a,b),g in zip(states,guards)],
      'edges':[[{'action':e['action'],'target':e['target'],'outcomes':e['outcomes'],'local':serial(e['local']),
                'mapping':{str(i):list(v) for i,v in e['mapping'].items()}} for e in row] for row in edges],
      'cells':model['cells'],'memoryBytes':model['size']}

def analyse(source,left,right):
    start=time.perf_counter()
    try:result=solve(parse(k.p.read(source)),left,right)
    except ValueError as e:result={'status':'unsupported','reason':str(e)}
    result.update({'sourceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'seconds':time.perf_counter()-start})
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('out',type=Path);p.add_argument('--left',required=True);p.add_argument('--right',required=True)
    v=p.parse_args();r=analyse(v.source,[x=='1' for x in v.left],[x=='1' for x in v.right]);v.out.write_text(json.dumps(r,indent=2));print(json.dumps({k:r[k] for k in ['status','guard','iterations'] if k in r}))
