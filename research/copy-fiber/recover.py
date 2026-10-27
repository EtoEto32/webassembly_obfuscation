"""Binary-only straight-line symbolic evaluator; no codec/seed/SHA knowledge.

This is an adaptive analysis implementation for this experiment, not a general
Wasm decompiler. Private memory at entry is symbolic, so successful extraction
does not assume that each call is the first call on a fresh instance.
"""
import argparse,hashlib,importlib.util,json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sp=importlib.util.spec_from_file_location('cf_recovery_common',ROOT/'research/isotope-swizzle/prototype.py');q=importlib.util.module_from_spec(sp);sp.loader.exec_module(q)
MASK=0xffffffff
class Unsupported(ValueError):pass
class Return(Exception):pass
class DAG:
    def __init__(self):self.nodes=[];self.ids={};self.simplifications=0
    def node(self,op,*xs):
        key=(op,*xs)
        if key not in self.ids:self.ids[key]=len(self.nodes);self.nodes.append(key)
        return self.ids[key]
    def const(self,x):return self.node('const',x&MASK)
    def cv(self,x):return self.nodes[x][1] if self.nodes[x][0]=='const' else None
    def make(self,op,*args):
        vals=[self.cv(x) for x in args]
        if all(v is not None for v in vals):
            a=vals[0];b=vals[1] if len(vals)>1 else None
            if op=='xor':v=a^b
            elif op=='and':v=a&b
            elif op=='or':v=a|b
            elif op=='add':v=a+b
            elif op=='sub':v=a-b
            elif op=='mul':v=a*b
            elif op=='shl':v=a<<(b&31)
            elif op=='shr_u':v=a>>(b&31)
            elif op=='rotl':v=(a<<(b&31))|(a>>((-b)&31))
            elif op=='rotr':v=(a>>(b&31))|(a<<((-b)&31))
            else:raise Unsupported(op)
            self.simplifications+=1;return self.const(v)
        if op=='xor':
            terms=set();constant=0
            def feed(x):
                nonlocal constant
                v=self.cv(x)
                if v is not None:constant^=v
                elif self.nodes[x][0]=='xor':
                    for y in self.nodes[x][1:]:feed(y)
                elif x in terms:terms.remove(x);self.simplifications+=1
                else:terms.add(x)
            for a in args:feed(a)
            if constant:terms.add(self.const(constant))
            if not terms:return self.const(0)
            if len(terms)==1:return next(iter(terms))
            return self.node('xor',*sorted(terms))
        if op in ('and','or','add','mul'):
            a,b=args
            if op in ('and','or') and a==b:self.simplifications+=1;return a
            if op=='and' and 0 in vals:return self.const(0)
            if op=='or' and MASK in vals:return self.const(MASK)
            identity={'and':MASK,'or':0,'add':0,'mul':1}[op]
            if vals[0]==identity:return b
            if vals[1]==identity:return a
            if op=='mul' and 0 in vals:return self.const(0)
            return self.node(op,*sorted(args))
        if op=='sub':
            if args[0]==args[1]:return self.const(0)
            if vals[1] is not None:return self.make('add',args[0],self.const(-vals[1]))
        if op in ('rotl','rotr') and vals[1] is not None:
            n=(vals[1] if op=='rotl' else -vals[1])&31
            if n==0:return args[0]
            return self.node('rotl',args[0],self.const(n))
        if op in ('shl','shr_u') and vals[1] is not None:
            n=vals[1]&31
            if n==0:return args[0]
            return self.node(op,args[0],self.const(n))
        return self.node(op,*args)
    def reachable(self,roots):
        found=set();todo=list(roots)
        while todo:
            n=todo.pop()
            if n in found:continue
            found.add(n);op,*args=self.nodes[n]
            if op not in ('const','param','initial'):todo.extend(args)
        return sorted(found)
    def fingerprint(self,roots):
        hs={}
        for n in self.reachable(roots):
            op,*args=self.nodes[n]
            children=args if op in ('const','param','initial') else [hs[x] for x in args]
            if op in ('xor','and','or','add','mul'):children=sorted(children)
            hs[n]=hashlib.sha256(json.dumps([op,*children]).encode()).hexdigest()
        return [hs[x] for x in roots]
    def wat(self,roots,params):
        reachable=self.reachable(roots)
        if any(self.nodes[x][0]=='initial' for x in reachable):raise Unsupported('output depends on entry memory')
        assignments=[x for x in reachable if self.nodes[x][0] not in ('const','param')];loc={x:params+i for i,x in enumerate(assignments)}
        def ref(x):
            op,*a=self.nodes[x]
            if op=='const':return ['i32.const',str(a[0] if a[0]<0x80000000 else a[0]-0x100000000)]
            return ['local.get',str(a[0] if op=='param' else loc[x])]
        code=[]
        for x in assignments:
            op,*a=self.nodes[x]
            expr=['i32.'+op,ref(a[0]),ref(a[1])]
            for y in a[2:]:expr=['i32.'+op,expr,ref(y)]
            code.append(['local.set',str(loc[x]),expr])
        return q.w.emit(['module',['func',['export','"compress"'],['param',*(['i32']*params)],['result',*(['i32']*len(roots))],['local',*(['i32']*len(assignments))],*code,*[ref(x) for x in roots]]])

