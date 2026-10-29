"""Equal-stack-shape splitting and two matched flattening representations.

The typed block arguments are standard Wasm, not a claimed new primitive.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import time

spec=importlib.util.spec_from_file_location('stack_cycle_common',Path(__file__).resolve().parents[1]/'connectivity-elimination/prototype.py')
w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
SCALARS=('i32','i64','f32','f64')


def flat(x):
    if isinstance(x,str):
        if x!='nop': raise ValueError('Unsupported statement token: '+x)
        return [(x,)]
    if not isinstance(x,list) or not x: raise ValueError('Bad expression')
    out=[];immediates=[]
    for value in x[1:]:
        if isinstance(value,list):out.extend(flat(value))
        else:immediates.append(value)
    out.append((x[0],*immediates))
    return out


def effect(ins,stack,local_types):
    op=ins[0]
    def pop(t=None):
        if not stack:raise ValueError('Stack underflow')
        actual=stack.pop()
        if t is not None and actual!=t:raise ValueError('Type mismatch')
        return actual
    if op=='nop':return
    if op=='drop':pop();return
    if op in ('local.get','local.set','local.tee'):
        t=local_types[int(ins[1])]
        if op!='local.get':pop(t)
        if op!='local.set':stack.append(t)
        return
    if op=='select':
        pop('i32');b=pop();pop(b);stack.append(b);return
    t,_,tail=op.partition('.')
    if t not in SCALARS:raise ValueError('Outside straight-line scalar profile: '+op)
    if tail=='const':stack.append(t);return
    if tail.startswith('load'):
        pop('i32');stack.append(t);return
    if tail.startswith('store'):
        pop(t);pop('i32');return
    if tail in ('add','sub','mul','div_s','div_u','rem_s','rem_u','and','or','xor','shl','shr_s','shr_u','rotl','rotr','div','min','max','copysign'):
        pop(t);pop(t);stack.append(t);return
    if tail in ('eq','ne','lt_s','lt_u','gt_s','gt_u','le_s','le_u','ge_s','ge_u','lt','gt','le','ge'):
        pop(t);pop(t);stack.append('i32');return
    if tail in ('clz','ctz','popcnt','abs','neg','sqrt','ceil','floor','trunc','nearest','extend8_s','extend16_s','extend32_s','eqz'):
        pop(t);stack.append('i32' if tail=='eqz' else t);return
    conversions={'i32.wrap_i64':'i64','i64.extend_i32_u':'i32','i64.extend_i32_s':'i32',
                 'i32.reinterpret_f32':'f32','f32.reinterpret_i32':'i32','i64.reinterpret_f64':'f64','f64.reinterpret_i64':'i64',
                 'f64.promote_f32':'f32','f32.demote_f64':'f64'}
    for target in ('f32','f64'):
        for source in ('i32','i64'):
            for sign in ('s','u'):conversions[f'{target}.convert_{source}_{sign}']=source
    for target in ('i32','i64'):
        for source in ('f32','f64'):
            for sign in ('s','u'):conversions[f'{target}.trunc_{source}_{sign}']=source
    if op in conversions:pop(conversions[op]);stack.append(t);return
    raise ValueError('Unsupported scalar operation: '+op)


def source(path):
    w.tool('wasm-validate',[path])
    mod=w.parse(w.tool('wasm2wat',[path,'--fold-exprs','--no-debug-names']))
    if any(x[0] not in ('type','func','export','memory','data') for x in mod[1:]):
        raise ValueError('Only one defined function, optional memory/data/exports are supported')
    functions=[x for x in mod[1:] if x[0]=='func']
    if len(functions)!=1:raise ValueError('Expected one defined function')
    f=functions[0]
    decl=[x for x in f[1:] if isinstance(x,list) and x[0] in ('param','result','local','type')]
    params=[v for x in decl if x[0]=='param' for v in x[1:]]
    locals_=[v for x in decl if x[0]=='local' for v in x[1:]]
    results=[v for x in decl if x[0]=='result' for v in x[1:]]
    if any(v not in SCALARS for v in params+locals_+results):raise ValueError('Only scalar values supported')
    body=[]
    for x in f[1:]:
        if x not in decl:body.extend(flat(x))
    if len(body)>1024:raise ValueError('Prototype instruction budget (1024) exceeded')
    stack=[];shapes=[()]
    for ins in body:
        effect(ins,stack,params+locals_);shapes.append(tuple(stack))
    if stack!=results:raise ValueError('Final stack mismatch')
    return mod,decl,body,shapes,len(params),len(locals_)


def cuts_for(shapes,count):
    if not 1 <= count <= 128:raise ValueError('Fragment count must be in 1..128')
    groups={}
    for i,shape in enumerate(shapes):
        if shape:groups.setdefault(shape,[]).append(i)
    eligible=[(positions[-1]-positions[0],len(shape),shape,positions) for shape,positions in groups.items() if len(positions)>=count+1]
    if not eligible:raise ValueError('Not enough repeated nonempty stack shapes')
    _,_,shape,pos=max(eligible)
    n=len(pos);inf=10**12
    dp=[[inf]*n for _ in range(count+1)];parent={};dp[0][0]=0
    for pieces in range(1,count+1):
        for j in range(pieces,n):
            best=min((max(dp[pieces-1][k],pos[j]-pos[k]),k) for k in range(pieces-1,j))
            dp[pieces][j]=best[0];parent[pieces,j]=best[1]
    chosen=[pos[-1]];j=n-1
    for pieces in range(count,0,-1):
        j=parent[pieces,j];chosen.append(pos[j])
    chosen.reverse()
    assert len(chosen)==count+1 and all(shapes[i]==shape for i in chosen)
    return shape,chosen,dp[count][n-1]


def instructions(body):return '\n'.join(' '.join(ins) for ins in body)


def output(mod,decl,body,shape,cuts,mode,seed=20261018):
    nparam=sum(len(x)-1 for x in decl if x[0]=='param')
    nlocal=sum(len(x)-1 for x in decl if x[0]=='local')
    spill=list(range(nparam+nlocal,nparam+nlocal+len(shape)))
    pc=nparam+nlocal+len(shape)
    count=len(cuts)-1;order=list(range(count));random.Random(seed).shuffle(order)
    fragments=[body[cuts[i]:cuts[i+1]] for i in range(count)]
    get='\n'.join(f'local.get {i}' for i in spill)
    put='\n'.join(f'local.set {i}' for i in reversed(spill))
    added=[] if mode=='payload' else [['local',*shape,'i32']]
    lines=[instructions(body[:cuts[0]])]
    if mode=='payload':
        sig='(param '+' '.join((*shape,'i32'))+') (result '+' '.join(shape)+')'
        block_sig=sig
        lines+=['i32.const 0',f'(block $done {sig}',f'(loop $dispatch {sig}']
    else:
        block_sig=''
        lines+=[put,f'i32.const 0\nlocal.set {pc}','(block $done','(loop $dispatch']
    for i in order:lines.append(f'(block $case{i} {block_sig}')
    if mode!='payload':lines.append(f'local.get {pc}')
    lines.append('br_table '+' '.join(f'$case{i}' for i in range(count))+' $done')
    for i in reversed(order):
        lines.append(')')
        if mode!='payload':lines.append(get)
        lines.append(instructions(fragments[i]))
        if mode!='payload':lines.append(put)
        if i==count-1:lines.append('br $done')
        elif mode=='payload':lines.append(f'i32.const {i+1}\nbr $dispatch')
        else:lines.append(f'i32.const {i+1}\nlocal.set {pc}\nbr $dispatch')
    lines+=['))']
    if mode!='payload':lines.append(get)
    lines.append(instructions(body[cuts[-1]:]))
    fn='(func '+' '.join(w.emit(x) for x in decl+added)+'\n'+'\n'.join(lines)+')'
    return '(module\n'+'\n'.join(fn if x[0]=='func' else w.emit(x) for x in mod[1:])+'\n)',order


def transform(src,out,mode='payload',count=8):
    if mode not in ('payload','locals'):raise ValueError('Unknown transport mode')
    if out.exists():raise ValueError('Refuse overwrite')
    started=time.perf_counter()
    mod,decl,body,shapes,nparam,nlocal=source(src)
    shape,cuts,max_length=cuts_for(shapes,count)
    text,order=output(mod,decl,body,shape,cuts,mode)
    out.parent.mkdir(parents=True,exist_ok=True);wp=out.with_suffix('.wat');wp.write_text(text,encoding='utf-8')
    w.tool('wat2wasm',[wp,'-o',out]);w.tool('wasm-validate',[out])
    report={'mode':mode,'shape':shape,'cuts':cuts,'physical_order':order,'source_instructions':len(body),
            'protected_instructions':cuts[-1]-cuts[0],'largest_fragment':max_length,
            'added_locals':0 if mode=='payload' else len(shape)+1,
            'seconds':time.perf_counter()-started,'input_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),
            'output_sha256':hashlib.sha256(out.read_bytes()).hexdigest()}
    Path(str(out)+'.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    return report


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('input',type=Path);ap.add_argument('output',type=Path)
    ap.add_argument('--mode',choices=['payload','locals'],default='payload');ap.add_argument('--fragments',type=int,default=8)
    a=ap.parse_args();print(json.dumps(transform(a.input,a.output,a.mode,a.fragments)))
