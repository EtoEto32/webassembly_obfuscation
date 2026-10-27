import hashlib
import itertools
import json
from pathlib import Path
import random
import shutil
import subprocess
import sys
import prototype as p
import run
import certify


def main(src,perf,out):
    src,perf,out=map(Path,(src,perf,out));out.mkdir(parents=True,exist_ok=False);verified={}
    for folder in (src,perf):
        pins=json.loads((folder/'pins.json').read_text())
        for file,h in pins.items():assert hashlib.sha256((folder/file).read_bytes()).hexdigest()==h
        verified[folder.name]=len(pins)
    m=json.loads((src/'manifest.json').read_text());replay=[];certificates=[];groups={};interpreter=[]
    for t in m['targets']:
        if t.get('negative'):continue
        file=t['file'];dst=out/file
        if t['mode'].endswith('-recovered'):
            rep=p.recover(src/file.replace('-recovered',''),dst,8)
            groups.setdefault(t['name'],set()).add(tuple(rep['query']['values']))
        elif t['stage']=='O3':p.w.tool('wasm-opt',[out/file.replace('-O3',''),'-O3','-o',dst])
        elif t['mode']=='plain':
            v=m['models'][t['name']];p.save(p.emit(v['a'],v['b'],v['c']),dst)
        else:p.transform(src/(t['name']+'-plain.wasm'),dst,m['models'][t['name']]['shifts'],t['mode'])
        assert dst.read_bytes()==(src/file).read_bytes(),file
        replay.append(file)
        if not t['mode'].endswith('-recovered'):
            cert=certify.certify(src/file,8);certificates.append({'file':file,**cert})
            values=[];state=[0]*cert['n']
            for i in range(16):
                state=[(x+(b if i==0 else 0))&p.MASK for x,b in zip(p.vec(cert['a'],state),cert['b'])]
                values.append(sum(x*y for x,y in zip(cert['c'],state))&p.MASK)
            recorded=next(x for x in m['recoveries'] if x['file']==file)
            assert values==recorded['query']['values']
        # A separate engine runs a complete persistent sequence and reset.
        mod=p.w.parse(p.w.tool('wasm2wat',[src/file,'--fold-exprs']))
        ex={x[1]:int(x[2][1]) for x in mod[1:] if x[0]=='export'}
        for k,u in enumerate((1,0,0,0xffffffff,0x80000000,123,0,0)):
            body=([['call',str(ex['"reset"'])]] if k in (0,5) else [])
            body.append(['call',str(ex['"step"']),['i32.const',str(u)]])
            mod.append(['func',['export',f'"probe{k}"'],['result','i32'],*body])
        probe=out/(dst.stem+'-interpreter.wasm');p.save(p.w.emit(mod),probe)
        text=p.w.tool('wasm-interp',[probe,'--run-all-exports'])
        # reset export runs before the newly added probes, and is also present in output.
        values=[int(line.split('i32:')[1]) for line in text.splitlines() if line.startswith('probe')]
        ref=m['models'][t['name']];state=[0]*len(ref['a']);expected=[]
        for k,u in enumerate((1,0,0,0xffffffff,0x80000000,123,0,0)):
            if k in (0,5):state=[0]*len(state)
            state=[(x+b*u)&p.MASK for x,b in zip(p.vec(ref['a'],state),ref['b'])]
            expected.append(sum(x*y for x,y in zip(ref['c'],state))&p.MASK)
        assert values==expected,(file,text,expected)
        interpreter.append({'file':file,'values':values,'output':text})
    assert all(len(v)==1 for v in groups.values())
    # Exhaustive small-ring oracle, then random systems with zero divisors.
    rng=random.Random(20261022);solver_checks=[]
    for bits in (1,2,3,4):
        mod=1<<bits;cases=itertools.product(range(mod),repeat=6) if bits<=2 else (tuple(rng.randrange(mod) for _ in range(6)) for _ in range(512))
        count=0;inconsistent=0
        for v in cases:
            a=[list(v[:2]),list(v[2:4])];b=list(v[4:]);answer=p.solve(a,b,2,bits)
            exists=any(all(sum(x*y for x,y in zip(row,xs))%mod==z for row,z in zip(a,b)) for xs in itertools.product(range(mod),repeat=2))
            assert (answer is not None)==exists,(bits,a,b,answer)
            inconsistent+=not exists;count+=1
        solver_checks.append({'bits':bits,'systems':count,'inconsistent':inconsistent,'exhaustive':bits<=2})
    # Both transformation conditions are necessary for this proposed relation.
    rejects=[];v=m['models']['state3'];base=src/'state3-plain.wasm'
    for name,aa,cc in [('kernel',[row[:] for row in v['a']],v['c'][:]),('observer',[row[:] for row in v['a']],v['c'][:])]:
        if name=='kernel':aa[0][1]|=1
        else:cc[1]|=1
        binary=out/('reject-'+name+'.wasm');p.save(p.emit(aa,v['b'],cc),binary)
        try:p.transform(binary,out/('unexpected-'+name+'.wasm'),v['shifts'],'quotient')
        except ValueError as e:rejects.append({'name':name,'reason':str(e)})
        else:raise AssertionError(name)
    # Nonlinear exception invisible to the 16-step impulse experiment.
    mod=p.w.parse(p.w.tool('wasm2wat',[base,'--fold-exprs']))
    for x in mod[1:]:
        if x[0]=='export' and x[1]=='"step"':x[2][1]='2'
    mod.append(['func',['param','i32'],['result','i32'],['i32.add',['call','0',['local.get','0']],['i32.eq',['local.get','0'],['i32.const',str(0xdeadbeef)]]]])
    binary=out/'outside-input-exception.wasm';p.save(p.w.emit(mod),binary);dst=binary.with_stem(binary.stem+'-recovered');rec=p.recover(binary,dst,8)
    outside=[{'name':'input-exception','file':binary.name,'recovered':dst.name,'recovery':rec}]
    # Linear system with dimension17: impulse appears on step17.
    n=17;aa=[[int(i==j+1) for j in range(n)] for i in range(n)];bb=[1]+[0]*(n-1);cc=[0]*(n-1)+[1]
    binary=out/'outside-delay17.wasm';p.save(p.emit(aa,bb,cc),binary);dst=binary.with_stem(binary.stem+'-recovered');rec=p.recover(binary,dst,8)
    assert rec['model']['order']==0
    outside.append({'name':'delay17','file':binary.name,'recovered':dst.name,'recovery':rec})
    corrected=binary.with_stem(binary.stem+'-bound17');rec=p.recover(binary,corrected,17)
    assert rec['model']['order']==17
    delay={'file':binary.name,'recovered':corrected.name,'recovery':rec}
    for row in outside:
        try:certify.certify(out/row['file'],8)
        except ValueError as e:row['promise_rejected']=str(e)
        else:raise AssertionError('Promise checker accepted counterexample')
    (out/'controls.json').write_text(json.dumps({'outside':outside,'delay':delay},indent=2),encoding='utf8')
    r=subprocess.run(['node',str(p.HERE/'controls.cjs'),str(out)],capture_output=True,text=True,timeout=30,check=True)
    (out/'control-checks.json').write_text(r.stdout,encoding='utf8')
    # Repeat only the model fit: all variants within a family have identical data.
    timings=[]
    import time
    for name in groups:
        values=list(next(iter(groups[name])));durations=[]
        for i in range(31):
            start=time.perf_counter();result=p.recurrence(values,8);durations.append((time.perf_counter()-start)*1000)
        timings.append({'name':name,'durations_ms':durations,'order':result['order']})
    report={'verified_pins':verified,'byte_reproduced':replay,'certificates':certificates,'interpreter':interpreter,
            'solver':solver_checks,'rejects':rejects,'timings':timings,'identical_query_transcripts':{n:len(v) for n,v in groups.items()}}
    (out/'audit.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    for file in ('audit.py','certify.py','controls.cjs','prototype.py','query.cjs','run.py'):
        shutil.copyfile(p.HERE/file,out/('source-'+file))
    shutil.copyfile(p.HERE.parent/'connectivity-elimination/prototype.py',out/'source-wat-helper.py')
    pins={x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in out.iterdir() if x.is_file()}
    (out/'pins.json').write_text(json.dumps(pins,indent=2),encoding='utf8')
    print(json.dumps({'reproduced':len(replay),'certified':len(certificates),'interpreter_calls':8*len(interpreter),'solver':solver_checks,'rejected':rejects,'controls':json.loads(r.stdout)},indent=2))

if __name__=='__main__':main(*sys.argv[1:])
