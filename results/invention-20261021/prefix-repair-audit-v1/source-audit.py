"""Reproduction, separate interpreter, and recovery rejection controls."""
import argparse, copy, json, re, shutil, subprocess
from pathlib import Path
import prototype as p
import recover as r

def run(main,analysis,runtime,out):
    main,analysis,runtime,out=map(lambda x:Path(x).resolve(),(main,analysis,runtime,out))
    out.mkdir(parents=True,exist_ok=False)
    pins=[]
    for root,name,key in [(main,'pins.json',None),(analysis,'pins.json',None),(runtime,'protocol.json','pins')]:
        data=json.loads((root/name).read_text(encoding='utf-8'));data=data[key] if key else data
        for rel,digest in data.items():
            assert p.q.digest(root/rel)==digest,(root,rel)
        pins.append(dict(directory=str(root),verified=len(data)))
    manifest=json.loads((main/'manifest.json').read_text(encoding='utf-8'));replay=[];interpreter=[]
    for t in manifest['targets']:
        data,ops=p.parse(main/(t['name']+'.source.wasm'))
        dst=out/t['file']
        if t['opt']=='raw':
            if t['mode']=='plain':p.q.compile(p.wat(data,ops),dst)
            else:p.transform(main/(t['name']+'.source.wasm'),dst,t['mode'],t['seed'])
        else:
            raw=out/t['file'].replace('.O3.','.raw.')
            p.q.tool('wasm-opt',[raw,'-O3','--enable-bulk-memory','-o',dst]);p.q.w.tool('wasm-validate',[dst])
        assert dst.read_bytes()==(main/t['file']).read_bytes(),t['file']
        probe=out/t['probe'];p.probe(dst,probe)
        assert probe.read_bytes()==(main/t['probe']).read_bytes()
        replay.append(dict(file=t['file'],binary=True,probe=True))
        if t['mode']=='bad':continue
        actions=[0xffffffff,*range(len(ops)),len(ops),0xffffffff]
        mod=p.q.read(dst);logical=bytearray(data);expected=[]
        for j,fail in enumerate(actions):
            for k,(d,s,n) in enumerate(ops):
                if fail==k:break
                logical[d:d+n]=logical[s:s+n]
            h=2166136261
            for b in logical:h=((h^b)*16777619)&0xffffffff
            expected.append(h)
            mod+=p.q.w.parse('(module (func (export "step'+str(j)+'") (call 0 (i32.const '+str(fail)+'))) (func (export "state'+str(j)+'") (result i32) (call 1)))')[1:]
        interp=out/(dst.stem+'.interp.wasm');p.q.compile(p.q.w.emit(mod),interp)
        result=subprocess.run([str(p.ROOT/'.tools/wabt-1.0.42/bin/wasm-interp.exe'),str(interp),'--run-all-exports'],capture_output=True,text=True,timeout=30)
        assert result.returncode==0,result.stderr
        observed=[int(x) for x in re.findall(r'state\d+\(\) => i32:(\d+)',result.stdout)]
        assert observed==expected,(t['file'],observed,expected)
        traps=[]
        for j,fail in enumerate(actions):
            line=next(x for x in result.stdout.splitlines() if x.startswith('step'+str(j)+'()'))
            actual='error:' in line;assert actual==(fail<len(ops)),line;traps.append(actual)
        (out/(dst.stem+'.interp.log')).write_text(result.stdout+result.stderr,encoding='utf-8')
        interpreter.append(dict(file=t['file'],calls=len(actions),traps=sum(traps),digests_equal=True))
    controls=[]
    base=p.q.read(main/'swap16.211070.plain.raw.wasm')
    for name in ('exported-memory','memory-grow','extra-guard','parameter-data'):
        mod=copy.deepcopy(base);f=next(e for e in mod[1:] if e[0]=='func')
        if name=='exported-memory':mod.append(['export','"memory"',['memory','0']])
        if name=='memory-grow':f.append(['drop',['memory.grow',['i32.const','1']]])
        if name=='extra-guard':f.append(['if',['i32.eq',['local.get','0'],['i32.const','123']],['then',['i32.store8',['i32.const','0'],['i32.const','1']]]])
        if name=='parameter-data':f.append(['i32.store8',['i32.const','0'],['i32.xor',['i32.load8_u',['i32.const','0']],['i32.eq',['local.get','0'],['i32.const','123']]]])
        src=out/(name+'.wasm');p.q.compile(p.q.w.emit(mod),src)
        try:p.parse(src)
        except ValueError as exc:parse_reason=str(exc)
        else:raise AssertionError('profile accepted '+name)
        try:r.recover(src,out/(name+'.recovered.wasm'))
        except ValueError as exc:recover_reason=str(exc)
        else:raise AssertionError('recovery accepted '+name)
        controls.append(dict(name=name,valid_wasm=True,parse_rejection=parse_reason,recovery_rejection=recover_reason))
    # Preserve the concrete counterexample to the previous partition checker.
    oldpath=p.ROOT/'results/invention-20261021/prefix-repair-analysis-v3/source-recover.py'
    historical=None
    if oldpath.exists():
        old=p.module('prefix_repair_old_audit',oldpath)
        src=out/'parameter-data.wasm';old.recover(src,out/'historical-accepted.wasm')
        f=next(e for e in p.q.read(src)[1:] if e[0]=='func')
        original=next(e for e in base[1:] if e[0]=='func')
        actual,_=r.execute(f,16,123);expected,_=r.execute(original,16,123)
        assert actual!=expected
        historical=dict(old_sha256=p.q.digest(oldpath),old_accepted=True,unverified_input=123,state_differs=True,current_rejected=True)
    for name in ('audit.py','prototype.py','recover.py'):shutil.copy2(Path(__file__).with_name(name),out/('source-'+name))
    report=dict(pins=pins,replay=replay,interpreter=interpreter,controls=controls,historical_counterexample=historical)
    p.q.save(out/'audit.json',report)
    p.q.save(out/'pins.json',{str(f.relative_to(out)):p.q.digest(f) for f in out.rglob('*') if f.is_file()})
    print(json.dumps(dict(replayed=len(replay),interpreter_modules=len(interpreter),interpreter_calls=sum(x['calls'] for x in interpreter),controls=len(controls))))

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    for name in ('main','analysis','runtime','output'):ap.add_argument(name)
    a=ap.parse_args();run(a.main,a.analysis,a.runtime,a.output)
