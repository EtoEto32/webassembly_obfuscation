# -*- coding: utf-8 -*-
"""An intentionally restricted dirty-memory prototype and exact-normal-form gate."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
spec = importlib.util.spec_from_file_location('catalytic_wasm', ROOT/'research/connectivity-elimination/prototype.py')
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)
MASK = 0xffffffff


def save(text, dest):
    dest = Path(dest)
    if dest.exists() or dest.with_suffix('.wat').exists():
        raise FileExistsError(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.with_suffix('.wat').write_text(text, encoding='utf8')
    w.tool('wat2wasm', [dest.with_suffix('.wat'), '-o', dest])
    w.tool('wasm-validate', [dest])


def module(body, n, locals=0):
    decl = '(local ' + ' '.join(['i32']*locals) + ')' if locals else ''
    return '(module (memory (export "memory") 1 1) (func (export "run") (param '+ ' '.join(['i32']*n)+') (result i32) '+decl+' '+body+'))'


def parsed(file):
    w.tool('wasm-validate', [file])
    mod = w.parse(w.tool('wasm2wat', [file, '--fold-exprs']))
    if any(a[0] not in ('type','memory','func','export') for a in mod[1:]):
        raise ValueError('Unsupported module fields')
    if [a for a in mod[1:] if a[0]=='memory'] != [['memory','1','1']]:
        raise ValueError('One bounded memory page required')
    funcs = [a for a in mod[1:] if a[0]=='func']
    if len(funcs)!=1: raise ValueError('One function required')
    exports = sorted(w.emit(a) for a in mod[1:] if a[0]=='export')
    if exports != sorted(['(export "memory" (memory 0))','(export "run" (func 0))']):
        raise ValueError('Expected run and memory exports')
    f = funcs[0]
    n = sum(len(a)-1 for a in f[1:] if a[0]=='param')
    locals = sum(len(a)-1 for a in f[1:] if a[0]=='local')
    if n not in (2,3) or [a for a in f[1:] if a[0]=='result'] != [['result','i32']]:
        raise ValueError('Bad signature')
    if any(t!='i32' for a in f[1:] if a[0] in ('param','local') for t in a[1:]):
        raise ValueError('Only i32')
    return n, locals, [a for a in f[1:] if a[0] not in ('param','local','result','type')]


def transform(src, dest, broken=False):
    start=time.perf_counter(); n,loc,body=parsed(src)
    if loc or len(body)!=1: raise ValueError('One expression source, no locals')
    t=body[0]; division=t[0]=='i32.div_u'
    core=t[1] if division else t
    if division and (n!=3 or t[2]!=['local.get','2']): raise ValueError('Expected quotient denominator parameter 2')
    if core not in (['i32.mul',['local.get','0'],['local.get','1']], ['i32.and',['local.get','0'],['local.get','1']]):
        raise ValueError('Only a two-input product or AND')
    if n!=(3 if division else 2):raise ValueError('Unexpected arity')
    bit=core[0]=='i32.and'; change='xor' if bit else 'add'; undo='xor' if bit else 'sub'; combine='xor' if bit else 'sub'
    load='(i32.load (i32.const 0))'
    first=f'(i32.store (i32.const 0) (i32.{change} {load} (local.get 0)))'
    middle=f'(local.set {n} ({core[0]} {load} (local.get 1)))'
    restore=f'(i32.store (i32.const 0) (i32.{undo} {load} (local.get 0)))'
    result=f'(i32.{combine} (local.get {n}) ({core[0]} {load} (local.get 1)))'
    if broken:
        if not division:raise ValueError('Broken probe needs division')
        # Produce the right normal output, but divide before restoration.
        old=f'(i32.{undo} {load} (local.get 0))'
        result=f'(i32.{combine} (local.get {n}) ({core[0]} {old} (local.get 1)))'
        text=first+middle+f'(local.set {n} (i32.div_u {result} (local.get 2)))'+restore+f'(local.get {n})'
    else:
        if division:result=f'(i32.div_u {result} (local.get 2))'
        text=first+middle+restore+result
    save(module(text,n,1),dest)
    return {'transform_ms':(time.perf_counter()-start)*1000,'bytes':Path(dest).stat().st_size}


# Canonical polynomials: monomial tuple -> coefficient. Ring is Z/2^32 for
# arithmetic; Boolean ANF has XOR coefficients and idempotent variables.
def add(a,b,bit,sign=1):
    out=dict(a)
    for k,v in b.items():
        out[k]=(out.get(k,0)+sign*v) % (2 if bit else 2**32)
        if not out[k]:del out[k]
    return out


def mul(a,b,bit):
    out={}
    for ka,va in a.items():
        for kb,vb in b.items():
            key=tuple(sorted(set(ka+kb) if bit else ka+kb))
            out=add(out,{key:va*vb},bit)
    return out


def poly(t,bit):
    op=t[0]
    if op=='v':return {(str(t[1]),):1}
    if op=='k':
        if bit and t[1] not in (0,MASK):raise ValueError('Nonuniform bit constant')
        value=(bool(t[1]) if bit else t[1]&MASK)
        return {():int(value)} if value else {}
    allowed=('xor','and') if bit else ('add','sub','mul')
    if op not in allowed:raise ValueError('Mixed algebra / unsupported expression: '+op)
    a,b=poly(t[1],bit),poly(t[2],bit)
    return mul(a,b,bit) if op in ('mul','and') else add(a,b,bit,-1 if op=='sub' else 1)


def pexpr(p,bit):
    out=[]
    for vars,c in sorted(p.items()):
        factors=[['local.get',v[1:]] for v in vars]
        if any(not v.startswith('p') for v in vars):raise ValueError('Depends on borrowed memory')
        if not bit and (c!=1 or not factors):factors.insert(0,['i32.const',str(c)])
        if not factors:factors=[['i32.const','-1']]
        e=factors[0]
        for f in factors[1:]:e=['i32.and' if bit else 'i32.mul',e,f]
        out.append(e)
    if not out:return ['i32.const','0']
    e=out[0]
    for f in out[1:]:e=['i32.xor' if bit else 'i32.add',e,f]
    return e


def recover(src,dest):
    start=time.perf_counter();n,loc,body=parsed(src);reader=(time.perf_counter()-start)*1000
    bit='i32.and' in w.emit(body)
    initial=('v','c'); memory=initial; env=[('v','p'+str(j)) for j in range(n)]+[('k',0)]*loc
    traps=[]; stack=[]
    def execute(t):
        nonlocal memory
        op=t[0]
        if op=='i32.const':stack.append(('k',int(t[1])&MASK));return
        if op=='local.get':stack.append(env[int(t[1])]);return
        if op not in ('local.set','local.tee','i32.load','i32.store','i32.add','i32.sub','i32.mul','i32.and','i32.xor','i32.div_u'):
            raise ValueError('Unsupported opcode '+op)
        # Folded WAT can retain operands on the stack across stores. Children
        # are executed before the enclosing opcode, exactly as in flat Wasm.
        for child in t[1:]:
            if isinstance(child,list):execute(child)
        if op in ('local.set','local.tee'):
            val=stack.pop();env[int(t[1])]=val
            if op.endswith('tee'):stack.append(val)
            return
        if op in ('i32.load','i32.store'):
            attrs=[a for a in t[1:] if isinstance(a,str)]
            if any(a not in ('align=4','offset=0') for a in attrs):raise ValueError('Nonzero/unsupported memory immediate')
            val=stack.pop() if op=='i32.store' else None
            if stack.pop()!=('k',0):raise ValueError('Only aligned private slot zero')
            if op=='i32.load':stack.append(memory)
            else:memory=val
            return
        if op in ('i32.add','i32.sub','i32.mul','i32.and','i32.xor'):
            b=stack.pop();a=stack.pop();stack.append((op[4:],a,b));return
        if op=='i32.div_u':
            b=stack.pop();a=stack.pop();traps.append(memory)
            stack.append(('div_u',a,b));return
    for expr in body:execute(expr)
    if len(stack)!=1:raise ValueError('Expected one final value')
    result=stack[0]
    if poly(memory,bit)!=poly(initial,bit):return {'status':'memory_changed','reader_ms':reader}
    if any(poly(state,bit)!=poly(initial,bit) for state in traps):
        return {'status':'trap_memory_changed','reader_ms':reader}
    def norm(t):
        if t[0]=='div_u':return ['i32.div_u',norm(t[1]),norm(t[2])]
        return pexpr(poly(t,bit),bit)
    simplified=norm(result)
    proof_ms=(time.perf_counter()-start)*1000-reader
    save(module(w.emit(simplified),n),dest)
    return {'status':'recovered','reader_ms':reader,'proof_ms':proof_ms,'expression':w.emit(simplified),'bytes':Path(dest).stat().st_size,'trap_points':len(traps)}


def run(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=False);(out/'sources').mkdir()
    for f in ('gate.py','check.cjs','plan.md'):shutil.copyfile(HERE/f,out/'sources'/f)
    manifest={'targets':[],'transforms':[],'recoveries':[],'negative':[]}
    fixtures={'and':(2,'(i32.and (local.get 0) (local.get 1))'), 'mul':(2,'(i32.mul (local.get 0) (local.get 1))'), 'div':(3,'(i32.div_u (i32.mul (local.get 0) (local.get 1)) (local.get 2))')}
    for name,(n,expr) in fixtures.items():
        source=out/(name+'-plain.wasm');save(module(expr,n),source)
        dest=out/(name+'-borrowed.wasm')
        manifest['transforms'].append({'fixture':name,**transform(source,dest)})
        for mode in ('plain','borrowed'):
            raw=out/(name+'-'+mode+'.wasm');opt=raw.with_stem(raw.stem+'-O3')
            w.tool('wasm-opt',[raw,'-O3','-o',opt]);w.tool('wasm-validate',[opt])
            for form,file in [('raw',raw),('O3',opt)]:
                target={'fixture':name,'mode':mode,'form':form,'file':file.name,'bytes':file.stat().st_size,'n':n}
                manifest['targets'].append(target)
                if mode=='borrowed':
                    rec=file.with_stem(file.stem+'-recovered')
                    result=recover(file,rec);manifest['recoveries'].append({**target,**result})
                    if result['status']=='recovered':manifest['targets'].append({**target,'mode':'recovered','file':rec.name,'bytes':rec.stat().st_size})
    bad=out/'div-broken.wasm';transform(out/'div-plain.wasm',bad,True)
    for form in ('raw','O3'):
        f=bad if form=='raw' else bad.with_stem('div-broken-O3')
        if form=='O3':w.tool('wasm-opt',[bad,'-O3','-o',f]);w.tool('wasm-validate',[f])
        result=recover(f,out/('bad-should-not-recover-'+form+'.wasm'))
        assert result['status']=='trap_memory_changed'
        manifest['negative'].append({'file':f.name,**result})
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
    r=subprocess.run(['node',str(HERE/'check.cjs'),str(out)],capture_output=True,text=True,timeout=120)
    (out/'stdout.txt').write_text(r.stdout,encoding='utf8');(out/'stderr.txt').write_text(r.stderr,encoding='utf8')
    if r.returncode:raise RuntimeError(r.stderr)
    (out/'sha256.json').write_text(json.dumps({str(f.relative_to(out)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(out.rglob('*')) if f.is_file()},indent=2),encoding='utf8')
    print(r.stdout)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('command',choices=['run','transform','recover']);ap.add_argument('input');ap.add_argument('output',nargs='?');a=ap.parse_args()
    if a.command=='run':run(a.input)
    else:print(json.dumps((transform if a.command=='transform' else recover)(a.input,a.output)))
