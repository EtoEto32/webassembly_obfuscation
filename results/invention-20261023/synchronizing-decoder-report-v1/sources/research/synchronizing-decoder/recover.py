"""Binary-only affine interpretation of a deterministic finite decoder helper."""
import json, sys, time
from pathlib import Path
import prototype as p
M=p.model.MASK
class Unsupported(ValueError):pass
class Branch(Exception):
    def __init__(self,depth):self.depth=depth
def const(x):return (0,0,x&M)
def value(x):
    if x[:2]!=(0,0):raise Unsupported('data-dependent address/control')
    return x[2]
def add(x,y):return tuple((a+b)&M for a,b in zip(x,y))
def scale(x,k):return tuple(a*k&M for a in x)
def unquote(s):
    s=s[1:-1];out=bytearray();i=0
    while i<len(s):
        if s[i]=='\\':
            out.append(int(s[i+1:i+3],16));i+=3
        else:out.extend(s[i].encode('utf-8'));i+=1
    return bytes(out)

def interpret(fn,args,memory):
    locals_=list(args)+[const(0) for e in fn[1:] if isinstance(e,list) and e[0]=='local' for _ in e[1:]];steps=0
    def seq(xs):
        r=None
        for x in xs:r=ev(x)
        return r
    def ev(e):
        nonlocal steps
        steps+=1
        if steps>200000:raise Unsupported('interpretation step bound')
        op=e[0]
        if op=='i32.const':return const(int(e[1],0))
        if op=='local.get':return locals_[int(e[1])]
        if op in ('local.set','local.tee'):
            v=ev(e[2]);locals_[int(e[1])]=v;return v if op=='local.tee' else None
        if op in ('block','loop','if'):
            if op=='if':
                body=e[2][1:] if value(ev(e[1])) else (e[3][1:] if len(e)>3 else [])
            else:body=[v for v in e[1:] if isinstance(v,list) and v[0] not in ('result','param')]
            while True:
                try:return seq(body)
                except Branch as b:
                    if b.depth:b.depth-=1;raise
                    if op!='loop':return None
        if op=='br':raise Branch(int(e[1]))
        if op=='br_if':
            if value(ev(e[2])):raise Branch(int(e[1]))
            return None
        if op in ('i32.load','i32.load8_u'):
            off=next((int(x.split('=')[1]) for x in e[1:] if isinstance(x,str) and x.startswith('offset=')),0)
            at=value(ev(e[-1]))+off;size=4 if op=='i32.load' else 1
            if at+size>len(memory):raise Unsupported('load out of bounds')
            return const(int.from_bytes(memory[at:at+size],'little'))
        if op=='i32.eqz':return const(value(ev(e[1]))==0)
        x=ev(e[1]);y=ev(e[2])
        if op=='i32.add':return add(x,y)
        if op=='i32.sub':return add(x,scale(y,-1))
        if op=='i32.mul':
            if y[:2]==(0,0):return scale(x,y[2])
            return scale(y,value(x))
        if op=='i32.shl':return scale(x,1<<(value(y)&31))
        if op=='i32.lt_u':return const(value(x)<value(y))
        if op=='i32.ge_u':return const(value(x)>=value(y))
        raise Unsupported('helper opcode '+op)
    body=[e for e in fn[1:] if isinstance(e,list) and e[0] not in ('type','param','result','local')]
    return seq(body),steps

def recover(src,dst,representative=False):
    start=time.perf_counter();mod=p.q.read(src);parse_end=time.perf_counter()
    funcs=[e for e in mod[1:] if e[0]=='func'];exports=[e for e in mod[1:] if e[0]=='export']
    if len(funcs)!=2 or exports!=[['export','"run"',['func','1']]]:raise Unsupported('two-function emitter profile')
    if any(e[0] not in ('type','func','export','memory','data') for e in mod[1:]):raise Unsupported('external state')
    if [e for e in mod[1:] if e[0]=='memory']!=[['memory','1','1']]:raise Unsupported('fixed private memory profile')
    memory=bytearray(65536)
    for e in mod[1:]:
        if e[0]=='data':
            at=p.const(e[1]);raw=b''.join(unquote(v) for v in e[2:])
            if at is None or at+len(raw)>65536:raise Unsupported('data bounds')
            memory[at:at+len(raw)]=raw
    fn=funcs[0];cert=[];memo={};calls=0
    def rec(e):
        nonlocal calls
        if isinstance(e,list) and e[0]=='call':
            if e[1]!='0' or len(e) not in (5,6):raise Unsupported('helper signature')
            args=e[2:];base=p.const(args[-1])
            if base is None:raise Unsupported('dynamic table base')
            if any(v[0] not in ('local.get','i32.const') for v in args[:2]):raise Unsupported('effectful caller operands')
            if len(args)==3:states=[None]
            else:
                state=args[2];v=p.const(state)
                if v is not None:states=[v]
                elif state[0]=='i32.rem_u' and p.const(state[2]) is not None and 1<=p.const(state[2])<=64:states=list(range(p.const(state[2])))
                elif state[0]=='i32.and' and p.const(state[2]) is not None and p.const(state[2])<64:states=[v for v in range(p.const(state[2])+1) if v&p.const(state[2])==v]
                else:raise Unsupported('unbounded starting state')
                if v is None and any(node[0] not in ('local.get','i32.const','i32.xor','i32.and','i32.or','i32.add','i32.mul') for node in p.q.walk(state[1])):raise Unsupported('effectful or trapping state expression')
            key=(base,tuple(states))
            if key not in memo:
                outputs=[];steps=0
                analyzed=states[:1] if representative else states
                for state in analyzed:
                    inputs=[(1,0,0),(0,1,0)]+([] if state is None else [const(state)])+[const(base)]
                    val,work=interpret(fn,inputs,memory);outputs.append(val);steps+=work
                if len(set(outputs))!=1 or outputs[0][0]!=1:raise Unsupported('nonuniform affine result')
                memo[key]=outputs[0];cert.append({'base':base,'states':states,'analyzed_states':analyzed,'output':outputs[0],'interpreter_steps':steps})
            _,a,b=memo[key];calls+=1
            return ['i32.add',['i32.add',args[0],['i32.mul',args[1],p.c(a)]],p.c(b)]
        return [rec(v) for v in e] if isinstance(e,list) else e
    run=rec([e for e in funcs[1] if not isinstance(e,list) or e[0]!='type']);analysis_end=time.perf_counter()
    p.q.compile('(module '+p.q.w.emit(run)+' (export "run" (func 0)))',dst)
    return {'status':'candidate_under_sync_promise' if representative else 'recovered','replaced_calls':calls,'certificates':cert,'parse_ms':(parse_end-start)*1000,'analysis_ms':(analysis_end-parse_end)*1000,'total_ms':(time.perf_counter()-start)*1000}
if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('source');ap.add_argument('output');ap.add_argument('--representative',action='store_true');a=ap.parse_args()
    info=recover(a.source,a.output,a.representative);p.q.save(a.output+'.json',info);print(json.dumps(info))
