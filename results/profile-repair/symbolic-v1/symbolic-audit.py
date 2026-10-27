"""Separate byte-lane evaluator for optimized actual binaries.

Shares only WABT/parser and Z3 dependencies with synthesis, not its transfer
functions, site indexing, or CEGIS algorithm. Still not a verified engine proof.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import time

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'.tools/encoding-synthesis-python'));import z3 as z
spec=importlib.util.spec_from_file_location('reader',ROOT/'research/connectivity-elimination/prototype.py');w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
X,Y=z.BitVecs('audit_x audit_y',32);R=z.Bool('audit_R_swizzle')


def evaluate(path,profile):
    w.tool('wasm-validate',[path]);mod=w.parse(w.tool('wasm2wat',[path,'--fold-exprs']))
    if any(e[0] not in ('type','func','export') for e in mod[1:]):raise ValueError('unsupported module')
    funcs=[e for e in mod[1:] if e[0]=='func']
    if len(funcs)!=1:raise ValueError('function count')
    f=funcs[0];types=[t for e in f[1:] if isinstance(e,list) and e[0]=='local' for t in e[1:]]
    params=[t for e in f[1:] if isinstance(e,list) and e[0]=='param' for t in e[1:]]
    if params!=['i32','i32'] or any(t not in ('i32','v128') for t in types):raise ValueError('type subset')
    local=[X,Y]+[[z.BitVecVal(0,8)]*16 if t=='v128' else z.BitVecVal(0,32) for t in types]
    body=[e for e in f[1:] if isinstance(e,list) and e[0] not in ('type','param','result','local')]
    def v(e):
        name=e[0]
        if name=='local.get':return local[int(e[1])]
        if name in ('local.tee','local.set'):
            value=v(e[2]);local[int(e[1])]=value;return value
        if name=='i32.const':return z.BitVecVal(int(e[1],0)&0xffffffff,32)
        if name=='i8x16.splat':return [z.Extract(7,0,v(e[1]))]*16
        if name=='v128.const':
            shape=e[1];width,count=map(int,shape[1:].split('x'))
            if width*count!=128 or len(e[2:])!=count:raise ValueError('vector constant')
            result=[]
            for token in e[2:]:
                bits=int(token,0)&((1<<width)-1)
                result.extend(z.BitVecVal((bits>>(8*i))&255,8) for i in range(width//8))
            return result
        if name in ('i8x16.relaxed_swizzle','i8x16.swizzle'):
            data=v(e[1]);indices=v(e[2]);result=[]
            for index in indices:
                selected=data[0]
                if not all(z.eq(data[0],a) for a in data):
                    selected=z.BitVecVal(0,8)
                    for j in range(16):selected=z.If((index&15)==j,data[j],selected)
                valid=z.ULT(index,16)
                if name=='i8x16.relaxed_swizzle':valid=z.Or(valid,z.And(profile,z.ULT(index,128)))
                result.append(z.simplify(z.If(valid,selected,z.BitVecVal(0,8))))
            return result
        if name=='i8x16.extract_lane_u':return z.ZeroExt(24,v(e[2])[int(e[1])])
        if name=='i32.eqz':return z.If(v(e[1])==0,z.BitVecVal(1,32),z.BitVecVal(0,32))
        if name=='select':
            a,b,cond=[v(x) for x in e[1:]];return z.If(cond!=0,a,b)
        a=v(e[1]);b=v(e[2])
        functions={'i32.and':lambda:a&b,'i32.or':lambda:a|b,'i32.xor':lambda:a^b,'i32.add':lambda:a+b,
            'i32.sub':lambda:a-b,'i32.mul':lambda:a*b,'i32.shl':lambda:a<<(b&31),'i32.shr_u':lambda:z.LShR(a,b&31),
            'i32.eq':lambda:z.If(a==b,z.BitVecVal(1,32),z.BitVecVal(0,32)),
            'i32.ne':lambda:z.If(a!=b,z.BitVecVal(1,32),z.BitVecVal(0,32)),
            'i32.lt_u':lambda:z.If(z.ULT(a,b),z.BitVecVal(1,32),z.BitVecVal(0,32))}
        if name not in functions:raise ValueError(name)
        return z.simplify(functions[name]())
    for statement in body[:-1]:v(statement)
    return v(body[-1])


def equivalence(reference,target):
    solver=z.Solver();solver.set(timeout=15000);solver.add(reference!=target);status=solver.check()
    if status==z.unknown:return {'status':'unknown','reason':solver.reason_unknown()}
    if status==z.unsat:return {'status':'unsat'}
    m=solver.model();return {'status':'sat','x':m.eval(X,model_completion=True).as_long(),'y':m.eval(Y,model_completion=True).as_long(),'profile':z.is_true(m.eval(R,model_completion=True))}


def main(source,optimized,out):
    out.mkdir(parents=True,exist_ok=False);shutil.copy2(__file__,out/'symbolic-audit.py');rows=[];start=time.perf_counter()
    try:
        records=json.loads((source/'results.json').read_text())['rows']
        for row in records:
            name=row['name'];ref=evaluate(source/(name+'-source.wasm'),z.BoolVal(False));targets=[]
            for mode in ('all','slice','independent','aware'):
                for folder,suffix in ((source,''),(optimized,'-O3')):
                    path=folder/(name+'-'+mode+suffix+'.wasm');result=equivalence(ref,evaluate(path,R));assert result['status']=='unsat',(str(path),result)
                    targets.append({'file':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),**result})
            rows.append({'name':name,'targets':targets})
        report={'rows':rows,'unsat':sum(len(r['targets']) for r in rows),'elapsedSeconds':time.perf_counter()-start,'z3':z.get_version_string(),'limitation':'All i32 inputs and two swizzle profiles in an independently coded finite expression model. Parser, symbolic transfer functions, optimizer and engines are not formally verified.'}
        (out/'results.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in report.items() if k!='rows'}))
    finally:
        (out/'sha256.json').write_text(json.dumps({str(f.relative_to(out)):hashlib.sha256(f.read_bytes()).hexdigest() for f in out.rglob('*') if f.is_file() and f.name!='sha256.json'},indent=2),encoding='utf8')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('optimized',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();main(a.source.resolve(),a.optimized.resolve(),a.output.resolve())
