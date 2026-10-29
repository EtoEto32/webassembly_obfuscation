import argparse,hashlib,json,math,random,re,shutil,statistics,subprocess
from pathlib import Path
import prototype as p
import recover as r
import run as producer


def small_models():
    rng=random.Random(221018);cases=0;calls=0;ambiguous=0
    for width in range(1,11):
        mod=1<<width
        for degree in range(1,13):
            for repeat in range(8):
                a=[rng.randrange(mod) for _ in range(degree+1)]
                def value(x):
                    y=0
                    for c in reversed(a):y=(y*x+c)%mod
                    return y
                vals=[(value(i+1)-value(i))%mod for i in range(degree)];bs=[a[0]]
                for k in range(1,degree+1):
                    f=math.factorial(k);v=(f&-f).bit_length()-1;d=vals[0]
                    if v>=width:assert d==0;bs.append(0)
                    else:
                        assert d%(1<<v)==0
                        bs.append(((d>>v)*pow(f>>v,-1,1<<(width-v)))%(1<<(width-v)))
                    vals=[(vals[i+1]-vals[i])%mod for i in range(len(vals)-1)]
                for x in range(mod):
                    falling=1;got=bs[0]
                    for k,b in enumerate(bs[1:],1):falling=falling*(x-k+1)%mod;got=(got+b*falling)%mod
                    assert got==value(x),(width,degree,x)
                    calls+=1
                cases+=1
    return dict(widths=[1,10],degrees=[1,12],coefficients_per_setting=8,cases=cases,all_residue_checks=calls)


