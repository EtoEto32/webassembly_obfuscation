import json
from pathlib import Path
import random
import sys
import time
import attack
import prototype as p
sys.path.insert(0,str(p.ROOT/'.tools/encoding-synthesis-python'))
import z3


def symbolic(binary,args):
    mod=p.w.parse(p.w.tool('wasm2wat',[binary,'--fold-exprs']))
    if any(a[0] not in ('type','func','export') for a in mod[1:]):raise ValueError('Pure model required')
    f=next(a for a in mod[1:] if a[0]=='func');nl=sum(len(a)-1 for a in f[1:] if a[0]=='local')
    env=list(args)+[z3.BitVecVal(0,32)]*nl;stack=[]
    def walk(t):
        op=t[0]
        if op=='local.get':stack.append(env[int(t[1])]);return
        if op=='i32.const':stack.append(z3.BitVecVal(int(t[1]),32));return
        for a in t[1:]:
            if isinstance(a,list):walk(a)
        if op in ('local.set','local.tee'):
            env[int(t[1])]=stack.pop()
            if op=='local.tee':stack.append(env[int(t[1])])
        elif op in ('i32.xor','i32.and','i32.or','i32.rotl','i32.rotr'):
            b,a=stack.pop(),stack.pop()
            if op=='i32.xor':v=a^b
            elif op=='i32.and':v=a&b
            elif op=='i32.or':v=a|b
            elif op=='i32.rotl':v=z3.RotateLeft(a,b)
            else:v=z3.RotateRight(a,b)
            stack.append(v)
        else:raise ValueError('Unsupported verification op '+op)
    for a in f[1:]:
        if a[0] not in ('type','param','result','local'):walk(a)
    assert len(stack)==1
    return stack[0]


def main(base,adapt,out):
    base=Path(base).resolve();adapt=Path(adapt).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False)
    rng=random.Random(20261023);linear_cases=0
    for _ in range(512):
        basis={}
        for i in range(16):
            v,mask=attack.eliminate(rng.getrandbits(64),basis,1<<i)
            if v:basis[v.bit_length()-1]=(v,mask)
        v=rng.getrandbits(64);got=attack.eliminate(v,basis);rep=0
        for k in sorted(basis,reverse=True):
            if v>>k&1:v^=basis[k][0];rep^=basis[k][1]
        assert got==(v,rep);linear_cases+=1
    args=[z3.BitVec('x',32),z3.BitVec('y',32)];proofs=[]
    for row in json.loads((adapt/'attacks.json').read_text()):
        a=symbolic(base/(row['name']+'-plain.wasm'),args);b=symbolic(row['output'],args);solver=z3.Solver();solver.set(timeout=15000);solver.add(a!=b);start=time.perf_counter();status=solver.check()
        proof={'name':row['name'],'mode':row['mode'],'optimization':row['optimization'],'status':str(status),'ms':1000*(time.perf_counter()-start)}
        if status==z3.sat:proof['counterexample']=str(solver.model())
        elif status==z3.unknown:proof['reason']=solver.reason_unknown()
        proofs.append(proof)
        (out/'proofs.json').write_text(json.dumps(proofs,indent=2));print(json.dumps(proof),flush=True)
    solver=z3.Solver();solver.add(args[0]!=(args[0]^1));assert solver.check()==z3.sat
    interpreters=[]
    for name in ('mix8','select10','chain12'):
        source=symbolic(base/(name+'-plain.wasm'),args)
        for mode in ('plain','pipeline','linear','nonlinear'):
            for opt in ('','-O3'):
                src=base/(name+'-'+mode+opt+'.wasm');mod=p.w.parse(p.w.tool('wasm2wat',[src,'--fold-exprs']));expected=[]
                values=[(0,0),(-1,-1),(-2147483648,2147483647),(0x12345678,0x8badf00d)]
                for j,(x,y) in enumerate(values):
                    value=z3.simplify(z3.substitute(source,(args[0],z3.BitVecVal(x,32)),(args[1],z3.BitVecVal(y,32)))).as_long();expected.append(value)
                    mod.append(p.w.parse(f'(module (func (export "probe{j}") (result i32) (call 0 (i32.const {x}) (i32.const {y}))))')[1])
                dest=out/(src.stem+'-probe.wasm');p.save(p.w.emit(mod),dest);log=p.w.tool('wasm-interp',[dest,'--run-all-exports']);(out/(src.stem+'.log')).write_text(log)
                for j,value in enumerate(expected):assert f'probe{j}() => i32:{value}' in log,log
                interpreters.append({'file':src.name,'calls':4})
    result={'z3':z3.get_version_string(),'linear_algebra_crosschecks':linear_cases,'recovered_equivalence':proofs,'negative_control':'sat','wabt':interpreters,'wabt_calls':sum(r['calls'] for r in interpreters)}
    (out/'verification.json').write_text(json.dumps(result,indent=2));print(json.dumps({'proofs':len(proofs),'statuses':{s:sum(r['status']==s for r in proofs) for s in ('sat','unsat','unknown')},'wabt_calls':result['wabt_calls']}))

if __name__=='__main__':main(*sys.argv[1:])
