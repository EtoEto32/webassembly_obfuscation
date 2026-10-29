"""Partial-evaluate known control state, preserving scalar operations/effects.

Reads a Wasm binary only. Symbolic branches are explicitly unsupported.
This is a deliberately limited ordinary constant-control specializer.
"""
import argparse
import json
from pathlib import Path
import time
import transform as t


def program(mod):
    types=[]
    for x in mod[1:]:
        if x[0]=='type':types.append(x[-1])
    def sig(node):
        params=[v for x in node[1:] if isinstance(x,list) and x[0]=='param' for v in x[1:]]
        results=[v for x in node[1:] if isinstance(x,list) and x[0]=='result' for v in x[1:]]
        refs=[x for x in node[1:] if isinstance(x,list) and x[0]=='type']
        if refs and not params and not results:return sig(types[int(refs[0][1])])
        return params,results
    ins=[]
    def emit(x):
        if isinstance(x,str):ins.append((x,(),None));return
        op=x[0]
        if op in ('block','loop','if'):
            body=[v for v in x[1:] if not (isinstance(v,list) and v[0] in ('type','param','result'))]
            start=None
            if op=='if':
                for v in body:
                    if isinstance(v,list) and v[0] not in ('then','else'):emit(v)
            start=len(ins);ins.append((op,(),sig(x)))
            for v in body:
                if op!='if':emit(v)
                elif isinstance(v,list) and v[0] in ('then','else'):
                    if v[0]=='else':ins.append(('else',(),None))
                    for child in v[1:]:emit(child)
            ins.append(('end',(),None));return
        args=[]
        for v in x[1:]:
            if isinstance(v,list):emit(v)
            else:args.append(v)
        ins.append((op,tuple(args),None))
    functions=[x for x in mod[1:] if x[0]=='func']
    if len(functions)!=1 or any(x[0] not in ('type','func','export','memory','data') for x in mod[1:]):raise ValueError('Outside module profile')
    f=functions[0];decl=[]
    for x in f[1:]:
        if isinstance(x,list) and x[0] in ('param','result','type','local'):decl.append(x)
        else:emit(x)
    links={};pending=[]
    for i,(op,args,signature) in enumerate(ins):
        if op in ('block','loop','if'):pending.append(i);links[i]={'else':None}
        elif op=='else':links[pending[-1]]['else']=i
        elif op=='end':links[pending.pop()]['end']=i
    if pending:raise ValueError('Unbalanced controls')
    return decl,ins,links


def const32(op,a):
    mask=2**32-1
    def s(x):return x-2**32 if x>=2**31 else x
    if op=='i32.eqz':return int(a[0]==0)
    if len(a)!=2:return None
    x,y=a
    if op=='i32.add':return (x+y)&mask
    if op=='i32.sub':return (x-y)&mask
    if op=='i32.mul':return (x*y)&mask
    if op=='i32.and':return x&y
    if op=='i32.or':return x|y
    if op=='i32.xor':return x^y
    if op=='i32.shl':return (x<<(y&31))&mask
    if op=='i32.shr_u':return x>>(y&31)
    if op=='i32.shr_s':return (s(x)>>(y&31))&mask
    if op=='i32.eq':return int(x==y)
    if op=='i32.ne':return int(x!=y)
    for relation,fn in [('lt',lambda a,b:a<b),('le',lambda a,b:a<=b),('gt',lambda a,b:a>b),('ge',lambda a,b:a>=b)]:
        if op=='i32.'+relation+'_u':return int(fn(x,y))
        if op=='i32.'+relation+'_s':return int(fn(s(x),s(y)))
    return None


