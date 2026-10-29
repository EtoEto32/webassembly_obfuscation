"""Direct local-variable lowering and binary-only symbolic interpretation."""
import time
import argparse
import json
import prototype as p

def render(r):
    n,d=r['n'],r['d'];rot=n;act=rot+d;new=act+d+2;m0=new+d+2;m1=m0+1;counter=m1+1
    get=lambda i:f'(local.get {i})'
    put=lambda i,e:f'(local.set {i} {e})'
    init=''.join(put(rot+i,get(i)) for i in range(n))+put(act,'(i32.const -1)')+put(counter,f'(i32.const {r["bound"]})')
    body=''.join(put(new+i,'(i32.const 0)') for i in range(d))+''.join(put(new+i,get(act+i)) for i in (d,d+1))
    for v,(left,right) in enumerate(r['edges']):
        body+=put(m0,f'(i32.and {get(act+v)} (i32.xor {get(rot+v)} (i32.const -1)))')+put(m1,f'(i32.and {get(act+v)} {get(rot+v)})')
        body+=put(rot+v,f'(i32.xor {get(rot+v)} {get(act+v)})')
        body+=put(new+left,f'(i32.or {get(new+left)} {get(m0)})')+put(new+right,f'(i32.or {get(new+right)} {get(m1)})')
    body+=''.join(put(act+i,get(new+i)) for i in range(d+2))
    body+=f'(br_if 0 (local.tee {counter} (i32.sub {get(counter)} (i32.const 1))))'
    return f'(module (func (export "run") (param {" ".join(["i32"]*n)}) (result i32) (local {" ".join(["i32"]*(counter+1-n))}) {init} (loop {body}) {get(act+d+1)}))'

def recover(binary):
    started=time.perf_counter();p.w.tool('wasm-validate',[binary]);mod=p.w.parse(p.w.tool('wasm2wat',[binary,'--fold-exprs','--no-debug-names']))
    if any(x[0] not in ('type','func','export') for x in mod[1:]):raise ValueError('Unsupported module')
    fs=[x for x in mod[1:] if x[0]=='func'];exports=[x for x in mod[1:] if x[0]=='export']
    if len(fs)!=1 or exports!=[['export','"run"',['func','0']]]:raise ValueError('Expected sole run export')
    f=fs[0];decl=[x for x in f[1:] if isinstance(x,list) and x[0] in ('type','param','result','local')]
    if any(t!='i32' for x in decl if x[0]!='type' for t in x[1:]):raise ValueError('i32 only')
    n=sum(len(x)-1 for x in decl if x[0]=='param');nl=sum(len(x)-1 for x in decl if x[0]=='local')
    b=p.reader.BDD();env=[('b',b.mk(i,0,1)) for i in range(n)]+[('c',0)]*nl;stack=[];count=0;iterations=0;parse_ms=1000*(time.perf_counter()-started);started=time.perf_counter()
    def bit(v):
        if v[0]=='b':return v[1]
        if v[1] in (0,p.MASK):return int(bool(v[1]))
        raise ValueError('Nonuniform word constant in symbolic lane expression')
    def execute(seq):
        nonlocal count,iterations
        for ins in seq:
            count+=1
            if count>100000:raise TimeoutError('instruction budget')
            if not isinstance(ins,list):raise ValueError('Unexpected atom')
            op=ins[0]
            if op in ('loop','block'):
                nested=[x for x in ins[1:] if isinstance(x,list)]
                while True:
                    if op=='loop':iterations+=1
                    jump=execute(nested)
                    if jump is None:break
                    if jump>0:return jump-1
                    if op=='block':break
                continue
            children=[x for x in ins[1:] if isinstance(x,list)]
            jump=execute(children)
            if jump is not None:raise ValueError('Branch in operand expression')
            args=[x for x in ins[1:] if not isinstance(x,list)]
            if op=='local.get':stack.append(env[int(args[0])])
            elif op=='i32.const':stack.append(('c',int(args[0])&p.MASK))
            elif op in ('local.set','local.tee'):
                env[int(args[0])]=stack[-1]
                if op=='local.set':stack.pop()
            elif op=='drop':stack.pop()
            elif op=='nop':pass
            elif op=='br_if':
                v=stack.pop()
                if v[0]!='c':raise ValueError('Input-dependent branch unsupported')
                if v[1]:return int(args[0])
            elif op=='i32.eqz':
                v=stack.pop()
                if v[0]!='c':raise ValueError('Symbolic whole-word eqz unsupported')
                stack.append(('c',int(v[1]==0)))
            elif op in ('i32.and','i32.or','i32.xor','i32.add','i32.sub'):
                right,left=stack.pop(),stack.pop();kind=op[4:]
                if left[0]==right[0]=='c':
                    a,c=left[1],right[1];v={'and':lambda:a&c,'or':lambda:a|c,'xor':lambda:a^c,'add':lambda:a+c,'sub':lambda:a-c}[kind]();stack.append(('c',v&p.MASK))
                elif kind in ('and','or','xor'):stack.append(('b',b.binary(kind,bit(left),bit(right))))
                else:raise ValueError('Nonbitwise symbolic arithmetic')
            else:raise ValueError('Unsupported instruction '+op)
        return None
    if execute([x for x in f[1:] if isinstance(x,list) and x not in decl]) is not None or len(stack)!=1:raise ValueError('Bad terminal stack')
    memo={0:('const',0),1:('const',p.MASK)}
    def expression(v):
        if v not in memo:
            i,lo,hi=b.nodes[v];a,c=expression(lo),expression(hi);memo[v]=('xor',a,('and',('var',i),('xor',a,c)))
        return memo[v]
    t=expression(bit(stack[0]));return n,t,{'status':'recovered','parse_ms':parse_ms,'analysis_ms':1000*(time.perf_counter()-started),'bdd_nodes':len(b.nodes),'instructions':count,'iterations':iterations,'input_assignments':0}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['lower','recover']);ap.add_argument('input');ap.add_argument('output');ap.add_argument('--tight',action='store_true');a=ap.parse_args()
    if a.mode=='lower':
        r=p.read(a.input);traces=[p.simulate(r,x) for x in range(1<<r['n'])]
        if any(y is None for y,_ in traces):raise ValueError('Graph not total within bound')
        if a.tight:r['bound']=max(len(t) for _,t in traces)
        p.save(render(r),a.output);print(json.dumps({'mode':'lower','bound':r['bound']}))
    else:
        n,f,r=recover(a.input);p.save(p.w.plain_wat(n,'"run"',f),a.output);print(json.dumps(r))
