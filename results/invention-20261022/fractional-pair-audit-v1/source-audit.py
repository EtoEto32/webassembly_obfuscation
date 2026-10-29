import argparse,json,platform,re,shutil
from pathlib import Path
import prototype as p

def expected(name,x,d):
    m=(1<<32)-1;h=0
    if name=='pair':return None if d==0 else (x//d<<32)|(x%d)
    for _ in range(16 if name=='chain' else 64):
        if name=='euclid' and d==0:break
        if d==0:return None
        q,r=divmod(x,d);h=(33*h+q)&m
        if name=='chain':x=((x<<7)|(x>>25))&m;x^=r;d=((d+h)&m)|1
        else:x,d=d,r
    return (x<<32)|h
def run(main,output):
    main,out=Path(main).resolve(),Path(output).resolve();out.mkdir(parents=True,exist_ok=False)
    pins=json.loads((main/'pins.json').read_text());assert all(p.q.digest(main/k)==v for k,v in pins.items())
    manifest=json.loads((main/'manifest.json').read_text());replay=[];interpreter=[]
    for t in manifest['targets']:
        file=out/t['file']
        if t['mode']=='recovered':p.recover(main/t['file'].replace('.recovered.wasm','.wasm'),file)
        elif t['opt']=='raw':p.transform(main/(t['name']+'.source.wasm'),file,t['mode'])
        else:p.q.tool('wasm-opt',[out/t['file'].replace('.O3.','.raw.'),'-O3','-o',file])
        assert file.read_bytes()==(main/t['file']).read_bytes();replay.append(t['file'])
        if t['mode']=='bad':continue
        mod=p.q.read(file);probes=[(0,0),(1,3),(0xffffffff,1),(0xffffffff,0xffffffff),(0x80000000,2),(1836311903,2971215073),(123456789,37),(0xffffffff,2)]
        for i,(x,d) in enumerate(probes):
            mod.append(p.q.w.parse(f'(module (func (export "probe{i}") (result i64) (call 0 (i32.const {x}) (i32.const {d}))))')[1])
        probe=out/(file.stem+'.interp.wasm');p.q.compile(p.q.w.emit(mod),probe)
        log=p.q.w.tool('wasm-interp',[probe,'--run-all-exports']);(probe.with_suffix('.log')).write_text(log,encoding='utf-8')
        lines=[line for line in log.splitlines() if line.startswith('probe')];assert len(lines)==len(probes)
        for i,((x,d),line) in enumerate(zip(probes,lines)):
            want=expected(t['name'],x,d)
            if want is None:assert 'error: integer divide by zero' in line,line
            else:assert re.search(r'i64:'+str(want)+r'$',line),line
        interpreter.append(dict(file=file.name,calls=len(probes)))
    # Valid but unsupported source/attack profiles. Retain their actual binaries.
    raw=p.fixture('pair');controls=[]
    cases=[('source-memory',raw.replace('(module ','(module (memory 1) '),'source'),
           ('source-signed',raw.replace('div_u','div_s').replace('rem_u','rem_s'),'source'),
           ('source-unpaired',raw.replace('(i32.rem_u (local.get 0) (local.get 1))','(i32.rem_u (local.get 1) (local.get 0))'),'source')]
    base=p.q.read(main/'pair.fraction.raw.wasm');func=next(x for x in base[1:] if x[0]=='func');body=func[-1]
    escape=json.loads(json.dumps(base));ef=next(x for x in escape[1:] if x[0]=='func');ef[-1]=p.op('i64.xor',ef[-1],p.get(2))
    cases.append(('escaping-packet',p.q.w.emit(escape),'recover'))
    corrupted=p.q.w.emit(base).replace('(i32.sub (local.get 1) (i32.const 1))','(i32.sub (local.get 1) (i32.const 2))')
    cases.append(('wrong-decoder',corrupted,'recover'))
    cases.append(('bad-bound',p.q.w.emit(p.q.read(main/'pair.bad.raw.wasm')),'recover'))
    for name,text,kind in cases:
        file=out/(name+'.wasm');p.q.compile(text,file)
        try:(p.transform if kind=='source' else p.recover)(file,out/(name+'.output.wasm'))
        except ValueError as e:controls.append(dict(name=name,rejected=True,reason=str(e)))
        else:raise AssertionError('control accepted '+name)
    result=dict(pins_verified=len(pins),replay_count=len(replay),replay=replay,interpreter=interpreter,interpreter_calls=sum(x['calls'] for x in interpreter),controls=controls,environment=dict(python=platform.python_version(),platform=platform.platform(),wabt=p.q.w.tool('wasm-validate',['--version']).strip(),binaryen=p.q.tool('wasm-opt',['--version']).strip()))
    p.q.save(out/'audit.json',result)
    for name in ('prototype.py','audit.py'):shutil.copy2(Path(__file__).with_name(name),out/('source-'+name))
    p.q.save(out/'pins.json',{str(f.relative_to(out)):p.q.digest(f) for f in out.rglob('*') if f.is_file()})
    print(json.dumps({k:result[k] for k in ('pins_verified','replay_count','interpreter_calls')}))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('main');ap.add_argument('output');a=ap.parse_args();run(a.main,a.output)
