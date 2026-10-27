import argparse, copy, json, platform, random, re, shutil, subprocess
from pathlib import Path
import prototype as p

def oracle(f,x,y):
    caps=[(1<<b)-1 for b in f['bits']]
    s=[min(c,(x>>(8*i))&255) for i,c in enumerate(caps)]
    d=[min(c,(y>>(8*i))&255) for i,c in enumerate(caps)]
    for op in f['ops']:
        for i in range(8):s[i]=min(caps[i],s[i]+(d[i]&op['mask'][i])) if op['sign']=='+' else max(0,s[i]-(d[i]&op['mask'][i]))
    return sum(v<<(8*i) for i,v in enumerate(s))

def run(main,runtime,output):
    main,runtime,out=map(lambda x:Path(x).resolve(),(main,runtime,output));out.mkdir(parents=True,exist_ok=False)
    pins=[]
    for directory in (main,runtime):
        data=json.loads((directory/'pins.json').read_text())
        for rel,digest in data.items():assert p.q.digest(directory/rel)==digest,(directory,rel)
        pins.append(dict(directory=str(directory),verified=len(data)))
    manifest=json.loads((main/'manifest.json').read_text());replay=[];interpreter=[]
    samples=[(0,0),(-1,-1),(1,0),(0,1),(0x0102030405060708,0x0807060504030201),(0x7f807f807f807f80,0x0101010101010101),(0x8000000000000000,0x7fffffffffffffff),(0x0f3fff070103ff0f,0x0105030201040203)]
    for t in manifest['targets']:
        dst=out/t['file']
        if t['mode']=='recovered':
            learned=json.loads((main/(Path(t['file']).stem.replace('.recovered','')+'.learn.json')).read_text())
            p.recovered(learned['tables'],dst)
        elif t['opt']=='raw':p.transform(main/(t['name']+'.source.wasm'),dst,t['mode'])
        else:p.q.tool('wasm-opt',[out/t['file'].replace('.O3.','.raw.'),'-O3','--enable-simd','-o',dst])
        assert dst.read_bytes()==(main/t['file']).read_bytes(),t['file']
        replay.append(dict(file=t['file'],byte_equal=True))
        if t['mode']=='bad':continue
        mod=p.q.read(dst)
        for i,(x,y) in enumerate(samples):mod+=p.q.w.parse(f'(module (func (export "case{i}") (result i64) (call 0 (i64.const {x}) (i64.const {y}))))')[1:]
        probe=out/(dst.stem+'.interp.wasm');p.q.compile(p.q.w.emit(mod),probe)
        result=subprocess.run([str(p.ROOT/'.tools/wabt-1.0.42/bin/wasm-interp.exe'),str(probe),'--run-all-exports'],capture_output=True,text=True,timeout=30)
        assert result.returncode==0,result.stderr
        observed=[int(v) for v in re.findall(r'case\d+\(\) => i64:(\d+)',result.stdout)]
        expected=[oracle(manifest['fixtures'][t['name']],x,y) for x,y in samples]
        assert observed==expected,(t['file'],observed,expected)
        (out/(dst.stem+'.interp.log')).write_text(result.stdout+result.stderr,encoding='utf-8')
        interpreter.append(dict(file=t['file'],calls=len(samples),mismatches=0))
    controls=[];base=p.q.read(main/'small12.source.wasm')
    for name in ('extra-export','memory-effect','input-substitution','non-power-bound'):
        mod=copy.deepcopy(base);f=next(e for e in mod[1:] if e[0]=='func')
        if name=='extra-export':mod.append(['export','"other"',['func','0']])
        elif name=='memory-effect':
            mod.append(['memory','1','1']);f.insert(-1,['drop',['memory.grow',['i32.const','1']]])
        elif name=='input-substitution':
            e=next(e for e in p.q.walk(f) if e[0]=='i64x2.splat');e[1]=['local.get','1']
        else:
            e=next(e for e in p.q.walk(f) if e[0]=='i16x8.min_u');e[2]=p.q.w.parse('(module '+p.vc([14]*8)+')')[1]
        src=out/(name+'.wasm');p.q.compile(p.q.w.emit(mod),src)
        try:p.read(src)
        except ValueError as exc:controls.append(dict(name=name,valid_wasm=True,rejected=True,reason=str(exc)))
        else:raise AssertionError('accepted '+name)
    model=[]
    for width in range(3,9):
        M=(1<<width)-1
        for b in range(1,min(width,5)):
            A=1<<(width-b);L=(1<<b)-1;count=0
            for Y in range(M+1):
                for d in range(L+1):
                    assert min(M,Y+A*d)//A==min(L,Y//A+d)
                    assert max(0,Y-A*d)//A==max(0,Y//A-d)
                    count+=2
            model.append(dict(width=width,bits=b,comparisons=count))
    rng=random.Random(221024);full=0
    for b in range(1,9):
        A=1<<(16-b);L=(1<<b)-1
        pairs=[(Y,d) for Y in [0,A-1,A,65535-A,65534,65535] for d in [0,1,L]]
        pairs += [(rng.randrange(65536),rng.randrange(L+1)) for _ in range(2048)]
        for Y,d in pairs:
            assert min(65535,Y+A*d)//A==min(L,Y//A+d)
            assert max(0,Y-A*d)//A==max(0,Y//A-d)
            full+=2
    A=4096;Y=Z=A-1
    binary_counterexample=dict(A=A,Y=Y,Z=Z,decoded_sum=min(65535,Y+Z)//A,sum_decoded=Y//A+Z//A)
    assert binary_counterexample['decoded_sum']!=binary_counterexample['sum_decoded']
    # Broadcast probes alone cannot certify lane independence for arbitrary code.
    control=out/'cross-lane.wasm'
    p.q.compile('(module (func (export "run") (param i64 i64) (result i64) (i64.rotl (local.get 0) (i64.const 8))))',control)
    log=out/'cross-lane.learn.json'
    result=subprocess.run(['node',str(Path(__file__).with_name('learn.cjs')),str(control),str(log)],capture_output=True,text=True,timeout=30)
    assert result.returncode==0,result.stderr
    learned=json.loads(log.read_text());recovered=out/'cross-lane.recovered.wasm';p.recovered(learned['tables'],recovered)
    js='const fs=require("fs");let r=process.argv.slice(1).map(f=>new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(f))).exports.run(1n,0n));console.log(JSON.stringify(r.map(String)));'
    actual=json.loads(subprocess.check_output(['node','-e',js,str(control),str(recovered)],text=True))
    assert actual==['256','1'],actual
    limitation=dict(original_at_1=actual[0],learned_at_1=actual[1],queries=learned['queries'],reason='broadcast queries do not establish absence of cross-lane dependencies')
    env=dict(python=platform.python_version(),platform=platform.platform(),node=subprocess.check_output(['node','--version'],text=True).strip(),wabt=p.q.w.tool('wasm-interp',['--version']).strip(),binaryen=p.q.tool('wasm-opt',['--version']).strip())
    report=dict(pins=pins,replay=replay,interpreter=interpreter,controls=controls,model=model,model_comparisons=sum(r['comparisons'] for r in model),full_width_comparisons=full,binary_counterexample=binary_counterexample,learning_limitation=limitation,environment=env)
    p.q.save(out/'audit.json',report)
    for name in ('prototype.py','audit.py','learn.cjs'):shutil.copy2(Path(__file__).with_name(name),out/('source-'+name))
    p.q.save(out/'pins.json',{str(f.relative_to(out)):p.q.digest(f) for f in out.rglob('*') if f.is_file()})
    print(json.dumps(dict(replayed=len(replay),interpreter_calls=sum(r['calls'] for r in interpreter),model_comparisons=report['model_comparisons'],full_width_comparisons=full,controls=len(controls))))

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    for name in ('main','runtime','output'):ap.add_argument(name)
    a=ap.parse_args();run(a.main,a.runtime,a.output)