def audit(main,perf,out):
    main,perf,out=map(lambda x:Path(x).resolve(),(main,perf,out));out.mkdir(parents=True,exist_ok=False)
    verified={}
    for folder in (main,perf):
        pins=json.loads((folder/'pins.json').read_text(encoding='utf-8'))
        for name,h in pins.items():assert p.q.digest(folder/name)==h,name
        verified[folder.name]=len(pins)
    producer.run(out/'reproduction');m=json.loads((main/'manifest.json').read_text(encoding='utf-8'))
    for t in m['targets']:assert (main/t['file']).read_bytes()==(out/'reproduction'/t['file']).read_bytes(),t['file']
    protected=[t for t in m['targets'] if t['mode'] in ('naive','delta')];spec=[]
    for t in protected:
        mod,fs,indices,_,_=r.inspect(main/t['file']);polys=[p.polynomial(fs[i]) for i in indices]
        for j,i in enumerate(indices):mod.append(['export','"step'+str(j)+'"',['func',str(i)]])
        file=out/'helpers'/t['file'];p.q.compile(p.q.w.emit(mod),file)
        spec.append(dict(file=str(file.relative_to(out)),source=m['fixtures'][t['name']],polynomials=polys))
    p.q.save(out/'helper-cases.json',spec)
    check=subprocess.run(['node',str(Path(__file__).with_suffix('.cjs')),str(out)],capture_output=True,text=True,timeout=60)
    (out/'helper.stderr.txt').write_text(check.stderr,encoding='utf-8')
    if check.returncode:raise RuntimeError(check.stderr)
    helpers=json.loads(check.stdout);p.q.save(out/'helpers.json',helpers)
    wabt=[];xs=[0,1,2,7,0x7fffffff,0x80000000,0xffffffff,0xaaaaaaaa]
    for t in m['targets']:
        if t['mode']=='bad':continue
        mod=p.q.read(main/t['file']);index=next(e[2][1] for e in mod[1:] if e[0]=='export')
        for i,x in enumerate(xs):mod.append(['func',['export','"case'+str(i)+'"'],['result','i32'],['call',index,['i32.const',str(x)]]])
        file=out/'wabt'/t['file'];p.q.compile(p.q.w.emit(mod),file)
        stdout=p.q.w.tool('wasm-interp',[file,'--run-all-exports']);file.with_suffix('.log').write_text(stdout,encoding='utf-8')
        for i,x in enumerate(xs):
            lines=[v for v in stdout.splitlines() if v.startswith('case'+str(i)+'()')]
            want=p.evaluate(m['fixtures'][t['name']],x)
            assert len(lines)==1 and re.search(r'=> i32:'+str(want)+r'\s*$',lines[0]),stdout
        wabt.append(dict(file=t['file'],calls=len(xs),mismatches=0))
    p.q.save(out/'wabt.json',wabt)
    rejects=[]
    def rejection(label,callback):
        try:callback()
        except ValueError as err:rejects.append(dict(label=label,error=str(err)))
        else:raise AssertionError('accepted '+label)
    mod=p.q.read(main/'cubic.source.wasm');mod.append(['export','"extra"',['func','0']]);file=out/'source-extra.wasm';p.q.compile(p.q.w.emit(mod),file)
    rejection('extra source export',lambda:p.transform(file,out/'must-not-exist-source.wasm'))
    mod=p.q.read(main/'cubic.delta.raw.wasm');fs=[e for e in mod[1:] if e[0]=='func'];f=fs[31]
    body=f[-1];f[-1]=['i32.add',body,['i32.const','1']];changed=out/'wrong-step31.wasm';p.q.compile(p.q.w.emit(mod),changed)
    rejection('inconsistent step31',lambda:r.recover(changed,out/'must-not-exist-step.wasm'))
    mod=p.q.read(main/'cubic.delta.raw.wasm');guard=next(e for e in p.q.walk(mod) if e[0]=='i32.ge_u');guard[2][1]='31'
    changed=out/'wrong-bound.wasm';p.q.compile(p.q.w.emit(mod),changed)
    rejection('driver skips high bit',lambda:r.recover(changed,out/'must-not-exist-bound.wasm'))
    p.q.save(out/'rejections.json',rejects)
    model=small_models();p.q.save(out/'models.json',model)
    tasks=[(t,k) for t in protected for k in range(5)];random.Random(221019).shuffle(tasks);attacks=[]
    for i,(t,k) in enumerate(tasks):
        file=out/'attacks'/f'{i:02}.wasm';a=r.recover(main/t['file'],file)
        assert file.read_bytes()==(main/(Path(t['file']).stem+'.recovered.wasm')).read_bytes()
        a.update(name=t['name'],mode=t['mode'],opt=t['opt'],repeat=k,file=t['file']);attacks.append(a)
    p.q.save(out/'attacks.json',attacks)
    summary=[]
    for name in m['fixtures']:
        for opt in ('raw','O3'):
            row=dict(name=name,opt=opt)
            for mode in ('naive','delta'):
                group=[a for a in attacks if a['name']==name and a['opt']==opt and a['mode']==mode]
                row[mode]={k:statistics.median(a[k] for a in group) for k in ('total_ms','integration_certificate_ms')}
            row['delta_over_naive']=row['delta']['total_ms']/row['naive']['total_ms'];summary.append(row)
    result=dict(verified_pins=verified,reproduced_targets=len(m['targets']),unique_positive_binaries=len({t['sha256'] for t in m['targets'] if t['mode']!='bad'}),helper_checks=helpers,wabt_calls=sum(v['calls'] for v in wabt),additional_rejections=len(rejects),models=model,attack_repetitions=len(attacks),attack_summary=summary,limitations='Model enumerates all inputs only at widths 1..10. Main inputs are full i32 samples. Reproduction and timing repeats are not additional independent programs.')
    p.q.save(out/'audit.json',result)
    snapshots=out/'sources';snapshots.mkdir()
    for f in [*Path(__file__).parent.glob('*.py'),*Path(__file__).parent.glob('*.cjs'),p.ROOT/'research/isotope-swizzle/prototype.py',p.ROOT/'research/connectivity-elimination/prototype.py']:
        shutil.copy2(f,snapshots/'__'.join(f.relative_to(p.ROOT).parts))
    p.q.save(out/'pins.json',{str(f.relative_to(out)):p.q.digest(f) for f in out.rglob('*') if f.is_file()})
    print(json.dumps(result))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('main');ap.add_argument('performance');ap.add_argument('output');a=ap.parse_args();audit(a.main,a.performance,a.output)
