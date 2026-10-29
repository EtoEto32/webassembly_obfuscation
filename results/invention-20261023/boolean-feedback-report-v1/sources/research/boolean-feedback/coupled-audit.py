import itertools
import json
from pathlib import Path
import random
import subprocess
import sys
import coupled
import prototype as base
from shared import h,a,load
attack=load('bf_ca_attack',Path(__file__).with_name('coupled-attack.py'))
saved=sys.modules.get('prototype');sys.modules['prototype']=h
verify=load('bf_ca_verify',h.HERE/'verify.py')
if saved is None:del sys.modules['prototype']
else:sys.modules['prototype']=saved
z3=verify.z3


def boolean_audit():
    rng=random.Random(20261023);count=0;accepted=0
    # One fixed input bit, two target bits and two independent external bits.
    # One external bit is a rotation of an internal word, to test overapproximation.
    keys=[0,32,64,39,96]
    def evaluate(bdd,node,bits):
        while node>=2:
            key,lo,hi=bdd.nodes[node];node=hi if bits[key] else lo
        return node
    for case in range(768):
        bdd=attack.BDD(seconds=10);maps=[]
        if case<256:
            def table(values,inputs):
                result=0
                for s,v in enumerate(values):
                    if not v:continue
                    term=1
                    for j,x in enumerate(inputs):term=bdd.binary('and',term,x if s>>j&1 else bdd.binary('xor',x,1))
                    result=bdd.binary('or',result,term)
                return result
            x,s0,s1,c0,c1=[bdd.mk(key,0,1) for key in keys];ft0=(case//16)%4;ft1=case%16
            f=[table([(ft0>>i)&1 for i in range(2)],[x]),table([(ft1>>i)&1 for i in range(4)],[x,s0])]
            errors=[bdd.binary('xor',v,z) for v,z in zip((s0,s1),f)];choice=(c0,c1,bdd.binary('xor',c0,c1),bdd.binary('and',c0,c1))[case//64]
            for j in range(2):
                na,nb=[table([(v>>j)&1 for v in N],errors) for N in coupled.FAMILIES[2]]
                maps.append(bdd.binary('xor',f[j],bdd.select(choice,na,nb)))
        else:
            for j in range(2):
                root=0
                for mon in range(32):
                    if rng.randrange(4):continue
                    term=1
                    for i,key in enumerate(keys):
                        if mon>>i&1:term=bdd.binary('and',term,bdd.mk(key,0,1))
                    root=bdd.binary('xor',root,term)
                maps.append(root)
        got=attack.certificate(bdd,maps,(0,1),1);expected=[];bounds=[]
        for x in (0,1):
            edges=[]
            for state in range(4):
                nexts=set()
                for a0,a1 in itertools.product((0,1),repeat=2):
                    bits={0:x,32:state&1,64:state>>1,39:a0,96:a1};nexts.add(sum(evaluate(bdd,r,bits)<<j for j,r in enumerate(maps)))
                edges.append(nexts)
            reach=set(range(4));found=None
            for steps in range(1,8):
                reach=set().union(*(edges[s] for s in reach))
                if len(reach)==1:
                    value=next(iter(reach))
                    if edges[value]=={value}:found=value;bounds.append(steps);break
            expected.append(found)
        assert (got is not None)==all(v is not None for v in expected)
        if got:
            accepted+=1;assert got['rounds']==max(bounds)
            for x in (0,1):assert sum(evaluate(bdd,r,{0:x})<<j for j,r in enumerate(got['values']))==expected[x]
        count+=1
    return {'cases':count,'accepted':accepted,'rejected':count-accepted,'mismatches':0}


def main(folder,adapt,out):
    folder=Path(folder).resolve();adapt=Path(adapt).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False);proofs=[];diagnostics=[];replays=0
    args=[z3.BitVec('x',32),z3.BitVec('y',32)]
    for row in json.loads((adapt/'attacks.json').read_text()):
        if row['status']!='recovered':continue
        solver=z3.Solver();solver.set(timeout=15000);solver.add(verify.symbolic(folder/(row['name']+'-plain.wasm'),args)!=verify.symbolic(row['output'],args));status=str(solver.check());proofs.append({'name':row['name'],'mode':row['mode'],'optimization':row['optimization'],'status':status})
        if status!='unsat':raise AssertionError(proofs[-1])
    for name in ('mix8','select10','chain12'):
        dest=out/(name+'-replay.wasm');coupled.transform(folder/(name+'-plain.wasm'),dest);assert dest.read_bytes()==(folder/(name+'-coupled.wasm')).read_bytes();replays+=1
        for opt in ('','-O3'):
            file=folder/(name+'-coupled'+opt+'.wasm');r,_=a.read(file);mod=h.w.parse(h.w.tool('wasm2wat',[file,'--fold-exprs']));mod.append(['export','"memory"',['memory','0']]);dest=out/(file.stem+'-diagnostic.wasm');h.save(h.w.emit(mod),dest);ap,old,new,cache,end,pages=h.layout(r);diagnostics.append({'file':str(dest),'name':name,'old':old,'end':end,'prefix':ap,'d':r['d']})
    (out/'diagnostics.json').write_text(json.dumps(diagnostics,indent=2));check=subprocess.run(['node',str(h.HERE/'scratch.cjs'),str(out/'diagnostics.json')],capture_output=True,text=True,timeout=180);(out/'scratch.stdout.log').write_text(check.stdout);(out/'scratch.stderr.log').write_text(check.stderr)
    if check.returncode:raise RuntimeError(check.stderr)
    # Two individually valid modes with an invalid state-dependent switching rule.
    f=[set(),h.add({()},h.var(1)),set()];err=[h.add(h.var(1+i),f[i]) for i in range(3)];selector=h.add({()},h.var(1));nf=[h.sub(v,err) for v in base.anf(base.N3,3)];maps=[h.add(fi,h.mul(selector,c)) for fi,c in zip(f,nf)]
    bad={'n':1,'d':3,'depth':8,'maps':[[list(m) for m in sorted(p)] for p in maps]};dest=out/'unsafe-switch.wasm';h.save(h.render(bad),dest);rejected=attack.run(dest,out/'unsafe-recovered.wasm')
    assert rejected['status']!='recovered';old=h.layout(bad)[1];mod=h.w.parse(h.w.tool('wasm2wat',[dest,'--fold-exprs']))
    mod.append(h.w.parse(f'(module (func (export "probe") (result i32) (drop (call 0 (i32.const 0))) (i32.load (i32.const {old+4}))))')[1]);probe=out/'unsafe-probe.wasm';h.save(h.w.emit(mod),probe);log=h.w.tool('wasm-interp',[probe,'--run-all-exports']);(out/'unsafe.log').write_text(log);assert 'probe() => i32:0' in log
    r,_=a.read(folder/'mix8-coupled.wasm');r['depth']=1;short=out/'short.wasm';h.save(h.render(r),short);short_result=attack.run(short,out/'short-recovered.wasm');assert short_result['status']=='bound_not_certified'
    result={'byte_replays':replays,'SMT':proofs,'scratch':json.loads(check.stdout),'certificate_crosscheck':boolean_audit(),'unsafe_switching':{'analysis':rejected,'actual_second_word_after8':0,'correct_second_word':4294967295},'short_round':short_result}
    (out/'audit.json').write_text(json.dumps(result,indent=2));print(json.dumps({'proofs':len(proofs),'replays':replays,'scratch':result['scratch']['calls'],'certificate_crosscheck':result['certificate_crosscheck'],'negative_statuses':[rejected['status'],short_result['status']]}))

if __name__=='__main__':
    if sys.argv[1]=='--certificate-only':
        path=Path(sys.argv[2]);assert not path.exists();result=boolean_audit();path.write_text(json.dumps(result,indent=2));print(json.dumps(result))
    else:main(*sys.argv[1:])
