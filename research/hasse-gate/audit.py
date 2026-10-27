"""Rebuild the actual experiment and probe a second Wasm execution engine."""
import argparse
import json
import re
from pathlib import Path
import prototype as p
from run import fixtures


def evaluate(d,root,x,y):
    vals=[]
    for n in d.nodes:
        if n[0]=='c':v=n[1]
        elif n[0]=='x':v=(x,y)[n[1]]
        elif n[0]=='add':v=vals[n[1]]+vals[n[2]]
        elif n[0]=='sub':v=vals[n[1]]-vals[n[2]]
        else:v=vals[n[1]]*vals[n[2]]
        vals.append(v&p.MASK)
    return vals[root]


def run(main,out):
    main=Path(main).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False)
    manifest=json.loads((main/'manifest.json').read_text(encoding='utf-8'))
    pins=json.loads((main/'pins.json').read_text(encoding='utf-8'))
    assert all(p.q.digest(main/name)==sha for name,sha in pins.items())
    replays=[]; probes=[]; cases={name:(k,d,r) for name,k,d,r in fixtures()}
    for name,(k,d,r) in cases.items():
        src=out/(name+'.source.raw.wasm');p.q.compile(p.emit(d,r),src)
        jet=out/(name+'.jet.raw.wasm');p.transform(src,jet,k)
        for f in (src,jet):
            assert f.read_bytes()==(main/f.name).read_bytes();replays.append(f.name)
            opt=out/(f.stem.replace('.raw','.O3')+'.wasm');p.q.tool('wasm-opt',[f,'-O3','-o',opt]);p.q.w.tool('wasm-validate',[opt])
            assert opt.read_bytes()==(main/opt.name).read_bytes();replays.append(opt.name)
    for t in manifest['targets']:
        dst=out/t['recovered'];p.recover(out/t['file'],dst)
        assert dst.read_bytes()==(main/t['recovered']).read_bytes();replays.append(dst.name)
        for f in (t['file'],t['recovered']):
            mod=p.q.read(out/f);expected=[]
            for i,(x,y) in enumerate([(0,1),(0x7fffffff,0x80000000),(0x80000001,0xfffffffe),(123456789,2654435761)]):
                mod.append(['func',['export','"probe'+str(i)+'"'],['result','i32'],['call','0',['i32.const',str(x)],['i32.const',str(y)]]])
                expected.append(evaluate(cases[t['name']][1],cases[t['name']][2],x,y))
            probe=out/(Path(f).stem+'.probe.wasm');p.q.compile(p.q.w.emit(mod),probe)
            stdout=p.q.w.tool('wasm-interp',[probe,'--run-all-exports'])
            actual=[int(n) for n in re.findall(r'probe\d+\(\) => i32:(\d+)',stdout)]
            assert actual==expected,(f,stdout,expected)
            probes.append(dict(file=f,expected=expected,actual=actual,stdout=stdout))
    small=[]
    for w in range(1,13):
        mod=1<<w;half=mod//2
        for x in range(mod):
            assert half*x*(x-1)%mod==0
            assert half*(2*x-1)%mod==half
        small.append(dict(width=w,inputs=mod))
    result=dict(input_pins=len(pins),byte_replays=len(replays),replays=replays,interpreter_probes=sum(len(x['actual']) for x in probes),probes=probes,
                null_function_models=small,source_hashes={str(f.relative_to(p.ROOT)):p.q.digest(f) for f in Path(__file__).parent.glob('*') if f.is_file()})
    p.q.save(out/'audit.json',result)
    print(json.dumps({k:result[k] for k in ('input_pins','byte_replays','interpreter_probes')}))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('main');ap.add_argument('output');a=ap.parse_args();run(a.main,a.output)