def model(mod):
    decl,ins,links=program(mod)
    params=[v for x in decl if x[0]=='param' for v in x[1:]]
    locals_=[v for x in decl if x[0]=='local' for v in x[1:]]
    results=[v for x in decl if x[0]=='result' for v in x[1:]]
    # Values are (type, WAT expression, known i32 value or None).
    env=[(kind,f'(local.get {i})',None) for i,kind in enumerate(params)]
    env += [(kind,f'({kind}.const 0)',0 if kind=='i32' else None) for kind in locals_]
    stack=[];frames=[{'kind':'function','height':0,'params':[],'results':results,'start':-1,'end':len(ins)}]
    output=[];temps=[];pc=0;steps=0;branches=0;folded=0
    def take(n):
        if n>len(stack):raise ValueError('Underflow during specialization')
        if n==0:return []
        values=stack[-n:];del stack[-n:];return values
    def jump(depth):
        nonlocal stack,frames,pc,branches
        index=len(frames)-1-depth
        if index<0:raise ValueError('Invalid branch depth')
        frame=frames[index];isloop=frame['kind']=='loop'
        values=take(len(frame['params'] if isloop else frame['results']))
        stack=stack[:frame['height']]+values
        frames=frames[:index+1] if isloop else frames[:index]
        pc=frame['start']+1 if isloop else frame['end']+1
        branches+=1
    while pc<len(ins):
        steps+=1
        if steps>100000:raise ValueError('Specialization step budget exceeded')
        op,args,signature=ins[pc]
        if op in ('block','loop','if'):
            condition=take(1)[0][2] if op=='if' else None
            if op=='if' and condition is None:raise ValueError('Symbolic branch (not a protection score)')
            ps,rs=signature;link=links[pc]
            frames.append({'kind':op,'height':len(stack)-len(ps),'params':ps,'results':rs,'start':pc,'end':link['end']})
            if op=='if' and condition==0:
                pc=link['else']+1 if link['else'] is not None else link['end'];continue
            pc+=1;continue
        if op=='else':pc=frames[-1]['end'];continue
        if op=='end':
            frame=frames.pop();values=take(len(frame['results']));stack=stack[:frame['height']]+values;pc+=1;continue
        if op=='br':jump(int(args[0]));continue
        if op=='return':jump(len(frames)-1);continue
        if op in ('br_if','br_table'):
            condition=take(1)[0][2]
            if condition is None:raise ValueError('Symbolic branch (not a protection score)')
            if op=='br_if':
                if condition:jump(int(args[0]));continue
            else:
                jump(int(args[min(condition,len(args)-1)]));continue
            pc+=1;continue
        if op=='nop':pc+=1;continue
        if op=='drop':take(1);pc+=1;continue
        if op=='local.get':stack.append(env[int(args[0])]);pc+=1;continue
        if op in ('local.set','local.tee'):
            value=take(1)[0];env[int(args[0])]=value
            if op=='local.tee':stack.append(value)
            pc+=1;continue
        if op.endswith('.const'):
            kind=op.split('.')[0];value=(int(args[0])&0xffffffff) if kind=='i32' else None
            stack.append((kind,'('+op+' '+' '.join(args)+')',value));pc+=1;continue
        before=[v[0] for v in stack];after=list(before)
        t.effect((op,*args),after,params+locals_)
        returns=0 if '.store' in op else 1
        values=take(len(before)+returns-len(after))
        known=None
        if op.startswith('i32.') and all(v[2] is not None for v in values):
            known=const32(op,[v[2] for v in values])
        if op=='select' and values[2][2] is not None:
            stack.append(values[0] if values[2][2] else values[1]);folded+=1
        elif known is not None:
            stack.append(('i32',f'(i32.const {known if known<2**31 else known-2**32})',known));folded+=1
        else:
            expression='('+op+' '+' '.join(args)+' '+' '.join(v[1] for v in values)+')'
            if returns:
                kind=after[-1];index=len(temps);temps.append(kind)
                output.append(f'(local.set $v{index} {expression})');stack.append((kind,f'(local.get $v{index})',None))
            else:output.append(expression)
        pc+=1
    if [v[0] for v in stack]!=results:raise ValueError('Result stack mismatch')
    declarations=[x for x in decl if x[0]!='local']
    declarations_text=' '.join(t.w.emit(x) for x in declarations)+' '+' '.join(f'(local $v{i} {kind})' for i,kind in enumerate(temps))
    fn='(func '+declarations_text+' '+' '.join(output+[v[1] for v in stack])+')'
    wat='(module '+' '.join(fn if x[0]=='func' else t.w.emit(x) for x in mod[1:])+')'
    return wat,{'steps':steps,'constant_control_branches':branches,'folded_operations':folded,'emitted_operations':len(output),'temporary_locals':len(temps)}


def recover(src,out):
    if out.exists():raise ValueError('Refuse overwrite')
    start=time.perf_counter();mod=t.w.parse(t.w.tool('wasm2wat',[src,'--fold-exprs','--no-debug-names']))
    a=time.perf_counter();wat,report=model(mod);report['analysis_seconds']=time.perf_counter()-a
    out.parent.mkdir(parents=True,exist_ok=True);wp=out.with_suffix('.wat');wp.write_text(wat,encoding='utf-8')
    t.w.tool('wat2wasm',[wp,'-o',out]);t.w.tool('wasm-validate',[out]);report['total_seconds']=time.perf_counter()-start
    report['status']='recovered';return report


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('input',type=Path);ap.add_argument('output',type=Path)
    a=ap.parse_args();print(json.dumps(recover(a.input,a.output)))