class Engine:
    def __init__(self,module):
        if any(x[0] not in ('type','func','memory','export') for x in module[1:]):raise Unsupported('closed code only')
        if [x for x in module[1:] if x[0]=='memory'] not in ([],[['memory','1','1']]):raise Unsupported('private fixed memory')
        exports=[x for x in module[1:] if x[0]=='export']
        if len(exports)!=1 or exports[0][1]!='"compress"' or exports[0][2][0]!='func':raise Unsupported('one compress export')
        self.entry=int(exports[0][2][1]);self.functions=[];self.d=DAG();self.memory={};self.steps=0;self.calls=0
        for x in module[1:]:
            if x[0]!='func':continue
            declarations={name:[t for y in x[1:] if y[0]==name for t in y[1:]] for name in ('param','result','local')}
            if any(t!='i32' for vs in declarations.values() for t in vs):raise Unsupported('i32 functions only')
            body=[e for e in x[1:] if e[0] not in ('type','param','result','local')]
            self.functions.append((len(declarations['param']),len(declarations['result']),len(declarations['local']),body))
    def read(self,p):
        if p<0 or p%4 or p+4>65536:raise Unsupported('aligned bounded memory')
        if p not in self.memory:self.memory[p]=self.d.node('initial',p)
        return self.memory[p]
    def address(self,node,attrs):
        p=self.d.cv(node)
        if p is None:raise Unsupported('symbolic address')
        for a in attrs:
            if a.startswith('offset='):p+=int(a[7:],0)
            elif not a.startswith('align='):raise Unsupported('memory attribute '+a)
        if p<0 or p%4 or p+4>65536:raise Unsupported('bounded aligned access')
        return p
    def call(self,index,args,depth=0):
        if depth>64:raise Unsupported('call depth')
        self.calls+=1;np,nr,nl,body=self.functions[index]
        if len(args)!=np:raise Unsupported('arity')
        locals_=list(args)+[self.d.const(0)]*nl;stack=[]
        def pop(n):
            if len(stack)<n:raise Unsupported('stack underflow')
            if n==0:return []
            a=stack[-n:];del stack[-n:];return a
        def ev(e):
            self.steps+=1
            if self.steps>4000000:raise Unsupported('instruction limit')
            tag=e[0]
            if tag=='block':
                for x in e[1:]:
                    if isinstance(x,list) and x[0] not in ('type','result'):ev(x)
                return
            for x in e[1:]:
                if isinstance(x,list):ev(x)
            attrs=[x for x in e[1:] if isinstance(x,str)]
            if tag=='i32.const':stack.append(self.d.const(int(attrs[0],0)))
            elif tag=='local.get':stack.append(locals_[int(attrs[0])])
            elif tag in ('local.set','local.tee'):
                v=pop(1)[0];locals_[int(attrs[0])]=v
                if tag=='local.tee':stack.append(v)
            elif tag=='drop':pop(1)
            elif tag=='nop':pass
            elif tag=='return':raise Return()
            elif tag=='call':
                ix=int(attrs[0]);count=self.functions[ix][0];stack.extend(self.call(ix,pop(count),depth+1))
            elif tag=='i32.load':stack.append(self.read(self.address(pop(1)[0],attrs)))
            elif tag=='i32.store':
                a,v=pop(2);self.memory[self.address(a,attrs)]=v
            elif tag=='memory.copy':
                d,s,n=[self.d.cv(x) for x in pop(3)]
                if None in (d,s,n) or d%4 or s%4 or n%4 or max(d,s)+n>65536:raise Unsupported('bounded aligned constant copy')
                snapshot=[self.read(s+i) for i in range(0,n,4)]
                for i,v in enumerate(snapshot):self.memory[d+4*i]=v
            elif tag.startswith('i32.') and tag[4:] in ('xor','and','or','add','sub','mul','rotl','rotr','shl','shr_u'):stack.append(self.d.make(tag[4:],*pop(2)))
            else:raise Unsupported('instruction '+tag)
        try:
            for e in body:ev(e)
        except Return:pass
        if len(stack)!=nr:raise Unsupported('return stack '+str((len(stack),nr)))
        return stack

def recover(src,dst):
    t=time.perf_counter();module=q.read(src);read_ms=1000*(time.perf_counter()-t);t=time.perf_counter();ex=Engine(module);np,nr,_,_=ex.functions[ex.entry]
    roots=ex.call(ex.entry,[ex.d.node('param',i) for i in range(np)]);wat=ex.d.wat(roots,np);analysis_ms=1000*(time.perf_counter()-t)
    t=time.perf_counter();q.compile(wat,dst);compile_ms=1000*(time.perf_counter()-t)
    reachable=ex.d.reachable(roots)
    return {'input_sha256':q.digest(src),'output_sha256':q.digest(dst),'input_bytes':Path(src).stat().st_size,'output_bytes':Path(dst).stat().st_size,'read_ms':read_ms,'analysis_ms':analysis_ms,'compile_ms':compile_ms,'instructions':ex.steps,'calls':ex.calls,'nodes_created':len(ex.d.nodes),'nodes_live':len(reachable),'operations_live':sum(ex.d.nodes[x][0] not in ('param','const') for x in reachable),'xor_cancellations_and_folds':ex.d.simplifications,'output_fingerprints':ex.d.fingerprint(roots),'entry_memory_dependencies':0}
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('src');ap.add_argument('dst');a=ap.parse_args();r=recover(a.src,a.dst);Path(a.dst).with_suffix('.json').write_text(json.dumps(r,indent=2));print(json.dumps({k:v for k,v in r.items() if k!='output_fingerprints'}))
