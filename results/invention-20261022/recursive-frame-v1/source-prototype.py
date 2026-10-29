"""Restricted recursive frame transport experiment; no novelty/security claim."""
import argparse, hashlib, importlib.util, json, subprocess, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('sexpr',ROOT/'research/connectivity-elimination/prototype.py')
sx=importlib.util.module_from_spec(spec);spec.loader.exec_module(sx)
WABT=ROOT/'.tools/wabt-1.0.42/bin'; BINARYEN=ROOT/'.tools/binaryen-version_133/bin'
LOG=[]; MASK=(1<<32)-1
class Unsupported(ValueError):pass
def save(path,value):Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def tool(name,args,data=None):
    folder=BINARYEN if name=='wasm-opt' else WABT
    cmd=[str(folder/(name+'.exe')),*map(str,args)];start=time.perf_counter()
    r=subprocess.run(cmd,input=data,capture_output=True,timeout=60)
    LOG.append(dict(command=cmd,ms=(time.perf_counter()-start)*1000,code=r.returncode,stderr=r.stderr.decode('utf-8',errors='replace'),stdout_bytes=len(r.stdout)))
    if r.returncode:raise RuntimeError(LOG[-1])
    return r.stdout
def read(path):
    tool('wasm-validate',[path]);return sx.parse(tool('wasm2wat',[path,'--fold-exprs','--no-debug-names']).decode())
def canonical(text):
    b=tool('wat2wasm',['-','-o','-'],text.encode());return sx.parse(tool('wasm2wat',['-','--fold-exprs','--no-debug-names'],b).decode())
def compile(text,path):
    path=Path(path)
    if path.exists() or path.with_suffix('.wat').exists():raise FileExistsError(path)
    path.parent.mkdir(parents=True,exist_ok=True);path.with_suffix('.wat').write_text(text,encoding='utf-8')
    tool('wat2wasm',[path.with_suffix('.wat'),'-o',path]);tool('wasm-validate',[path])
def walk(e):
    if isinstance(e,list):
        yield e
        for v in e[1:]:yield from walk(v)
