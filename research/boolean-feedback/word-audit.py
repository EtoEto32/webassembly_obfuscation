"""Independent concrete semantics, byte replay and attack negative controls."""
import json
from pathlib import Path
import sys
from shared import h,load
import word
attack=load('bf_wa_attack',Path(__file__).with_name('word-attack.py'))
runner=load('bf_wa_runner',Path(__file__).with_name('word-run.py'))
sys.path.insert(0,str(h.ROOT/'.tools/encoding-synthesis-python'))
import z3


def symbolic(binary,args):
    mod=h.w.parse(h.w.tool('wasm2wat',[binary,'--fold-exprs']))
    if any(a[0] not in ('type','func','export') for a in mod[1:]):raise ValueError('Pure model required')
    f=next(a for a in mod[1:] if a[0]=='func');nl=sum(len(a)-1 for a in f[1:] if a[0]=='local');env=list(args)+[z3.BitVecVal(0,32)]*nl;stack=[]
    def walk(t):
        op=t[0]
        if op=='local.get':stack.append(env[int(t[1])]);return
        if op=='i32.const':stack.append(z3.BitVecVal(int(t[1]),32));return
        for a in t[1:]:
            if isinstance(a,list):walk(a)
        if op in ('local.set','local.tee'):
            env[int(t[1])]=stack.pop()
            if op=='local.tee':stack.append(env[int(t[1])])
        elif op in ('i32.add','i32.sub','i32.mul','i32.xor','i32.and','i32.or'):
            b,a=stack.pop(),stack.pop();stack.append({'i32.add':lambda:a+b,'i32.sub':lambda:a-b,'i32.mul':lambda:a*b,'i32.xor':lambda:a^b,'i32.and':lambda:a&b,'i32.or':lambda:a|b}[op]())
        else:raise ValueError(op)
    for t in f[1:]:
        if t[0] not in ('type','param','result','local'):walk(t)
    assert len(stack)==1
    return stack[0]


def main(base,adapt,out):
    base=Path(base).resolve();adapt=Path(adapt).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False)
    replays=[];wabt=[];proofs=[];args=[z3.BitVec('x'+str(i),32) for i in range(3)]
    for name,nodes in runner.FIXTURES.items():
        for mode in ('pipeline','feedback'):
            dest=out/(name+'-'+mode+'.wasm');word.transform(base/(name+'-plain.wasm'),dest,mode)
            assert dest.read_bytes()==(base/(name+'-'+mode+'-0.wasm')).read_bytes();replays.append(dest.name)
        reference=symbolic(base/(name+'-plain.wasm'),args)
        for opt in ('','-O3'):
            recovered=adapt/(name+opt+'-recovered.wasm');solver=z3.Solver();solver.set(timeout=15000);solver.add(reference!=symbolic(recovered,args));status=str(solver.check())
            proofs.append({'name':name,'optimization':opt or 'raw','status':status})
            if status!='unsat':raise AssertionError(proofs[-1])
            for mode in ('plain','pipeline','feedback'):
                src=base/(name+'-'+mode+('' if mode=='plain' else '-0')+opt+'.wasm');h.w.tool('wasm-validate',[src]);mod=h.w.parse(h.w.tool('wasm2wat',[src,'--fold-exprs']));expected=[]
                for j,values in enumerate(((0,0,0),(-1,-1,-1),(-2147483648,2147483647,1),(0x12345678,0x89abcdef,0x76543210))):
                    desired=[]
                    for node in nodes:desired.append(word.front.calc(node,desired,[v&h.MASK for v in values],32))
                    expected.append(desired[-1]);param=' '.join(f'(i32.const {v})' for v in values)
                    mod.append(h.w.parse(f'(module (func (export "probe{j}") (result i32) (call 0 {param})))')[1])
                dest=out/(src.stem+'-probe.wasm');h.save(h.w.emit(mod),dest);log=h.w.tool('wasm-interp',[dest,'--run-all-exports']);(out/(dest.stem+'.log')).write_text(log)
                for j,value in enumerate(expected):assert f'probe{j}() => i32:{value}' in log
                wabt.append({'file':src.name,'calls':4})
    # Necessary congruence hypothesis: a two-bit rotate example cycles.
    bad=[('xor',('p',0),('c',0)),('rotl',('n',0),('c',1)),('add',('n',1),('n',0))];states=[];s=[0,1,1]
    for _ in range(8):states.append(s);s=word.step(bad,[0],s,2)
    assert s!=[0,0,0]
    badsrc=out/'noncongruent.wasm';h.save('(module (func (export "run") (param i32) (result i32) (local i32 i32 i32) (local.set 1 (i32.xor (local.get 0) (i32.const 0))) (local.set 2 (i32.rotl (local.get 1) (i32.const 1))) (local.set 3 (i32.add (local.get 2) (local.get 1))) (local.get 3)))',badsrc)
    negatives=[]
    try:word.source(badsrc)
    except ValueError as e:negatives.append({'case':'internal_rotation','reason':str(e)})
    else:raise AssertionError('Invalid input accepted')
    dest=out/'short.wasm';h.save(word.render(3,runner.FIXTURES['muladd'],('n',2),'feedback').replace('(i32.const 128)','(i32.const 1)'),dest)
    try:attack.run(dest,out/'short-recovered.wasm')
    except ValueError as e:negatives.append({'case':'insufficient_rounds','reason':str(e)})
    else:raise AssertionError('Short schedule accepted')
    # Exact certificate must distinguish a changed recurrence, independently of random probes.
    fs=[('mul',('p',0),('p',1)),('add',('v',0),('p',2)),('mul',('v',1),('v',0))];rhs=attack.candidate_update(fs,(0,1,2))
    assert attack.bpoly(rhs[0])!=attack.bpoly(('xor',rhs[0],('c',1)))
    solver=z3.Solver();solver.add(args[0]!=(args[0]^1));assert solver.check()==z3.sat
    result={'replays':replays,'z3_version':z3.get_version_string(),'proofs':proofs,'negative_controls':negatives,'exact_certificate_mutation_rejected':True,'noncongruent_2bit':{'states':states,'after_8':s,'expected':[0,0,0]},'wabt':wabt,'wabt_calls':sum(r['calls'] for r in wabt)}
    (out/'audit.json').write_text(json.dumps(result,indent=2));print(json.dumps({'byte_replays':len(replays),'proofs':len(proofs),'wabt_calls':result['wabt_calls'],'negatives':len(negatives)}))

if __name__=='__main__':main(*sys.argv[1:])