def c(n):return f'(i32.const {n & MASK})'
def g(n):return f'(local.get ${n})'
def op(o,a,b):return f'(i32.{o} {a} {b})'
def add(a,b):return op('add',a,b)
def sub(a,b):return op('sub',a,b)
def mul(a,b):return op('mul',a,b)
def setv(n,e):return f'(local.set ${n} {e})'
def pack(a,b):return f'(i64.or (i64.extend_i32_u {a}) (i64.shl (i64.extend_i32_u {b}) (i64.const 32)))'
def unpack(q):return f'(i32.wrap_i64 {q})',f'(i32.wrap_i64 (i64.shr_u {q} (i64.const 32)))'
def mv(m,x,y):return add(mul(m[0],x),mul(m[1],y)),add(mul(m[2],x),mul(m[3],y))
def iv(m,x,y):return sub(mul(m[3],x),mul(m[1],y)),sub(mul(m[0],y),mul(m[2],x))
def source_text(c1,c2,rot):return target_text(c1,c2,rot,'plain')
def target_text(c1,c2,rot,mode):
    if mode not in ('plain','fixed','dynamic','bad'):raise Unsupported('mode')
    enc=mode!='plain'; m=[g(x) for x in ('a','b','c','d')]
    x,y=iv(m,g('x'),g('y')) if enc else (g('x'),g('y'))
    bx,by=op('xor',x,c(c1)),add(y,c(c2));base=mv(m,bx,by) if enc else (bx,by)
    px,py=y,op('xor',x,add(op('rotl',y,c(rot)),mul(g('n'),c(c1))))
    statements=[]
    if enc:
        if mode in ('dynamic','bad'):
            statements += [setv('k',op('xor',g('x'),op('rotl',g('y'),g('n')))),setv('l',add(g('y'),g('n')))]
            statements += [setv('a1',add(g('a'),mul(g('k'),g('c')))),setv('b1',add(g('b'),mul(g('k'),g('d'))))]
            statements += [setv('c1',add(g('c'),mul(g('l'),g('a1')))),setv('d1',add(add(g('d'),mul(g('l'),g('b1'))),c(1)) if mode=='bad' else add(g('d'),mul(g('l'),g('b1'))))]
        else:statements += [setv(v,g(u)) for u,v in zip(('a','b','c','d'),('a1','b1','c1','d1'))]
        nm=[g(t) for t in ('a1','b1','c1','d1')];child=mv(nm,px,py)
        call=f'(call $work {sub(g("n"),c(1))} {child[0]} {child[1]} {" ".join(nm)})'
    else:call=f'(call $work {sub(g("n"),c(1))} {px} {py})'
    statements.append(setv('q',call));wx,wy=unpack(g('q'))
    if enc:wx,wy=iv(nm,wx,wy)
    qx,qy=add(wx,mul(g('n'),c(c2))),op('xor',wy,op('rotl',g('n'),c(5)))
    result=mv(m,qx,qy) if enc else (qx,qy)
    work=f'''(func $work (param $n i32) (param $x i32) (param $y i32)
    {''.join('(param $'+t+' i32)' for t in ('a','b','c','d')) if enc else ''} (result i64)
    {''.join('(local $'+t+' i32)' for t in ('k','l','a1','b1','c1','d1')) if enc else ''} (local $q i64)
    (if (result i64) (i32.eqz {g('n')}) (then {pack(*base)})
    (else {' '.join(statements)} {pack(*result)})))'''
    root=[c(v) for v in ([1,3,5,16] if mode=='fixed' else [1,0,0,1])]
    rx,ry=mv(root,g('x'),g('y')) if enc else (g('x'),g('y'))
    rootcall=f'(call $work (i32.and {g("n")} {c(31)}) {rx} {ry} {" ".join(root) if enc else ""})'
    if enc:
        out=iv(root,*unpack(g('q')));rb=setv('q',rootcall)+' '+pack(*out)
    else:rb=rootcall
    return f'''(module {work}
    (func (export "run") (param $n i32) (param $x i32) (param $y i32) (result i64) (local $q i64) {rb}))'''
def source_params(m):
    fs=[x for x in m[1:] if x[0]=='func']
    if any(x[0] not in ('type','func','export') for x in m[1:]) or len(fs)!=2:raise Unsupported('closed two-function module required')
    if [x for x in m[1:] if x[0]=='export']!=[['export','"run"',['func','1']]]:raise Unsupported('run ABI')
    branches=[x for x in walk(fs[0]) if x[0]=='then']
    if len(branches)!=1:raise Unsupported('one base branch')
    consts=[int(x[1]) & MASK for x in walk(branches[0]) if x[0]=='i32.const']
    rots=[x for x in walk(fs[0]) if x[0]=='i32.rotl']
    if len(consts)!=2 or len(rots)!=2 or rots[0][2][0]!='i32.const':raise Unsupported('source constants')
    pars=(*consts,int(rots[0][2][1]) & MASK)
    if not 1<=pars[2]<=31 or canonical(source_text(*pars))!=m:raise Unsupported('exact recursive source profile required')
    return pars
def transform(src,dst,mode):
    t=time.perf_counter();m=read(src);pars=source_params(m);t1=time.perf_counter();text=target_text(*pars,mode);t2=time.perf_counter();compile(text,dst);t3=time.perf_counter()
    return dict(mode=mode,parameters=pars,read_profile_ms=(t1-t)*1000,build_ms=(t2-t1)*1000,compile_validate_ms=(t3-t2)*1000,total_ms=(t3-t)*1000)
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('source');ap.add_argument('output');ap.add_argument('--mode',choices=['fixed','dynamic','bad'],default='dynamic');a=ap.parse_args();print(json.dumps(transform(a.source,a.output,a.mode)))
